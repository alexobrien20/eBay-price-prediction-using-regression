import os 
import sys
import re
import time
from argparse import ArgumentParser
import ebaysdk
from ebaysdk.trading import Connection as Trading
from ebaysdk.exception import ConnectionError
import psycopg2
from psycopg2 import Error


def init_options():
    usage = "Init options"
    parser = ArgumentParser(description=usage)

    parser.add_argument("-d", "--debug", default=False,
                      help="Enabled debugging")
    parser.add_argument("-y", "--yaml", default='ebay.yaml',
                      help="Specifies the name of the YAML defaults file")
    parser.add_argument("-a", "--appid", default=None,
                      help="Specifies the eBay application id to use.")
    parser.add_argument("-n", "--domain",
                      dest="domain", default='svcs.ebay.com',
                      help="Specifies the eBay domain to use (e.g. svcs.sandbox.ebay.com).")

    args = parser.parse_args()
    return args
def connect_to_database(username,password,dbname):
    try:
        connection = psycopg2.connect(dbname=dbname,user=username,password=password)
        print("Connected to : {}".format(dbname))
        return connection
    except psycopg2.Error as error:
        print("Unable to connect to database called : ".format(dbname))
        print(error)

def insert_value_into_db(connection,cursor,item,tablename,itemID):
    columns = []
    item_keys = list(item.keys())
    for x in item_keys:
        columns.append('"' + x + '"')
    columns = ', '.join(columns)
    placeholders = ', '.join(["%s"] * len(item_keys))
    values = tuple(item.values()) + (itemID,)
    query = """UPDATE {} SET ({}) = ({}) WHERE "itemId" = %s""".format(tablename,columns,placeholders)
    try:
        cursor.execute(query,(values))
        connection.commit()
    except psycopg2.errors.UniqueViolation as e:
        connection.rollback()
        pass
    except psycopg2.errors.UndefinedColumn as e:
        print("This is running!")
        connection.rollback()
        print(e)
        error = e
        column_error = error.diag.message_primary
        column_name = column_error.split('"')[1]
        column_insert_name_value = column_name.join('""')
        datatype = type(item[column_name])
        if(datatype == str):
            datatype = 'TEXT'
        elif(datatype  == int):
            datatype = 'INT'
        elif(datatype  == float):
            datatype = 'FLOAT'
        elif(datatype  == bool):
            datatype = 'BOOLEAN'
        elif(datatype == list):
            str_value = str(item[column_name])
            item[column_name] = str_value
            datatype= 'TEXT'
        else:
            print("Datatype isn't TEXT, INT, FLOAT or BOOLEAN")
            print(datatype)
        try:
            print("Altering the table!")
            alter_table_query = 'ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} {}'.format(tablename,column_insert_name_value,datatype)
            cursor.execute(alter_table_query)
            connection.commit()
            print("New Colum has been added! called {} with datatype {}".format(column_insert_name_value,datatype))
            insert_value_into_db(connection,cursor,item,tablename,itemID)
        except psycopg2.Error as e:
            print("Error inside of Error")
            print(e)   

def item_to_flat_dictionary(item):
    empty_dict = {}
    for key1,val1 in item.items(): 
        if(type(val1) == dict):
            for key2, val2 in val1.items():
                if(type(val2) == dict):
                    for key3,val3 in val2.items():
                        if(type(val3) == dict):
                            print("There is a deeper dict")
                        else:
                            key = key1 + "." + key2 + "." + key3
                            empty_dict[key] = val3
                else:
                    key = key1 + "." + key2
                    empty_dict[key] = val2
        else:
            empty_dict[key1] = val1
        
    return empty_dict

def specifics_to_dict(item_specifics):
    empty_dict = {}
    if(type(item_specifics['NameValueList']) == dict):
        name = item_specifics['NameValueList']['Name']
        value = item_specifics['NameValueList']['Value']
        empty_dict[name] = value
        return empty_dict
    else:
        for item in item_specifics['NameValueList']:
            for key1,val1 in enumerate(item.items()):
                if(key1 == 0):
                    key = val1[1]
                elif(key1 == 1):
                    value = val1[1]
                else:
                    empty_dict[key] = value

        return empty_dict
    
def get_item_details(args, username, password,dbname,tablename):
    f = open('appId.txt')
    appId = f.read()
    connection_to_db = connect_to_database(username,password,dbname)
    cursor = connection_to_db.cursor()
    try:
        query = '''SELECT "itemId" FROM datatable'''
        cursor.execute(query)
        list_of_itemids = cursor.fetchall()
    except psycopg2.Error as error:
        print("Unable to retrieve itemID's from database : {}".format(dbname))
        print(error)

    try:
        api = Trading(config_file=args.yaml)
    except ConnectionError as e:
        print("There has been a connection error")
        print(e)
        print(e.response.dict())
    
    for counter,itemid in enumerate(list_of_itemids):
        if(counter % 50 == 0):
            start = time.time()
            print("Getting Information from Item : {} out of : {}".format(counter,len(list_of_itemids)))
        itemid = str(itemid).split(',')
        itemid = itemid[0].split('(')[1]
        itemid = int(itemid)
        api_request = {
            'ItemID' : itemid,
            'IncludeItemSpecifics' : True,
            'DetailLevel' : 'ReturnAll'
        }
        try:
            response = api.execute('GetItem',api_request)
            item_information = response.dict()['Item']
            item_specifics = item_information.pop('ItemSpecifics',None)
            if(item_specifics is not None):
                keys_to_keep = ['ListingDetails', 'Description','PictureDetails']

                relevant_information = {}
                for key in keys_to_keep:
                    relevant_information[key] = item_information.pop(key)

                relevant_information = item_to_flat_dictionary(relevant_information)
                item_specifics = specifics_to_dict(item_specifics)
                relevant_information.update(item_specifics) ##combines the three dictionaries together

                insert_value_into_db(connection_to_db,cursor,relevant_information,tablename,itemid)
                if(counter % 50 == 0):
                    end = time.time()
                    time_taken = (end - start) * counter
                    time_remaining = (end - start) * len(list_of_itemids) - time_taken
                    hours = int(time_remaining/3600)
                    mins = (time_remaining/60) % 60
                    print("Time Remaining Roughly : {} Hours and {} Minutes".format(hours, mins))
            else:
                print("Item specifics for item : {} does not exist! ".format(itemid))
                pass
        except ConnectionError as e:
            print("There has been a connection error")
            print(e)
            print(e.response.dict())
            pass 
            
    cursor.close()
    connection_to_db.close()

if __name__ == '__main__':
    try:
        f = open('dbinfo.txt','r')
        info = f.readlines()
        user = info[0].strip()
        password = info[1].strip() 
        f.close()
    except:
        print("There was an error reading your dbinfo file")  

    args = init_options()
    dbname = input(print("What is the name of the Database you want to use? : "))
    tablename = input(print("What is the name of the datatable that you want to use? : "))
    get_item_details(args,user,password,dbname,tablename)




        
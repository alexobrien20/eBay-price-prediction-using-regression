import os 
import sys
import re
from argparse import ArgumentParser
import ebaysdk
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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

def insert_value_into_db(connection,cursor,item,tablename):
    columns = []
    item_keys = list(item.keys())
    for x in item_keys:
        columns.append('"' + x + '"')
    columns = ', '.join(columns)
    placeholders = ', '.join(["%s"] * len(item_keys))
    #selling_state = re.sub(r"(\w)([A-Z])", r"\1 \2", item['sellingStatus.sellingState'])
    #item['sellingStatus.sellingState'] = selling_state
    values = tuple(item.values())
    insert_query = 'INSERT INTO {} ({}) VALUES ({})'.format(tablename,columns, placeholders)
    try:
        cursor.execute(insert_query, values)
        connection.commit()
    except psycopg2.errors.UniqueViolation as e:
        connection.rollback()
        pass
    except psycopg2.errors.UndefinedColumn as e:
        print("This is running!")
        print(item['itemId'])
        connection.rollback()
        print(e)
        error = e
        column_error = error.diag.message_primary
        column_name = column_error.split(' ')[1]
        column_name_value = column_name.replace('"','')
        datatype = type(item[column_name_value])
        if(datatype == str):
            datatype = 'TEXT'
        elif(datatype  == int):
            datatype = 'INT'
        elif(datatype  == float):
            datatype = 'FLOAT'
        elif(datatype  == bool):
            datatype = 'BOOLEAN'
        else:
            print("Datatype isn't TEXT, INT, FLOAT or BOOLEAN")
            print(value)
        try:
            print("Altering the table!")
            alter_table_query = 'ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} {}'.format(tablename,column_name,datatype)
            cursor.execute(alter_table_query)
            connection.commit()
            print("New Colum has been added! called {} with datatype {}".format(column_name,datatype))
            insert_value_into_db(connection,cursor,item,tablename)
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

def get_completed_findings_data(args, username, password,dbname,tablename):
    f = open('appId.txt')
    appId = f.read()
    connection_to_db = connect_to_database(username,password,dbname)
    cursor = connection_to_db.cursor()

    try:
        api = Finding(config_file=None,siteid='EBAY-GB',appid=appId,
                    domain=args.domain, debug = args.debug, warnings=True)
        
        api_requests = {
            'keywords': u'PlayStation 3 Console',
            'paginationInput': {
                'entriesPerPage': 100,
                'pageNumber': 1
            },
            'outputSelector':[
                'SellerInfo',
                'UnitPriceInfo',
                'StoreInfo',
                'PictureURLLarge',
                'AspectHistogram'
            ]
        }
        
        response = api.execute('findCompletedItems',api_requests)
        max_num_of_pages = int(response.dict()['paginationOutput']['totalPages'])
        if(max_num_of_pages > 100): ##ebay api only allows to search for max of 10,000 items, 100 items per page 
            max_num_of_pages = 100
        print("There is a total of : {} Pages".format(max_num_of_pages))
        print("Starting to pull information from all {} Pages".format(max_num_of_pages))

        for page in range(max_num_of_pages):
            api_requests = {
                'keywords': u'PlayStation 3 Console',
                'paginationInput': {
                    'entriesPerPage': 100,
                    'pageNumber': page + 1
                },
                'outputSelector':[
                    'SellerInfo',
                    'UnitPriceInfo',
                    'StoreInfo',
                    'PictureURLLarge',
                    'AspectHistogram'
                ]
            }
            response = api.execute('findCompletedItems',api_requests)
            item_results = response.dict()['searchResult']

            print("Inserting Page : {} Out of : {} Into Table : {} In Database : {}".format(page,max_num_of_pages,tablename, dbname))


            print("There are {} items on page {}".format(len(item_results['item']),page))

            for item in item_results['item']:
                item_flattened = item_to_flat_dictionary(item)
                insert_value_into_db(connection_to_db,cursor,item_flattened,tablename)


        cursor.close()
        connection_to_db.close()
        
    except ConnectionError as e:
        print("There has been a connection error")
        print(e)
        print(e.response.dict())

if __name__ == "__main__":
    try:
        f = open('dbinfo.txt','r')
        info = f.readlines()
        user = info[0].strip()
        password = info[1].strip() 
        f.close()
    except:
        print("There was an error reading your dbinfo file")  

    args = init_options()
    dbname = input(print("What do you want to call the database? : "))
    tablename = input(print("What do you want to call the table? : "))
    get_completed_findings_data(args,user,password,dbname,tablename)

    

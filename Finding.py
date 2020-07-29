import os 
import sys
from argparse import ArgumentParser
import ebaysdk
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError
import pandas as pd
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
        print("Unable to connect to database")
        print(error)

 def insert_value_into_db(connection,cursor,item_to_insert):
    columns = []
    item_keys = list(item.keys())
    for x in item_keys:
         columns.append('"' + x + '"')
    columns = ', '.join(columns)
    placeholders = ', '.join(["%s"] * len(item_keys))
    values = tuple(item.values())
    insert_query = 'INSERT INTO {} ({}) VALUES ({})'.format(tablename,columns, placeholders)
    cursor.execute(insert_query, values)
    connection.commit()

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

def get_completed_findings_data(args, username, password,dbname):

    connection_to_db = connect_to_database(username,password,dbname)
    cursor = connection_to_db.cursor()

    try:
        api = Finding(config_file=args.yaml,siteid='EBAY-GB',appid=opts.appid,
                    domain=opts.domain, debug = opts.debug, warnings=True)
        
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
        max_num_of_pages = response.dict()['paginationOutput']['totalPages']
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
            item_results = response.dict()['searchResults']
            flattened_results = item_to_flat_dictionary(item_results)

            print("Inserting Page : {} Out of : {} Into Table : {} In Database : {}".format(page,max_num_of_pages,tablename, dbname))

            for item in item_results['item']:
                item_flattened = item_to_flat_dictionary(item):
                insert_value_into_db(connection_to_db,cursor,item_flattened)

        cursor.close()
        connection_to_db.close()
        
    except ConnectionError as e:
        print("There has been a connection error")
        print(e)
        print(e.response.dict())

if __name__ = "__main__":
    

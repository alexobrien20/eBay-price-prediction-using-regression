import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database(user,password,dbname):
    try:
        con = psycopg2.connect(user=user, password=password)
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{}'".format(dbname))
        exists = cur.fetchone()
        if(not exists):
            sql_create_database = "create database {}".format(dbname)
            cur.execute(sql_create_database)
            print("Database called {} created".format(dbname))
        else:
            print("Database of name : {} already exists".format(dbname))
    except psycopg2.Error as error:
        print("Unable to connect to the database")
        print(error)
    finally:
        if(con):
            cur.close()
            con.close()
            print("PostgreSQL connection is closed")

def create_table(user,password,dbname,tablename):
    try:
        con = psycopg2.connect(dbname=dbname,user=user, password=password)
        cur = con.cursor()

        create_table_query = '''CREATE TABLE IF NOT EXISTS {}
        ("itemId" BIGINT PRIMARY KEY NOT NULL,
        "title" TEXT,
        "globalId" TEXT,
        "primaryCategory.categoryId" INT,
        "primaryCategory.categoryName" TEXT,
        "galleryURL" TEXT,
        "viewItemURL" TEXT,
        "paymentMethod" TEXT,
        "autoPay" BOOLEAN,
        "postalCode" TEXT,
        "location" TEXT,
        "country" TEXT,
        "sellerInfo.sellerUserName" TEXT,
        "sellerInfo.feedbackScore" INT,
        "sellerInfo.positiveFeedbackPercent" FLOAT,
        "sellerInfo.feedbackRatingStar" TEXT,
        "sellerInfo.topRatedSeller" BOOLEAN,
        "shippingInfo.shippingServiceCost._currencyId" TEXT,
        "shippingInfo.shippingServiceCost.value" FLOAT,
        "shippingInfo.shippingType" TEXT,
        "shippingInfo.shipToLocations" TEXT,
        "sellingStatus.currentPrice._currencyId" TEXT,
        "sellingStatus.currentPrice.value" FLOAT,
        "sellingStatus.convertedCurrentPrice._currencyId" TEXT,
        "sellingStatus.convertedCurrentPrice.value" FLOAT,
        "sellingStatus.bidCount" INT,
        "sellingStatus.sellingState" TEXT,
        "listingInfo.bestOfferEnabled" BOOLEAN,
        "listingInfo.buyItNowAvailable" BOOLEAN,
        "listingInfo.startTime" TIMESTAMP,
        "listingInfo.endTime" TIMESTAMP,
        "listingInfo.listingType" TEXT,
        "listingInfo.gift" BOOLEAN,
        "listingInfo.watchCount" INT,
        "condition.conditionId" INT,
        "condition.conditionDisplayName" TEXT,
        "isMultiVariationListing" BOOLEAN,
        "pictureURLLarge" TEXT,
        "topRatedListing" BOOLEAN,
        "productId._type" TEXT,
        "productId.value" BIGINT
,
        "listingInfo.buyItNowPrice._currencyId" TEXT,
        "listingInfo.buyItNowPrice.value" FLOAT,
        "listingInfo.convertedBuyItNowPrice._currencyId" TEXT,
        "listingInfo.convertedBuyItNowPrice.value" FLOAT,
        "storeInfo.storeName" TEXT, 
        "storeInfo.storeURL" TEXT,
        "unitPrice.type" TEXT,
        "unitPrice.quantity" FLOAT,
        "galleryPlusPictureURL" TEXT,
        "subtitle" TEXT);'''.format(tablename)

        cur.execute(create_table_query)
        con.commit()
        print("Table called {} created".format(tablename))
    except psycopg2.Error as error:
        print("Unable to connect to the database")
        print(error)
    finally:
        if(con):
            cur.close()
            con.close()
            print("PostgreSQL connection is closed")

if __name__ == '__main__':
    try:
        f = open('dbinfo.txt','r')
        info = f.readlines()
        user = info[0].strip()
        password = info[1].strip() 
        f.close()
    except:
        print("There was an error reading your dbinfo file")    
    dbname = input(print("What do you want to call the database? : "))
    tablename = input(print("What do you want to call the table? : "))
    create_database(user,password,dbname)
    create_table(user,password,dbname,tablename)

import pymongo
import time
import pprint
import argparse

input_ip = '218.107.249.34'
input_name = 'PGA-CN'

# obj_id = ObjectId('64e49a63d73cec290b49a0c8')

def get_ip_label_dict():
    client = pymongo.MongoClient('mongodb://joseph:RH4pgWKQv3f3N2cS@10.2.2.195:27017,10.2.2.198:27017,10.2.2.58:27017/?replicaSet=rs0', authSource='FCD',authMechanism='SCRAM-SHA-1')
    db = client["FCD"]
    collection = db["ip_label"]
    query = {
        'ip': input_ip
    }
    list_ip = list(collection.find(query))
    pprint.pprint(list_ip)


def modify_ip_label_dict():
    client = pymongo.MongoClient('mongodb://joseph:RH4pgWKQv3f3N2cS@10.2.2.195:27017,10.2.2.198:27017,10.2.2.58:27017/?replicaSet=rs0', authSource='FCD',authMechanism='SCRAM-SHA-1')
    db = client["FCD"]
    collection = db["ip_label"]

    filter_id = {'ip': input_ip}
    update_db = {'$set': {"ip_label": input_name}}

    collection.update_one(filter_id, update_db)


def add_ip_label_dict():
    client = pymongo.MongoClient('mongodb://joseph:RH4pgWKQv3f3N2cS@10.2.2.195:27017,10.2.2.198:27017,10.2.2.58:27017/?replicaSet=rs0', authSource='FCD',authMechanism='SCRAM-SHA-1')
    db = client["FCD"]
    collection = db["ip_label"]
    query = {
        'ip': input_ip,
        'ip_label': input_name
    }
    inserted_ip = collection.insert_one(query)
    print("Inserted ip:", inserted_ip.inserted_id)


if __name__ == "__main__":
    parse = argparse.ArgumentParser(description="DB args Parser")
    parse.add_argument('--modify', '-m', dest='modify_flag', help='Modify the content of the database', default=None)
    parse.add_argument('--add', '-a', dest='add_flag', help='Add item to the database', default=None)
    parse.add_argument('--query', '-q', dest='query_db_flag', help='Get item from the database', default=None)

    args, _ = parse.parse_known_args()
    print(args)
    if args.modify_flag == "y":
        modify_ip_label_dict()
        time.sleep(2)
        get_ip_label_dict()
    elif args.add_flag == "y":
        add_ip_label_dict()
        time.sleep(2)
        get_ip_label_dict()
    elif args.query_db_flag == "y":
        get_ip_label_dict()
    else:
        print("Nothing support !!!")

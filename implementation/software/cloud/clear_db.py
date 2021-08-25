from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client["database"]
storage = db["storage"]
orders = db["order"]
sensors = db["sensor"]

def initialize_database():
    storage.delete_many({})
    orders.delete_many({})
    sensors.delete_many({})
    print("DB initialized")

if __name__=='__main__':
    initialize_database()

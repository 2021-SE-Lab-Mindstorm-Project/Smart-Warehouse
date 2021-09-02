import json

from pymongo import MongoClient

settings_file = open("../../settings.json")
settings_data = json.load(settings_file)
settings_file.close()

client = MongoClient(settings_data['cloud']['db_address'], settings_data['cloud']['db_port'])
db = client[settings_data['cloud']['db_name']]
repository = db[settings_data['cloud']['db_repository_table_name']]
orders = db[settings_data['cloud']['db_order_table_name']]
sensors = db[settings_data['cloud']['db_sensor_table_name']]


def initialize_database():
    repository.delete_many({})
    orders.delete_many({})
    sensors.delete_many({})
    print("DB initialized")


if __name__ == '__main__':
    initialize_database()

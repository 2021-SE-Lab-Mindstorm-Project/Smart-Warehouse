import socket
import threading
import time
import pymongo
import json
from pymongo import MongoClient

client = MongoClient('localhost', 27018)
db = client["database"]
storage = db["storage"]
orders = db["order"]
sensors = db["sensor"]

edges = ['sorting', 'storage', 'shipment']

servers = []
ship_storage = 0
shipping_queue = []
INTERVAL = 5 #unit : seconds

def setInterval(interval, times = -1):
    # This will be the actual decorator,
    # with fixed interval and times parameter
    def outer_wrap(function):
        # This will be the function to be
        # called
        def wrap(*args, **kwargs):
            stop = threading.Event()

            # This is another function to be executed
            # in a different thread to simulate setInterval
            def inner_wrap():
                i = 0
                while i != times and not stop.isSet():
                    stop.wait(interval)
                    function(*args, **kwargs)
                    i += 1

            t = threading.Timer(0, inner_wrap)
            t.daemon = True
            t.start()
            return stop
        return wrap
    return outer_wrap


class cloud_server(threading.Thread):
    def __init__(self, port_num=8080):
        super().__init__()
        self.port_num = port_num
        self.edge_name = edges[port_num-27000]
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.port_num))
        self.client_socket = object()
        self.connection = 0
        print("init done")
    
    def run(self):
        self.server_socket.listen(5)
        print ("port" + str(self.port_num) + " open & listening")
        try:
            self.client_socket, self.address = self.server_socket.accept()
            self.connection = 1
            print ("I got a connection from ", self.address)
        except:
            self.connection = 0
            print ("connection failed")

        if self.port_num == 27000:
            while True:
                self.sorting2cloud()

        elif self.port_num == 27001:
            stopper = self.cloud2storage()
            while True:
                self.storage2cloud()

        elif self.port_num == 27002:
            self.shipment_is_ready = True
            stopper = self.cloud2shipment()
            while True:
                self.shipment2cloud()

        else:
            print("invalid port_num!")

    
    def receive(self):
        ret = self.client_socket.recv(4096).decode()
        print('received(json):', ret)
        return ret

    def send(self, data):
        if self.connection == 1:
            self.client_socket.send(data.encode())
            return True
        else:
            return False
    
    def update_sensor_db(self, data):
        print("SENSOR DB UPDATED : data from " + self.edge_name)
        for sensor in data:
            sensors.insert_one({
                'time': sensor['time'], 
                'ev3id': sensor['ev3id'],
                'sensor_name': sensor['sensor_name'],
                'value': sensor['value']})

    def sorting2cloud(self):
        #data format : {'red' : 00 , 'white': 00, 'yellow': 00}
        data_json = self.receive()
        data = json.loads(str(data_json))
        print(self.edge_name, data)
        if(data['type']=='sensor'):
            self.update_sensor_db(data['data'])
        elif(data['type']=='request'):
            for color in data['data']:
                for i in range(data['data'][color]):
                    storage.insert_one({'color':color})

    def storage2cloud(self):
        data_json = self.receive()
        data = json.loads(data_json)
        print(self.edge_name, data)
        if(data['type']=='sensor'):
            self.update_sensor_db(data['data'])
        elif(data['type']=='request'):
            for color in data['data']:
                storage.delete_one({'color':color})
                orders.find_one_and_update({'color':color, 'status':1},{ '$set' : {'status':2} }, sort=[('_id', pymongo.ASCENDING)])

    def shipment2cloud(self):
        data_json = self.receive()
        data = json.loads(data_json)
        print(self.edge_name, data)
        if(data['type']=='sensor'):
            self.update_sensor_db(data['data'])
        elif(data['type']=='request'):
            self.shipment_is_ready = True
            print("shipment is now READY")
            #data format : [{'color': color1, 'dest': dest1}, {'color': color1, 'dest': dest1}...]
            for order in data['data']:
                orders.find_one_and_update({'color':order['color'], 'dest':order['dest'], 'status':3},{ '$set' : {'status':4} }, sort=[('_id', pymongo.ASCENDING)])
           

    #request storage_edge to release items
    @setInterval(INTERVAL)
    def cloud2storage(self):
        recent_orders = list(orders.find({'status':0}))
        data = []
        for order in recent_orders:
            data.append(order['color'])
        data_json = json.dumps(data)
        if self.connection and data:
            self.client_socket.send(data_json.encode())
            orders.update_many({'status':0}, { '$set' : {'status':1} } )
            print(f'Requested {self.edge_name} to release {data_json}')
            return True
        else:
            return False

    #request shipmet_edge to ship items
    @setInterval(INTERVAL)
    def cloud2shipment(self):
        if not self.shipment_is_ready:
            print("shipment is NOT READY")
            return
        orders_stat2 = list(orders.find({'status':2}))
        data = []
        for order in orders_stat2:
            data.append({'color':order['color'], 'dest':order['dest']})
        data_json = json.dumps(data)
        
        if self.connection and data:
            self.client_socket.send(data_json.encode())
            orders.update_many({'status':2}, { '$set' : {'status':3} } )
            print(f'Requested {self.edge_name} to deliver {data_json}')
            self.shipment_is_ready = False
            return True
        else:
            return False

    def disconnect(self):
        # ASSERT(self.connection == 1)
        self.client_socket.close()
        self.connection = 0
        self.server_socket.close()
        print("socket to "+str(self.address)+"disconnected")
        self.exit()

def init():
    for i in range(3):
        while True:
            try:
                new_edge = cloud_server(27000+i)
                new_edge.start()
                servers.append(new_edge)
                break
            except:
                time.sleep(5)
                print('waiting for connection...')
                pass

    print("waiting for order...")



if __name__ == '__main__':
    init()

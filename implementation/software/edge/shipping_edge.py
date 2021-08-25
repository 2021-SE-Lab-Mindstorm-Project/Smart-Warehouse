import socket
import threading 
import time
import json

from socketio import server

ship_ev3 = object()

EtoE_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


ship_queue = []

class shippment_ev3_connection(threading.Thread):
    def __init__(self, port_num=5000):
        super().__init__()
        self.port_num = port_num
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("", self.port_num))
        self.client_socket = object()
        self.connection = 0
        print("init done")
    
    def run(self):
        self.server_socket.listen(5)
        print ("port" + str(self.port_num) + " open & listening")
        self.client_socket, self.address = self.server_socket.accept()
        self.connection = 1
        print ("Got a connection from", self.address)
    
    def wait_ack(self):
        ret = self.client_socket.recv(512).decode()
        return ret

    def ship(self, data):
        if self.connection == 1:
            self.client_socket.send(data.encode())
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

class connect_to_server(threading.Thread):
    def __init__(self, port_num=27000):
	    super().__init__()
	    self.port_num = port_num
	    self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    self.connection = 0
	    print("init done")

    def run(self):
        self.client_socket.connect(("169.56.76.12", self.port_num))
        self.connection = 1
        print ("connected to server")
        while 1:
            data = self.wait_command()
            self.req_shipment(data)
            time.sleep(10)
    

    # cloud => shipment_edge
    def req_shipment(self, data):
        global ship_ev3
        global ship_queue

        #data format : [{color: red, dest: 3} ... ]
        print(f'received: {data}')

        ship_queue.extend(data)
        shipped = []
        while True:
            if len(ship_queue) == 0:
                break

            if ship_ev3.ship('1') == False:
                print("Connecion ERROR")

            color = ship_ev3.wait_ack()
            dest = None

            for item_data in ship_queue:
                item_color = item_data['color']
                item_dest = item_data['dest']
                if item_color == color:
                    dest = item_dest
                    ship_queue.remove(item_data)
                    break

            if dest == None:
                print("Color ERROR")
            elif ship_ev3.ship(dest) == False:
                print("Connection Error")
            else:
                shipped.append({'color': color, 'dest': dest})
                EtoE_sock.send("True".encode())

        self.message(shipped)

    def wait_command(self):
        ret = self.client_socket.recv(512).decode()
        print(ret)
        ret = json.loads(ret)
        return ret

    def message(self, data):
        print("edge->cloud : requesting shipping update: " + str(data))
        data_to_server = {'type':'request', 'data': data}
        data_to_server = json.dumps(data_to_server)
        self.client_socket.send(data_to_server.encode())

def init():
    # connection to ev3
    global ship_ev3
    ship_ev3 = shippment_ev3_connection(5000)
    ship_ev3.start()

	# connection to cloud
    server_connectioon = connect_to_server(27002)
    server_connectioon.start()

    # sio.connect('http://169.56.76.12:'+target_port)
	
    # connect to storage edge server, check storage update
    EtoE_sock.connect(("143.248.41.213", 5004))

    ship_ev3.join()
    server_connectioon.join()

    # while 1:
    #     sensor_db = ship_ev3.wait_ack()
    #     # data reprocess
    #     server_connectioon.message_sensor(sensor_db)

# sio.emit('update_sensor_db', [{'time_stamp': 1, 'ev3_id': 'shipment', 'sensor_type':'color', 'value':0xFF0000}]) 

if __name__ == '__main__':
    init()

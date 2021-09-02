import json
import socket
import threading
import time

settings_file = open("../../settings.json")
settings_data = json.load(settings_file)
settings_file.close()

shipment_ev3 = object()
EtoE_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_connection = object()
ship_queue = []


class shippment_ev3_connection(threading.Thread):
    def __init__(self, port_num=5007):
        super().__init__()
        self.port_num = port_num
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("", self.port_num))
        self.client_socket = object()
        self.connection = 0
        self.color_ack = ''
        print("init done")

    def run(self):
        self.server_socket.listen(5)
        print("port" + str(self.port_num) + " open & listening")
        self.client_socket, self.address = self.server_socket.accept()
        self.connection = 1
        print("Got a connection from", self.address)
        while 1:
            self.wait_request()

    def wait_request(self):
        global server_connection
        ret = self.client_socket.recv(512).decode()
        ret = json.loads(ret)
        if ret['type'] == "sensor":
            server_connection.log_message(ret)
        elif ret['type'] == "request":
            while 1:
                print("ERROR:double ack from ev3")
                if self.color_ack == '':
                    break
            self.color_ack = ret['data']
        else:
            raise TypeError
        return ret

    def ship(self, data):
        if self.connection == 1:
            print("edge->cloud : requesting shipping complete update: " + str(data))
            data_to_server = {'type': 'request', 'data': data}
            data_to_server = json.dumps(data_to_server)
            self.client_socket.send(data_to_server.encode())
            return True
        else:
            return False

    def disconnect(self):
        # ASSERT(self.connection == 1)
        self.client_socket.close()
        self.connection = 0
        self.server_socket.close()
        print("socket to " + str(self.address) + "disconnected")
        self.exit()


class connect_to_server(threading.Thread):
    def __init__(self, port_num=5002):
        super().__init__()
        self.port_num = port_num
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = 0
        print("init done")

    def run(self):
        self.client_socket.connect((settings_data['cloud']['address'], self.port_num))
        self.connection = 1
        print("connected to server")
        while 1:
            data = self.wait_command()
            self.req_shipment(data)
            time.sleep(10)

    # cloud => shipment_edge
    def req_shipment(self, data):
        global shipment_ev3
        global ship_queue

        # data format : [{color: red, dest: 3} ... ]
        print(f'received: {data}')

        ship_queue.extend(data)
        shipped = []
        while True:
            if len(ship_queue) == 0:
                break

            if shipment_ev3.ship('1') == False:
                print("Connecion ERROR")

            color = ''
            while 1:
                if not shipment_ev3.color_ack == '':
                    color = shipment_ev3.color_ack
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
            elif shipment_ev3.ship(dest) == False:
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
        data_to_server = {'type': 'request', 'data': data}
        data_to_server = json.dumps(data_to_server)
        self.client_socket.send(data_to_server.encode())

    def log_message(self, data):
        print("edge->cloud : log " + str(data))
        data_to_server = {'type': 'sensor', 'data': data}
        data_to_server = json.dumps(data_to_server)
        self.client_socket.send(data_to_server.encode())


def init():
    # connection to ev3
    global shipment_ev3
    shipment_ev3 = shippment_ev3_connection(settings_data['shipment_edge'])
    shipment_ev3.start()

    # connection to cloud
    global server_connection
    server_connectioon = connect_to_server(settings_data['cloud']['service_port_shipment'])
    server_connectioon.start()

    # connect to repository edge server, check repository update
    EtoE_sock.connect(
        (settings_data['repository_edge']['address'], settings_data['repository_edge']['service_port_shipment']))

    shipment_ev3.join()
    server_connectioon.join()


# sio.emit('update_sensor_db', [{'time_stamp': 1, 'ev3_id': 'shipment', 'sensor_type':'color', 'value':0xFF0000}])

if __name__ == '__main__':
    init()

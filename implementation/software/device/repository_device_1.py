#!/usr/bin/env pybricks-micropython
import json
import socket
import time
from threading import Thread

from pybricks.ev3devices import Motor, ColorSensor
from pybricks.parameters import Port, Stop, Direction
from pybricks.tools import wait

# Initialize the motors.
belt_motor = Motor(Port.D, Direction.CLOCKWISE)
catch_motor = Motor(Port.C, Direction.CLOCKWISE)

# Initialize the sensor.
color_sensor = ColorSensor(Port.S1)

# Initialize the color num.
BLACK = 'Color.BLACK'
RED = 'Color.RED'
YELLOW = 'Color.YELLOW'
WHITE = 'Color.WHITE'

# Initialize the socket.
use_socket = True

settings_file = open("../../settings.json")
settings_data = json.load(settings_file)
settings_file.close()

if use_socket:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(
        (settings_data['repository_edge']['address'], settings_data['repository_edge']['service_port_1']))

catch_motor.reset_angle(0)

saw_object = False
object_list = []


def run_belt():
    belt_motor.run(180)


def watch_color():
    def check_same_stamp(object_buffer, time):
        if len(object_buffer) == 0:
            return False

        last_stamp = object_buffer[-1]

        if (time - last_stamp >= 1):
            return False

        return True

    color_buffer = []
    saw_black = True

    while True:
        color = color_sensor.color()
        if str(color) in (YELLOW, RED, WHITE):
            saw_black = False

            if (len(color_buffer) != 0) and (color_buffer[-1] != str(color)):
                color_buffer = []
                continue
            else:
                color_buffer.append(str(color))
                if (saw_black == False) and ((len(color_buffer)) < 20):
                    continue

            if saw_black or (not check_same_stamp(object_list, time.time())):
                object_list.append(time.time())
                color_buffer = []
                client_socket.send('white')

        elif str(color) == BLACK:
            saw_black = True


def catch_object():
    global object_list
    global saw_object

    while True:
        if len(object_list) > 0:

            if (time.time() - object_list[0] < 1.4):
                wait(10)
                continue
            else:
                wait(500)

            print("catching object..")
            print("object_count :", len(object_list))
            print()

            catch_motor.run_angle(200, -30, Stop.COAST, True)

            if use_socket:
                client_socket.recv(512).decode()
            else:
                wait(1500)

            print("releasing object..")
            print()

            catch_motor.run_angle(200, 30, Stop.COAST, True)

            del object_list[0]

            if use_socket:
                client_socket.send('True')


t1 = Thread(target=run_belt)
t1.start()

t2 = Thread(target=watch_color)
t2.start()

t3 = Thread(target=catch_object)
t3.start()

while True:
    pass

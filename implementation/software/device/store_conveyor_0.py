#!/usr/bin/env pybricks-micropython

from pybricks.ev3devices import Motor, ColorSensor, UltrasonicSensor
from pybricks import ev3brick
from pybricks.parameters import Port, Stop, Direction
from pybricks.tools import wait
from threading import Thread
import socket
import time

# Initialize the motors.
belt_motor = Motor(Port.D, Direction.COUNTERCLOCKWISE)
catch_motor = Motor(Port.C, Direction.CLOCKWISE)
combine_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)

# Initialize the sensor.
color_sensor = ColorSensor(Port.S1)

# Initialize the color num.
BLACK = 'Color.BLACK'
RED = 'Color.RED'
YELLOW = 'Color.YELLOW'
WHITE = 'Color.WHITE'

# Initialize the socket.
use_socket = True

if use_socket:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("143.248.41.213", 5002))

catch_motor.reset_angle(0)

saw_object = False
object_list = []
run_combine_belt = None

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

            if saw_black or (not check_same_stamp (object_list, time.time())):
                object_list.append(time.time())
                color_buffer = []
                client_socket.send('yellow')

        elif str(color) == BLACK:
            saw_black = True

def catch_object():
    global object_list
    global saw_object
    global run_combine_belt

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
            run_combine_belt = time.time()
            
            del object_list[0]

def combine_object():
    global run_combine_belt
    
    while True:
        if (run_combine_belt != None) and (time.time() - run_combine_belt > 0.4):
            combine_motor.run_time(400, 3000)
            run_combine_belt = None

            if use_socket:
                client_socket.send('True')

t1 = Thread(target = run_belt)
t1.start()

t2 = Thread(target = watch_color)
t2.start()

t3 = Thread(target = catch_object)
t3.start()

t4 = Thread(target = combine_object)
t4.start()

while True:
    pass
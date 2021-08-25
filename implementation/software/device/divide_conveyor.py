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
wheel_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
divide_motor = Motor(Port.B, Direction.CLOCKWISE)

# Initialize the sensor.
color_sensor = ColorSensor(Port.S1)
distance_sensor = UltrasonicSensor(Port.S2)

# Initialize the color num.
BLACK = 'Color.BLACK'
RED = 'Color.RED'
YELLOW = 'Color.YELLOW'
WHITE = 'Color.WHITE'

# Initialize the socket.
use_socket = True

# Initlalize constant variables.
BELT_MOTOR_SPEED = 180
DISTANCE_SENSOR_DISTANCE = 0
COLOR_SENSOR_COLOR = None

if use_socket:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("143.248.41.212", 5000))

catch_motor.reset_angle(0)

car_at_start = True

object_list = []
object_color = None

def run_belt():
    belt_motor.run(BELT_MOTOR_SPEED)

def watch_object():
    object_buffer = []
    global object_list
    global DISTANCE_SENSOR_DISTANCE

    def not_in_list():
        cond1 = (len(object_list) == 0)
        cond2 = ((len(object_list) > 0) and (time.time()-object_list[-1] > 1.5))

        return cond1 or cond2

    saw_belt = None
    wait_for_belt = False

    while True:
        distance = distance_sensor.distance()
        DISTANCE_SENSOR_DISTANCE = min(59, distance)

        if (56 < DISTANCE_SENSOR_DISTANCE < 60):
            object_buffer = []
            saw_belt = time.time()

            if wait_for_belt == True:
                print("two object now..")
                object_list = [time.time()-5]*2
                
            wait_for_belt = False

        elif (30 < DISTANCE_SENSOR_DISTANCE < 52) and not_in_list() and (wait_for_belt == False):
            if len(object_buffer) < 30:
                if len(object_buffer) > 0:
                    if time.time()-object_buffer[0] > 0.5:
                        object_buffer = []

                object_buffer.append(time.time())
                continue
            
            object_buffer = []
            object_list.append(time.time())

            if (time.time() - saw_belt > 1):
                wait_for_belt = True
                # object_list = [time.time()-5]*100


def catch_object():
    global object_list
    global car_at_start

    while True:
        if len(object_list) > 0:

            saw_time = object_list[0]

            if (time.time() - saw_time) < 1.0:  # new item
                continue
            else:                               # waiting item
                wait(500)
            
            print("catching object..")
            print("object_count :", len(object_list))
            print()

            del object_list[0]
                
            catch_motor.run_angle(200, -25, Stop.COAST, True)
            
            wait(1000)
            while car_at_start == False:
                wait(50)

            catch_motor.run_angle(200, 25, Stop.COAST, True)
            

def watch_color():
    global object_color
    global object_list
    global COLOR_SENSOR_COLOR

    color_buffer = []

    while True:
        color = color_sensor.color()

        if str(color) in (YELLOW, RED, WHITE, BLACK):

            if str(color) == BLACK:
                color_buffer = []
            elif (len(color_buffer) != 0) and (color_buffer[-1] != str(color)):
                color_buffer = []
            elif len(color_buffer) == 0:
                color_buffer.append(str(color))
            elif (len(color_buffer) < 15) and (color_buffer[-1] == str(color)):
                color_buffer.append(str(color))
            elif len(color_buffer) >= 15:
                object_color = color_buffer[-1]
                COLOR_SENSOR_COLOR = color_buffer[-1]

        wait(10)

def divide_object():
    global object_color
    global car_at_start
    global COLOR_SENSOR_COLOR

    while True:
        if object_color == None:
            continue

        print("dividing object..")
        print("object_color :", object_color)
        print()

        car_at_start = False
        COLOR_SENSOR_COLOR = None

        wheel_motor.position = 0
        wait(900)
        wheel_motor.run_angle(200, 95, Stop.COAST, True)

        if use_socket:
            while True:
                color_encode = object_color[6:].lower()
                client_socket.send(color_encode)
                ack = client_socket.recv(512).decode()
                if (ack == 'True'):
                    print("storage available..")
                    print()
                    break
                else:
                    print("storage full..")
                    time.sleep(1)

        if object_color == YELLOW: # right direction
            divide_motor.run_angle(200, 455, Stop.COAST, True)
        elif object_color == RED: # left direction
            divide_motor.run_angle(200, -465, Stop.COAST, True)
        else:
            pass

        wheel_motor.run_angle(250, 500, Stop.COAST, True)
        wait(100)

        if object_color == YELLOW:
            divide_motor.run_angle(200, -455, Stop.COAST, True)
        elif object_color == RED:
            divide_motor.run_angle(200, 465, Stop.COAST, True)
        else:
            pass

        car_at_start = True
        object_color = None


# def send_log():

#     def get_position(motor):
#         motor.position * (360 / motor.count_per_rot)

#     last_sent_time = time.time()-10
#     log_delay_time = 1
#     log_data = {'type': 'sensor', 'data': []}
    
#     while True:
#         time.sleep(log_delay_time)

#         belt_motor_log = {
#             'time': time.time(),
#             'ev3id': 'sort',
#             'motor_name': 'belt_motor_log',
#             'value': BELT_MOTOR_SPEED
#         }

#         catch_motor_log = {
#             'time': time.time(),
#             'ev3id': 'sort',
#             'sensor_name': 'catch_motor_log',
#             'value': get_position(catch_motor)
#         }

#         wheel_motor_log = {
#             'time': time.time(),
#             'ev3id': 'sort',
#             'sensor_name': 'wheel_motor',
#             'value': get_position(wheel_motor)
#         }

#         divide_motor_log = {
#             'time': time.time(),
#             'ev3id': 'sort',
#             'sensor_name': 'divide_motor',
#             'value': get_position(divide_motor)
#         }

#         color_sensor_log = {
#             'time': time.time(),
#             'ev3id': 'sort',
#             'sensor_name': 'color_sensor',
#             'value': COLOR_SENSOR_COLOR
#         }

#         distance_sensor_log = {
#             'time': time.time(),
#             'ev3id': 'sort',
#             'sensor_name': 'distance_sensor',
#             'value': DISTANCE_SENSOR_DISTANCE
#         }

#         log_data['data'].extend([belt_motor_log, catch_motor_log, wheel_motor_log, divide_motor_log, color_sensor_log, distance_sensor_log])
        
#         time.sleep(log_delay_time)

#         if time.time() - last_sent_time > 10:
#             client_socket.send(log_data)


t1 = Thread(target = run_belt)
t1.start()

t2 = Thread(target = watch_object)
t2.start()

t3 = Thread(target = catch_object)
t3.start()

t4 = Thread(target = watch_color)
t4.start()

t5 = Thread(target = divide_object)
t5.start()

# t6 = Thread(target = send_log)
# t6.start()
    
while True:
    pass

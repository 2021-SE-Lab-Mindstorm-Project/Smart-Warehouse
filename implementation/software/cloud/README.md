# Cloud Server
The cloud accepts connections to the server via sockets. Ports `27000`, `27001`, and `27002` are open for connection.
* Sorting Edge  (212) : 27000 port
* Storage Edge  (213) : 27001 port
* Shipment Edge (214) : 27002 port

To start the server:

1. Connect to the VM
2. Navigate to the socket folder `cd itrc-cloud/`
3. Run `python3 server.py`

## Database
MongoDB is used for the implementation. 

### SensorDB

|Fields|Type|Remarks|
|-------|-----|-----|
|time_stamp|timestamp||
|ev3_id|int|
|sensor_type|string|color, sonar|
|value|float|

### Order DB

|Fields|Type|Remarks|
|-------|-----|----|
|color|string|Red, Blue, Green|
|item|int|match item in storage db
|status|int|0 : order received|
|      |   |1 : requested storage to release, not released yet)|
|      |   |2 : released from storage, not requested shipment yet|
|      |   |3 : requested shipment edge to ship, not shipped yet|
|      |   |4 : order completed|

### Storage DB

|Fields|Type|Remarks|
|-------|-----|-----|
|color|string|Red, Blue, Green|
|stored|boolean|True, False|
|wear_time|timestamp| |



## Web Server
The web server is implemented by using Flask. The web server allows the customer to send an order by selecting the color and the destination or to check current stocks. 

To start the flask server:

1. Connect to the VM
2. Navigate to the flask folder `cd itrc-cloud/test/flask/`
3. Run `sudo python3 app.py` on the server to start the web server
4. Browse to `http://169.56.76.12:55555/` from a web browser

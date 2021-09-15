# EV3 Device

There are 3 kind of EV3s.

* Classification Device
* Repository Device
* Shipment Device

## Classification Device 
Classification Device uses 1 EV3 and `classification_device.py`. Classification Device receives the object for the first time, distinguish the color, and send it to Repository Device. The colors are divided into three categories: Yellow, White, and Red

## Repository Device
Repository Device uses 3 EV3s because they are classified into three colors. The relationship between the color, device num, file name is as follows.


|Color|Repository Device Num|File Name|
|-------|-----|-----|
|Yellow|0|`repository_device_0.py`|
|White|1|`repository_device_1.py`|
|Red|2|`repository_device_2.py`|

Repository Device saves the separated object, and send it to Shipment Edge upon request. 

## Shipment Device
Shipment Device uses 1 EV3 and `shipment_device.py`. Shipment Device collects the requested objects and deliver them to the delivery destination.

## How to Run
To start any file in EV3, use `brickrun -r --directory="DIRECTORY" "FILEPATH"`. Change `DIRECTORY` and `FILEPATH` to the appropriate path.

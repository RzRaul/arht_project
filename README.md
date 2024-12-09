
# Adjacent Room Heating Transfer Project 🔥❄

This is a project that uses ESP32 and DHT sensors to implement a solution for making adjacent room heating transfer studies. The scope of the project is to collect data from DHTs sensors that are connected to multiple ESP32 devices, via internet, so a server can take that data and process it to generate relevant information. This is with the idea in mind of taking decisions that can help accomodate one or multiple rooms to get certain behaviour, backed up with data.

In this repo the code is for the ESP32 clients that will be making the logging to the database. The Code for the server and the website will be in other repos.

> Note: Add repos when created

# General model 📡

For the general view, the multiple DHT sensors will be hooked up to multiple ESP32, and they will send via API calls the requests to write into the database. And a website will use the database to show visualizations, analysis, and more

```
                                            Orange pi Zero 2w        python flask
+---------------+      +-----------+      +------------------+      +-----------+
|  DHT Sensor 1 |      |           |      |                  |      |           |
|  DHT Sensor 2 | ---> |  ESP32 1  | ---> |   Database       | ---> |   Website |
|  DHT Sensor 3 |      |           |      |  (TCP  API)      |      |           |
+---------------+      +-----------+      +------------------+      +-----------+
                                      ^
                                      |
+---------------+      +-----------+  |
|               |      |           |  |
|  DHT Sensors  | ---> |  ESP32 2  |--+
|               |      |           |
+---------------+      +-----------+
                                      ^
                                      |
+---------------+      +-----------+  |
|               |      |           |  |
|  DHT Sensors  | ---> |  ESP32 3  |--+
|               |      |           |
+---------------+      +-----------+
```

## General Schematic for the ESP32 🔍
ESP32 will be powered from the USB port, which will provide around 4.7 volts in the VIN pin. 
This pin will be used as VCC for the DHT22 sensors, which work in the range of 3.3V - 5V.
Besides that, data lines for the sensors require a pull-up resistor of around 10K ohms, so internal 10K pull-up resistors will be enabled for the selected GPIOs.
![image](https://github.com/user-attachments/assets/6f7e28d9-e6cf-4632-b386-168e2b1ed50f)

### Cable connection 🔌
The connection is made with RJ11 (4 wires) and its respective connector
![image](https://github.com/user-attachments/assets/e40cfe30-0aad-4c02-83c6-c7f953bc4c49)

And these are the connectors </br>
![image](https://github.com/user-attachments/assets/f5b3d895-4a3d-44a1-939a-f83288e0adcf)

# Database model
![image](https://github.com/user-attachments/assets/620924e7-e06d-4f4d-b096-8ece9e5900c1)

# Website stack
For the website [Flask](https://flask.palletsprojects.com/en/stable/) will be used in order to take advantage of [Pandas](https://pandas.pydata.org/docs/) library 
Everything is running in the [Orange Pi Zero 2 W](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-Zero-2W.html)

# Technical details 
This codebase will be using Espressif IDF (IoT Development Framework) to achieve its porpuse. And will be programmed in C. 
> Site: https://idf.espressif.com

# Progress

![image](https://github.com/user-attachments/assets/149fd469-4099-4532-9e72-374b8af31535)

What it will look like </br>
![image](https://github.com/user-attachments/assets/3c80a949-79f1-4bb9-9145-5525c41f1597)
</br>
![image](https://github.com/user-attachments/assets/c218b509-729a-4250-8523-7bb7195d3a52)






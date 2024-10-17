
# Adjacent Room Heating Transfer Project 🔥❄

This is a project that uses ESP32 and DHT sensors to implement a solution for making adjacent room heating transfer studies. The scope of the project is to collect data from DHTs sensors that are connected to multiple ESP32 devices, via internet, so a server can take that data and process it to generate relevant information. This is with the idea in mind of taking decisions that can help accomodate one or multiple rooms to get certain behaviour, backed up with data.

In this repo the code is for the ESP32 clients that will be making the logging to the database. The Code for the server and the website will be in other repos.

> Note: Add repos when created

# General model 📡

For the general view, the multiple DHT sensors will be hooked up to multiple ESP32, and they will send via API calls the requests to write into the database. And a website will use the database to show visualizations, analysis, and more

```
+---------------+      +-----------+      +------------------+      +-----------+
|               |      |           |      |                  |      |           |
|  DHT Sensor 1 | ---> |  ESP32 1  | ---> |   Database       | ---> |   Website |
|               |      |           |      |  (TCP  API)      |      |           |
+---------------+      +-----------+      +------------------+      +-----------+
                                      ^
                                      |
+---------------+      +-----------+  |
|               |      |           |  |
|  DHT Sensor 2 | ---> |  ESP32 2  |--+
|               |      |           |
+---------------+      +-----------+
                                      ^
                                      |
+---------------+      +-----------+  |
|               |      |           |  |
|  DHT Sensor 3 | ---> |  ESP32 3  |--+
|               |      |           |
+---------------+      +-----------+
```

# Technical details
This codebase will be using Espressif IDF (IoT Development Framework) to achieve its porpuse. And will be programmed in C. 
> Site: https://idf.espressif.com


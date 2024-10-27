/* 
	DHT22 temperature sensor driver
*/

#ifndef DHT22_H_  
#define DHT22_H_

#define DHT_OK 0
#define DHT_CHECKSUM_ERROR -1
#define DHT_TIMEOUT_ERROR -2

typedef struct {
    gpio_num_t pin;
    float temp;
    float humidity;
}dht_data_t;

// == function prototypes =======================================

void 	set_dht_pin(int gpio);
void set_dht_pin( int gpio );
void 	errorHandler(int response);
int 	readDHT();
float 	getHumidity();
float 	getTemperature();
int 	getSignalLevel( int usTimeOut, bool state );

#endif
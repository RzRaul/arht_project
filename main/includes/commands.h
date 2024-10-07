#ifndef COMMANDS_H
#define COMMANDS_H
#include <string.h>
#include "driver/gpio.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "lwip/err.h"
#include "lwip/sockets.h"
#include "nvs_flash.h"
#include "DHT22.h"
#include "resources.h"

#define PORT 57006
#define COMMAND(X) (*X == 'R' || *X == 'W')
#define ELEMENT(X) (strcmp())
#define ARGS 6
#define COLONS ARGS-1
#define BUFF_LEN 254

#define DHT_PIN GPIO_NUM_32
//Custom protocol symbols
#define HEADER      "UABC"
#define USER_ID     "RRC"
#define OP_WRITE    'W'
#define OP_READ     'R'
#define ELEMENT_LED     'L'
#define ELEMENT_ADC     'A'
#define CMD_LOGIN       HEADER ":" USER_ID ":L:S:LoginCMD"
#define CMD_KEEP_ALIVE  "UABC:" USER_ID ":K:S:KeepAliveCMD"
#define KEEP_ALIVE_TIMEOUT 10
#define NACK_RESPONSE   "NACK"
#define ACK_RESPONSE    "ACK"

//Util symbols
#define BUFFER_SIZE 128
#define PORT 8266
#define PORT_UDP 8267

#define DEBUG 1

// #define SERVER_IP "82.180.173.228" //IoT server
// #define SERVER_IP "201.142.138.246" //Home server
#define SERVER_IP "192.168.1.113" //Local server
#define SECONDS_TO_TICKS(x) (x * 1000 / portTICK_PERIOD_MS) 


typedef struct {
    char* valids;
    uint8_t consider;
}optional_arg_t;

typedef enum {
    VALID_CMD,
    INVALID_HEADER,
    INVALID_OPERATION,
    INVALID_ELEMENT,
    INVALID_VALUE,
    INVALID
}cmd_valid_t;

void udp_server_task(void *pvParameters);
void setup_pins();
void dht_read_data();
void keep_alive_task(int *sock);
int process_command(char* command, int len);
void tcp_client_task(void* pvParameters);

#endif
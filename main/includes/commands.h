#ifndef COMMANDS_H
#define COMMANDS_H
#include "DHT22.h"
#include "driver/gpio.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "lwip/err.h"
#include "lwip/sockets.h"
#include "mdns.h"
#include "nvs_flash.h"
#include "resources.h"
#include <string.h>

#define COMMAND(X) (*X == 'R' || *X == 'W')
#define ELEMENT(X) (strcmp())
#define ARGS 6
#define COLONS ARGS - 1
#define BUFF_LEN 254
#define DHT_MAX_TRIES 5

#define DHT_PIN GPIO_NUM_32
// Custom protocol symbols
#define CMD_ASK_EMAIL "GET_INFO:"
#define KEEP_ALIVE_TIMEOUT 10
#define NACK_RESPONSE "NACK"
#define ACK_RESPONSE "ACK"

// Util symbols
#define BUFFER_SIZE 128
#define PORT 8266

#define DEBUG 1

// #define SERVER_IP "82.180.173.228" //IoT server
// #define SERVER_IP "201.142.138.246" //Home server
#define SERVER_IP "192.168.1.200" // Local server
#define SERVER_NAME "orangepi"    // Local server
#define SECONDS_TO_TICKS(x) (x * 1000 / portTICK_PERIOD_MS)

#define SENSORS_PER_DEVICE 5
#define PARAMETERS_PER_SENSOR 2
#define MEASURES_SAMPLING_TIME SECONDS_TO_TICKS(1200)

// float measures[SENSORS_PER_DEVICE * 2];

typedef struct {
    char *valids;
    uint8_t consider;
} optional_arg_t;

typedef enum {
    VALID_CMD,
    INVALID_HEADER,
    INVALID_OPERATION,
    INVALID_ELEMENT,
    INVALID_VALUE,
    INVALID
} cmd_valid_t;

void udp_server_task(void *pvParameters);
void print_sensors_pins();
void setup_pins_pullups();
void dht_read_data(float *measures);
void init_mDNS();
void periodic_send(int *sock);
int process_command(char *command, int len);
void tcp_client_task(void *pvParameters);
static esp_err_t resolve_hostname(const char *hostname,
                                  struct sockaddr_in *resolved_addr);

#endif

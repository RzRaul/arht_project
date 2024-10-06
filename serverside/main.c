#include <string.h>
#include "driver/gpio.h"vTaskDelay
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

#include "resources.h"

#define DEBUG 1

//Wifi Symbols
#define SSID "IoT_AP"
#define PASS "12345678"
#define MAX_RETRY 5
static int reconect_tries = 5;

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
#define ARGS 6
#define COLONS ARGS - 1

//Util symbols
#define BUFFER_SIZE 128
#define PORT 8266
#define SERVER_IP "82.180.173.228" //IoT server
// #define SERVER_IP "201.142.138.246" //Home server
// #define SERVER_IP "192.168.1.113" //Local server
#define SECONDS_TO_TICKS(x) (x * 1000 / portTICK_PERIOD_MS) 

const char* TAG = "TCP";
//Control variables
static int logged = 0;
static int keep_alive = 0;
static int connected_to_wifi = 0;
TaskHandle_t keep_alive_task_handle = NULL;

static void wifi_event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data){
    if(event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START){
        esp_wifi_connect();
    }else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_CONNECTED){
        ESP_LOGI("WIFI", "Connected to AP");
        connected_to_wifi = 1;
        reconect_tries = MAX_RETRY;
    }else if(event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED){
        ESP_LOGI("WIFI", "Disconnected from AP");
        if(reconect_tries > 0){
            esp_wifi_connect();
            reconect_tries--;
        }
    }else if(event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP){
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI("WIFI", "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));
    }else{
        ESP_LOGI("WIFI", "Unexpected event");
    }
}

void init_wifiSTA(){
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL, &instance_any_id);
    esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL, &instance_got_ip);
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = SSID,
            .password = PASS
        }
    };
    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_config);
    esp_wifi_start();
    esp_wifi_connect();
}

void keep_alive_task(int *sock){
    //Every 10 seconds Queue to the event handler so the TCP task will send the keep alive command
    while(1){
        vTaskDelay(SECONDS_TO_TICKS(1));
        send(*sock, CMD_KEEP_ALIVE, strlen(CMD_KEEP_ALIVE), 0);
        ESP_LOGI("KEEP_ALIVE", "Sent keep alive command");
        vTaskDelay(SECONDS_TO_TICKS(KEEP_ALIVE_TIMEOUT));
    }
}

int process_command(char* command, int len){
    if(!strncmp(command, ACK_RESPONSE, strlen(ACK_RESPONSE)) || !strncmp(command, NACK_RESPONSE, strlen(NACK_RESPONSE))){
        return -1;
    }
    uint8_t aux = 1;
    uint8_t args[ARGS] = {0};
    char buffer_temp[BUFFER_SIZE] = {0};
    strcpy(buffer_temp, command);
    if(DEBUG){
        ESP_LOGI("TCP", "Command: %s", buffer_temp);
    }
    for(uint8_t i = 0; i < len; i++){
        if(buffer_temp[i] == ':'){
            buffer_temp[i] = '\0';
            args[aux] = i + 1;
            aux++;
        }
    }
    if(aux < ARGS-1){
        return -2;
    }
    if(strncmp(buffer_temp, HEADER, strlen(HEADER)) ||
            strncmp(buffer_temp+args[1], USER_ID, strlen(USER_ID)) ){
            if(DEBUG){
                ESP_LOGW("TCP", "Invalid header or user id");
            }
        return -2;
    }else{
        if (buffer_temp[args[2]] == OP_WRITE){
            if(buffer_temp[args[3]] == ELEMENT_ADC){
                ESP_LOGW("TCP", "Writing to ADC (?)");
                return -2;
            }else{
                if(DEBUG){
                    ESP_LOGI("TCP", "Setting resource %c to %d", buffer_temp[args[3]], atoi(buffer_temp+args[4]));
                }
                return set_resource(buffer_temp[args[3]], atoi(buffer_temp+args[4]));
            }
        }else if(buffer_temp[args[2]] == OP_READ){
            return get_resource(buffer_temp[args[3]]);
        }
    }
    return 0;
}

void tcp_client_task(void* pvParameters){
    char rx_buffer[BUFFER_SIZE] = {0};
    char tx_buffer[BUFFER_SIZE] = {0};
    char host_ip[] = SERVER_IP;
    int addr_family = 0;
    int ip_protocol = 0;

    while (1) {
        struct sockaddr_in dest_addr;
        inet_pton(AF_INET, host_ip, &dest_addr.sin_addr);
        dest_addr.sin_family = AF_INET;
        dest_addr.sin_port = htons(PORT);
        addr_family = AF_INET;
        ip_protocol = IPPROTO_IP;
        int cmd_response=0;
        int len = 0;
        
        int sock = socket(addr_family, SOCK_STREAM, ip_protocol);

        if (sock < 0) {ESP_LOGE(TAG, "Unable to create socket: errno %d", errno); break;}

        ESP_LOGI(TAG, "Socket created, connecting to %s:%d", host_ip, PORT);

        int err = connect(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr));
        if (err != 0) {ESP_LOGE(TAG, "Socket unable to connect: errno %d", errno); break;}
        
        ESP_LOGI(TAG, "Successfully connected");
        xTaskCreate(keep_alive_task, "keep_alive", 4096, &sock, 5, &keep_alive_task_handle);
        vTaskSuspend(keep_alive_task_handle);

        while (1) {
            err = 0;
            bzero(rx_buffer, sizeof(rx_buffer));
            bzero(tx_buffer, sizeof(tx_buffer));
            if (!logged) {
                ESP_LOGI(TAG, "Sending login command");
                err = send(sock, CMD_LOGIN, strlen(CMD_LOGIN), 0);  
                len = recv(sock, rx_buffer, sizeof(rx_buffer) - 1, 0);
                if(len < 0){
                    ESP_LOGE(TAG, "recv failed: errno %d", errno);
                    break;
                }else{
                    rx_buffer[len] = 0;
                    if(!strncmp(rx_buffer, ACK_RESPONSE, strlen(ACK_RESPONSE))){
                        ESP_LOGI(TAG, "Logged in");
                        logged = 1;
                    }else{
                        ESP_LOGE(TAG, "Login failed");
                        break;
                    }
                }
                vTaskResume(keep_alive_task_handle);
            }
            if (err < 0) {ESP_LOGE(TAG, "Error occurred during sending: errno %d", errno); break;}

            len = recv(sock, rx_buffer, sizeof(rx_buffer) - 1, 0);
            if (len < 0) {ESP_LOGE(TAG, "recv failed: errno %d", errno); break;
            } else {
                rx_buffer[len] = 0;
                cmd_response = process_command(rx_buffer, len);
                if (cmd_response != -1){
                    if (cmd_response < 0) {
                        ESP_LOGE(TAG, "Invalid command received");
                        strncpy(tx_buffer, NACK_RESPONSE, strlen(NACK_RESPONSE));
                    } else{
                        ESP_LOGI(TAG, "RECEIVED FROM %s:", host_ip);
                        ESP_LOGI(TAG, "\'%s\'\n", rx_buffer);
                            strncpy(tx_buffer, ACK_RESPONSE, strlen(ACK_RESPONSE));
                            strcat(tx_buffer, ":");
                            itoa(cmd_response, tx_buffer + strlen(ACK_RESPONSE) + 1, 10);
                    }
                    if(DEBUG){
                        ESP_LOGI(TAG, "Sending response: %s\n", tx_buffer);
                    }
                    send(sock, tx_buffer, strlen(tx_buffer), 0);  
                } 
            }
        }
        if (sock != -1) {
            ESP_LOGE(TAG, "Shutting down socket and restarting...");
            shutdown(sock, 0);
            close(sock);
            vTaskDelete(keep_alive_task_handle);
            vTaskDelay(SECONDS_TO_TICKS(10));
        } else if (sock == 0) {
            ESP_LOGE(TAG, "Connection closed by server");
            vTaskSuspend(keep_alive_task_handle);
            logged = 0;
            vTaskDelay(SECONDS_TO_TICKS(10));
        }
   }
}

void app_main(void)
{
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_LOGI("MAIN", "Starting main function");
    init_wifiSTA();
    setupPins();
    setup_ledc_pwm();
    ESP_LOGI("MAIN", "Pins configured");
    while(!connected_to_wifi){
        vTaskDelay(1000);
        ESP_LOGI("MAIN", "Waiting for wifi to connect");
    }
    xTaskCreate(tcp_client_task, "TCPTask", 4096, NULL, 1, NULL);

    while(1){
        vTaskDelay(1000);
    }
 }

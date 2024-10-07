
#include "commands.h"

static const char *TAG_UDP = "UDP";
static const char* TAG_TCP = "TCP";
static const char* TAG_CMD = "CMD";
esp_err_t err_check;


//Control variables
static int logged = 0;
static int keep_alive = 0;
static int connected_to_wifi = 0;
TaskHandle_t keep_alive_task_handle = NULL;


optional_arg_t valid_args[COLONS] = {
    {.consider = 1, .valids = {"UABC"}},
    {.consider = 2, .valids = {"R","W"}},
    {.consider = 2, .valids = {"L","G"}},
    {.consider = 2, .valids = {"1","0"}},
};

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

void udp_server_task(void *pvParameters)
{
    char rx_buffer[BUFFER_SIZE] = {0};
    char tx_buffer[BUFFER_SIZE] = {0};
    char addr_str[BUFF_LEN];
    char host_ip[] = SERVER_IP;
    int addr_family = (int)pvParameters;
    int ip_protocol = 0;
    int cmd_response=0;
    struct sockaddr_in6 dest_addr;

    while (1) {

        struct sockaddr_in *dest_addr_ip4 = (struct sockaddr_in *)&dest_addr;
        dest_addr_ip4->sin_addr.s_addr = htonl(INADDR_ANY);
        dest_addr_ip4->sin_family = AF_INET;
        dest_addr_ip4->sin_port = htons(PORT_UDP);
        ip_protocol = IPPROTO_IP;

        int sock = socket(addr_family, SOCK_DGRAM, ip_protocol);
        if (sock < 0) {
            ESP_LOGE(TAG_UDP, "Unable to create socket: errno %d", errno);
            break;
        }
        ESP_LOGI(TAG_UDP, "Socket created");

        // Set timeout
        struct timeval timeout;
        timeout.tv_sec = 10;
        timeout.tv_usec = 0;
        setsockopt (sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof timeout);

        int err = bind(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr));
        if (err < 0) {
            ESP_LOGE(TAG_UDP, "Socket unable to bind: errno %d", errno);
        }
        ESP_LOGI(TAG_UDP, "Socket bound, port %d", PORT_UDP);

        struct sockaddr_storage source_addr; // Large enough for both IPv4 or IPv6
        socklen_t socklen = sizeof(source_addr);

        while (1) {
            ESP_LOGI(TAG_UDP, "Waiting for data");
            int len = recvfrom(sock, rx_buffer, sizeof(rx_buffer) - 1, 0, (struct sockaddr *)&source_addr, &socklen);
            // Error occurred during receiving
            if (len < 0) {
                ESP_LOGE(TAG_UDP, "recvfrom failed: errno %d", errno);
                break;
            }
            // Data received
            else {
                // Get the sender's ip address as string
                inet_ntoa_r(((struct sockaddr_in *)&source_addr)->sin_addr, addr_str, sizeof(addr_str) - 1);

                rx_buffer[len] = 0; // Null-terminate whatever we received and treat like a string...
                ESP_LOGI(TAG_UDP, "Received %d bytes from %s:", len, addr_str);
                ESP_LOGI(TAG_UDP, "%s", rx_buffer);
                // checkCommands(rx_buffer, len);

                cmd_response = process_command(rx_buffer, len);
                if (cmd_response != -1){
                    if (cmd_response < 0) {
                        ESP_LOGE(TAG_UDP, "Invalid command received");
                        strncpy(tx_buffer, NACK_RESPONSE, strlen(NACK_RESPONSE));
                    } else{
                        ESP_LOGI(TAG_UDP, "RECEIVED FROM %s:", addr_str);
                        ESP_LOGI(TAG_UDP, "\'%s\'\n", rx_buffer);
                            strncpy(tx_buffer, ACK_RESPONSE, strlen(ACK_RESPONSE));
                            strcat(tx_buffer, ":");
                            itoa(cmd_response, tx_buffer + strlen(ACK_RESPONSE) + 1, 10);
                    }
                    if(DEBUG){
                        ESP_LOGI(TAG_UDP, "Sending response: %s\n", tx_buffer);
                    }
                    // send(sock, tx_buffer, strlen(tx_buffer), 0);
                }  
            }
        }

        if (sock != -1) {
            ESP_LOGE(TAG_UDP, "Shutting down socket and restarting...");
            shutdown(sock, 0);
            close(sock);
        }
    }
    vTaskDelete(NULL);
}

void setup_pins(){

    set_dth_pin(GPIO_NUM_32);
}
void dht_read_data(){
    ESP_LOGD(TAG_CMD,"DHT Sensor Readings\n" );
    int ret = readDHT();
    
    errorHandler(ret);

    ESP_LOGD(TAG_CMD,"Humidity %.2f %%\n", getHumidity());
    ESP_LOGD(TAG_CMD,"Temperature %.2f degC\n\n", getTemperature());
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

        if (sock < 0) {ESP_LOGE(TAG_TCP, "Unable to create socket: errno %d", errno); break;}

        ESP_LOGI(TAG_TCP, "Socket created, connecting to %s:%d", host_ip, PORT);

        int err = connect(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr));
        if (err != 0) {ESP_LOGE(TAG_TCP, "Socket unable to connect: errno %d", errno); break;}
        
        ESP_LOGI(TAG_TCP, "Successfully connected");
        xTaskCreate(keep_alive_task, "keep_alive", 4096, &sock, 5, &keep_alive_task_handle);
        vTaskSuspend(keep_alive_task_handle);

        while (1) {
            err = 0;
            bzero(rx_buffer, sizeof(rx_buffer));
            bzero(tx_buffer, sizeof(tx_buffer));
            if (!logged) {
                ESP_LOGI(TAG_TCP, "Sending login command");
                err = send(sock, CMD_LOGIN, strlen(CMD_LOGIN), 0);  
                len = recv(sock, rx_buffer, sizeof(rx_buffer) - 1, 0);
                if(len < 0){
                    ESP_LOGE(TAG_TCP, "recv failed: errno %d", errno);
                    break;
                }else{
                    rx_buffer[len] = 0;
                    if(!strncmp(rx_buffer, ACK_RESPONSE, strlen(ACK_RESPONSE))){
                        ESP_LOGI(TAG_TCP, "Logged in");
                        logged = 1;
                    }else{
                        ESP_LOGE(TAG_TCP, "Login failed");
                        break;
                    }
                }
                vTaskResume(keep_alive_task_handle);
            }
            if (err < 0) {ESP_LOGE(TAG_TCP, "Error occurred during sending: errno %d", errno); break;}

            len = recv(sock, rx_buffer, sizeof(rx_buffer) - 1, 0);
            if (len < 0) {ESP_LOGE(TAG_TCP, "recv failed: errno %d", errno); break;
            } else {
                rx_buffer[len] = 0;
                cmd_response = process_command(rx_buffer, len);
                if (cmd_response != -1){
                    if (cmd_response < 0) {
                        ESP_LOGE(TAG_TCP, "Invalid command received");
                        strncpy(tx_buffer, NACK_RESPONSE, strlen(NACK_RESPONSE));
                    } else{
                        ESP_LOGI(TAG_TCP, "RECEIVED FROM %s:", host_ip);
                        ESP_LOGI(TAG_TCP, "\'%s\'\n", rx_buffer);
                            strncpy(tx_buffer, ACK_RESPONSE, strlen(ACK_RESPONSE));
                            strcat(tx_buffer, ":");
                            itoa(cmd_response, tx_buffer + strlen(ACK_RESPONSE) + 1, 10);
                    }
                    if(DEBUG){
                        ESP_LOGI(TAG_TCP, "Sending response: %s\n", tx_buffer);
                    }
                    send(sock, tx_buffer, strlen(tx_buffer), 0);  
                } 
            }
        }
        if (sock != -1) {
            ESP_LOGE(TAG_TCP, "Shutting down socket and restarting...");
            shutdown(sock, 0);
            close(sock);
            vTaskDelete(keep_alive_task_handle);
            vTaskDelay(SECONDS_TO_TICKS(10));
        } else if (sock == 0) {
            ESP_LOGE(TAG_TCP, "Connection closed by server");
            vTaskSuspend(keep_alive_task_handle);
            logged = 0;
            vTaskDelay(SECONDS_TO_TICKS(10));
        }
   }
}

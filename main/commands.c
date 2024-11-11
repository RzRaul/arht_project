
#include "commands.h"
#include "my_wifi.h"

static const char *TAG_UDP = "UDP";
static const char* TAG_TCP = "TCP";
static const char* TAG_CMD = "CMD";
esp_err_t err_check;


//Control variables
static int logged = 0;
static int keep_alive = 0;
static int connected_to_wifi = 0;
int power_saving_mode = 0;
uint8_t dht_pins[SENSORS_PER_DEVICE] = {GPIO_NUM_17, GPIO_NUM_19, GPIO_NUM_23, GPIO_NUM_32, GPIO_NUM_33};
TaskHandle_t periodic_send_handle = NULL;
float measures[SENSORS_PER_DEVICE * PARAMETERS_PER_SENSOR]={0};
uint8_t failure_counts[SENSORS_PER_DEVICE] = {0};

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
void print_sensors_pins(){
    uint8_t pins_vals[SENSORS_PER_DEVICE] = {0};
    for (uint8_t i = 0; i < SENSORS_PER_DEVICE; i++){
        pins_vals[i] = gpio_get_level(dht_pins[i]);
        ESP_LOGI("cmd", "Pin %d -> %d", dht_pins[i], pins_vals[i]);
    }   
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
void setup_pins_pullups(){
    for(uint8_t i = 0; i < sizeof(dht_pins); i++){
        gpio_set_pull_mode(dht_pins[i], GPIO_PULLUP_ONLY);
    }
}
void dht_read_data(float *measures){
    ESP_LOGI(TAG_CMD,"DHT Sensors Readings" );
    for(uint8_t i = 0; i < sizeof(dht_pins); i++){
        set_dht_pin((int)dht_pins[i]);
        for(int j = 0; j < DHT_MAX_TRIES; j++){
                int ret = readDHT();
            if(ret == DHT_OK){
                break;
            }
        }
        measures[i*2] = getTemperature();
        measures[i*2+1] = getHumidity();
        //Check for 0,0 and adds to accumulator, if repeated erro
        if(getTemperature() == 0 && getHumidity() ==0 ){
            //Logs that the senor failed after DHT_MAX_TRIES 
            failure_counts[i]++;
        }else{
            //If it is not consecutives failures reset failure counts
            failure_counts[i]=0;
        }


        // ESP_LOGI(TAG_CMD,"Reading from pin %d - Temp:%.2f - Hum:%.2f %%", dht_pins[i], getTemperature(), getHumidity());
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
        // xTaskCreate(periodic_send, "keep_alive", 4096, &sock, 5, &periodic_send_handle);

        while (1) {
            err = 0;
            bzero(rx_buffer, sizeof(rx_buffer));
            bzero(tx_buffer, sizeof(tx_buffer));
            dht_read_data(measures);
            memcpy(tx_buffer, measures, sizeof(measures));
            strncpy(tx_buffer + sizeof(measures), deviceName, sizeof(deviceName));
            strncpy(tx_buffer+ sizeof(measures)+sizeof(deviceName),study_key, sizeof(study_key));
            err = send(sock, tx_buffer, sizeof(measures) + sizeof(deviceName) + sizeof(study_key), 0);
            ESP_LOGI(TAG_TCP, "Name of the device: %s for the study %s", deviceName,study_key);
            ESP_LOGI(TAG_TCP, "Temps: %.2f %.2f %.2f %.2f %.2f", measures[0], measures[2], measures[4], measures[6], measures[8]);
            ESP_LOGI(TAG_TCP, "Hums: %.2f %.2f %.2f %.2f %.2f", measures[1], measures[3], measures[5], measures[7], measures[9]);
            if (err < 0) {
                ESP_LOGE(TAG_TCP, "Error occurred during sending: errno %d", errno);
                break;
            }
            for(int i=0;i<SENSORS_PER_DEVICE;i++){
                if(failure_counts[i] >= 3){
                    ESP_LOGE(TAG_TCP, "Error on pin %d", dht_pins[i]);
                    memset(failure_counts, 0, sizeof(failure_counts));
                }
            }
            vTaskDelay(MEASURES_SAMPLING_TIME);
        }
        if (sock != -1) {
            ESP_LOGE(TAG_TCP, "Shutting down socket and restarting...");
            shutdown(sock, 0);
            close(sock);
            vTaskDelete(periodic_send_handle);
            vTaskDelay(SECONDS_TO_TICKS(10));
        } else if (sock == 0) {
            ESP_LOGE(TAG_TCP, "Connection closed by server");
            vTaskSuspend(periodic_send_handle);
            logged = 0;
            vTaskDelay(SECONDS_TO_TICKS(10));
        }
   }
}

#include "commands.h"
#include "lwip/sockets.h"
#include "my_wifi.h"

static const char *TAG_TCP = "TCP";
static const char *TAG_CMD = "CMD";
esp_err_t err_check;

// Control variables
static int logged = 0;
static int keep_alive = 0;
static int connected_to_wifi = 0;
int power_saving_mode = 0;
uint8_t dht_pins[SENSORS_PER_DEVICE] = {GPIO_NUM_17, GPIO_NUM_19, GPIO_NUM_23,
                                        GPIO_NUM_32, GPIO_NUM_33};
TaskHandle_t periodic_send_handle = NULL;
float measures[SENSORS_PER_DEVICE * PARAMETERS_PER_SENSOR] = {0};
uint8_t failure_counts[SENSORS_PER_DEVICE] = {0};

void print_sensors_pins() {
    uint8_t pins_vals[SENSORS_PER_DEVICE] = {0};
    for (uint8_t i = 0; i < SENSORS_PER_DEVICE; i++) {
        pins_vals[i] = gpio_get_level(dht_pins[i]);
        ESP_LOGI("cmd", "Pin %d -> %d", dht_pins[i], pins_vals[i]);
    }
}
void setup_pins_pullups() {
    for (uint8_t i = 0; i < sizeof(dht_pins); i++) {
        gpio_set_pull_mode(dht_pins[i], GPIO_PULLUP_ONLY);
    }
}
void setup_inputPins() {
    gpio_config_t io_conf;
    io_conf.intr_type = GPIO_INTR_DISABLE;
    io_conf.mode = GPIO_MODE_INPUT_OUTPUT;
    io_conf.pin_bit_mask = 1ULL << SENSOR_1 | 1ULL << SENSOR_2 |
                           1ULL << SENSOR_3 | 1ULL << SENSOR_4 |
                           1ULL << SENSOR_5;
    io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
    io_conf.pull_up_en = GPIO_PULLUP_ENABLE;
    gpio_config(&io_conf);

    io_conf.intr_type = GPIO_INTR_DISABLE;
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pin_bit_mask = 1ULL << RST_BTN;
    io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
    io_conf.pull_up_en = GPIO_PULLUP_ENABLE;
    gpio_config(&io_conf);

    io_conf.intr_type = GPIO_INTR_DISABLE;
    io_conf.mode = GPIO_MODE_INPUT_OUTPUT;
    io_conf.pin_bit_mask = 1ULL << RESOURCE_LED;
    io_conf.pull_down_en = 0;
    io_conf.pull_up_en = 0;
    gpio_config(&io_conf);
}
void dht_read_data(float *measures) {
    ESP_LOGI(TAG_CMD, "DHT Sensors Readings");
    for (uint8_t i = 0; i < sizeof(dht_pins); i++) {
        set_dht_pin((int)dht_pins[i]);
        for (int j = 0; j < DHT_MAX_TRIES; j++) {
            int ret = readDHT();
            if (ret == DHT_OK) {
                break;
            }
        }
        measures[i * 2] = getTemperature();
        measures[i * 2 + 1] = getHumidity();
        // Check for 0,0 and adds to accumulator, if repeated error, do
        // something
        if (getTemperature() == 0 && getHumidity() == 0) {
            // Logs that the senor failed after DHT_MAX_TRIES
            failure_counts[i]++;
        } else {
            // If it is not consecutives failures reset failure counts
            failure_counts[i] = 0;
        }

        ESP_LOGI(TAG_CMD,"Reading from pin %d - Temp:%.2f - Hum:%.2f %%",
        dht_pins[i], getTemperature(), getHumidity());
    }
}

void tcp_client_task(void *pvParameters) {
    // char rx_buffer[BUFFER_SIZE] = {0};
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

        int sock = socket(addr_family, SOCK_STREAM, ip_protocol);

        if (sock < 0) {
            ESP_LOGE(TAG_TCP, "Unable to create socket: errno %d", errno);
            break;
        }

        ESP_LOGI(TAG_TCP, "Socket created, connecting to %s:%d", host_ip, PORT);

        int err =
            connect(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr));
        if (err != 0) {
            ESP_LOGE(TAG_TCP, "Socket unable to connect: errno %d", errno);
            break;
        }

        ESP_LOGI(TAG_TCP, "Successfully connected");
        // Asks for the email for the notification
        // strcat(tx_buffer, CMD_ASK_EMAIL);
        // strcat(tx_buffer, study_key);
        // send(sock, const void *dataptr, size_t size, int flags)
            //  xTaskCreate(periodic_send, "keep_alive", 4096, &sock, 5,
            //  &periodic_send_handle);

            while (1) {
            err = 0;
            // bzero(rx_buffer, sizeof(rx_buffer));
            bzero(tx_buffer, sizeof(tx_buffer));
            dht_read_data(measures);
            memcpy(tx_buffer, measures, sizeof(measures));
            strncpy(tx_buffer + sizeof(measures), deviceName,
                    sizeof(deviceName));
            strncpy(tx_buffer + sizeof(measures) + sizeof(deviceName),
                    study_key, sizeof(study_key));
            err = send(
                sock, tx_buffer,
                sizeof(measures) + sizeof(deviceName) + sizeof(study_key), 0);
            if (err < 0) {
                ESP_LOGE(TAG_TCP, "Error occurred during sending: errno %d",
                         errno);
                break;
            }
            for (int i = 0; i < SENSORS_PER_DEVICE; i++) {
                if (failure_counts[i] >= 3) {
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

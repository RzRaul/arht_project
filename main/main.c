// Create a description with a box of asciis
/* This project responds to a prototype of the client for:
https://github.com/RzRaul/arht_project


*/
#include "commands.h"
#include "driver/gpio.h"
#include "esp_err.h"
#include "esp_pm.h"
#include "my_wifi.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "web_server.h"
#define TIMER_WAKEUP_TIME_US (20 * 1000 * 1000)
#define GPIO_ERASE_CREDENTIALS GPIO_NUM_18

const char *TAG = "main";
int connected_to_wifi = 0;

TaskHandle_t orchestrator = NULL;

void init_power_management() {
    esp_pm_config_t pm_config = {
        .max_freq_mhz = 240,
        .min_freq_mhz = 80,
        .light_sleep_enable = true,
    };
}

void app_main(void) {
    httpd_handle_t server = NULL;
    setup_pins_pullups();
    init_power_management();
    setup_inputPins();
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    if (!gpio_get_level(GPIO_ERASE_CREDENTIALS)) {
        // If started with button pressed delete NVS and credentials
        ESP_LOGI("main", "Entered beacuse of the button");
        ESP_ERROR_CHECK(nvs_flash_erase());
    };

    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES ||
        ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    /* Initialize event group */
    s_wifi_event_group = xEventGroupCreate();

    /* Register Event handler */
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL, NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL, NULL));

    /*Initialize WiFi */
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    if (!check_credentials()) {
        wifi_init_softap();
        ESP_LOGI(TAG, "Setup as AP initializing server...");
        server = start_webserver();
        // start_captative_portal(); //WIP
    } else {
        wifi_init_sta();
        ESP_LOGI(TAG, "Setup as WIFI client");
    }
    while (WIFI_CONNECTED_BIT !=
           (xEventGroupWaitBits(s_wifi_event_group, WIFI_CONNECTED_BIT, pdFALSE,
                                pdFALSE, portMAX_DELAY) &
            WIFI_CONNECTED_BIT)) {
        ESP_LOGI(TAG, "Waiting for connection to the wifi network");
    }
    xTaskCreate(&tcp_client_task, "tcp_client", 4096, (void *)deviceName, 5,
                &orchestrator);
}

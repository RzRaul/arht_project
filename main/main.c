#include <stdio.h>
#include <string.h>
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_mac.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif_net_stack.h"
#include <esp_http_server.h>
#include "esp_eth.h"
#include "esp_netif.h"
#include "nvs_flash.h"
#include "lwip/inet.h"
#include "lwip/netdb.h"
#include "lwip/sockets.h"
#include "lwip/err.h"
#include "lwip/sys.h"

#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1
#define DEFAULT_WIFI_CHANNEL 1
#define DEFAULT_MAX_STA_CONN 4
#define AP_DEFAULT_SSID "Configure Me..."
#define AP_DEFAULT_PASS "12345678"
#define DEFAULT_WIFI_RETRY 5
#define WiFi_MAX_CHARS 32

const char *TAG_AP = "WiFi SoftAP";
const char *TAG_STA = "WiFi Sta";
const char *TAG_WEBS = "Web Server";
int s_retry_num = 5;

static EventGroupHandle_t s_wifi_event_group;
char ssid[WiFi_MAX_CHARS] = {0};
char password[WiFi_MAX_CHARS] = {0};
char deviceName[WiFi_MAX_CHARS] = {0};


esp_netif_t * wifi_init_sta(void);
esp_netif_t * wifi_init_softap(void);
uint8_t check_credentials();
void wifi_event_handler(void *arg, esp_event_base_t event_base,int32_t event_id, void *event_data);
esp_err_t set_nvs_creds_and_name(char* new_ssid, char* new_pass, char* deviceName);

esp_err_t config_get_handler(httpd_req_t *req);
httpd_handle_t start_webserver(void);
const httpd_uri_t configSite = {
    .uri       = "/config",
    .method    = HTTP_GET,
    .handler   = config_get_handler,
};



void app_main(void){
    httpd_handle_t server = NULL;
    ESP_ERROR_CHECK(esp_netif_init());
    // ESP_ERROR_CHECK(nvs_flash_erase());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    //Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    /* Initialize event group */
    s_wifi_event_group = xEventGroupCreate();

    /* Register Event handler */
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                    ESP_EVENT_ANY_ID,
                    &wifi_event_handler,
                    NULL,
                    NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                    IP_EVENT_STA_GOT_IP,
                    &wifi_event_handler,
                    NULL,
                    NULL));

    /*Initialize WiFi */
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    if (check_credentials()){
        wifi_init_sta();
        ESP_LOGI(TAG_AP, "Setup as WIFI client");

    } else {
        wifi_init_softap();
        //Start server to get credentials via HTTP
        server = start_webserver();
        // ESP_LOGI(TAG_AP, "Setting default credentials...");
        //set_nvs_creds("IoT_PROJECT", "IoTUABC123");
        // ESP_LOGI(TAG_AP, "Done, please restart.");

        
    }
    while(1){
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }

}



/*-------------------------------------------------------------------METHODS------------------------------------------------------------------------------------*/
void wifi_event_handler(void *arg, esp_event_base_t event_base, int32_t event_id, void *event_data){
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_AP_STACONNECTED) {
        wifi_event_ap_staconnected_t *event = (wifi_event_ap_staconnected_t *) event_data;
        ESP_LOGI(TAG_AP, "Station "MACSTR" joined, AID=%d",
                 MAC2STR(event->mac), event->aid);
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_AP_STADISCONNECTED) {
        wifi_event_ap_stadisconnected_t *event = (wifi_event_ap_stadisconnected_t *) event_data;
        ESP_LOGI(TAG_AP, "Station "MACSTR" left, AID=%d",
                 MAC2STR(event->mac), event->aid);
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
        ESP_LOGI(TAG_STA, "Station started");
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *) event_data;
        ESP_LOGI(TAG_STA, "Got IP:" IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

/* Initialize soft AP */
esp_netif_t *wifi_init_softap(void){
    esp_netif_t *esp_netif_ap = esp_netif_create_default_wifi_ap();

    wifi_config_t wifi_ap_config = {
        .ap = {
            .ssid = AP_DEFAULT_SSID,
            .ssid_len = strlen(AP_DEFAULT_SSID),
            .password = AP_DEFAULT_PASS,
            .channel = DEFAULT_WIFI_CHANNEL,
            .max_connection = DEFAULT_MAX_STA_CONN,
            .authmode = WIFI_AUTH_WPA2_PSK,
        },
    };

    if (strlen(AP_DEFAULT_PASS) == 0) {
        wifi_ap_config.ap.authmode = WIFI_AUTH_OPEN;
    }
    
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_APSTA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &wifi_ap_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG_AP, "wifi_init_softap finished. SSID:%s password:%s channel:%d",
             AP_DEFAULT_SSID, AP_DEFAULT_PASS, DEFAULT_WIFI_CHANNEL);

    return esp_netif_ap;
}

/* Initialize wifi station */
esp_netif_t *wifi_init_sta(void){
    esp_netif_t *esp_netif_sta = esp_netif_create_default_wifi_sta();

    wifi_config_t wifi_sta_config = {
        .sta = {
            .scan_method = WIFI_ALL_CHANNEL_SCAN,
            .failure_retry_cnt = DEFAULT_WIFI_RETRY,
            /* Authmode threshold resets to WPA2 as default if password matches WPA2 standards (pasword len => 8).
             * If you want to connect the device to deprecated WEP/WPA networks, Please set the threshold value
             * to WIFI_AUTH_WEP/WIFI_AUTH_WPA_PSK and set the password with length and format matching to
            * WIFI_AUTH_WEP/WIFI_AUTH_WPA_PSK standards.
             */
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
            .sae_pwe_h2e = WPA3_SAE_PWE_BOTH,
        },
    };
    ESP_LOGI(TAG_STA, "Setting SSID: %s, Password: %s", ssid, password);
    strncpy((char*)wifi_sta_config.sta.ssid, ssid, sizeof(ssid));
    strncpy((char*)wifi_sta_config.sta.password, password, sizeof(password));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_sta_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG_STA, "wifi_init_sta finished.");

    return esp_netif_sta;
}

esp_err_t set_nvs_creds_and_name(char* new_ssid, char* new_pass, char* deviceName){
    nvs_handle_t nvs_handle;
    esp_err_t err = nvs_open("storage", NVS_READWRITE, &nvs_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG_AP, "Error (%s) opening NVS handle", esp_err_to_name(err));
        return err;
    } else {
        err = nvs_set_str(nvs_handle, "ssid", new_ssid);
        if (err != ESP_OK) {
            ESP_LOGE(TAG_AP, "Error (%s) setting ssid in NVS", esp_err_to_name(err));
            return err;
        }
        err = nvs_set_str(nvs_handle, "password", new_pass);
        if (err != ESP_OK) {
            ESP_LOGE(TAG_AP, "Error (%s) setting password in NVS", esp_err_to_name(err));
            return err;
        }
        err = nvs_set_str(nvs_handle, "deviceName", deviceName);
        if (err != ESP_OK) {
            ESP_LOGE(TAG_AP, "Error (%s) setting password in NVS", esp_err_to_name(err));
            return err;
        }
        nvs_close(nvs_handle);
    }
    return ESP_OK;
}

//Check for credentials in NVS and if not found, set default values
uint8_t check_credentials(){
    nvs_handle_t nvs_handle;
    esp_err_t err = nvs_open("storage", NVS_READWRITE, &nvs_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG_AP, "Error (%s) opening NVS handle", esp_err_to_name(err));
        return 0;
    } else {
        size_t ssid_len = sizeof(ssid);
        size_t password_len = sizeof(password);
        err = nvs_get_str(nvs_handle, "ssid", ssid, &ssid_len);
        if (err != ESP_OK) {
            ESP_LOGI(TAG_AP, "SSID not found initializing as AP");
           return 0;
        }
        err = nvs_get_str(nvs_handle, "password", password, &password_len);
        if (err != ESP_OK) {
            ESP_LOGI(TAG_AP, "Password not found, setting default");
           return 0;
        }
        nvs_close(nvs_handle);
        return 1;
    }
}

/* An HTTP GET handler */
esp_err_t config_get_handler(httpd_req_t *req)
{
    char*  buf;
    size_t buf_len;
    extern unsigned char view_start[] asm("_binary_view_html_start");
    extern unsigned char view_end[] asm("_binary_view_html_end");
    size_t view_len = view_end - view_start;
    char viewHtml[view_len];
    memcpy(viewHtml, view_start, view_len);
    ESP_LOGI(TAG_WEBS, "URI: %s\n", req->uri);

    /* Get header value string length and allocate memory for length + 1,
     * extra byte for null termination */
    buf_len = httpd_req_get_hdr_value_len(req, "Host") + 1;
    if (buf_len > 1) {
        buf = malloc(buf_len);
        /* Copy null terminated value string into buffer */
        if (httpd_req_get_hdr_value_str(req, "Host", buf, buf_len) == ESP_OK) {
            ESP_LOGI(TAG_WEBS, "Found header => Host: %s\n", buf);
        }
        free(buf);
    }

    // buf_len = httpd_req_get_hdr_value_len(req, "Test-Header-2") + 1;
    // if (buf_len > 1) {
    //     buf = malloc(buf_len);
    //     if (httpd_req_get_hdr_value_str(req, "Test-Header-2", buf, buf_len) == ESP_OK) {
    //         ESP_LOGI(TAG_WEBS, "Found header => Test-Header-2: %s", buf);
    //     }
    //     free(buf);
    // }


    /* Read URL query string length and allocate memory for length + 1,
     * extra byte for null termination */
    buf_len = httpd_req_get_url_query_len(req) + 1;
    if (buf_len > 1) {
        buf = malloc(buf_len);
        if (httpd_req_get_url_query_str(req, buf, buf_len) == ESP_OK) {
            ESP_LOGI(TAG_WEBS, "Found URL query => %s", buf);
            char param[WiFi_MAX_CHARS];
            /* Get value of expected key from query string */
            if (httpd_query_key_value(buf, "fssid", ssid, sizeof(ssid)) == ESP_OK) {
                ESP_LOGI(TAG_WEBS, "Found URL query parameter => fssid=%s", ssid);
            }
            if (httpd_query_key_value(buf, "fpass", password, sizeof(password)) == ESP_OK) {
                ESP_LOGI(TAG_WEBS, "Found URL query parameter => fpass=%s", password);
            }
            if (httpd_query_key_value(buf, "fname", deviceName, sizeof(deviceName)) == ESP_OK) {
                ESP_LOGI(TAG_WEBS, "Found URL query parameter => fname=%s", deviceName);
            }
            if(strlen(ssid) > 0 && strlen(password) > 0 && strlen(deviceName) > 0){
                set_nvs_creds_and_name(ssid, password, deviceName);
                ESP_LOGI(TAG_WEBS, "Credentials set, restarting...");
                free(buf);
                esp_restart();
            }
        }
        free(buf);
    }

    // /* Set some custom headers */
    // httpd_resp_set_hdr(req, "Custom-Header-1", "Custom-Value-1");
    // httpd_resp_set_hdr(req, "Custom-Header-2", "Custom-Value-2");

    /* Send response with custom headers and body set as the
     * string passed in user context*/
    httpd_resp_set_type(req, "text/html");
    httpd_resp_send(req, viewHtml, view_len);

    /* After sending the HTTP response the old HTTP request
     * headers are lost. Check if HTTP request headers can be read now. */
    if (httpd_req_get_hdr_value_len(req, "Host") == 0) {
        ESP_LOGI(TAG_WEBS, "Request headers lost");
    }
    return ESP_OK;
}



httpd_handle_t start_webserver(void)
{
    httpd_handle_t server = NULL;
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();

    // Iniciar el servidor httpd 
    ESP_LOGI(TAG_WEBS, "Iniciando el servidor en el puerto: '%d'", config.server_port);
    if (httpd_start(&server, &config) == ESP_OK) {
        // Manejadores de URI
        ESP_LOGI(TAG_WEBS, "Registrando manejadores de URI");
        httpd_register_uri_handler(server, &configSite);
        return server;
    }

    ESP_LOGI(TAG_WEBS, "Error starting server!");
    return NULL;
}
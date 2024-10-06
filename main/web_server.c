#include "web_server.h"
#include "my_wifi.h"


const char *TAG_WEBS = "Web Server";

static const httpd_uri_t configSite = {
    .uri       = "/config",
    .method    = HTTP_GET,
    .handler   = config_get_handler,
};

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
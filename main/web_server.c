#include "web_server.h"
#include "my_wifi.h"
#include "dns_server.h"


const char *TAG_WEBS = "Web Server";
 char*  buf;
size_t buf_len;
extern unsigned char view_start[] asm("_binary_view_html_start");
extern unsigned char view_end[] asm("_binary_view_html_end");

esp_err_t config_root_handler(httpd_req_t *req)
{
    size_t view_len = view_end - view_start;
    ESP_LOGI(TAG_WEBS, "URI: %s\n", req->uri);
    httpd_resp_send(req,(const char*) view_start, view_len);
    return ESP_OK;
}
static const httpd_uri_t root = {
    .uri       = "/",
    .method    = HTTP_GET,
    .handler   = config_root_handler,
};
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
            if (httpd_query_key_value(buf, "fstudy", study_key, sizeof(study_key)) == ESP_OK) {
                ESP_LOGI(TAG_WEBS, "Found URL query parameter => fname=%s", study_key);
            }
            if(strlen(ssid) > 0 && strlen(password) > 0 && strlen(deviceName) > 0 && strlen(study_key) > 0){
                char * aux=ssid;
                while(*aux!=0) {*aux = *aux=='+'? ' ':*aux; aux++;}
                aux = deviceName;
                while(*aux!=0) {*aux = *aux=='+'? ' ':*aux; aux++;}
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

esp_err_t generate_204_handler(httpd_req_t *req) {
    // You can just return a 204 No Content response
    httpd_resp_set_status(req, "204 No Content");
    httpd_resp_set_hdr(req, "Location", "/config");
     httpd_resp_send(req, "Redirect to the captive portal", HTTPD_RESP_USE_STRLEN);
    return ESP_OK;
}

httpd_uri_t generate_204_uri = {
    .uri = "/generate_204",
    .method = HTTP_GET,
    .handler = generate_204_handler,
    .user_ctx = NULL
};

esp_err_t http_404_error_handler(httpd_req_t *req, httpd_err_code_t err)
{
    // Set status
    httpd_resp_set_status(req, "302 Temporary Redirect");
    // Redirect to the "/" root directory
    httpd_resp_set_hdr(req, "Location", "/config");
    // iOS requires content in the response to detect a captive portal, simply redirecting is not sufficient.
    httpd_resp_send(req, "Redirect to the captive portal", HTTPD_RESP_USE_STRLEN);

    ESP_LOGI(TAG_WEBS, "Redirecting to root");
    return ESP_OK;
}



httpd_handle_t start_webserver(void)
{
    httpd_handle_t server = NULL;
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.max_open_sockets = 7;
    config.lru_purge_enable = true;

    // Iniciar el servidor httpd 
    ESP_LOGI(TAG_WEBS, "Iniciando el servidor en el puerto: '%d'", config.server_port);
    if (httpd_start(&server, &config) == ESP_OK) {
        // Manejadores de URI
        ESP_LOGI(TAG_WEBS, "Registrando manejadores de URI");
        httpd_register_uri_handler(server, &root);
        httpd_register_uri_handler(server, &configSite);
        httpd_register_err_handler(server, HTTPD_404_NOT_FOUND, http_404_error_handler);
        ESP_ERROR_CHECK(httpd_register_uri_handler(server, &generate_204_uri));
        return server;
    }

    ESP_LOGI(TAG_WEBS, "Error starting server!");
    
    return NULL;
}

void start_captative_portal() {
    dns_server_config_t config = DNS_SERVER_CONFIG_SINGLE("*" /* all A queries */, "WIFI_AP_DEF" /* softAP netif ID */);
    start_dns_server(&config);
}


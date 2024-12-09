idf_component_register(SRCS "email_handler.c" "dns_server.c" "main.c" "DHT22.c" "my_wifi.c" "web_server.c" "commands.c" 
                    INCLUDE_DIRS "includes/."
                    EMBED_TXTFILES "view.html" "server_root_cert.pem")

#ifndef __MY_SMTP_H
#define __MY_SMTP_H
#include <mbedtls/base64.h>
#include <stdlib.h>
#include <string.h>
#include <sys/param.h>

#include "esp_event.h"
#include "esp_log.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/entropy.h"
#include "mbedtls/error.h"
#include "mbedtls/esp_debug.h"
#include "mbedtls/net_sockets.h"
#include "mbedtls/platform.h"
#include "mbedtls/ssl.h"

#define MAIL_SERVER "smtp.gmail.com"
#define MAIL_PORT "587" 
#define SENDER_MAIL "arht.notification.sender@gmail.com"
#define SENDER_PASSWORD "gpam pjrj dgzg utis"
#define RECIPIENT_MAIL "rodriguez.raul54@uabc.edu.mx"

#define SERVER_USES_STARTSSL 1

#define TASK_STACK_SIZE (8 * 1024)
#define SMTP_BUFFER_SIZE 512

#define VALIDATE_MBEDTLS_RETURN(ret, min_valid_ret, max_valid_ret, goto_label) \
   do {                                                                        \
      if (ret < min_valid_ret || ret > max_valid_ret) {                        \
         goto goto_label;                                                      \
      }                                                                        \
   } while (0)

void smtp_client_task();

#endif // __MY_SMTP_H
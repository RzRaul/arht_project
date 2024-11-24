#ifndef RESOURCES_H
#define RESOURCES_H
#include "driver/gpio.h"
#include "esp_adc/adc_oneshot.h"

#define ADC_CHANNEL ADC_CHANNEL_4
#define RESOURCE_ADC GPIO_NUM_32
#define ADC_WIDTH ADC_BITWIDTH_12
#define ADC_ATTEN ADC_ATTEN_DB_0
#define RESOURCE_LED GPIO_NUM_2
#define ELEMENT_LED 'L'
#define ELEMENT_ADC 'A'

static adc_oneshot_unit_handle_t adc_unit_handler;

int read_adc_();
void setup_inputPins();
int get_resource(char resource);
int set_resource(char resource, int value);
void adc_init();
void setupPins();

#endif

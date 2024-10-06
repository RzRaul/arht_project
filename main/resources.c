#include "resources.h"

int read_adc_(){
    int raw;
    adc_oneshot_read(adc_unit_handler, ADC_CHANNEL, &raw);
    return raw;
}

int get_resource(char resource){
    int raw;
    switch (resource){
        case ELEMENT_LED:
            return gpio_get_level(RESOURCE_LED);
        case ELEMENT_ADC:
            return read_adc_();
        default:
            return -1;
    }
}

int set_resource(char resource, int value){
    switch (resource){
        case ELEMENT_LED:
            gpio_set_level(RESOURCE_LED, value);
            return get_resource(ELEMENT_LED);
        case ELEMENT_ADC:
            return get_resource(ELEMENT_ADC);
        default:
            return -1;
    }
}

void adc_init(){
    adc_oneshot_unit_init_cfg_t adc_init = {
        .unit_id = ADC_UNIT_1,
    };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&adc_init, &adc_unit_handler));
    adc_oneshot_chan_cfg_t adc_channel = {
        .atten = ADC_ATTEN,
        .bitwidth = ADC_WIDTH,
    };
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc_unit_handler, ADC_CHANNEL, &adc_channel));
}

void setupPins(){
    gpio_config_t io_conf;
    io_conf.intr_type = GPIO_INTR_DISABLE;
    io_conf.mode = GPIO_MODE_INPUT_OUTPUT;
    io_conf.pin_bit_mask = 1ULL << RESOURCE_LED;
    io_conf.pull_down_en = 0;
    io_conf.pull_up_en = 0;
    gpio_config(&io_conf);

    io_conf.intr_type = GPIO_INTR_DISABLE;
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pin_bit_mask = 1ULL << RESOURCE_ADC;
    io_conf.pull_down_en = 0;
    io_conf.pull_up_en = 0;
    gpio_config(&io_conf);
    adc_init();
}
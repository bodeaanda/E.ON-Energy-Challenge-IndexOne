#include "esp_camera.h"
#include <Wire.h>
#include <Rtc_Pcf8563.h>

// --- CONFIGURARE PINI REZULTATĂ DIN MĂSURĂTORI ---
const int PIN_LATCH = 14; 
const int I2C_SDA = 2;    // MUTAT PE GPIO 2 (curat)
const int I2C_SCL = 15;   // PE GPIO 15 (curat)
const int PIN_FLASH = 4;

// Configurație Cameră AI-Thinker
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void setup() {
  // 1. LATCH - Pornim imediat pe pinul 14
  pinMode(PIN_LATCH, OUTPUT);
  digitalWrite(PIN_LATCH, HIGH); 

  Serial.begin(115200);
  delay(500);
  Serial.println("\n[SISTEM] >> Latch pe 14, I2C pe 2 si 15");

  // 2. PORNIRE I2C
  Wire.begin(I2C_SDA, I2C_SCL);
  
  Wire.beginTransmission(0x51);
  if (Wire.endTransmission() == 0) {
    Serial.println("[RTC]    >> GASIT pe pinii 2 si 15!");
  } else {
    Serial.println("[ERROR]  >> RTC nu raspunde pe 2 si 15. Verifica firele!");
  }

  // 3. INITIALIZARE CAMERA
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM; config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM; config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM; config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM; config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM; config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM; config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM; config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM; config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000; config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA; config.jpeg_quality = 12; config.fb_count = 1;

  if (esp_camera_init(&config) == ESP_OK) {
    Serial.println("[CAMERA] >> OK.");
    pinMode(PIN_FLASH, OUTPUT);
    digitalWrite(PIN_FLASH, HIGH);
    delay(500);
    camera_fb_t * fb = esp_camera_fb_get();
    if (fb) {
      Serial.printf("[FOTO]   >> Captura OK (%zu bytes).\n", fb->len);
      esp_camera_fb_return(fb);
    }
    digitalWrite(PIN_FLASH, LOW);
  }

  // 4. PROGRAMARE RTC (30 SECUNDE)
  Wire.beginTransmission(0x51);
  Wire.write(0x01); Wire.write(0x00); 
  Wire.endTransmission();
  Wire.beginTransmission(0x51);
  Wire.write(0x0E); Wire.write(0x82); 
  Wire.endTransmission();
  Wire.beginTransmission(0x51);
  Wire.write(0x0F); Wire.write(30);   
  Wire.endTransmission();
  Wire.beginTransmission(0x51);
  Wire.write(0x01); Wire.write(0x11); 
  Wire.endTransmission();

  Serial.println("[RTC]    >> Programat. Inchidere LATCH...");
  delay(500);
  digitalWrite(PIN_LATCH, LOW); 
}

void loop() {}
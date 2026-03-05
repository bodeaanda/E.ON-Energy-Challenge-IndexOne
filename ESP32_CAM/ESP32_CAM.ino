#include "esp_camera.h"
#include <Wire.h>
#include <Rtc_Pcf8563.h>
#include <WiFi.h>
#include <HTTPClient.h>

// --- CONFIGURARE REȚEA ---
const char* ssid = "marasti3";           
const char* password = "calinlungu";     
const char* serverName = "http://192.168.0.67:8000/receive-image"; 

// --- CONFIGURARE PINI ---
const int PIN_LATCH = 14; 
const int I2C_SDA = 2;    
const int I2C_SCL = 15;   
const int PIN_FLASH = 4;

// --- CONFIGURARE FLASH (1/3 LUMINĂ) ---
const int flashFreq = 5000; 
const int flashRes = 8;     
const int flashBrightness = 10; // 1/3 din 255 este ~85

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
  // 1. LATCH - Pornim imediat
  pinMode(PIN_LATCH, OUTPUT);
  digitalWrite(PIN_LATCH, HIGH); 

  Serial.begin(115200);
  delay(500);
  Serial.println("\n[SISTEM] >> Start...");

  // --- CONFIGURARE PWM FLASH (Versiunea Nouă ESP32) ---
  ledcAttach(PIN_FLASH, flashFreq, flashRes);

  // --- CONECTARE WIFI ---
  Serial.print("[WIFI]    >> Conectare la ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  
  int wifi_attempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifi_attempts < 20) {
    delay(500);
    Serial.print(".");
    wifi_attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI]    >> Conectat! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n[WIFI]    >> ESEC conexiune!");
  }

  // 2. PORNIRE I2C
  Wire.begin(I2C_SDA, I2C_SCL);
  
  Wire.beginTransmission(0x51);
  if (Wire.endTransmission() == 0) {
    Serial.println("[RTC]     >> OK.");
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
  config.frame_size = FRAMESIZE_VGA; 
  config.jpeg_quality = 12; 
  config.fb_count = 1;

  if (esp_camera_init(&config) == ESP_OK) {
    Serial.println("[CAMERA] >> OK.");
    
    // --- FLASH ON LA 1/3 (85) ---
    ledcWrite(PIN_FLASH, flashBrightness); 
    delay(500);
    
    camera_fb_t * fb = esp_camera_fb_get();
    
    // --- FLASH OFF ---
    ledcWrite(PIN_FLASH, 0); 
    
    if (fb) {
      Serial.printf("[FOTO]    >> Captura OK (%zu bytes).\n", fb->len);

      if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(serverName);

        String boundary = "----ESP32Boundary123456";
        String head = "--" + boundary + "\r\nContent-Disposition: form-data; name=\"file\"; filename=\"capture.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n";
        String tail = "\r\n--" + boundary + "--\r\n";

        size_t totalLen = head.length() + fb->len + tail.length();
        uint8_t *post_data = (uint8_t *)ps_malloc(totalLen); 
        
        if (post_data) {
          memcpy(post_data, head.c_str(), head.length());
          memcpy(post_data + head.length(), fb->buf, fb->len);
          memcpy(post_data + head.length() + fb->len, tail.c_str(), tail.length());

          http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
          
          Serial.println("[SERVER] >> Trimitere HTTP...");
          int httpResponseCode = http.POST(post_data, totalLen);

          if (httpResponseCode > 0) {
            Serial.printf("[SERVER] >> Raspuns: %d\n", httpResponseCode);
          } else {
            Serial.printf("[SERVER] >> EROARE: %d\n", httpResponseCode);
          }
          free(post_data);
        } else {
          Serial.println("[SERVER] >> EROARE: Memorie PSRAM insuficienta!");
        }
        http.end();
      }
      esp_camera_fb_return(fb);
    }
  }

  // 4. PROGRAMARE RTC & SHUTDOWN
  programRTC();
}

void loop() {}

void programRTC() {
  Wire.beginTransmission(0x51); Wire.write(0x01); Wire.write(0x00); Wire.endTransmission();
  Wire.beginTransmission(0x51); Wire.write(0x0E); Wire.write(0x82); Wire.endTransmission();
  Wire.beginTransmission(0x51); Wire.write(0x0F); Wire.write(30);   Wire.endTransmission();
  Wire.beginTransmission(0x51); Wire.write(0x01); Wire.write(0x11); Wire.endTransmission();
  
  Serial.println("[RTC]     >> Sleep. Bye!");
  delay(200);
  digitalWrite(PIN_LATCH, LOW); 
}
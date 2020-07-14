#include <OneWire.h>
#include <DallasTemperature.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <string.h>

#ifndef STASSID
#define STASSID "hudnet"
#define STAPSK  "7950295932"
#endif

#include <Arduino.h>
#include <U8g2lib.h>

#ifdef U8X8_HAVE_HW_SPI
#include <SPI.h>
#endif
#ifdef U8X8_HAVE_HW_I2C
#include <Wire.h>
#endif

String client_name = "sensor_outside";

const char* ssid     = STASSID;
const char* password = STAPSK;

const char* host = "192.168.18.1";
const uint16_t port = 8585;
ESP8266WiFiMulti WiFiMulti;

DeviceAddress outsideThermometer = {0x28, 0xFF, 0x95, 0x7F, 0x93, 0x16, 0x04, 0xF4};

// сигнальный провод датчика температуры
#define ONE_WIRE_BUS 4
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

#define hc_sr501_pin 5
#define analogInPin A0
#define button_pin 14
#define buzzerPin 15

boolean flagHCSR501 = false;
int analog_sensor_val = 0;

U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

bool guard_mode = false;
bool button_pressed = false;

void setup() {
  pinMode(buzzerPin, OUTPUT);
    
  Serial.begin(115200);
  // change hardware I2C pins to (5,4) (D1,D2)
  Wire.begin(0,2);
  u8g2.begin();
  
  // We start by connecting to a WiFi network
  WiFi.mode(WIFI_STA);
  WiFiMulti.addAP(ssid, password);

  Serial.println();
  Serial.println();
  Serial.print("Wait for WiFi... ");

  u8g2.clearBuffer();         
  u8g2.setFont(u8g2_font_ncenB08_tf); 
  String str = "Connecting to WiFi...";
  u8g2.drawStr(0,42,str.c_str()); 
  u8g2.sendBuffer();         

  while (WiFiMulti.run() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }

  u8g2.clearBuffer();         
  u8g2.setFont(u8g2_font_ncenB08_tf);
  str = "Wifi connected.";
  u8g2.drawStr(0,20,str.c_str());

  str = "IP " + WiFi.localIP().toString();
  u8g2.setCursor(0, 42);
  u8g2.print(str); 
  u8g2.sendBuffer();          
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  pinMode(hc_sr501_pin, INPUT);
  pinMode(button_pin, INPUT);
  
  sensors.setResolution(outsideThermometer, 12);
  play_song();
  u8g2.clearBuffer();
  u8g2.clear();
}

void loop() {
  String str;
  String time_str;
  WiFiClient client;
  client.setTimeout(5000);

  if (!client.connect(host, port)) {
    Serial.println("connection failed");
    Serial.println("wait 5 sec...");
    u8g2.clearBuffer();
    u8g2.clear();         
    u8g2.setFont(u8g2_font_ncenB08_tf);
    str = "disconnect from server.";
    u8g2.setCursor(0, 42);
    u8g2.print(str); 
    u8g2.sendBuffer();
    delay(5000);
    u8g2.clear();
    u8g2.clearBuffer();
    return;
  }

  while (client.connected()) {    
    // read motion sensor
    readHCSR501();
    
    // read button
    read_button();
    
    // read light sensor
    analog_sensor_val = analogRead(analogInPin);

    // read temperature sensor
    sensors.requestTemperaturesByAddress(outsideThermometer);
    double temp = sensors.getTempC(outsideThermometer);

    String message = client_name + ":move=";
    if (flagHCSR501) {
      message += "1";
    } else {
      message += "0";
    }
    message += ";light=" + String(analog_sensor_val) + ";temp=" + String(temp) + ";button=";
    if (button_pressed) {
      message += "1";
    } else {
      message += "0";
    }
    Serial.println(message);
    client.print(message);

    unsigned long timeout = millis();

    while (client.available() == 0) // ждёт ответ от сервера
    {
      if (millis() - timeout > 5000) // если нет ответа в течении 1 сек, то разрывает соединение
      {
        Serial.println("Client Timeout");
        client.stop();
        return;
      }
    }
    String answer = client.readStringUntil('\r');
    Serial.println(answer);
    if (answer.length() > 0){
      time_str = "";
      for(int i=0; i<answer.length()+1; i++){
        if (answer.charAt(i) != ';'){
          time_str += answer.charAt(i);  
        } else {
          if (answer.charAt(i+1) == 'g'){
            if (!guard_mode){
              guard_mode = true;
              change_guard_mode_song();
            } 
          } else {
            if (guard_mode){
              guard_mode = false;
              change_guard_mode_song2();
            } 
          }
          break;
        }
      }
    }

    // ***************** display ****************
    u8g2.clearBuffer();
    //u8g2.clear(); 
    // *** temperature ***        
    u8g2.setFont(u8g2_font_ncenB18_tf);
    str = temp;
    u8g2.setCursor(0, 20);
    u8g2.print(str);
    u8g2.setFont(u8g2_font_ncenB08_tf);
    str = "C";
    u8g2.setCursor(62, 8);
    u8g2.print(str); 
    // *** time ***
    u8g2.setFont(u8g2_font_ncenB18_tf);
    str = time_str;
    u8g2.setCursor(10, 50);
    u8g2.print(str);
     // *** move ***
    u8g2.setFont(u8g2_font_ncenB08_tf);
    if (flagHCSR501){
      str = "move";
    } else {
      str = "";
    }
    u8g2.setCursor(0, 62);
    u8g2.print(str);
    // *** guard mode ***
    u8g2.setFont(u8g2_font_ncenB08_tf);
    if (guard_mode){
      str = "guard mode";
    } else {
      str = "";
    }
    u8g2.setCursor(60, 62);
    u8g2.print(str);

    // *** button ***
    u8g2.setFont(u8g2_font_ncenB12_tf);
    if (button_pressed){
      str = "B";
    } else {
      str = "";
    }
    u8g2.setCursor(100, 12);
    u8g2.print(str);
    
    u8g2.sendBuffer();
  }
}

// считывание датчика движения
void readHCSR501(){
  int _pin_state = digitalRead(hc_sr501_pin);
  flagHCSR501 = _pin_state;
}

// считывание кнопки
void read_button(){
  button_pressed = digitalRead(button_pin);
}

// song
void change_guard_mode_song(){
  // Длина должна равняться общему количеству нот и пауз
  const int songLength = 5;
  char notes[] = "cdfda"; // пробелы означают паузы
  // Ритм задается массивом из длительности нот и пауз между ними.
  // "1" - четвертная нота, "2" - половинная, и т.д.
  // Не забывайте, что пробелы должны быть тоже определенной длинны.
  int beats[] = {1,1,1,1,1,1,4,4,2,1,1,1,1,1,1,4,4,2};
  // "tempo" это скорость проигрывания мелодии.
  // Для того, чтобы мелодия проигрывалась быстрее, вы
  // должны уменьшить следующее значение.

  int tempo = 150;
  
  int i, duration;
  for (i = 0; i < songLength; i++) // пошаговое воспроизведение
                                   // из массива
  {
    duration = beats[i] * tempo;  // длительность нот/пауз в ms
    
    if (notes[i] == ' ')          // если нота отсутствует? 
    {
      delay(duration);            // тогда не большая пауза
    }
    else                          // в противном случае играть
    {
      tone(buzzerPin, frequency(notes[i]), duration);
      delay(duration);            // ждать пока проигрывается
    }
    delay(tempo/10);              // маленькая пауза между нотами
  }
}

// song
void change_guard_mode_song2(){
  // Длина должна равняться общему количеству нот и пауз
  const int songLength = 5;
  char notes[] = "cdfdg"; // пробелы означают паузы
  // Ритм задается массивом из длительности нот и пауз между ними.
  // "1" - четвертная нота, "2" - половинная, и т.д.
  // Не забывайте, что пробелы должны быть тоже определенной длинны.
  int beats[] = {1,1,1,1,1,1,4,4,2,1,1,1,1,1,1,4,4,2};
  // "tempo" это скорость проигрывания мелодии.
  // Для того, чтобы мелодия проигрывалась быстрее, вы
  // должны уменьшить следующее значение.

  int tempo = 150;
  
  int i, duration;
  for (i = 0; i < songLength; i++) // пошаговое воспроизведение
                                   // из массива
  {
    duration = beats[i] * tempo;  // длительность нот/пауз в ms
    
    if (notes[i] == ' ')          // если нота отсутствует? 
    {
      delay(duration);            // тогда не большая пауза
    }
    else                          // в противном случае играть
    {
      tone(buzzerPin, frequency(notes[i]), duration);
      delay(duration);            // ждать пока проигрывается
    }
    delay(tempo/10);              // маленькая пауза между нотами
  }
}

// play song
void play_song(){
  // Длина должна равняться общему количеству нот и пауз
  const int songLength = 18;
  char notes[] = "cdfda ag cdfdg gf "; // пробелы означают паузы
  // Ритм задается массивом из длительности нот и пауз между ними.
  // "1" - четвертная нота, "2" - половинная, и т.д.
  // Не забывайте, что пробелы должны быть тоже определенной длинны.
  int beats[] = {1,1,1,1,1,1,4,4,2,1,1,1,1,1,1,4,4,2};
  // "tempo" это скорость проигрывания мелодии.
  // Для того, чтобы мелодия проигрывалась быстрее, вы
  // должны уменьшить следующее значение.

  int tempo = 150;
  
  int i, duration;
  for (i = 0; i < songLength; i++) // пошаговое воспроизведение
                                   // из массива
  {
    duration = beats[i] * tempo;  // длительность нот/пауз в ms
    
    if (notes[i] == ' ')          // если нота отсутствует? 
    {
      delay(duration);            // тогда не большая пауза
    }
    else                          // в противном случае играть
    {
      tone(buzzerPin, frequency(notes[i]), duration);
      delay(duration);            // ждать пока проигрывается
    }
    delay(tempo/10);              // маленькая пауза между нотами
  }
}

int frequency(char note) 
{
  // Эта функция принимает символ ноты (a-g), и возвращает
  // частоту в Гц для функции tone().
  
  int i;
  const int numNotes = 8;  // количество хранимых нот
  
  // Следующие массивы содержат символы нот и соответствующие им
  // частоты. Последний символ "C" (нота "ДО") в верхнем регистре
  // (большая), это сделано для того чтобы отличить ее от первой
  // ноты "с", более низкого тона. Если вы хотите добавить больше
  // нот, вы должны будете использовать уникальный символ для
  // каждой новой ноты.

  // Каждый "char" (символ), мы заключаем в одинарные кавычки.

  char names[] = { 'c', 'd', 'e', 'f', 'g', 'a', 'b', 'C' };
  int frequencies[] = {262, 294, 330, 349, 392, 440, 494, 523};
  
  // Теперь мы будем искать во всем массиве, символ ноты и если
   // находим, возвращаем частоту для этой ноты.
  
  for (i = 0; i < numNotes; i++)  // пошаговый перебор нот
  {
    if (names[i] == note)         // если находим
    {
      return(frequencies[i]);     // возвращаем частоту
    }
  }
  return(0);  // Поиск символа не дал результата? Но, необходимо
        // вернуть какое-то значение, так вернем 0.
}

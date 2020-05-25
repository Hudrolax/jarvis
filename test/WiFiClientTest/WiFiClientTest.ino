/*
    This sketch sends a string to a TCP server, and prints a one-line response.
    You must run a TCP server in your local network.
    For example, on Linux you can use this command: nc -v -l 3000
*/

#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>

#ifndef STASSID
#define STASSID "hudnet"
#define STAPSK  "7950295932"
#endif

String client_name = "wemos1";

const char* ssid     = STASSID;
const char* password = STAPSK;

const char* host = "192.168.18.3";
const uint16_t port = 8586;

ESP8266WiFiMulti WiFiMulti;

void setup() {
  Serial.begin(115200);

  // We start by connecting to a WiFi network
  WiFi.mode(WIFI_STA);
  WiFiMulti.addAP(ssid, password);

  Serial.println();
  Serial.println();
  Serial.print("Wait for WiFi... ");

  while (WiFiMulti.run() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  delay(500);
  pinMode(16, OUTPUT);
}


void loop() {
  WiFiClient client;

  if (!client.connect(host, port)) {
    Serial.println("connection failed");
    Serial.println("wait 5 sec...");
    delay(5000);
    return;
  }

  // This will send the request to the server
  String string = client_name+":"+"hello from ESP8266";
  client.println(string);

  unsigned long timeout = millis();
  
  while(client.available() == 0) // ждёт ответ от сервера
  {
    if(millis() - timeout > 5000) // если нет ответа в течении 5 сек, то разрывает соединение
    {
      Serial.println("Client Timeout");
      client.stop();
      return;
    }
  }

  String line = client.readStringUntil('\r');
  if (line == "on"){
    digitalWrite(16, HIGH);
     Serial.println(line);
  }else if (line == "off"){
    digitalWrite(16, LOW);
     Serial.println(line);
  }
 
  Serial.println("closing connection");
  client.stop();

  delay(200);
}

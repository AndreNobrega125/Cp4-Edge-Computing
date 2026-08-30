#include <WiFi.h>
#include <PubSubClient.h>
#include "arduino_secrets.h"

const char* MQTT_BROKER = "broker.hivemq.com";
const int MQTT_PORTA = 1883;
const char* MQTT_TOPICO = "fiap/cp01/rack/temperatura";

const float FAIXA_MIN = 18.0;
const float FAIXA_MAX = 27.0;
const unsigned long INTERVALO_MS = 10000;

WiFiClient espClient;
PubSubClient cliente(espClient);

unsigned long ultimoEnvio = 0;

void conectarWiFi() {
  Serial.print("Conectando ao WiFi");
  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi conectado, IP: ");
  Serial.println(WiFi.localIP());
}

void conectarMQTT() {
  while (!cliente.connected()) {
    Serial.print("Conectando ao broker MQTT...");
    String clientId = "esp32-rack-" + String(random(0xffff), HEX);
    if (cliente.connect(clientId.c_str())) {
      Serial.println("conectado");
    } else {
      Serial.print("falhou, rc=");
      Serial.print(cliente.state());
      Serial.println(" tentando novamente em 5s");
      delay(5000);
    }
  }
}

float gerarLeituraMockada() {
  // 70% dentro da faixa aceitavel, 30% simulando anomalia (fora da faixa)
  if (random(100) < 70) {
    return FAIXA_MIN + (random(0, (int)((FAIXA_MAX - FAIXA_MIN) * 10) + 1)) / 10.0;
  } else {
    if (random(2) == 0) {
      return random(50, (int)(FAIXA_MIN * 10)) / 10.0;      // abaixo da faixa
    } else {
      return random((int)(FAIXA_MAX * 10) + 1, 400) / 10.0; // acima da faixa
    }
  }
}

void publicarLeitura() {
  float valor = gerarLeituraMockada();

  String payload = "{";
  payload += "\"sensor\":\"temperatura_rack\",";
  payload += "\"valor\":" + String(valor, 1) + ",";
  payload += "\"unidade\":\"C\",";
  payload += "\"timestamp\":\"" + String(millis()) + "\"";
  payload += "}";

  cliente.publish(MQTT_TOPICO, payload.c_str());
  Serial.print("Publicado: ");
  Serial.println(payload);
}

void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(0));
  conectarWiFi();
  cliente.setServer(MQTT_BROKER, MQTT_PORTA);
}

void loop() {
  if (!cliente.connected()) {
    conectarMQTT();
  }
  cliente.loop();

  unsigned long agora = millis();
  if (agora - ultimoEnvio >= INTERVALO_MS) {
    ultimoEnvio = agora;
    publicarLeitura();
  }
}

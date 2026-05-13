#include <DHT.h>

#define DHTPIN 8
#define DHTTYPE DHT11
#define RELE 7

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  pinMode(RELE, OUTPUT);
  digitalWrite(RELE, LOW);  // começa desligado
  dht.begin();
}

void loop() {
  // Verifica se chegou comando do Node-RED
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == '1') {
      digitalWrite(RELE, HIGH);  // liga
    } else if (cmd == '0') {
      digitalWrite(RELE, LOW);   // desliga
    }
  }

  // Lê e envia temperatura para o Node-RED
  float temperatura = dht.readTemperature();

  if (isnan(temperatura)) {
    Serial.println("0,0");
  } else {
    Serial.println(temperatura);
  }

  delay(2000);
}

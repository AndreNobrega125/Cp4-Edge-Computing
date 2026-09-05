# CP01 - Edge com Agentes de IA

Aplicação que usa **CrewAI** para receber dados de um sensor (mockado) conectado a um
**ESP32** via **MQTT** e decidir automaticamente para quem enviar um relatório:

- Se o dado estiver **fora da especificação** → relatório técnico para a **equipe de sustentação**
  (desvio, causas prováveis e ação recomendada).
- Se o dado estiver **dentro da especificação** → relatório executivo para a **direção**
  (status da operação e impacto positivo).

## Integrantes

- André Ayello de Nobrega — RM561754
- Caio Castelão Carminato — RM563630
- Guilherme Vasques Tamai — RM563276
- Mirella Mascarenhas — RM562092
- Vitor Komura de Freitas — RM563694

## Como funciona

1. **ESP32** ([`esp32_sensor_mock/esp32_sensor_mock.ino`](esp32_sensor_mock/esp32_sensor_mock.ino)) conecta ao WiFi e simula um
   sensor de temperatura de rack de servidor, publicando uma leitura mockada a cada 10s via
   MQTT no broker público HiveMQ (`broker.hivemq.com`), no tópico `fiap/cp01/rack/temperatura`.
2. **`main.py`** assina esse tópico, recebe cada leitura e avalia se o valor está dentro da
   faixa aceitável (18,0°C a 27,0°C).
3. Um agente **CrewAI** é acionado para escrever o relatório certo para o público certo:
   - fora da faixa → *Engenheiro de Sustentação de Infraestrutura*
   - dentro da faixa → *Analista de Performance de Infraestrutura*
4. O relatório é salvo em [`relatorios/`](relatorios) com data, hora, dados da leitura e o texto gerado.

Um script alternativo, [`sensor_publisher.py`](sensor_publisher.py), publica leituras mockadas direto do
computador (sem precisar do ESP32 físico), útil para testar o fluxo de ponta a ponta.

## Tecnologias

- Python 3.13, [CrewAI](https://www.crewai.com/), `paho-mqtt`, `python-dotenv`
- ESP32 (Arduino IDE), bibliotecas `WiFi.h` e `PubSubClient`
- Broker MQTT público HiveMQ

## Como rodar

### 1. App Python (CrewAI + MQTT)

Dentro da pasta do projeto, com [`uv`](https://docs.astral.sh/uv/) instalado:

```bash
uv sync
```

Crie um arquivo `.env` na raiz do projeto com sua chave da OpenAI:

```
OPENAI_API_KEY=sua_chave_aqui
```

Depois rode:

```bash
uv run python main.py
```

### 2. Firmware do ESP32

1. No Arduino IDE, instale o core **esp32 by Espressif Systems** e a biblioteca **PubSubClient**.
2. Abra a pasta [`esp32_sensor_mock`](esp32_sensor_mock) no IDE.
3. Crie o arquivo `esp32_sensor_mock/arduino_secrets.h` (não versionado) com:

   ```cpp
   #pragma once
   #define WIFI_SSID "sua_rede"
   #define WIFI_SENHA "sua_senha"
   ```

4. Selecione a placa **ESP32 Dev Module** e a porta correta, compile e faça o upload.
5. Abra o Serial Monitor (115200 baud) para acompanhar a conexão e as publicações.

## Estrutura

```
agentes-b2b/
├── main.py                          # App CrewAI que escuta o MQTT e gera os relatórios
├── sensor_publisher.py              # Publisher mockado alternativo (sem ESP32 físico)
├── esp32_sensor_mock/
│   ├── esp32_sensor_mock.ino        # Firmware do ESP32 (sensor mockado + MQTT)
│   └── arduino_secrets.h            # Credenciais de WiFi (não versionado)
└── relatorios/                      # Relatórios gerados pelo agente, um arquivo por leitura
```

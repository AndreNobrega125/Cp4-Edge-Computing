import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORTA = 1883
TOPICO = "fiap/cp01/rack/temperatura"

INTERVALO_SEGUNDOS = 10
FAIXA_MIN = 18.0
FAIXA_MAX = 27.0


def gerar_leitura() -> dict:
    if random.random() < 0.7:
        valor = round(random.uniform(FAIXA_MIN, FAIXA_MAX), 1)
    else:
        valor = round(
            random.choice(
                [
                    random.uniform(5.0, FAIXA_MIN - 0.1),
                    random.uniform(FAIXA_MAX + 0.1, 40.0),
                ]
            ),
            1,
        )

    return {
        "sensor": "temperatura_rack",
        "valor": valor,
        "unidade": "C",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    cliente.connect(BROKER, PORTA, keepalive=60)
    cliente.loop_start()

    print(f"Publicando leituras mockadas em '{TOPICO}' a cada {INTERVALO_SEGUNDOS}s (Ctrl+C para sair)")
    try:
        while True:
            leitura = gerar_leitura()
            cliente.publish(TOPICO, json.dumps(leitura))
            print(f"[PUBLICADO] {leitura}")
            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        pass
    finally:
        cliente.loop_stop()
        cliente.disconnect()


if __name__ == "__main__":
    main()

import json
import os
import sys
from datetime import datetime

import paho.mqtt.client as mqtt
from crewai import Agent, Crew, Task
from dotenv import load_dotenv

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

BROKER = "broker.hivemq.com"
PORTA = 1883
TOPICO = "fiap/cp01/rack/temperatura"

FAIXA_MIN = 18.0
FAIXA_MAX = 27.0

PASTA_RELATORIOS = os.path.join(os.path.dirname(__file__), "relatorios")

analista_sustentacao = Agent(
    role="Engenheiro de Sustentação de Infraestrutura",
    goal=(
        "Investigar leituras de sensores fora da especificação e orientar a "
        "equipe de sustentação sobre causa provável e ação corretiva"
    ),
    backstory=(
        "Você atua na equipe de sustentação de um datacenter corporativo, "
        "responsável por manter racks de servidores dentro da faixa segura de temperatura."
    ),
    verbose=True,
)

analista_diretoria = Agent(
    role="Analista de Performance de Infraestrutura",
    goal="Comunicar à direção os resultados operacionais quando os sensores indicam operação dentro do padrão",
    backstory=(
        "Você prepara relatórios executivos e traduz dados técnicos de infraestrutura "
        "em impacto de negócio para a diretoria."
    ),
    verbose=True,
)


def avaliar_leitura(leitura: dict) -> str:
    dentro_do_padrao = FAIXA_MIN <= leitura["valor"] <= FAIXA_MAX
    return "dentro_da_especificacao" if dentro_do_padrao else "fora_da_especificacao"


def montar_task(status: str, leitura: dict) -> Task:
    contexto = (
        f"Sensor: {leitura['sensor']}\n"
        f"Valor lido: {leitura['valor']} {leitura['unidade']}\n"
        f"Faixa aceitável: {FAIXA_MIN}-{FAIXA_MAX} {leitura['unidade']}\n"
        f"Horário da leitura: {leitura['timestamp']}"
    )

    if status == "fora_da_especificacao":
        return Task(
            description=(
                "Um sensor de temperatura de rack reportou um valor fora da faixa aceitável.\n"
                f"{contexto}\n\n"
                "Escreva um relatório curto e direto para a equipe de sustentação, contendo "
                "o desvio identificado, possíveis causas e a ação recomendada."
            ),
            expected_output="Relatório técnico em texto, com seções Desvio, Causas prováveis e Ação recomendada.",
            agent=analista_sustentacao,
        )

    return Task(
        description=(
            "Um sensor de temperatura de rack reportou um valor dentro da faixa aceitável.\n"
            f"{contexto}\n\n"
            "Escreva um relatório curto para a direção, destacando que a operação está estável "
            "e o impacto positivo disso (continuidade, redução de risco de falha, economia)."
        ),
        expected_output="Relatório executivo em texto, com seções Status e Impacto positivo.",
        agent=analista_diretoria,
    )


def salvar_relatorio(status: str, leitura: dict, resultado: str) -> str:
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)

    sufixo = "sustentacao" if status == "fora_da_especificacao" else "direcao"
    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    caminho = os.path.join(PASTA_RELATORIOS, f"{agora}_{sufixo}.md")

    destinatario = "Equipe de Sustentação" if status == "fora_da_especificacao" else "Direção"
    conteudo = (
        f"# Relatório para: {destinatario}\n\n"
        f"- Gerado em: {agora}\n"
        f"- Sensor: {leitura['sensor']}\n"
        f"- Valor lido: {leitura['valor']} {leitura['unidade']}\n"
        f"- Faixa aceitável: {FAIXA_MIN}-{FAIXA_MAX} {leitura['unidade']}\n"
        f"- Status: {status}\n\n"
        f"---\n\n"
        f"{resultado}\n"
    )

    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)

    return caminho


def processar_leitura(leitura: dict) -> None:
    status = avaliar_leitura(leitura)
    print(f"\n[LEITURA] {leitura} -> status: {status}")

    task = montar_task(status, leitura)
    crew = Crew(agents=[task.agent], tasks=[task], verbose=True)
    resultado = crew.kickoff()

    destinatario = "equipe de sustentação" if status == "fora_da_especificacao" else "direção"
    print(f"\n[RELATÓRIO -> {destinatario}]\n{resultado}\n")

    caminho = salvar_relatorio(status, leitura, str(resultado))
    print(f"[SALVO EM] {caminho}\n")


def ao_conectar(cliente, userdata, flags, reason_code, properties=None):
    print(f"Conectado ao broker MQTT ({BROKER}) com código: {reason_code}")
    cliente.subscribe(TOPICO)


def ao_receber(cliente, userdata, mensagem):
    try:
        leitura = json.loads(mensagem.payload.decode())
    except json.JSONDecodeError:
        print(f"Payload inválido recebido em {TOPICO}: {mensagem.payload!r}")
        return
    processar_leitura(leitura)


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY não encontrada no ambiente. Configure o .env antes de rodar.")

    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber

    cliente.connect(BROKER, PORTA, keepalive=60)
    print(f"Aguardando leituras em '{TOPICO}'... (Ctrl+C para sair)")
    cliente.loop_forever()


if __name__ == "__main__":
    main()

import requests
import time
import os
ultimo_giro = 0

TOKEN = os.getenv("TOKEN")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")

MOEDAS_FREE = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
    "litecoin": "LTC"
}

historico = {}
ultimo_sinal = {}
ultimo_preco_compra = {}

for coin in MOEDAS_FREE:
    historico[coin] = []

def get_price(coin):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        data = requests.get(url).json()
        return data[coin]["usd"]
    except:
        return None

def calcular_rsi(precos, periodo=14):
    if len(precos) < periodo:
        return None

    ganhos = []
    perdas = []

    for i in range(1, len(precos)):
        diff = precos[i] - precos[i-1]
        if diff >= 0:
            ganhos.append(diff)
        else:
            perdas.append(abs(diff))

    media_ganho = sum(ganhos[-periodo:]) / periodo if ganhos else 0
    media_perda = sum(perdas[-periodo:]) / periodo if perdas else 1

    rs = media_ganho / media_perda
    return 100 - (100 / (1 + rs))

def enviar_free(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID_FREE, "text": msg})

enviar_free("🟢 Bot FREE reiniciado e funcionando")
def giro_mercado():
        mensagem = "🌎 GIRO DO MERCADO\n\n"

        for coin, simbolo in MOEDAS_FREE.items():
            try:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd&include_24hr_change=true"
                data = requests.get(url).json()

                preco = data[coin]["usd"]
                variacao = data[coin]["usd_24h_change"]

                if variacao > 1:
                    resumo = "🟢 Subindo bem"
                elif variacao > 0:
                    resumo = "🟡 Leve alta"
                elif variacao > -2:
                    resumo = "🔴 Leve queda"
                else:
                    resumo = "🔴 Queda forte"

                mensagem += (
                    f"🪙 {simbolo}\n"
                    f"Preço: ${preco}\n"
                    f"Variação 24h: {variacao:.2f}%\n"
                    f"{resumo}\n\n"
                )

            except:
                continue

        return mensagem

while True:
    try:
        print("Rodando...")

        for coin, simbolo in MOEDAS_FREE.items():
            preco = get_price(coin)

            if preco is None:
                continue

            historico[coin].append(preco)

            if len(historico[coin]) > 50:
                historico[coin].pop(0)

            rsi = calcular_rsi(historico[coin])

            if rsi is None:
                continue

            if rsi < 35:
                if coin not in ultimo_sinal or ultimo_sinal[coin] != "COMPRA":
                    enviar_free(
                        f"🟢 COMPRA\n"
                        f"Moeda: {simbolo}\n"
                        f"Preço: ${preco}\n"
                        f"RSI: {rsi:.2f}"
                    )
                    ultimo_sinal[coin] = "COMPRA"
                    ultimo_preco_compra[coin] = preco

            elif rsi > 60:
                if coin in ultimo_preco_compra and preco >= ultimo_preco_compra[coin] * 1.01:
                    if coin not in ultimo_sinal or ultimo_sinal[coin] != "VENDA":
                        enviar_free(
                            f"🔴 VENDA\n"
                            f"Moeda: {simbolo}\n"
                            f"Preço: ${preco}\n"
                            f"RSI: {rsi:.2f}"
                        )
                        ultimo_sinal[coin] = "VENDA"
        agora = time.time()
        print("Verificando giro...")
        if agora - ultimo_giro > 1800:
           mensagem = giro_mercado()
           enviar_free(mensagem)
           ultimo_giro = agora
    
        time.sleep(60)

    except Exception as e:
        print("Erro:", e)
        time.sleep(10)

import requests
import time

import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

MOEDAS = {    
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "litecoin": "LTC",
    "binancecoin": "BNB",
    "tether": "USDT",
    "ripple": "XRP",      # XRP
    "solana": "SOL"       # SOL
}

def get_price(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
    data = requests.get(url).json()
    return data[coin]["usd"]

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
    rsi = 100 - (100 / (1 + rs))

    return rsi

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

historico = {coin: [] for coin in MOEDAS}
enviar_telegram("🚀 Bot online!")
while True:
    try:
        for coin, simbolo in MOEDAS.items():
            preco = get_price(coin)
            historico[coin].append(preco)

            if len(historico[coin]) > 50:
                historico[coin].pop(0)

            rsi = calcular_rsi(historico[coin])

            if rsi:
                if rsi < 35:
                    enviar_telegram(
                        f"{'🟢 COMPRA' if sinal=='COMPRA' else '🔴 VENDA'}\n"
                        f"Moeda: {simbolo} ({coin.upper()})\n"
                        f"Preço: ${preco}\n"
                        f"RSI: {rsi:.2f}"
)        
        time.sleep(60)

    except Exception as e:
        print("Erro:", e)        
        time.sleep(10)

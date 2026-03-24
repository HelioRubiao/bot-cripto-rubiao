import requests
import time
import feedparser
import pandas as pd

import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

moedas = {
    "bitcoin": "usd",
    "ethereum": "usd",
    "litecoin": "usd",
    "binancecoin": "usd",
    "tether": "brl",
    "ripple": "usd",      # XRP
    "solana": "usd"       # SOL
}

historico_precos = {moeda: [] for moeda in moedas}

ultima_noticia = ""
ultimo_envio_noticia = 0

def calcular_rsi(precos, periodo=14):
    if len(precos) < periodo:
        return None

    series = pd.Series(precos)
    delta = series.diff()

    ganho = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perda = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()

    rs = ganho / perda
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]

def enviar_noticia():
    global ultima_noticia

    import random

    feeds = [
        "https://portaldobitcoin.uol.com.br/feed/",
        "https://livecoins.com.br/feed/",
        "https://cointelegraph.com.br/rss"
    ]

    feed_url = random.choice(feeds)
    feed = feedparser.parse(feed_url)

    if len(feed.entries) == 0:
        print("Sem notícias")
        return

    noticia = feed.entries[0]

    if noticia.title == ultima_noticia:
        print("Notícia repetida")
        return

    ultima_noticia = noticia.title

    msg = (
        "📰 NOTÍCIA CRIPTO (BR)\n\n"
        f"{noticia.title}\n\n"
        f"{noticia.link}"
    )

    print("Enviando notícia...")
    enviar_telegram(
    "🚀 💎 Em breve: sinais completos no grupo VIP\n"
    "📊 Monitorando mercado em tempo real..."
)
enviar_noticia()

while True:

    ids = ",".join(moedas.keys())
    vs = ",".join(set(moedas.values()))

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies={vs}"

    try:
        response = requests.get(url)

        if response.status_code == 429:
            print("Rate limit atingido... aguardando")
            time.sleep(120)
            continue

        elif response.status_code != 200:
            print("Erro na API:", response.status_code)
            time.sleep(10)
            continue

        data = response.json()

    except Exception as e:
        print("Erro ao pegar dados:", e)
        time.sleep(10)
        continue

    for moeda, moeda_vs in moedas.items():

        if moeda in data and moeda_vs in data[moeda]:
            preco = data[moeda][moeda_vs]
        else:
            print(f"Erro ao pegar preço de {moeda}")
            continue

        historico_precos[moeda].append(preco)

        if len(historico_precos[moeda]) > 50:
            historico_precos[moeda].pop(0)

        rsi = calcular_rsi(historico_precos[moeda])

        if rsi is None:
            continue

        if rsi < 45:
            enviar_telegram(f"🟢 COMPRA {moeda.upper()} | RSI: {rsi:.2f} | Preço: {preco}")

        elif rsi > 50:
            enviar_telegram(f"🔴 VENDA {moeda.upper()} | RSI: {rsi:.2f} | Preço: {preco}")

    # notícias
    if time.time() - ultimo_envio_noticia > 1800:
        enviar_noticia()
        ultimo_envio_noticia = time.time()

    time.sleep(60)

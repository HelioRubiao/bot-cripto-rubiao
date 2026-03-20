import requests
import time
import feedparser

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
    "tether": "brl"
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

    feed = feedparser.parse("https://www.coindesk.com/arc/outboundfeeds/rss/")

    if len(feed.entries) == 0:
        return

    noticia = feed.entries[0]

    if noticia.title == ultima_noticia:
        return

    ultima_noticia = noticia.title

    msg = (
        "📰 NOTÍCIA CRIPTO\n\n"
        f"{noticia.title}\n\n"
        f"{noticia.link}"
    )

    enviar_telegram(msg)

while True:

    ids = ",".join(moedas.keys())
    vs = ",".join(set(moedas.values()))

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies={vs}"
    data = requests.get(url).json()

    for moeda, moeda_vs in moedas.items():

        preco = data[moeda][moeda_vs]

        historico_precos[moeda].append(preco)

        if len(historico_precos[moeda]) > 50:
            historico_precos[moeda].pop(0)

        rsi = calcular_rsi(historico_precos[moeda])

        if rsi is None:
    continue

if rsi < 30:
    enviar_telegram(
        f"🟢 OPORTUNIDADE DE COMPRA\n\n"
        f"{moeda.upper()}\n"
        f"Preço: {preco}\n"
        f"RSI: {rsi:.2f}"
    )

elif rsi > 70:
    enviar_telegram(
        f"🔴 POSSÍVEL REALIZAÇÃO\n\n"
        f"{moeda.upper()}\n"
        f"Preço: {preco}\n"
        f"RSI: {rsi:.2f}"
    )
    # notícia a cada 30 minutos
    if time.time() - ultimo_envio_noticia > 1800:
        enviar_noticia()
        ultimo_envio_noticia = time.time()

    time.sleep(60)

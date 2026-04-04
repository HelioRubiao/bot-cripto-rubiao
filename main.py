import requests
import time
ultimo_sinal = {}
ultimo_preco_compra = {}
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")
CHAT_ID_V1 = os.getenv("CHAT_ID_V1")
MAPA_BINANCE = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
    "litecoin": "LTC",
    "binancecoin": "BNB",
    "cardano": "ADA",
    "dogecoin": "DOGE",
    "tron": "TRX",
    "avalanche-2": "AVAX"
}
MOEDAS_FREE = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
    "litecoin": "LTC"
}

MOEDAS_V1 = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
    "litecoin": "LTC",
    "binancecoin": "BNB",
    "cardano": "ADA",
    "dogecoin": "DOGE",
    "tron": "TRX",
    "avalanche-2": "AVAX"
}
def get_price(coin):
    try:
        symbol = MAPA_BINANCE[coin]
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        response = requests.get(url)
        data = response.json()
        return float(data["price"])
    except:
        return None

def calcular_rsi(precos, periodo=14):
    if len(precos) < periodo:
        return None
def get_price_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        response = requests.get(url)
        data = response.json()
        return float(data["price"])
    except:
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

def enviar_free(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID_FREE, "text": msg})

def enviar_v1(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID_V1, "text": msg})

historico = {}

for coin in set(list(MOEDAS_FREE.keys()) + list(MOEDAS_V1.keys())):
    historico[coin] = []
enviar_free("🟢 Free funcionando")
enviar_v1("🔒 VIP funcionando")

ultima_noticia = 0

while True:
    try:
        #free
        for coin, simbolo in MOEDAS_FREE.items():
            preco = get_price(coin)
            historico[coin].append(preco)

            if len(historico[coin]) > 50:
                historico[coin].pop(0)

            rsi = calcular_rsi(historico[coin])

            media = sum(historico[coin]) / len(historico[coin])

            
            if rsi < 35 and preco < media:
            
                    if coin not in ultimo_sinal or ultimo_sinal[coin] != "COMPRA":
                        enviar_free(
                            f"🟢 COMPRA\n"
                            f"Moeda: {simbolo} ({coin.upper()})\n"
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
                                f"Moeda: {simbolo} ({coin.upper()})\n"
                                f"Preço: ${preco}\n"
                                f"RSI: {rsi:.2f}"
                )
                ultimo_sinal[coin] = "VENDA"
                
                    #V1
        for coin, simbolo in MOEDAS_V1.items():
            preco = get_price(coin)
            historico[coin].append(preco)

            if len(historico[coin]) > 50:
                historico[coin].pop(0)

            rsi = calcular_rsi(historico[coin])

            if rsi:
                if rsi < 35:
                    enviar_v1(
                    f"🔥 SINAL VIP\n"
                    f"Moeda: {simbolo} ({coin.upper()})\n"
                    f"Preço: ${preco}\n"
                    f"RSI: {rsi:.2f}\n"
                    f"⚡ Possível oportunidade identificada"
            ) 
                    
        agora = time.time()

        if agora - ultima_noticia > 1800:  # 30 minutos
           enviar_telegram("📰 Atualização do mercado em breve...")
           ultima_noticia = agora
        time.sleep(60)

    except Exception as e:
        print("Erro:", e)        
        time.sleep(10)

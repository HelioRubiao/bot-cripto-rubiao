import requests
import time
import os
resultado_dia = []
ultimo_resumo = 0
ultimo_sinal_free = {}
ultimo_sinal_v1 = {}

ultimo_preco_compra_free = {}
ultimo_preco_compra_v1 = {}

TOKEN = os.getenv("TOKEN")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")
CHAT_ID_V1 = os.getenv("CHAT_ID_V1")

MOEDAS_FREE = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
    "binancecoin" : "BNB",
    "litecoin": "LTC"
}
MOEDAS_V1 = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
    "binancecoin": "BNB",
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
def enviar_v1(msg):
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID_V1, "text": msg})

enviar_free("🟢 Bot FREE reiniciado e funcionando")
enviar_v1("🔒 VIP funcionando")

def resumo_resultado():
    if not resultado_dia:
        return "📊 RESUMO DO DIA\n\nNenhuma operação fechada ainda."

    total = sum(resultado_dia)
    media = total / len(resultado_dia)

    return (
        "📊 RESUMO DO DIA\n\n"
        f"Operações: {len(resultado_dia)}\n"
        f"Resultado acumulado: {total:.2f}%\n"
        f"Média por operação: {media:.2f}%\n\n"
        "⚠️ Simulação baseada nos sinais do bot"
    )

while True:
    try:
        print("Rodando...")

        for coin, simbolo in MOEDAS_FREE.items():
            preco = get_price_binance(MAPA_BINANCE[coin])

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
                        f"RSI: {rsi:.2f}\n"
                        f"📊 Sinal baseado no mercado global (COINGEKO)"
                    )
                    ultimo_sinal_free[coin] = "COMPRA"
                    ultimo_preco_compra_free[coin] = preco
                for coin, simbolo in MOEDAS_V1.items():
                    preco = get_price(coin)

                    if preco is None:
                        continue

                    historico[coin].append(preco)

                    if len(historico[coin]) > 50:
                        historico[coin].pop(0)

                    rsi = calcular_rsi(historico[coin])

                    if rsi is None:
                        continue

                    
                        
            elif rsi > 60:
                if coin in ultimo_preco_compra and preco >= ultimo_preco_compra[coin] * 1.01:
                    if coin not in ultimo_sinal or ultimo_sinal[coin] != "VENDA":

                        lucro = ((preco - ultimo_preco_compra[coin]) / ultimo_preco_compra[coin]) * 100
                        resultado_dia.append(lucro)

                        enviar_free(
                            f"🔴 VENDA\n"
                            f"Moeda: {simbolo}\n"
                            f"Preço: ${preco}\n"
                            f"RSI: {rsi:.2f}"
                        )
                        ultimo_sinal_free[coin] = "VENDA"
     #v1
            if rsi < 35:
                        enviar_v1(
                            f"🔥 SINAL VIP\n\n"
                            f"🪙 Moeda: {simbolo}\n"
                            f"💰 Preço: ${preco}\n"
                            f"📊 RSI: {rsi:.2f}\n\n"
                            f"🎯 Entrada identificada\n"
                            f"⚠️ Gestão de risco recomendada"
)
            agora = time.time()

            if agora - ultimo_resumo > 86400:  # 24 horas
                mensagem = resumo_resultado()
                enviar_free(mensagem)
                resultado_dia.clear()
                ultimo_resumo = agora
                
        time.sleep(60)

    except Exception as e:
        print("Erro:", e)
        time.sleep(10)

import requests
import time
import os

# --- CONFIGURAÇÕES DE AMBIENTE ---
# Certifique-se de configurar estas variáveis no seu novo servidor
TOKEN = os.getenv("TOKEN")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")
CHAT_ID_V1 = os.getenv("CHAT_ID_V1")
CHAT_ID_V2 = os.getenv("CHAT_ID_V2")

# Moedas fixas do Grupo FREE
MOEDAS_FREE_IDS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
    "binancecoin": "BNB",
    "litecoin": "LTC",
    "kucoin-shares": "KCS"
}

# Estados do Bot
historico = {}
ultimo_sinal = {"free": {}, "v1": {}, "v2": {}}
preco_compra = {"free": {}, "v1": {}, "v2": {}}
resultado_dia = []
ultimo_resumo = time.time()

# --- FUNÇÕES DE API ---

def get_binance_top_100():
    """Busca as 100 moedas com maior volume na Binance."""
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=10).json()
        tickers = [t for t in response if t['symbol'].endswith('USDT')]
        tickers.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
        return [t['symbol'].replace('USDT', '') for t in tickers[:100]]
    except Exception as e:
        print(f"Erro ao buscar Top 100 Binance: {e}")
        return []

def get_price_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT"
        response = requests.get(url, timeout=10).json()
        return float(response["price"])
    except:
        return None

def get_price_kucoin(symbol):
    try:
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol.upper()}-USDT"
        response = requests.get(url, timeout=10).json()
        return float(response["data"]["price"])
    except:
        return None

def get_price_coingecko(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        data = requests.get(url, timeout=10).json()
        return data[coin_id]["usd"]
    except:
        return None

# --- INDICADORES ---

def calcular_rsi(precos, periodo=14):
    if len(precos) < periodo + 1:
        return None
    
    ganhos = []
    perdas = []
    for i in range(1, len(precos)):
        diff = precos[i] - precos[i-1]
        if diff >= 0: ganhos.append(diff)
        else: perdas.append(abs(diff))
    
    if not ganhos or not perdas: return 50
    
    media_ganho = sum(ganhos[-periodo:]) / periodo
    media_perda = sum(perdas[-periodo:]) / periodo
    
    if media_perda == 0: return 100
    rs = media_ganho / media_perda
    return 100 - (100 / (1 + rs))

# --- MENSAGENS ---

def enviar_telegram(chat_id, msg):
    if not TOKEN or not chat_id: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Erro envio Telegram: {e}")

# --- INICIALIZAÇÃO ---

print("🤖 Robô de Sinais Iniciado com Sucesso!")

# Mensagem padrão solicitada para os 3 grupos
MENSAGEM_REINICIO = "✅ *Grupo de sinais ok* 👍"

enviar_telegram(CHAT_ID_FREE, MENSAGEM_REINICIO)
enviar_telegram(CHAT_ID_V1, MENSAGEM_REINICIO)
enviar_telegram(CHAT_ID_V2, MENSAGEM_REINICIO)

# Mensagens informativas de Status
enviar_telegram(CHAT_ID_FREE, "🟢 *Bot FREE Online*\nMonitorando principais moedas + KCS e LTC.")
enviar_telegram(CHAT_ID_V1, "🔒 *Bot VIP V1 Online*\nMonitorando Top 100 Binance + KCS.\n*Alvo: 2%*")
enviar_telegram(CHAT_ID_V2, "⚡ *Bot VIP V2 Scalping Online*\nMonitorando Top 100 Binance + KCS.\n*Alvo: 0.7%*")

# --- LOOP PRINCIPAL ---

while True:
    try:
        # Atualiza o Top 100 da Binance a cada ciclo (ou você pode mover para fora do loop para economizar API)
        moedas_binance = get_binance_top_100()
        todas_vips = list(set(moedas_binance + ["KCS"]))

        # 1. PROCESSAMENTO GRUPO FREE
        for id_cg, simbolo in MOEDAS_FREE_IDS.items():
            preco = get_price_kucoin(simbolo) if simbolo == "KCS" else get_price_coingecko(id_cg)
            if preco:
                key = f"free_{simbolo}"
                if key not in historico: historico[key] = []
                historico[key].append(preco)
                if len(historico[key]) > 50: historico[key].pop(0)

                rsi = calcular_rsi(historico[key])
                if rsi and rsi < 35:
                    if ultimo_sinal["free"].get(simbolo) != "COMPRA":
                        enviar_telegram(CHAT_ID_FREE, f"🟢 *COMPRA FREE*\nMoeda: {simbolo}\nPreço: ${preco}\nRSI: {rsi:.2f}")
                        ultimo_sinal["free"][simbolo] = "COMPRA"
                        preco_compra["free"][simbolo] = preco
                elif rsi and rsi > 60:
                    if ultimo_sinal["free"].get(simbolo) == "COMPRA":
                        lucro = ((preco - preco_compra["free"][simbolo]) / preco_compra["free"][simbolo]) * 100
                        enviar_telegram(CHAT_ID_FREE, f"🔴 *VENDA FREE*\nMoeda: {simbolo}\nPreço: ${preco}\nLucro: {lucro:.2f}%")
                        ultimo_sinal["free"][simbolo] = "VENDA"
                        resultado_dia.append(lucro)

        # 2. PROCESSAMENTO VIP V1 (Top 100 Binance + KCS)
        for simbolo in todas_vips:
            preco = get_price_kucoin("KCS") if simbolo == "KCS" else get_price_binance(simbolo)
            if preco:
                key = f"v1_{simbolo}"
                if key not in historico: historico[key] = []
                historico[key].append(preco)
                if len(historico[key]) > 60: historico[key].pop(0)

                rsi = calcular_rsi(historico[key])
                if ultimo_sinal["v1"].get(simbolo) != "COMPRA":
                    if rsi and rsi < 35:
                        enviar_telegram(CHAT_ID_V1, f"🟢 *VIP V1: COMPRA*\nMoeda: {simbolo}\nPreço: ${preco}\nRSI: {rsi:.2f}")
                        ultimo_sinal["v1"][simbolo] = "COMPRA"
                        preco_compra["v1"][simbolo] = preco
                else:
                    lucro = ((preco - preco_compra["v1"][simbolo]) / preco_compra["v1"][simbolo]) * 100
                    if lucro >= 2.0 or (rsi and rsi > 75):
                        status = "ALVO 2% ATINGIDO" if lucro >= 2.0 else "SAÍDA RSI ALTO"
                        enviar_telegram(CHAT_ID_V1, f"🔵 *VIP V1: {status}*\nMoeda: {simbolo}\nLucro: {lucro:.2f}%")
                        ultimo_sinal["v1"][simbolo] = "VENDA"
                        resultado_dia.append(lucro)

        # 3. PROCESSAMENTO VIP V2 (Scalping)
        for simbolo in todas_vips:
            preco = get_price_kucoin("KCS") if simbolo == "KCS" else get_price_binance(simbolo)
            if preco:
                key = f"v2_{simbolo}"
                if key not in historico: historico[key] = []
                historico[key].append(preco)
                if len(historico[key]) > 30: historico[key].pop(0)

                rsi = calcular_rsi(historico[key], periodo=7)
                if ultimo_sinal["v2"].get(simbolo) != "COMPRA":
                    if rsi and rsi < 30:
                        enviar_telegram(CHAT_ID_V2, f"⚡ *V2 SCALP: COMPRA*\nMoeda: {simbolo}\nPreço: ${preco}\nRSI: {rsi:.2f}")
                        ultimo_sinal["v2"][simbolo] = "COMPRA"
                        preco_compra["v2"][simbolo] = preco
                else:
                    lucro = ((preco - preco_compra["v2"][simbolo]) / preco_compra["v2"][simbolo]) * 100
                    if lucro >= 0.7:
                        enviar_telegram(CHAT_ID_V2, f"🔥 *V2 SCALP: FECHADO*\nMoeda: {simbolo}\nLucro: {lucro:.2f}%")
                        ultimo_sinal["v2"][simbolo] = "VENDA"
                        resultado_dia.append(lucro)

        # 4. RESUMO DIÁRIO
        if time.time() - ultimo_resumo > 86400:
            msg = "📊 *RESUMO DO DIA*"
            if resultado_dia:
                total = sum(resultado_dia)
                media = total / len(resultado_dia)
                msg += f"\n\nOperações: {len(resultado_dia)}\nResultado: {total:.2f}%\nMédia: {media:.2f}%"
            else:
                msg += "\nNenhuma operação fechada hoje."
            
            for cid in [CHAT_ID_FREE, CHAT_ID_V1, CHAT_ID_V2]:
                enviar_telegram(cid, msg)
            
            resultado_dia = []
            ultimo_resumo = time.time()

        print(f"Ciclo concluído. ({time.strftime('%H:%M:%S')})")
        time.sleep(60)

    except Exception as e:
        print(f"Erro no loop geral: {e}")
        time.sleep(20)

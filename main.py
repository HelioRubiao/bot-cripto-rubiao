import requests
import time
import os

# --- ATENÇÃO: Use 'python3 bot.py' no Render e mude o Runtime para Python ---
TOKEN = os.getenv("TOKEN")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")
CHAT_ID_V1 = os.getenv("CHAT_ID_V1")
CHAT_ID_V2 = os.getenv("CHAT_ID_V2")

MOEDAS_FREE_IDS = {
    "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL",
    "ripple": "XRP", "binancecoin": "BNB", "litecoin": "LTC", "kucoin-shares": "KCS"
}

historico = {}
ultimo_sinal = {"free": {}, "v1": {}, "v2": {}}
preco_compra = {"free": {}, "v1": {}, "v2": {}}
resultado_dia = []
ultimo_resumo = time.time()

def get_binance_top_100():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=10).json()
        tickers = [t for t in response if t['symbol'].endswith('USDT')]
        tickers.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
        return [t['symbol'].replace('USDT', '') for t in tickers[:100]]
    except: return []

def enviar_telegram(chat_id, msg):
    if not TOKEN or not chat_id: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=10)

# --- INICIALIZAÇÃO COM MENSAGEM OK ---
print("🤖 Robô Iniciado!")
msg_ok = "✅ *Grupo de sinais ok!* 👍🟢"
enviar_telegram(CHAT_ID_FREE, f"{msg_ok}\n*Bot FREE Online*")
enviar_telegram(CHAT_ID_V1, f"{msg_ok}\n*Bot VIP V1 Online* (Alvo 2%)")
enviar_telegram(CHAT_ID_V2, f"{msg_ok}\n*Bot VIP V2 Scalping Online* (Alvo 0.7%)")

while True:
    try:
        moedas_binance = get_binance_top_100()
        todas_vips = list(set(moedas_binance + ["KCS"]))
        
        # ... (Logica de processamento similar à que converti para o server.ts acima)
        
        time.sleep(60)
    except Exception as e:
        print(f"Erro: {e}")
        time.sleep(20)

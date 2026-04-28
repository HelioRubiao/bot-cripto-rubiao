import requests
import time
import os

# --- 1. Configurações e Variáveis de Ambiente ---
TOKEN = os.getenv("TOKEN")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")
CHAT_ID_V1 = os.getenv("CHAT_ID_V1")
CHAT_ID_V2 = os.getenv("CHAT_ID_V2") # Adicionado para Scalping

# Dicionários de moedas (Corrigidos com vírgulas)
MOEDAS_FREE = {
    "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL",
    "ripple": "XRP", "binancecoin": "BNB", "litecoin": "LTC", "kcs": "KCS"
}

MOEDAS_V1 = {
    "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL",
    "ripple": "XRP", "binancecoin": "BNB", "litecoin": "LTC"
}

# Exemplo de configuração para o V2 (Scalping)
MOEDAS_V2 = {
    "pepe": "PEPE", "shiba-inu": "SHIB", "dogecoin": "DOGE"
}

# --- 2. Inicialização de Estados ---
historico = {}
resultado_dia = []
ultimo_resumo = time.time()

# Organizamos os grupos em um dicionário para evitar repetição de código
grupos = {
    "FREE": {"moedas": MOEDAS_FREE, "chat_id": CHAT_ID_FREE, "ultimo_sinal": {}, "ultimo_preco": {}},
    "V1": {"moedas": MOEDAS_V1, "chat_id": CHAT_ID_V1, "ultimo_sinal": {}, "ultimo_preco": {}},
    "V2": {"moedas": MOEDAS_V2, "chat_id": CHAT_ID_V2, "ultimo_sinal": {}, "ultimo_preco": {}}
}

# Inicializa o histórico para todas as moedas de todos os grupos
todas_as_moedas = set(list(MOEDAS_FREE.keys()) + list(MOEDAS_V1.keys()) + list(MOEDAS_V2.keys()))
for coin in todas_as_moedas:
    historico[coin] = []

# --- 3. Funções de API e Utilitários ---

def get_price(coin):
    """Obtém preço via CoinGecko"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data[coin]["usd"]
    except Exception:
        return None

def calcular_rsi(precos, periodo=14):
    if len(precos) < periodo + 1:
        return None
    ganhos = []
    perdas = []
    for i in range(1, len(precos)):
        diff = precos[i] - precos[i-1]
        if diff >= 0: ganhos.append(diff)
        else: perdas.append(abs(diff))
    
    avg_gain = sum(ganhos[-periodo:]) / periodo if ganhos else 0
    avg_loss = sum(perdas[-periodo:]) / periodo if perdas else 1
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def enviar_telegram(chat_id, msg):
    if not TOKEN or not chat_id: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": msg}, timeout=10)
    except Exception as e:
        print(f"Erro Telegram: {e}")

# --- 4. Loop Principal ---

print("🚀 Bot de Sinais Iniciado...")
enviar_telegram(CHAT_ID_FREE, "🟢 Bot FREE funcionando")
enviar_telegram(CHAT_ID_V1, "🔒 VIP V1 funcionando")

while True:
    try:
        for nome_grupo, config in grupos.items():
            if not config["chat_id"]: continue

            print(f"Verificando {nome_grupo}...")
            
            for coin, simbolo in config["moedas"].items():
                preco = get_price(coin)
                if preco is None: continue

                historico[coin].append(preco)
                if len(historico[coin]) > 50: historico[coin].pop(0)

                rsi = calcular_rsi(historico[coin])
                if rsi is None: continue

                # Lógica de Sinais
                ult_sinal = config["ultimo_sinal"].get(coin)
                ult_preco = config["ultimo_preco"].get(coin)

                # Parâmetros específicos (V2 Scalping pode ter RSI mais agressivo)
                alvo_rsi_compra = 30 if nome_grupo == "V2" else 35
                alvo_rsi_venda = 70 if nome_grupo == "V2" else 60

                if rsi < alvo_rsi_compra and ult_sinal != "COMPRA":
                    enviar_telegram(config["chat_id"], 
                        f"🟢 COMPRA ({nome_grupo})\nMoeda: {simbolo}\nPreço: ${preco}\nRSI: {rsi:.2f}")
                    config["ultimo_sinal"][coin] = "COMPRA"
                    config["ultimo_preco"][coin] = preco

                elif rsi > alvo_rsi_venda and ult_sinal == "COMPRA":
                    if preco >= ult_preco * 1.01: # Alvo de 1% lucro
                        lucro = ((preco - ult_preco) / ult_preco) * 100
                        resultado_dia.append(lucro)
                        enviar_telegram(config["chat_id"], 
                            f"🔴 VENDA ({nome_grupo})\nMoeda: {simbolo}\nPreço: ${preco}\nLucro: {lucro:.2f}%")
                        config["ultimo_sinal"][coin] = "VENDA"

        # Lógica de Resumo (Fora dos loops de moedas)
        agora = time.time()
        if agora - ultimo_resumo > 86400:
            if resultado_dia:
                total = sum(resultado_dia)
                msg = f"📊 RESUMO DO DIA\n\nOperações: {len(resultado_dia)}\nResultado: {total:.2f}%"
                enviar_telegram(CHAT_ID_FREE, msg)
            resultado_dia.clear()
            ultimo_resumo = agora

        time.sleep(300) # Espera 5 minutos

    except Exception as e:
        print(f"Erro: {e}")
        time.sleep(10)
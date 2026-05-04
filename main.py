import requests
import time
import os

# Configurações de Ambiente
TOKEN = os.getenv("TOKEN")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")
CHAT_ID_V1 = os.getenv("CHAT_ID_V1")
CHAT_ID_V2 = os.getenv("CHAT_ID_V2") # Certifique-se de configurar este env

# Listas de Moedas
MOEDAS_FIXAS_FREE = ["BTC", "ETH", "SOL", "XRP", "BNB", "LTC", "KCS"]

# Estruturas de Dados
historico = {}  # { 'BTC': [precos...] }
estados = {
    "free": {"sinais": {}, "compras": {}},
    "v1": {"sinais": {}, "compras": {}},
    "v2": {"sinais": {}, "compras": {}}
}
resultado_dia = []
ultimo_resumo = time.time()

# --- FUNÇÕES DE API ---

def get_top_100_binance():
    """Busca as 100 moedas com maior volume nas últimas 24h na Binance."""
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url).json()
        # Filtra apenas pares USDT e ordena por volume
        pares_usdt = [item for item in response if item['symbol'].endswith('USDT')]
        ordenados = sorted(pares_usdt, key=lambda x: float(x['quoteVolume']), reverse=True)
        top_100 = [item['symbol'].replace('USDT', '') for item in ordenados[:100]]
        return top_100
    except Exception as e:
        print(f"Erro ao buscar Top 100 Binance: {e}")
        return []

def get_price(symbol):
    """Tenta buscar preço na Binance, se não achar (como KCS), busca na KuCoin."""
    # Tenta Binance
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        res = requests.get(url).json()
        if "price" in res:
            return float(res["price"])
    except:
        pass
    
    # Tenta KuCoin (Geralmente para KCS)
    try:
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}-USDT"
        res = requests.get(url).json()
        if res.get("data") and res["data"].get("price"):
            return float(res["data"]["price"])
    except:
        pass
    
    return None

def enviar_telegram(chat_id, msg):
    if not chat_id or not TOKEN: return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg})
    except Exception as e:
        print(f"Erro Telegram: {e}")

# --- LÓGICA MATEMÁTICA ---

def calcular_rsi(precos, periodo=14):
    if len(precos) < periodo + 1: return None
    ganhos = []
    perdas = []
    for i in range(1, len(precos)):
        diff = precos[i] - precos[i-1]
        ganhos.append(max(0, diff))
        perdas.append(max(0, -diff))
    
    avg_ganho = sum(ganhos[-periodo:]) / periodo
    avg_perda = sum(perdas[-periodo:]) / periodo
    if avg_perda == 0: return 100
    rs = avg_ganho / avg_perda
    return 100 - (100 / (1 + rs))

# --- EXECUÇÃO PRINCIPAL ---

def processar_sinais(grupo, moedas, chat_id, rsi_compra, alvo_lucro, prefixo):
    for coin in moedas:
        preco = get_price(coin)
        if preco is None: continue

        # Atualiza histórico global da moeda
        if coin not in historico: historico[coin] = []
        historico[coin].append(preco)
        if len(historico[coin]) > 50: historico[coin].pop(0)

        rsi = calcular_rsi(historico[coin])
        if rsi is None: continue

        state = estados[grupo]
        
        # Lógica de Compra
        if rsi < rsi_compra:
            if state["sinais"].get(coin) != "COMPRA":
                msg = (f"{prefixo} 🟢 COMPRA\n"
                       f"Moeda: {coin}\n"
                       f"Preço: ${preco}\n"
                       f"RSI: {rsi:.2f}")
                enviar_telegram(chat_id, msg)
                state["sinais"][coin] = "COMPRA"
                state["compras"][coin] = preco

        # Lógica de Venda (Baseada em Alvo ou RSI Alto)
        elif coin in state["compras"]:
            preco_compra = state["compras"][coin]
            lucro = ((preco - preco_compra) / preco_compra) * 100
            
            # Vende se atingir o alvo de lucro OU RSI ficar muito esticado (> 70)
            if lucro >= alvo_lucro or rsi > 70:
                msg = (f"{prefixo} 🔴 VENDA\n"
                       f"Moeda: {coin}\n"
                       f"Venda: ${preco}\n"
                       f"Lucro: {lucro:.2f}%\n"
                       f"RSI: {rsi:.2f}")
                enviar_telegram(chat_id, msg)
                resultado_dia.append(lucro)
                state["sinais"][coin] = "VENDA"
                del state["compras"][coin]

def resumo_diario():
    if not resultado_dia:
        return "📊 RESUMO 24H: Nenhuma operação finalizada."
    total = sum(resultado_dia)
    msg = (f"📊 RESUMO DO DIA\n\n"
           f"✅ Operações: {len(resultado_dia)}\n"
           f"💰 Lucro Total: {total:.2f}%\n"
           f"📈 Média: {(total/len(resultado_dia)):.2f}%")
    return msg

# Inicialização
print("🚀 Bots iniciados...")
enviar_telegram(CHAT_ID_FREE, "🟢 Sistema de Sinais Reiniciado")

while True:
    try:
        # 1. Atualiza lista de moedas V1/V2 (Top 100 + KCS)
        top_binance = get_top_100_binance()
        moedas_vip = list(set(top_binance + ["KCS"]))
        
        # 2. Processa Grupo FREE
        processar_sinais("free", MOEDAS_FIXAS_FREE, CHAT_ID_FREE, 35, 1.5, "🆓 [FREE]")
        
        # 3. Processa Grupo V1 (Alvo 2%)
        processar_sinais("v1", moedas_vip, CHAT_ID_V1, 35, 2.0, "💎 [V1 VIP]")
        
        # 4. Processa Grupo V2 (Scalping - Alvo 0.8%)
        processar_sinais("v2", moedas_vip, CHAT_ID_V2, 30, 0.8, "⚡ [V2 SCALP]")

        # 5. Check de Resumo (24h)
        if time.time() - ultimo_resumo > 86400:
            relatorio = resumo_diario()
            enviar_telegram(CHAT_ID_FREE, relatorio)
            enviar_telegram(CHAT_ID_V1, relatorio)
            resultado_dia.clear()
            ultimo_resumo = time.time()

        print(f"Loop finalizado. Aguardando... {time.strftime('%H:%M:%S')}")
        time.sleep(300) # 5 minutos entre as varreduras

    except Exception as e:
        print(f"Erro Crítico no Loop: {e}")
        time.sleep(30)

import requests
import time
import os

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv("TOKEN")
CHAT_ID_FREE = os.getenv("CHAT_ID_FREE")
CHAT_ID_V1 = os.getenv("CHAT_ID_V1")
CHAT_ID_V2 = os.getenv("CHAT_ID_V2") # Configure este no seu ambiente

# Moedas fixas para o grupo FREE
MOEDAS_FREE = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
    "binancecoin": "BNB",
    "litecoin": "LTC",
    "kucoin-shares": "KCS"
}

# Variáveis globais de controle
resultado_dia = []
ultimo_resumo = time.time()
historico = {}
ultimo_sinal = {"free": {}, "v1": {}, "v2": {}}
ultimo_preco_compra = {"free": {}, "v1": {}, "v2": {}}

# --- FUNÇÕES DE SUPORTE ---

def get_binance_top_100():
    """Busca as 100 moedas mais negociadas na Binance + KCS"""
    try:
        # Busca top 100 por volume no CoinGecko (mais estável para IDs)
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=100&page=1"
        data = requests.get(url, timeout=10).json()
        moedas = {coin['id']: coin['symbol'].upper() for coin in data}
        
        # Garante que KCS (moeda da Kucoin) esteja na lista
        moedas["kucoin-shares"] = "KCS"
        return moedas
    except Exception as e:
        print(f"Erro ao buscar top 100: {e}")
        # Fallback básico caso a API falhe
        return {"bitcoin": "BTC", "ethereum": "ETH", "kucoin-shares": "KCS"}

def get_price(coin_id):
    """Busca o preço atual via CoinGecko"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        data = requests.get(url, timeout=10).json()
        return data[coin_id]["usd"]
    except:
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
    
    media_ganho = sum(ganhos[-periodo:]) / periodo
    media_perda = sum(perdas[-periodo:]) / periodo
    
    if media_perda == 0: return 100
    rs = media_ganho / media_perda
    return 100 - (100 / (1 + rs))

def enviar_telegram(chat_id, msg):
    if not TOKEN or not chat_id: return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg}, timeout=10)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def resumo_resultado():
    if not resultado_dia:
        return "📊 RESUMO DO DIA\n\nNenhuma operação fechada ainda."
    total = sum(resultado_dia)
    media = total / len(resultado_dia)
    return (
        "📊 RESUMO DO DIA\n\n"
        f"✅ Operações: {len(resultado_dia)}\n"
        f"📈 Resultado acumulado: {total:.2f}%\n"
        f"🎯 Média por operação: {media:.2f}%\n\n"
        "⚠️ Simulação baseada nos sinais do bot"
    )

# --- INICIALIZAÇÃO ---

print("Iniciando Bot...")
MOEDAS_V1 = get_binance_top_100()
MOEDAS_V2 = MOEDAS_V1.copy()

# Inicializa o histórico para todas as moedas detectadas
todas_moedas = {**MOEDAS_FREE, **MOEDAS_V1}
for coin in todas_moedas:
    historico[coin] = []

enviar_telegram(CHAT_ID_FREE, "🟢 Bot FREE (BTC/ETH/SOL/XRP/BNB/LTC/KCS) Iniciado!")
enviar_telegram(CHAT_ID_V1, "🔒 VIP V1 (Top 100 Binance + KCS) Iniciado!")
enviar_telegram(CHAT_ID_V2, "⚡ VIP V2 (Scalping Top 100 + KCS) Iniciado!")

# --- LOOP PRINCIPAL ---

while True:
    try:
        agora = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] Analisando mercado...")

        # Processamento por Grupo
        config_grupos = [
            ("free", MOEDAS_FREE, CHAT_ID_FREE, 35, 60, 1.01),  # Nome, Lista, Chat, RSI_Comp, RSI_Vend, Alvo
            ("v1", MOEDAS_V1, CHAT_ID_V1, 35, 60, 1.01),
            ("v2", MOEDAS_V2, CHAT_ID_V2, 30, 70, 1.005) # Scalping (Alvo menor: 0.5%)
        ]

        for nome_grupo, lista_moedas, chat_id, rsi_compra, rsi_venda, alvo_lucro in config_grupos:
            if not chat_id: continue

            for coin, simbolo in lista_moedas.items():
                preco = get_price(coin)
                if preco is None: continue

                # Atualiza histórico global da moeda
                if coin not in historico: historico[coin] = []
                historico[coin].append(preco)
                if len(historico[coin]) > 50: historico[coin].pop(0)

                rsi = calcular_rsi(historico[coin])
                if rsi is None: continue

                # Lógica de COMPRA
                if rsi < rsi_compra:
                    if coin not in ultimo_sinal[nome_grupo] or ultimo_sinal[nome_grupo][coin] != "COMPRA":
                        enviar_telegram(chat_id, 
                            f"🟢 SINAL DE COMPRA ({nome_grupo.upper()})\n"
                            f"Moeda: {simbolo}\n"
                            f"Preço: ${preco}\n"
                            f"RSI: {rsi:.2f}\n"
                            f"📊 Fonte: Global Market Data"
                        )
                        ultimo_sinal[nome_grupo][coin] = "COMPRA"
                        ultimo_preco_compra[nome_grupo][coin] = preco

                # Lógica de VENDA
                elif rsi > rsi_venda:
                    if coin in ultimo_preco_compra[nome_grupo]:
                        p_compra = ultimo_preco_compra[nome_grupo][coin]
                        if preco >= p_compra * alvo_lucro:
                            if ultimo_sinal[nome_grupo].get(coin) != "VENDA":
                                lucro = ((preco - p_compra) / p_compra) * 100
                                resultado_dia.append(lucro)
                                
                                enviar_telegram(chat_id, 
                                    f"🔴 SINAL DE VENDA ({nome_grupo.upper()})\n"
                                    f"Moeda: {simbolo}\n"
                                    f"Preço: ${preco}\n"
                                    f"Lucro: +{lucro:.2f}%"
                                )
                                ultimo_sinal[nome_grupo][coin] = "VENDA"
                                del ultimo_preco_compra[nome_grupo][coin]

        # Envio do resumo diário (estratégia 24h corrigida)
        if agora - ultimo_resumo > 86400:
            msg_resumo = resumo_resultado()
            enviar_telegram(CHAT_ID_FREE, msg_resumo)
            enviar_telegram(CHAT_ID_V1, msg_resumo)
            resultado_dia.clear()
            ultimo_resumo = agora
            # Atualiza a lista de moedas top 100 uma vez por dia
            MOEDAS_V1 = get_binance_top_100()
            MOEDAS_V2 = MOEDAS_V1.copy()

        time.sleep(300) # Checa a cada 5 minutos

    except Exception as e:
        print(f"Erro no loop principal: {e}")
        time.sleep(10)

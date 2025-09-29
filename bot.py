import discord
import os
from dotenv import load_dotenv
import datetime
import re
import json
import asyncio

load_dotenv()
TOKEN = os.getenv('TOKEN')

# Configurações do monitoramento
TARGET_SERVER_ID = 1313305951004135434  # Servidor alvo
TARGET_CHANNEL_ID = 1404475603788365975  # Canal onde as logs são enviadas
LOG_USER_ID = 1404475673682116792  # Usuário que envia as logs
ALERT_CHANNEL_ID = 1422269418720989204  # Canal para enviar alertas de quality 1.0

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

def extrair_metadados_json(texto):
    """Extrai e parseia os metadados JSON de uma log"""
    try:
        # Procura por texto entre parênteses que contém JSON
        match = re.search(r'\(metadados:\s*(\{.*?\})\)', texto, re.DOTALL)
        if match:
            json_str = match.group(1)
            # Corrige aspas simples para aspas duplas para JSON válido
            json_str = json_str.replace("'", '"')
            return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        pass
    return None

def e_log_drop_pickup(texto):
    """Verifica se a mensagem é uma log de Drop ou Pickup"""
    return texto.strip().startswith(('Drop', 'Pickup'))

def extrair_info_log(texto):
    """Extrai informações principais da log (tipo, jogador, item, metadados)"""
    linhas = texto.strip().split('\n')
    if not linhas:
        return None
    
    primeira_linha = linhas[0]
    tipo = primeira_linha.split()[0] if primeira_linha else None
    
    # Extrai nome do jogador
    match_jogador = re.search(r'O jogador (\w+)', primeira_linha)
    jogador = match_jogador.group(1) if match_jogador else None
    
    # Extrai nome do item
    match_item = re.search(r'item (\w+)', primeira_linha)
    item = match_item.group(1) if match_item else None
    
    # Extrai metadados
    metadados = extrair_metadados_json(primeira_linha)
    
    return {
        'tipo': tipo,
        'jogador': jogador,
        'item': item,
        'metadados': metadados,
        'texto_completo': texto
    }

async def processar_mensagem_log(message, historico=False):
    """Processa uma mensagem de log - usado tanto para mensagens novas quanto históricas"""
    # Obtém o conteúdo da mensagem
    conteudo = message.content.strip()
    
    # Verifica se é uma log de Drop ou Pickup
    if not e_log_drop_pickup(conteudo):
        return False
    
    prefix = "📚 [HISTÓRICO]" if historico else "📋"
    print(f"{prefix} Log detectada: {conteudo[:50]}...")
    
    # Extrai informações da log
    info_log = extrair_info_log(conteudo)
    if not info_log or not info_log['metadados']:
        print("❌ Não foi possível extrair metadados da log")
        return False
    
    metadados = info_log['metadados']
    
    # Verifica se tem quality 1.0
    if metadados.get('quality') == 1.0:
        print(f"🎯 QUALITY 1.0 DETECTADO!")
        print(f"Jogador: {info_log['jogador']}")
        print(f"Item: {info_log['item']}")
        print(f"Tipo: {info_log['tipo']}")
        
        # Prepara mensagem de alerta
        item_name = metadados.get('name_peca', info_log['item'])
        material_name = metadados.get('material_name', 'N/A')
        rarity = metadados.get('rarity', 'N/A')
        
        timestamp_msg = f"🕐 **Timestamp:** {message.created_at.strftime('%d/%m/%Y %H:%M:%S')}\n" if historico else ""
        
        alert_message = (
            f"@everyone 🔥 **ITEM QUALITY 1.0 DETECTADO!** 🔥\n\n"
            f"👤 **Jogador:** {info_log['jogador']}\n"
            f"📦 **Item:** {item_name}\n"
            f"🔧 **Material:** {material_name}\n"
            f"💎 **Raridade:** {rarity}\n"
            f"⚡ **Ação:** {info_log['tipo']}\n"
            f"✨ **Quality:** {metadados.get('quality')}\n"
            f"{timestamp_msg}"
            f"\n```{conteudo[:500]}```"
        )
        
        # Envia alerta
        try:
            alert_channel = client.get_channel(ALERT_CHANNEL_ID)
            if alert_channel:
                await alert_channel.send(alert_message)
                print(f"✅ Alerta enviado para canal: {ALERT_CHANNEL_ID}")
            else:
                print(f"❌ Canal de alerta não encontrado: {ALERT_CHANNEL_ID}")
        except Exception as e:
            print(f"❌ ERRO ao enviar alerta: {e}")
        
        return True
    else:
        print(f"ℹ️ Item com quality {metadados.get('quality', 'N/A')} - ignorando")
        return False

@client.event
async def on_ready():
    print(f'🤖 Bot Detector de Quality 1.0 conectado como {client.user}')
    print(f'🎯 Servidor monitorado: {TARGET_SERVER_ID}')
    print(f'📺 Canal de logs: {TARGET_CHANNEL_ID}')
    print(f'👤 Usuário de logs: {LOG_USER_ID}')
    print(f'🚨 Canal de alertas: {ALERT_CHANNEL_ID}')
    print(f'🔍 Procurando por itens com quality: 1.0')
    print(f'✅ Bot online!')
    print(f'📚 Verificando últimas 100 mensagens do canal...')
    
    # Verificar mensagens históricas
    try:
        channel = client.get_channel(TARGET_CHANNEL_ID)
        if channel:
            count_processadas = 0
            count_quality_10 = 0
            
            # Pega as últimas 100 mensagens do canal
            async for message in channel.history(limit=100):
                # Verifica se é do usuário correto
                if message.author.id == LOG_USER_ID:
                    count_processadas += 1
                    resultado = await processar_mensagem_log(message, historico=True)
                    if resultado:
                        count_quality_10 += 1
                    # Pequeno delay para evitar rate limits
                    await asyncio.sleep(0.1)
            
            print(f'📊 Verificação concluída:')
            print(f'   - {count_processadas} logs processadas')
            print(f'   - {count_quality_10} itens quality 1.0 encontrados')
        else:
            print(f'❌ Canal {TARGET_CHANNEL_ID} não encontrado!')
    except Exception as e:
        print(f'❌ Erro ao verificar histórico: {e}')
    
    print(f'🔄 Monitoramento em tempo real ativado!')

@client.event
async def on_message(message):
    # Verifica se é no canal correto e do usuário correto
    if (message.author == client.user or 
        message.channel.id != TARGET_CHANNEL_ID or 
        message.author.id != LOG_USER_ID):
        return

    # Processa a mensagem usando a função compartilhada
    await processar_mensagem_log(message, historico=False)

async def main():
    """Função principal com reconexão automática"""
    while True:
        try:
            if TOKEN:
                await client.start(TOKEN)
            else:
                print("❌ TOKEN não encontrado! Verifique o arquivo .env")
                break
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            print("🔄 Tentando reconectar em 30 segundos...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
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
ALERT_CHANNEL_ID = 1422269418720989204  # Canal para enviar alertas de metadados incompletos

# Lista de itens que devem ter metadados completos
ITEMS_MONITORADOS = [
    # Materiais básicos
    'ferro_fundido', 'ferro_fundido_pesado', 'aluminio_forjado', 'aluminio_forjado_leve',
    'billet', 'magnesio', 'aco_fundido_leve', 'aco_fundido', 'aco_forjado_pesado',
    'aco_fundido_pesado', 'aluminio_forjado_leve', 'tarugo_aco', 'aluminio_forjado',
    'aluminio', 'titanio', 'aco_forjado',
    
    # Peças específicas - Escape
    'escape_aco_fundido_leve', 'escape_aluminio', 'escape_titanio',
    
    # Peças específicas - Biela
    'biela_aco_fundido_leve', 'biela_aco_fundido', 'biela_aco_fundido_pesado',
    'biela_aluminio_forjado_leve', 'biela_aluminio_forjado', 'biela_titanio',
    
    # Peças específicas - Cabeçote
    'cabecote_ferro_fundido', 'cabecote_aluminio', 'cabecote_aco_forjado',
    
    # Peças específicas - Virabrequim
    'virabrequim_ferro_fundido', 'virabrequim_ferro_fundido_pesado', 'virabrequim_aco_forjado_leve',
    'virabrequim_aco_forjado', 'virabrequim_aco_forjado_pesado', 'virabrequim_tarugo_aco',
    'virabrequim_billet',
    
    # Peças específicas - Pistão
    'pistao_aco_fundido_leve', 'pistao_aco_fundido', 'pistao_aco_fundido_pesado',
    'pistao_aluminio_forjado_leve', 'pistao_aluminio_forjado',
    
    # Peças específicas - Bloco
    'bloco_inline_3', 'bloco_inline_4', 'bloco_inline_5', 'bloco_inline_6',
    'bloco_v_6', 'bloco_v_8', 'bloco_v_10', 'bloco_v_12',
    'bloco_boxer_4', 'bloco_boxer_6'
]

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
            print(f"🔍 JSON extraído: {json_str}")
            result = json.loads(json_str)
            print(f"✅ JSON parseado com sucesso: {result}")
            return result
        else:
            print(f"❌ Nenhum match encontrado para metadados no texto: {texto}")
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"❌ Erro ao parsear JSON: {e}")
        print(f"   Texto: {texto}")
    return None

def e_log_drop_pickup(texto):
    """Verifica se a mensagem é uma log de Drop ou Pickup"""
    # Verifica formato antigo (Drop/Pickup)
    if texto.strip().startswith(('Drop', 'Pickup')):
        return True
    
    # Verifica formato novo (O jogador **nome** **pegou/deixou**)
    return ('**pegou**' in texto or '**deixou**' in texto) and 'O jogador **' in texto

def extrair_info_log(texto):
    """Extrai informações principais da log (tipo, jogador, item, metadados)"""
    linhas = texto.strip().split('\n')
    if not linhas:
        return None
    
    primeira_linha = linhas[0]
    
    # Para formato antigo (Drop/Pickup)
    if primeira_linha.startswith(('Drop', 'Pickup')):
        tipo = primeira_linha.split()[0] if primeira_linha else None
        match_jogador = re.search(r'O jogador (\w+)', primeira_linha)
        jogador = match_jogador.group(1) if match_jogador else None
        match_item = re.search(r'item (\w+)', primeira_linha)
        item = match_item.group(1) if match_item else None
    
    # Para formato novo (O jogador **nome** **pegou/deixou**)
    else:
        # Extrai tipo de ação
        if '**pegou**' in primeira_linha:
            tipo = 'Pickup'
        elif '**deixou**' in primeira_linha:
            tipo = 'Drop'
        else:
            tipo = 'Unknown'
        
        # Extrai nome do jogador (formato **nome**)
        match_jogador = re.search(r'O jogador \*\*([^*]+)\*\*', primeira_linha)
        jogador = match_jogador.group(1) if match_jogador else None
        
        # Extrai nome do item (formato **item**)
        match_item = re.search(r'item \*\*([^*]+)\*\*', primeira_linha)
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

def verificar_metadados_incompletos(item, metadados):
    """Verifica se os metadados estão incompletos para um item monitorado"""
    print(f"🔍 Verificando item: {item}")
    print(f"🔍 Metadados: {metadados}")
    print(f"🔍 Item está na lista monitorada: {item in ITEMS_MONITORADOS}")
    
    if item not in ITEMS_MONITORADOS:
        print(f"❌ Item {item} não está na lista de monitorados")
        return False
    
    if not metadados:
        print(f"❌ Sem metadados - INCOMPLETO")
        return True
    
    # Verifica se tem apenas 'rarity' (metadados incompletos)
    chaves = set(metadados.keys())
    print(f"🔍 Chaves encontradas: {chaves}")
    
    if chaves == {'rarity'}:
        print(f"🚨 APENAS RARITY - METADADOS INCOMPLETOS!")
        return True
    
    # Verifica se não tem campos essenciais de qualidade
    campos_essenciais = {'quality', 'quality_percent', 'forged_by', 'forged_at'}
    campos_encontrados = campos_essenciais.intersection(chaves)
    print(f"🔍 Campos essenciais encontrados: {campos_encontrados}")
    
    if not campos_encontrados:
        print(f"🚨 SEM CAMPOS ESSENCIAIS - METADADOS INCOMPLETOS!")
        return True
    
    print(f"✅ Metadados completos")
    return False

async def processar_mensagem_log(message, historico=False):
    """Processa uma mensagem de log - usado tanto para mensagens novas quanto históricas"""
    # Obtém o conteúdo da mensagem
    conteudo = message.content.strip()
    
    # Se não tem conteúdo, tenta extrair dos embeds
    if not conteudo and message.embeds:
        for embed in message.embeds:
            if embed.description:
                conteudo = embed.description
                break
    
    print(f"🔍 CONTEÚDO A SER PROCESSADO: '{conteudo}'")
    
    # Verifica se é uma log de Drop ou Pickup
    is_drop_pickup = e_log_drop_pickup(conteudo)
    print(f"🔍 É Drop/Pickup? {is_drop_pickup}")
    
    if not is_drop_pickup:
        print("❌ Não é uma log de Drop/Pickup - ignorando")
        return False
    
    prefix = "📚 [HISTÓRICO]" if historico else "📋"
    print(f"{prefix} Log detectada: {conteudo[:50]}...")
    
    # Extrai informações da log
    info_log = extrair_info_log(conteudo)
    if not info_log:
        print("❌ Não foi possível extrair informações da log")
        return False
    
    metadados = info_log['metadados']
    item = info_log['item']
    
    # Verifica se é um item monitorado com metadados incompletos
    if verificar_metadados_incompletos(item, metadados):
        print(f"🚨 METADADOS INCOMPLETOS DETECTADOS!")
        print(f"Jogador: {info_log['jogador']}")
        print(f"Item: {item}")
        print(f"Tipo: {info_log['tipo']}")
        print(f"Metadados: {metadados}")
        
        # Prepara mensagem de alerta
        rarity = metadados.get('rarity', 'N/A') if metadados else 'N/A'
        quality_info = f"Quality: {metadados.get('quality', 'N/A')}" if metadados and 'quality' in metadados else "❌ Sem qualidade"
        
        timestamp_msg = f"🕐 **Timestamp:** {message.created_at.strftime('%d/%m/%Y %H:%M:%S')}\n" if historico else ""
        
        alert_message = (
            f"@everyone 🚨 **METADADOS INCOMPLETOS DETECTADOS!** 🚨\n\n"
            f"👤 **Jogador:** {info_log['jogador']}\n"
            f"📦 **Item:** {item}\n"
            f"💎 **Raridade:** {rarity}\n"
            f"⚡ **Ação:** {info_log['tipo']}\n"
            f"🔍 **Status:** {quality_info}\n"
            f"⚠️ **Problema:** Item monitorado com metadados incompletos!\n"
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
        if item in ITEMS_MONITORADOS:
            print(f"✅ Item {item} com metadados completos - OK")
        else:
            print(f"ℹ️ Item {item} não monitorado - ignorando")
        return False

@client.event
async def on_ready():
    print(f'🤖 Bot Detector de Metadados Incompletos conectado como {client.user}')
    print(f'🎯 Servidor monitorado: {TARGET_SERVER_ID}')
    print(f'📺 Canal de logs: {TARGET_CHANNEL_ID}')
    print(f'👤 Usuário de logs: {LOG_USER_ID}')
    print(f'🚨 Canal de alertas: {ALERT_CHANNEL_ID}')
    print(f'🔍 Monitorando {len(ITEMS_MONITORADOS)} itens para metadados incompletos:')
    for item in ITEMS_MONITORADOS:
        print(f'   - {item}')
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
            print(f'   - {count_quality_10} itens com metadados incompletos encontrados')
        else:
            print(f'❌ Canal {TARGET_CHANNEL_ID} não encontrado!')
    except Exception as e:
        print(f'❌ Erro ao verificar histórico: {e}')
    
    print(f'🔄 Monitoramento em tempo real ativado!')

@client.event
async def on_message(message):
    # Debug: Mostra todas as mensagens recebidas
    print(f"🔍 MENSAGEM RECEBIDA:")
    print(f"   Canal ID: {message.channel.id}")
    print(f"   Autor ID: {message.author.id}")
    print(f"   Conteúdo COMPLETO:")
    print(f"   '{message.content}'")
    print(f"   Tem attachments: {len(message.attachments) > 0}")
    print(f"   Tem embeds: {len(message.embeds) > 0}")
    print(f"   Canal correto: {message.channel.id == TARGET_CHANNEL_ID}")
    print(f"   Usuário correto: {message.author.id == LOG_USER_ID}")
    
    # Verifica se é no canal correto e do usuário correto
    if (message.author == client.user or 
        message.channel.id != TARGET_CHANNEL_ID or 
        message.author.id != LOG_USER_ID):
        print("❌ Mensagem ignorada - não atende aos critérios")
        return

    # Verifica se a mensagem tem conteúdo ou embeds
    conteudo_mensagem = message.content.strip()
    
    # Se não tem conteúdo, tenta extrair dos embeds
    if not conteudo_mensagem and message.embeds:
        print("🔍 Extraindo conteúdo dos embeds...")
        for embed in message.embeds:
            print(f"   Embed title: {embed.title}")
            print(f"   Embed description: {embed.description}")
            print(f"   Embed fields: {len(embed.fields)}")
            
            # Tenta extrair o conteúdo do embed
            if embed.description:
                conteudo_mensagem = embed.description
                print(f"✅ Conteúdo extraído do embed: {conteudo_mensagem[:100]}...")
                break
    
    if not conteudo_mensagem:
        print("❌ Mensagem vazia e sem embeds - ignorando")
        return

    print("✅ Mensagem atende aos critérios - processando...")
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
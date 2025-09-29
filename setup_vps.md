# Setup para VPS - Bot Detector Quality 1.0

## Instalação

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Configurar token do Discord:**
   - Crie um arquivo `.env` na mesma pasta do bot
   - Adicione a linha: `TOKEN=SEU_TOKEN_AQUI`
   - Substitua `SEU_TOKEN_AQUI` pelo token do seu bot

## Como obter o token:
1. Vá para https://discord.com/developers/applications
2. Crie um novo aplicativo ou selecione um existente
3. Vá em "Bot" no menu lateral
4. Copie o token

## Executar o bot:
```bash
python bot.py
```

## Funcionalidades:
- ✅ Monitora canal específico em tempo real
- ✅ Verifica últimas 100 mensagens na inicialização
- ✅ Detecta itens com quality: 1.0
- ✅ Reconexão automática em caso de queda
- ✅ Otimizado para VPS (rate limiting, error handling)

## Configurações no bot.py:
- `TARGET_SERVER_ID`: ID do servidor Discord
- `TARGET_CHANNEL_ID`: ID do canal com as logs
- `LOG_USER_ID`: ID do usuário que envia as logs
- `ALERT_CHANNEL_ID`: ID do canal onde enviar alertas

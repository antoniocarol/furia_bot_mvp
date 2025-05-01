"""
Handler para o comando /start do bot.
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, user_service) -> None:
    """
    Handler para o comando /start.
    
    Args:
        update: Update do Telegram
        context: Contexto do bot
        user_service: Serviço de usuários
    """
    user = update.effective_user
    logger.info(f"Processando comando /start para usuário {user.id}")
    
    # Cria ou recupera o usuário
    db_user = await user_service.get_or_create_user(user.id, user.username)
    logger.info(f"Usuário recuperado/criado: {db_user}")
    
    # Mensagem de boas-vindas
    welcome_text = (
        f"👋 Olá {user.first_name}!\n\n"
        "Bem-vindo ao bot oficial da FURIA CS! 🐯\n\n"
        "Aqui você pode:\n"
        "• Completar missões e ganhar XP 🎯\n"
        "• Participar de pesquisas exclusivas 📝\n"
        "• Conectar suas redes sociais 🌐\n"
        "• Acompanhar seu progresso 📊\n\n"
        "Comandos disponíveis:\n"
        "/profile - Ver seu perfil\n"
        "/missions - Ver missões disponíveis\n"
        "/mission <id> - Iniciar uma missão\n"
        "/survey - Participar de pesquisas\n"
        "/connect - Conectar redes sociais\n"
        "/help - Ver ajuda\n\n"
        "Quanto mais você interagir, mais XP ganha e sobe de nível! 🔥"
    )
    
    await update.message.reply_text(welcome_text)
    logger.info(f"Mensagem de boas-vindas enviada para {user.id}") 
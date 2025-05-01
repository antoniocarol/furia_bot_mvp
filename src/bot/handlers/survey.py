"""
Handlers para gerenciamento de pesquisas.
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE, survey_service) -> None:
    """Inicia uma nova pesquisa."""
    await update.message.reply_text("🚧 Sistema de pesquisas em desenvolvimento...")
    return ConversationHandler.END

async def process_survey_response(update: Update, context: ContextTypes.DEFAULT_TYPE, survey_service, user_service) -> None:
    """Processa a resposta de uma pesquisa."""
    await update.message.reply_text("🚧 Processamento de respostas em desenvolvimento...")
    return ConversationHandler.END

async def cancel_survey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancela uma pesquisa em andamento."""
    await update.message.reply_text("Pesquisa cancelada.")
    return ConversationHandler.END 
"""
Handlers para gerenciamento de missões.
"""
from telegram import Update
from telegram.ext import ContextTypes

async def list_missions(update: Update, context: ContextTypes.DEFAULT_TYPE, mission_service, user_service) -> None:
    """Lista as missões disponíveis para o usuário."""
    await update.message.reply_text("🚧 Lista de missões em desenvolvimento...")

async def start_mission(update: Update, context: ContextTypes.DEFAULT_TYPE, mission_service, user_service) -> None:
    """Inicia uma missão específica."""
    await update.message.reply_text("🚧 Início de missão em desenvolvimento...")

async def complete_mission(update: Update, context: ContextTypes.DEFAULT_TYPE, mission_service, user_service) -> None:
    """Completa uma missão em andamento."""
    await update.message.reply_text("🚧 Conclusão de missão em desenvolvimento...") 
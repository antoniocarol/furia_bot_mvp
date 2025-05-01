#!/usr/bin/env python3
"""
src/bot/bot.py
Bot principal da FURIA CS — conecta ao Mongo e inicia polling,
com menu interativo e MVP funcional, agora com integração de notícias.
"""
import os
import logging
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import BadRequest

# Modelos & Serviços
from src.models.database import Database
from src.services.user_service    import UserService
from src.services.mission_service import MissionService
from src.services.survey_service  import SurveyService
from src.services.analytics_service import AnalyticsService
from src.services.news_service   import NewsService
from src.services.players_service import PlayerService

# Handlers puros
from src.bot.handlers.profile import show_profile as show_profile_fn
from src.bot.handlers.mission import (
    list_missions as list_missions_fn,
    start_mission as start_mission_fn,
)
from src.bot.handlers.social    import connect_social_media as connect_social_fn
from src.bot.handlers.survey    import (
    start_survey as start_survey_fn,
    process_survey_response as process_survey_fn,
    cancel_survey as cancel_survey_fn,
)

# Configurações de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Menu principal de onboarding
MAIN_MENU = [
    [
        InlineKeyboardButton("📊 Line-up CS2",   callback_data="menu_lineup"),
        InlineKeyboardButton("📰 Notícias",      callback_data="menu_news"),
    ],
    [
        InlineKeyboardButton("💬 Comunidade",    callback_data="menu_community"),
        InlineKeyboardButton("🏆 Conquistas",    callback_data="menu_achievements"),
    ],
    [
        InlineKeyboardButton("🎯 Próximas Partidas", callback_data="menu_next_matches"),
        InlineKeyboardButton("🛍 FURIA Store",        callback_data="menu_store"),
    ],
    [
        InlineKeyboardButton("⚙️ Configurações", callback_data="menu_settings"),
        InlineKeyboardButton("❓ Ajuda",           callback_data="menu_help"),
    ],
]

# Callback do submenu Notícias de Jogadores
PLAYER_MENU = [
    [InlineKeyboardButton("yuurih",    callback_data="player_yuurih")],
    [InlineKeyboardButton("KSCERATO",  callback_data="player_kscerato")],
    [InlineKeyboardButton("FalleN",    callback_data="player_fallen")],
    [InlineKeyboardButton("molodoy",   callback_data="player_molodoy")],
    [InlineKeyboardButton("Yekindar",  callback_data="player_yekindar")],
    [InlineKeyboardButton("🔙 Voltar", callback_data="menu_news")],
]

async def on_startup(application: Application):
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name   = os.getenv("DATABASE_NAME", "furia_bot")

    application.db = Database()
    await application.db.connect(mongo_uri, db_name)
    logger.info("✓ Conectado ao MongoDB")

    # Instancia serviços
    application.player_svc = PlayerService(application.db.db)
    application.user_svc      = UserService(application.db)
    application.mission_svc   = MissionService(application.db)
    application.survey_svc    = SurveyService(application.db)
    application.analytics_svc = AnalyticsService(application.db)
    application.news_svc      = NewsService(application.db.db, application.player_svc)

    logger.info("✓ Serviços instanciados")


def main():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("🚨 BOT_TOKEN não encontrado no arquivo .env")
        return

    app = (
        Application.builder()
        .token(token)
        .post_init(on_startup)
        .build()
    )

    # 1) /start — boas-vindas e menu
    async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if not context.user_data.get("welcomed"):
            await context.bot.send_animation(
                chat_id=chat_id,
                animation="https://media.giphy.com/media/3oEduV4SOS9mmmIOkw/giphy.gif",
                caption="🎉 Seja muito bem-vindo(a) à família FURIA CS!",
            )
            context.user_data["welcomed"] = True

        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        welcome_text = (
            f"👋 *Bem-vindo à família FURIA CS, {update.effective_user.first_name}!*\n"
            "🌟 Escolha uma opção abaixo:"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(MAIN_MENU),
        )

    # 2) Callback do menu principal
    async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query   = update.callback_query
        await query.answer()
        cmd     = query.data
        bot     = context.bot
        chat_id = query.message.chat_id
        msg_id  = query.message.message_id
        news_svc = context.application.news_svc

        # Voltar ao menu inicial
        if cmd == "menu_home":
            return await start_handler(update, context)

        # Notícia: submenu
        if cmd == "menu_news":
            text = "📰 *Notícias*\n\nEscolha a categoria:"  
            return await bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id,
                text=text, parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Time",    callback_data="menu_team_news")],
                    [InlineKeyboardButton("Jogadores", callback_data="menu_player_news")],
                    [InlineKeyboardButton("🔙 Voltar", callback_data="menu_home")]
                ]),
            )

        # Notícias do Time
        if cmd == "menu_team_news":
            items = await news_svc.get_latest_team_news(5)
            if not items:
                text = "📰 Nenhuma notícia do time encontrada."
            else:
                text = "📰 *Últimas Notícias do Time:*\n\n" + "\n\n".join(
                    f"• {i['text']} (<a href='{i['url']}'>ver</a>)" for i in items
                )
            return await bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id,
                text=text, parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="menu_news")]
                ]),
            )

        # Notícias dos Jogadores: abre lista
        if cmd == "menu_player_news":
            text = "📸 *Notícias dos Jogadores*\n\nEscolha um jogador:"  
            return await bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id,
                text=text, parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(PLAYER_MENU),
            )

        # Handler individual de player
        if cmd.startswith("player_"):
            player_id = cmd.split("_")[1]
            items = await news_svc.get_latest_player_news(player_id, 5)
            if not items:
                text = f"📸 Nenhuma notícia de {player_id} encontrada."
            else:
                text = f"📸 *Últimas de {player_id}:*\n\n" + "\n\n".join(
                    f"• {i['text']} (<a href='{i['url']}'>ver</a>)" for i in items
                )
            return await bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id,
                text=text, parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="menu_player_news")]
                ]),
            )

        # ... existing cases for other menu options ...
        # fallback genérico
        return await bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id,
            text="🔧 Em construção…",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Voltar", callback_data="menu_home")]
            ]),
        )

    # 3) Registra handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^(menu_|player_).+"))

    # Comandos diretos de backup
    app.add_handler(CommandHandler("profile",
        lambda u, c: show_profile_fn(u, c, c.application.user_svc)
    ))
    app.add_handler(CommandHandler("missions",
        lambda u, c: list_missions_fn(u, c, c.application.mission_svc, c.application.user_svc)
    ))
    app.add_handler(CommandHandler("mission",
        lambda u, c: start_mission_fn(u, c, c.application.mission_svc, c.application.user_svc)
    ))
    app.add_handler(CommandHandler("connect",
        lambda u, c: connect_social_fn(u, c, c.application.user_svc)
    ))

    # 4) Survey Conversation
    survey_conv = ConversationHandler(
        entry_points=[CommandHandler("survey", start_survey_fn)],
        states={
            "QUESTION": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_survey_fn)],
            "CONFIRMATION": [
                CallbackQueryHandler(process_survey_fn, pattern="^confirm$"),
                CallbackQueryHandler(cancel_survey_fn, pattern="^cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_survey_fn)],
    )
    app.add_handler(survey_conv)

    # 5) Polling
    logger.info("🔄 Iniciando polling do bot…")
    app.run_polling()

    # 6) Fechar conexão com MongoDB
    if hasattr(app, "db"):
        app.db.client.close()
        logger.info("✓ MongoDB desconectado")

if __name__ == "__main__":
    main()

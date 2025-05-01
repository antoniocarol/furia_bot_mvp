"""
Handler para o comando /profile do bot.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_service) -> None:
    """
    Handler para o comando /profile.
    
    Args:
        update: Update do Telegram
        context: Contexto do bot
        user_service: Serviço de usuários
    """
    user = update.effective_user
    profile = await user_service.get_user_profile(user.id)
    
    if not profile:
        await update.message.reply_text(
            "❌ Perfil não encontrado. Use /start para criar seu perfil."
        )
        return
    
    # Calcula a barra de progresso
    progress_bar_length = 20
    xp_for_level = profile["xp_to_next_level"]
    current_xp = profile["xp"] % xp_for_level
    progress = int((current_xp / xp_for_level) * progress_bar_length)
    progress_bar = "▓" * progress + "░" * (progress_bar_length - progress)
    
    # Formata as redes sociais conectadas
    social_platforms = profile["connected_platforms"]
    social_text = "Nenhuma" if not social_platforms else ", ".join(social_platforms)
    
    # Monta a mensagem do perfil
    profile_text = (
        f"👤 Perfil de {profile['username']}\n\n"
        f"📊 Nível: {profile['level']}\n"
        f"⭐ XP: {profile['xp']} / {profile['xp'] + profile['xp_to_next_level']}\n"
        f"[{progress_bar}] {int((current_xp / xp_for_level) * 100)}%\n\n"
        f"🎯 Missões completadas: {profile['missions_completed']}\n"
        f"📝 Pesquisas respondidas: {profile['surveys_completed']}\n"
        f"🌐 Redes sociais: {social_text}\n"
        f"📅 Membro desde: {profile['member_since']}\n\n"
        "📈 Métricas de engajamento:\n"
        f"• Interações: {profile['engagement_metrics'].get('bot_interactions', 0)}\n"
        f"• Missões: {profile['engagement_metrics'].get('mission_completions', 0)}\n"
        f"• Pesquisas: {profile['engagement_metrics'].get('survey_completions', 0)}\n"
        f"• Compartilhamentos: {profile['engagement_metrics'].get('social_shares', 0)}"
    )
    
    # Cria botões inline para ações relacionadas ao perfil
    keyboard = [
        [
            InlineKeyboardButton("🎯 Missões", callback_data="show_missions"),
            InlineKeyboardButton("📝 Pesquisas", callback_data="show_surveys")
        ],
        [
            InlineKeyboardButton("🌐 Conectar Redes", callback_data="connect_social"),
            InlineKeyboardButton("📊 Ranking", callback_data="show_ranking")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(profile_text, reply_markup=reply_markup)

async def update_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_service) -> None:
    """
    Handler para atualização de perfil via botões inline.
    
    Args:
        update: Update do Telegram
        context: Contexto do bot
        user_service: Serviço de usuários
    """
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "show_missions":
        # Redireciona para o comando de missões
        context.args = []
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Redirecionando para missões...\nUse /missions para ver as missões disponíveis."
        )
    
    elif action == "show_surveys":
        # Redireciona para o comando de pesquisas
        context.args = []
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Redirecionando para pesquisas...\nUse /survey para participar das pesquisas."
        )
    
    elif action == "connect_social":
        # Redireciona para o comando de conexão de redes sociais
        context.args = []
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Redirecionando para conexão de redes sociais...\nUse /connect para conectar suas redes."
        )
    
    elif action == "show_ranking":
        # Busca o ranking dos top 10 usuários
        top_users = await user_service.get_users_by_level(min_level=1)
        top_users = sorted(top_users, key=lambda x: (x["level"], x["xp"]), reverse=True)[:10]
        
        ranking_text = "🏆 Top 10 Fãs da FURIA:\n\n"
        for i, user in enumerate(top_users, 1):
            ranking_text += (
                f"{i}. {user['username']}\n"
                f"   Nível {user['level']} • {user['xp']} XP\n"
            )
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=ranking_text
        ) 
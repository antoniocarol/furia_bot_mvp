"""
Serviço para gerenciamento de usuários do bot.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorCollection

class UserService:
    def __init__(self, db_collection: AsyncIOMotorCollection):
        """
        Inicializa o serviço de usuários.
        
        Args:
            db_collection: Coleção do MongoDB para usuários
        """
        self.collection = db_collection
        
    async def create_user(self, user_id: int, username: str) -> Dict[str, Any]:
        """
        Cria um novo usuário no banco de dados.
        
        Args:
            user_id: ID do usuário no Telegram
            username: Nome de usuário no Telegram
            
        Returns:
            Dict com os dados do usuário criado
        """
        user = {
            "user_id": user_id,
            "username": username,
            "level": 1,
            "xp": 0,
            "xp_to_next_level": 100,  # XP necessário para o próximo nível
            "missions_completed": 0,
            "surveys_completed": 0,
            "connected_platforms": [],
            "member_since": datetime.utcnow(),
            "last_interaction": datetime.utcnow(),
            "engagement_metrics": {
                "bot_interactions": 0,
                "mission_completions": 0,
                "survey_completions": 0,
                "social_shares": 0
            }
        }
        
        await self.collection.insert_one(user)
        return user
        
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca o perfil de um usuário pelo ID.
        
        Args:
            user_id: ID do usuário no Telegram
            
        Returns:
            Dict com os dados do usuário ou None se não encontrado
        """
        return await self.collection.find_one({"user_id": user_id})
        
    async def update_user_xp(self, user_id: int, xp_gained: int) -> Dict[str, Any]:
        """
        Atualiza o XP do usuário e verifica se subiu de nível.
        
        Args:
            user_id: ID do usuário no Telegram
            xp_gained: Quantidade de XP ganho
            
        Returns:
            Dict com os dados atualizados do usuário
        """
        user = await self.get_user_profile(user_id)
        if not user:
            return None
            
        new_xp = user["xp"] + xp_gained
        new_level = user["level"]
        xp_to_next = user["xp_to_next_level"]
        
        # Verifica se subiu de nível
        while new_xp >= xp_to_next:
            new_xp -= xp_to_next
            new_level += 1
            xp_to_next = int(xp_to_next * 1.5)  # Aumenta XP necessário para próximo nível
            
        update = {
            "$set": {
                "xp": new_xp,
                "level": new_level,
                "xp_to_next_level": xp_to_next,
                "last_interaction": datetime.utcnow()
            }
        }
        
        await self.collection.update_one({"user_id": user_id}, update)
        return await self.get_user_profile(user_id)
        
    async def update_engagement_metric(self, user_id: int, metric: str) -> None:
        """
        Atualiza uma métrica de engajamento do usuário.
        
        Args:
            user_id: ID do usuário no Telegram
            metric: Nome da métrica a ser atualizada
        """
        update = {
            "$inc": {f"engagement_metrics.{metric}": 1},
            "$set": {"last_interaction": datetime.utcnow()}
        }
        await self.collection.update_one({"user_id": user_id}, update)
        
    async def get_users_by_level(self, min_level: int = 1) -> List[Dict[str, Any]]:
        """
        Busca usuários com nível maior ou igual ao especificado.
        
        Args:
            min_level: Nível mínimo dos usuários
            
        Returns:
            Lista de usuários ordenada por nível e XP
        """
        cursor = self.collection.find({"level": {"$gte": min_level}})
        return await cursor.to_list(length=None)
        
    async def connect_social_platform(self, user_id: int, platform: str) -> None:
        """
        Conecta uma rede social ao perfil do usuário.
        
        Args:
            user_id: ID do usuário no Telegram
            platform: Nome da plataforma social
        """
        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$addToSet": {"connected_platforms": platform},
                "$set": {"last_interaction": datetime.utcnow()}
            }
        ) 
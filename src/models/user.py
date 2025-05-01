"""
Modelo de usuário para o bot da FURIA CS.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo.results import UpdateResult, InsertOneResult
import logging

logger = logging.getLogger(__name__)

class UserModel:
    """
    Modelo para gerenciar usuários no banco de dados.
    """
    def __init__(self, db):
        """
        Inicializa o modelo de usuário.
        
        Args:
            db: Instância do banco de dados
        """
        self.collection = db.db.users
    
    async def get_or_create_user(self, telegram_id: int, username: str) -> Dict:
        """
        Busca um usuário pelo ID do Telegram ou cria um novo se não existir.
        
        Args:
            telegram_id: ID do usuário no Telegram
            username: Nome de usuário no Telegram
            
        Returns:
            Dados do usuário
        """
        logger.info(f"Buscando usuário {telegram_id}")
        user = await self.get_user(telegram_id)
        if not user:
            logger.info(f"Usuário {telegram_id} não encontrado, criando novo")
            await self.create_user(telegram_id, username)
            user = await self.get_user(telegram_id)
            logger.info(f"Novo usuário criado: {user}")
        else:
            logger.info(f"Usuário {telegram_id} encontrado: {user}")
        return user
    
    async def create_user(self, telegram_id: int, username: str) -> InsertOneResult:
        """
        Cria um novo usuário no banco de dados.
        
        Args:
            telegram_id: ID do usuário no Telegram
            username: Nome de usuário no Telegram
            
        Returns:
            Resultado da operação de inserção
        """
        now = datetime.utcnow()
        user_data = {
            "telegram_id": telegram_id,
            "username": username,
            "xp": 0,
            "level": 1,
            "missions_completed": [],
            "surveys_completed": [],
            "social_connections": {},
            "demographics": {},
            "engagement_metrics": {
                "mission_completions": 0,
                "survey_completions": 0,
                "social_shares": 0,
                "bot_interactions": 1  # Primeira interação
            },
            "preferences": {},
            "last_active": now,
            "created_at": now,
            "updated_at": now
        }
        
        try:
            result = await self.collection.insert_one(user_data)
            logger.info(f"Novo usuário criado: {telegram_id}")
            return result
        except Exception as e:
            logger.error(f"Erro ao criar usuário {telegram_id}: {e}")
            raise
    
    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        """
        Busca um usuário pelo ID do Telegram.
        
        Args:
            telegram_id: ID do usuário no Telegram
            
        Returns:
            Dados do usuário ou None se não encontrado
        """
        try:
            user = await self.collection.find_one({"telegram_id": telegram_id})
            return user
        except Exception as e:
            logger.error(f"Erro ao buscar usuário {telegram_id}: {e}")
            raise
    
    async def update_user(self, telegram_id: int, update_data: Dict) -> UpdateResult:
        """
        Atualiza os dados de um usuário.
        
        Args:
            telegram_id: ID do usuário no Telegram
            update_data: Dados a serem atualizados
            
        Returns:
            Resultado da operação de atualização
        """
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await self.collection.update_one(
                {"telegram_id": telegram_id},
                {"$set": update_data}
            )
            logger.info(f"Usuário {telegram_id} atualizado: {update_data.keys()}")
            return result
        except Exception as e:
            logger.error(f"Erro ao atualizar usuário {telegram_id}: {e}")
            raise
    
    async def add_xp(self, telegram_id: int, xp_amount: int) -> Dict:
        """
        Adiciona XP ao usuário e atualiza o nível se necessário.
        
        Args:
            telegram_id: ID do usuário no Telegram
            xp_amount: Quantidade de XP a ser adicionada
            
        Returns:
            Dados atualizados do usuário
        """
        user = await self.get_user(telegram_id)
        if not user:
            raise ValueError(f"Usuário {telegram_id} não encontrado")
        
        current_xp = user["xp"]
        new_xp = current_xp + xp_amount
        
        # Calcula o novo nível baseado no XP (fórmula simples)
        # Cada nível requer mais XP que o anterior
        new_level = 1 + int((new_xp / 100) ** 0.8)  # Fórmula de crescimento não linear
        
        level_up = new_level > user["level"]
        
        update_data = {
            "xp": new_xp,
            "level": new_level,
            "last_active": datetime.utcnow()
        }
        
        await self.update_user(telegram_id, update_data)
        
        # Incrementa métricas de engajamento
        await self.collection.update_one(
            {"telegram_id": telegram_id},
            {"$inc": {"engagement_metrics.bot_interactions": 1}}
        )
        
        # Retorna os dados atualizados e se houve level up
        return {
            "current_xp": new_xp,
            "new_level": new_level,
            "level_up": level_up,
            "previous_level": user["level"] if level_up else None
        }
    
    async def record_mission_completion(self, telegram_id: int, mission_id: str) -> UpdateResult:
        """
        Registra a conclusão de uma missão pelo usuário.
        
        Args:
            telegram_id: ID do usuário no Telegram
            mission_id: ID da missão concluída
            
        Returns:
            Resultado da operação de atualização
        """
        now = datetime.utcnow()
        
        try:
            # Adiciona a missão à lista de missões completadas
            result = await self.collection.update_one(
                {"telegram_id": telegram_id},
                {
                    "$push": {
                        "missions_completed": {
                            "mission_id": mission_id,
                            "completed_at": now
                        }
                    },
                    "$inc": {
                        "engagement_metrics.mission_completions": 1,
                        "engagement_metrics.bot_interactions": 1
                    },
                    "$set": {
                        "last_active": now,
                        "updated_at": now
                    }
                }
            )
            logger.info(f"Missão {mission_id} registrada para usuário {telegram_id}")
            return result
        except Exception as e:
            logger.error(f"Erro ao registrar missão {mission_id} para usuário {telegram_id}: {e}")
            raise
    
    async def update_demographics(self, telegram_id: int, demographics_data: Dict) -> UpdateResult:
        """
        Atualiza os dados demográficos do usuário.
        
        Args:
            telegram_id: ID do usuário no Telegram
            demographics_data: Dados demográficos a serem atualizados
            
        Returns:
            Resultado da operação de atualização
        """
        try:
            result = await self.collection.update_one(
                {"telegram_id": telegram_id},
                {
                    "$set": {
                        "demographics": demographics_data,
                        "updated_at": datetime.utcnow()
                    },
                    "$inc": {"engagement_metrics.bot_interactions": 1}
                }
            )
            logger.info(f"Dados demográficos atualizados para usuário {telegram_id}")
            return result
        except Exception as e:
            logger.error(f"Erro ao atualizar dados demográficos do usuário {telegram_id}: {e}")
            raise
    
    async def update_preferences(self, telegram_id: int, preferences_data: Dict) -> UpdateResult:
        """
        Atualiza as preferências do usuário.
        
        Args:
            telegram_id: ID do usuário no Telegram
            preferences_data: Preferências a serem atualizadas
            
        Returns:
            Resultado da operação de atualização
        """
        try:
            result = await self.collection.update_one(
                {"telegram_id": telegram_id},
                {
                    "$set": {
                        "preferences": preferences_data,
                        "updated_at": datetime.utcnow()
                    },
                    "$inc": {"engagement_metrics.bot_interactions": 1}
                }
            )
            logger.info(f"Preferências atualizadas para usuário {telegram_id}")
            return result
        except Exception as e:
            logger.error(f"Erro ao atualizar preferências do usuário {telegram_id}: {e}")
            raise
    
    async def connect_social_media(self, telegram_id: int, platform: str, data: Dict) -> UpdateResult:
        """
        Conecta uma rede social à conta do usuário.
        
        Args:
            telegram_id: ID do usuário no Telegram
            platform: Nome da plataforma (ex: "instagram", "twitter")
            data: Dados da conexão com a rede social
            
        Returns:
            Resultado da operação de atualização
        """
        update_key = f"social_connections.{platform}"
        
        try:
            result = await self.collection.update_one(
                {"telegram_id": telegram_id},
                {
                    "$set": {
                        update_key: data,
                        "updated_at": datetime.utcnow()
                    },
                    "$inc": {"engagement_metrics.bot_interactions": 1}
                }
            )
            logger.info(f"Rede social {platform} conectada para usuário {telegram_id}")
            return result
        except Exception as e:
            logger.error(f"Erro ao conectar rede social {platform} para usuário {telegram_id}: {e}")
            raise
    
    async def record_survey_completion(self, telegram_id: int, survey_id: str, responses: Dict) -> UpdateResult:
        """
        Registra a conclusão de uma pesquisa pelo usuário.
        
        Args:
            telegram_id: ID do usuário no Telegram
            survey_id: ID da pesquisa concluída
            responses: Respostas do usuário à pesquisa
            
        Returns:
            Resultado da operação de atualização
        """
        now = datetime.utcnow()
        
        try:
            # Adiciona a pesquisa à lista de pesquisas completadas
            result = await self.collection.update_one(
                {"telegram_id": telegram_id},
                {
                    "$push": {
                        "surveys_completed": {
                            "survey_id": survey_id,
                            "responses": responses,
                            "completed_at": now
                        }
                    },
                    "$inc": {
                        "engagement_metrics.survey_completions": 1,
                        "engagement_metrics.bot_interactions": 1
                    },
                    "$set": {
                        "last_active": now,
                        "updated_at": now
                    }
                }
            )
            logger.info(f"Pesquisa {survey_id} registrada para usuário {telegram_id}")
            return result
        except Exception as e:
            logger.error(f"Erro ao registrar pesquisa {survey_id} para usuário {telegram_id}: {e}")
            raise
    
    async def get_all_users(self, filter_query: Dict = None) -> List[Dict]:
        """
        Busca todos os usuários que correspondem ao filtro.
        
        Args:
            filter_query: Filtro para a busca (opcional)
            
        Returns:
            Lista de usuários
        """
        query = filter_query or {}
        
        try:
            cursor = self.collection.find(query)
            users = await cursor.to_list(length=None)
            return users
        except Exception as e:
            logger.error(f"Erro ao buscar usuários: {e}")
            raise
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas gerais sobre os usuários.
        
        Returns:
            Dicionário com estatísticas dos usuários
        """
        try:
            # Total de usuários
            total_users = await self.collection.count_documents({})
            
            # Distribuição de níveis
            pipeline = [
                {"$group": {"_id": "$level", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            level_distribution = await self.collection.aggregate(pipeline).to_list(length=None)
            
            # Usuários ativos nos últimos 7 dias
            week_ago = datetime.utcnow() - datetime.timedelta(days=7)
            active_users = await self.collection.count_documents({"last_active": {"$gte": week_ago}})
            
            return {
                "total_users": total_users,
                "active_users_last_7_days": active_users,
                "level_distribution": {str(item["_id"]): item["count"] for item in level_distribution}
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de usuários: {e}")
            raise 
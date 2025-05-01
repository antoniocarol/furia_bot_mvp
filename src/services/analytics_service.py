"""
Serviço para análise de dados e geração de métricas para o dashboard.
"""
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging
import json
import os

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Serviço para análise de dados e métricas dos usuários do bot.
    """
    def __init__(self, db):
        """
        Inicializa o serviço de análise.
        
        Args:
            db: Instância do banco de dados
        """
        self.db = db
    
    async def get_user_growth_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Obtém métricas de crescimento de usuários nos últimos dias.
        
        Args:
            days: Número de dias para análise
            
        Returns:
            Métricas de crescimento de usuários
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Agrupa usuários por data de criação
            pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"},
                            "day": {"$dayOfMonth": "$created_at"}
                        },
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}
                }
            ]
            
            result = await self.db.db.users.aggregate(pipeline).to_list(length=None)
            
            # Formata o resultado para o dashboard
            daily_signups = []
            for item in result:
                date_str = f"{item['_id']['year']}-{item['_id']['month']:02d}-{item['_id']['day']:02d}"
                daily_signups.append({
                    "date": date_str,
                    "users": item["count"]
                })
            
            # Total de usuários
            total_users = await self.db.db.users.count_documents({})
            
            # Usuários nos últimos X dias
            new_users = await self.db.db.users.count_documents({
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
            
            return {
                "total_users": total_users,
                "new_users_last_days": new_users,
                "daily_signups": daily_signups
            }
        except Exception as e:
            logger.error(f"Erro ao obter métricas de crescimento de usuários: {e}")
            raise
    
    async def get_engagement_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Obtém métricas de engajamento dos usuários.
        
        Args:
            days: Número de dias para análise
            
        Returns:
            Métricas de engajamento
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Usuários ativos nos últimos X dias
            active_users = await self.db.db.users.count_documents({
                "last_active": {"$gte": start_date, "$lte": end_date}
            })
            
            # Média de missões por usuário
            pipeline_missions = [
                {
                    "$project": {
                        "mission_count": {"$size": "$missions_completed"}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_missions": {"$avg": "$mission_count"}
                    }
                }
            ]
            
            missions_result = await self.db.db.users.aggregate(pipeline_missions).to_list(length=None)
            avg_missions = missions_result[0]["avg_missions"] if missions_result else 0
            
            # Média de pesquisas por usuário
            pipeline_surveys = [
                {
                    "$project": {
                        "survey_count": {"$size": {"$ifNull": ["$surveys_completed", []]}}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_surveys": {"$avg": "$survey_count"}
                    }
                }
            ]
            
            surveys_result = await self.db.db.users.aggregate(pipeline_surveys).to_list(length=None)
            avg_surveys = surveys_result[0]["avg_surveys"] if surveys_result else 0
            
            # Distribuição de XP
            pipeline_xp = [
                {
                    "$group": {
                        "_id": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$lt": ["$xp", 100]}, "then": "0-100"},
                                    {"case": {"$lt": ["$xp", 500]}, "then": "100-500"},
                                    {"case": {"$lt": ["$xp", 1000]}, "then": "500-1000"},
                                    {"case": {"$lt": ["$xp", 5000]}, "then": "1000-5000"},
                                ],
                                "default": "5000+"
                            }
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            xp_result = await self.db.db.users.aggregate(pipeline_xp).to_list(length=None)
            xp_distribution = {item["_id"]: item["count"] for item in xp_result}
            
            # Total de interações com o bot
            pipeline_interactions = [
                {
                    "$group": {
                        "_id": None,
                        "total_interactions": {"$sum": "$engagement_metrics.bot_interactions"}
                    }
                }
            ]
            
            interactions_result = await self.db.db.users.aggregate(pipeline_interactions).to_list(length=None)
            total_interactions = interactions_result[0]["total_interactions"] if interactions_result else 0
            
            return {
                "active_users": active_users,
                "avg_missions_per_user": avg_missions,
                "avg_surveys_per_user": avg_surveys,
                "xp_distribution": xp_distribution,
                "total_bot_interactions": total_interactions
            }
        except Exception as e:
            logger.error(f"Erro ao obter métricas de engajamento: {e}")
            raise
    
    async def get_demographic_data(self) -> Dict[str, Any]:
        """
        Obtém dados demográficos dos usuários.
        
        Returns:
            Dados demográficos agregados
        """
        try:
            # Distribuição de idade
            pipeline_age = [
                {"$match": {"demographics.age": {"$exists": True}}},
                {"$group": {"_id": "$demographics.age", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            
            age_result = await self.db.db.users.aggregate(pipeline_age).to_list(length=None)
            age_distribution = {item["_id"]: item["count"] for item in age_result}
            
            # Distribuição de gênero
            pipeline_gender = [
                {"$match": {"demographics.gender": {"$exists": True}}},
                {"$group": {"_id": "$demographics.gender", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            
            gender_result = await self.db.db.users.aggregate(pipeline_gender).to_list(length=None)
            gender_distribution = {item["_id"]: item["count"] for item in gender_result}
            
            # Distribuição por região
            pipeline_region = [
                {"$match": {"demographics.region": {"$exists": True}}},
                {"$group": {"_id": "$demographics.region", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            
            region_result = await self.db.db.users.aggregate(pipeline_region).to_list(length=None)
            region_distribution = {item["_id"]: item["count"] for item in region_result}
            
            # Tempo de fã da FURIA
            pipeline_fan_time = [
                {"$match": {"demographics.fan_time": {"$exists": True}}},
                {"$group": {"_id": "$demographics.fan_time", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            
            fan_time_result = await self.db.db.users.aggregate(pipeline_fan_time).to_list(length=None)
            fan_time_distribution = {item["_id"]: item["count"] for item in fan_time_result}
            
            # Jogos favoritos
            pipeline_games = [
                {"$match": {"demographics.favorite_games": {"$exists": True}}},
                {"$unwind": "$demographics.favorite_games"},
                {"$group": {"_id": "$demographics.favorite_games", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            games_result = await self.db.db.users.aggregate(pipeline_games).to_list(length=None)
            games_distribution = {item["_id"]: item["count"] for item in games_result}
            
            return {
                "age_distribution": age_distribution,
                "gender_distribution": gender_distribution,
                "region_distribution": region_distribution,
                "fan_time_distribution": fan_time_distribution,
                "favorite_games": games_distribution
            }
        except Exception as e:
            logger.error(f"Erro ao obter dados demográficos: {e}")
            raise
    
    async def get_social_media_metrics(self) -> Dict[str, Any]:
        """
        Obtém métricas relacionadas às redes sociais.
        
        Returns:
            Métricas de redes sociais
        """
        try:
            # Contagem de conexões por plataforma
            pipeline_platforms = [
                {"$project": {"platforms": {"$objectToArray": "$social_connections"}}},
                {"$unwind": "$platforms"},
                {"$group": {"_id": "$platforms.k", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            platforms_result = await self.db.db.users.aggregate(pipeline_platforms).to_list(length=None)
            platform_distribution = {item["_id"]: item["count"] for item in platforms_result}
            
            # Total de usuários com pelo menos uma rede social conectada
            users_with_social = await self.db.db.users.count_documents({
                "social_connections": {"$ne": {}}
            })
            
            # Total de compartilhamentos
            pipeline_shares = [
                {
                    "$group": {
                        "_id": None,
                        "total_shares": {"$sum": "$engagement_metrics.social_shares"}
                    }
                }
            ]
            
            shares_result = await self.db.db.users.aggregate(pipeline_shares).to_list(length=None)
            total_shares = shares_result[0]["total_shares"] if shares_result else 0
            
            return {
                "platform_distribution": platform_distribution,
                "users_with_social": users_with_social,
                "total_shares": total_shares
            }
        except Exception as e:
            logger.error(f"Erro ao obter métricas de redes sociais: {e}")
            raise
    
    async def export_analytics_data(self, output_dir: str = "analytics_exports") -> str:
        """
        Exporta todos os dados analíticos para arquivos JSON.
        
        Args:
            output_dir: Diretório para salvar os arquivos
            
        Returns:
            Caminho do diretório com os arquivos exportados
        """
        try:
            # Cria o diretório se não existir
            os.makedirs(output_dir, exist_ok=True)
            
            # Coleta todos os dados
            growth_metrics = await self.get_user_growth_metrics()
            engagement_metrics = await self.get_engagement_metrics()
            demographic_data = await self.get_demographic_data()
            social_metrics = await self.get_social_media_metrics()
            
            # Timestamp para o nome dos arquivos
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Salva cada conjunto de dados em um arquivo separado
            files = {
                f"growth_metrics_{timestamp}.json": growth_metrics,
                f"engagement_metrics_{timestamp}.json": engagement_metrics,
                f"demographic_data_{timestamp}.json": demographic_data,
                f"social_metrics_{timestamp}.json": social_metrics
            }
            
            for filename, data in files.items():
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Dados analíticos exportados para {output_dir}")
            return output_dir
        except Exception as e:
            logger.error(f"Erro ao exportar dados analíticos: {e}")
            raise 
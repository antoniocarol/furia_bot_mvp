"""
Módulo de conexão com o banco de dados MongoDB.
"""
import motor.motor_asyncio
from pymongo import IndexModel, ASCENDING
import logging

logger = logging.getLogger(__name__)

class Database:
    """
    Classe para gerenciar a conexão com o MongoDB.
    """
    def __init__(self):
        """
        Inicializa a classe Database.
        """
        self.client = None
        self.db = None
    
    async def connect(self, uri: str, db_name: str):
        """
        Estabelece a conexão com o MongoDB e configura os índices.
        
        Args:
            uri: URI de conexão com o MongoDB
            db_name: Nome do banco de dados
        """
        try:
            logger.info(f"Conectando ao MongoDB: {uri}")
            self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            self.db = self.client[db_name]
            
            # Configura os índices
            await self._setup_indexes()
            
            logger.info("Conexão com MongoDB estabelecida com sucesso")
        except Exception as e:
            logger.error(f"Erro ao conectar ao MongoDB: {e}")
            raise
    
    async def _setup_indexes(self):
        """
        Configura os índices necessários no banco de dados.
        """
        # Índices para a coleção de usuários
        user_indexes = [
            IndexModel([("telegram_id", ASCENDING)], unique=True),
            IndexModel([("username", ASCENDING)]),
            IndexModel([("level", ASCENDING)])
        ]
        
        # Índices para a coleção de missões
        mission_indexes = [
            IndexModel([("title", ASCENDING)]),
            IndexModel([("type", ASCENDING)]),
            IndexModel([("requirements.min_level", ASCENDING)])
        ]
        
        # Índices para a coleção de pesquisas
        survey_indexes = [
            IndexModel([("active", ASCENDING)]),
            IndexModel([("created_at", ASCENDING)])
        ]
        
        # Cria os índices
        await self.db.users.create_indexes(user_indexes)
        await self.db.missions.create_indexes(mission_indexes)
        await self.db.surveys.create_indexes(survey_indexes)
        
        logger.info("Índices configurados com sucesso")
    
    async def close(self):
        """
        Fecha a conexão com o MongoDB.
        """
        if self.client:
            self.client.close()
            logger.info("Conexão com MongoDB fechada") 
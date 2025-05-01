"""
Configuração e conexão com o MongoDB.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

class MongoDBConfig:
    def __init__(self):
        """
        Inicializa a configuração do MongoDB usando variáveis de ambiente.
        """
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = os.getenv("MONGODB_DATABASE", "furia_bot")
        
    async def get_database(self) -> AsyncIOMotorDatabase:
        """
        Estabelece conexão com o MongoDB e retorna a instância do banco de dados.
        
        Returns:
            AsyncIOMotorDatabase: Instância do banco de dados MongoDB
        """
        client = AsyncIOMotorClient(self.mongo_uri)
        return client[self.database_name]
        
    async def get_collection(self, collection_name: str):
        """
        Retorna uma coleção específica do banco de dados.
        
        Args:
            collection_name: Nome da coleção
            
        Returns:
            AsyncIOMotorCollection: Instância da coleção MongoDB
        """
        db = await self.get_database()
        return db[collection_name] 
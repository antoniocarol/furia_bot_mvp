import json
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

class PlayerService:
    """
    Serviço para gerenciamento dos handles de redes sociais dos jogadores.
    Lê o arquivo config/players.json ou (opcional) de uma coleção Mongo.
    """

    def __init__(self, db: AsyncIOMotorDatabase, config_path: Optional[str] = None):
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Carrega do JSON de configuração
        cfg = config_path or os.path.join(os.getcwd(), "config", "players.json")
        try:
            with open(cfg, "r", encoding="utf-8") as f:
                self.players = json.load(f)
        except Exception as e:
            self.logger.error(f"Não foi possível carregar {cfg}: {e}")
            self.players = {}

    def get_twitter_handle(self, player_id: str) -> Optional[str]:
        return self.players.get(player_id, {}).get("twitter")

    def get_instagram_id(self, player_id: str) -> Optional[str]:
        return self.players.get(player_id, {}).get("instagram_id")

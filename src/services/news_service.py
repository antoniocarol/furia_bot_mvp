import os
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.services.players_service import PlayerService

class NewsService:
    """
    Serviço para integrar e gerenciar notícias do time e dos jogadores.
    Reúne postagens do Twitter e Instagram e armazena no MongoDB.
    """

    TWITTER_API_URL = "https://api.twitter.com/2"
    INSTAGRAM_API_URL = "https://graph.instagram.com"

    def __init__(self, db: AsyncIOMotorDatabase, player_svc: PlayerService):
        self.db = db
        self.player_svc = player_svc
        self.team_news_col = db.team_news
        self.player_news_col = db.player_news
        self.twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN")
        self.instagram_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.logger = logging.getLogger(__name__)
        self.team_twitter_username = "FURIA"
        self.team_instagram_userid = None  # será preenchido no fetch

    def _twitter_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.twitter_bearer}"}

    def _get_twitter_user_id(self, username: str) -> str:
        url = f"{self.TWITTER_API_URL}/users/by/username/{username}"
        resp = requests.get(url, headers=self._twitter_headers())
        resp.raise_for_status()
        return resp.json()["data"]["id"]

    async def fetch_team_tweets(self) -> None:
        """
        Busca últimos tweets do perfil oficial do time e faz upsert na coleção team_news.
        """
        try:
            user_id = self._get_twitter_user_id(self.team_twitter_username)
            url = f"{self.TWITTER_API_URL}/users/{user_id}/tweets"
            params = {"tweet.fields": "created_at", "max_results": 5}
            resp = requests.get(url, headers=self._twitter_headers(), params=params)
            resp.raise_for_status()
            tweets = resp.json().get("data", [])
            for t in tweets:
                tweet_id = t["id"]
                doc = {
                    "source": "twitter",
                    "post_id": tweet_id,
                    "timestamp": datetime.fromisoformat(t["created_at"].replace('Z','+00:00')),
                    "text": t.get("text", ""),
                    "media": [],
                    "url": f"https://twitter.com/{self.team_twitter_username}/status/{tweet_id}"
                }
                await self.team_news_col.update_one(
                    {"source": "twitter", "post_id": tweet_id},
                    {"$setOnInsert": doc},
                    upsert=True
                )
            self.logger.info("Team tweets fetched and stored: %d items", len(tweets))
        except Exception as e:
            self.logger.error("Error fetching team tweets: %s", e)

    async def fetch_team_instagram(self) -> None:
        """
        Busca postagens recentes do Instagram e armazena em team_news.
        """
        try:
            # Primeiro obtém o user-id do token
            if not self.team_instagram_userid:
                me = requests.get(
                    f"{self.INSTAGRAM_API_URL}/me",
                    params={"fields": "id", "access_token": self.instagram_token}
                )
                me.raise_for_status()
                self.team_instagram_userid = me.json()["id"]
            # Busca mídias
            url = f"{self.INSTAGRAM_API_URL}/{self.team_instagram_userid}/media"
            params = {"fields": "id,caption,media_url,permalink,timestamp", "access_token": self.instagram_token}
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            items = resp.json().get("data", [])
            for item in items:
                pid = item["id"]
                doc = {
                    "source": "instagram",
                    "post_id": pid,
                    "timestamp": datetime.fromisoformat(item["timestamp"].replace('Z','+00:00')),
                    "text": item.get("caption", ""),
                    "media": [item.get("media_url")],
                    "url": item.get("permalink")
                }
                await self.team_news_col.update_one(
                    {"source": "instagram", "post_id": pid},
                    {"$setOnInsert": doc},
                    upsert=True
                )
            self.logger.info("Team instagram posts fetched and stored: %d items", len(items))
        except Exception as e:
            self.logger.error("Error fetching team Instagram: %s", e)

    async def fetch_player_tweets(self, player_id: str) -> None:
        """
        Busca últimos tweets de um jogador (usando handle correto) e grava em player_news.
        """
        try:
            handle = self.player_svc.get_twitter_handle(player_id)
            if not handle:
                raise ValueError(f"Twitter handle não configurado para {player_id}")
            user_id = self._get_twitter_user_id(handle)
            url     = f"{self.TWITTER_API_URL}/users/{user_id}/tweets"
            params  = {"tweet.fields": "created_at", "max_results": 5}
            resp    = requests.get(url, headers=self._twitter_headers(), params=params)
            resp.raise_for_status()
            tweets = resp.json().get("data", [])
            for t in tweets:
                tid = t["id"]
                doc = {
                    "player_id": player_id,
                    "source":    "twitter",
                    "post_id":   tid,
                    "timestamp": datetime.fromisoformat(t["created_at"].replace('Z','+00:00')),
                    "text":      t.get("text", ""),
                    "media":     [],
                    "url":       f"https://twitter.com/{handle}/status/{tid}"
                }
                await self.player_news_col.update_one(
                    {"player_id": player_id, "post_id": tid},
                    {"$setOnInsert": doc},
                    upsert=True
                )
            self.logger.info("Player tweets fetched for %s: %d", player_id, len(tweets))
        except Exception as e:
            self.logger.error("Error fetching tweets for %s: %s", player_id, e)

    async def fetch_player_instagram(self, player_username: str) -> None:
        """
        A API do Instagram Graph só permite mídia do próprio token; 
        para contas de jogadores, implementar manualmente se houver token específico.
        """
        self.logger.warning("fetch_player_instagram não implementado para %s", player_username)

    async def get_latest_team_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        cursor = self.team_news_col.find().sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_latest_player_news(self, player_username: str, limit: int = 5) -> List[Dict[str, Any]]:
        cursor = (
            self.player_news_col.find({"player_id": player_username})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)
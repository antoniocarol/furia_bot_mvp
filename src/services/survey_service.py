"""
Serviço para gerenciamento de pesquisas e coleta de dados.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

class SurveyService:
    """
    Serviço para gerenciamento de pesquisas do bot.
    """
    def __init__(self, db):
        """
        Inicializa o serviço de pesquisas.
        
        Args:
            db: Instância do banco de dados
        """
        self.db = db
        self.collection = db.db.surveys
    
    async def create_survey(self, title: str, description: str, questions: List[Dict], 
                     category: str, min_level: int = 1) -> str:
        """
        Cria uma nova pesquisa.
        
        Args:
            title: Título da pesquisa
            description: Descrição da pesquisa
            questions: Lista de perguntas da pesquisa
            category: Categoria da pesquisa (ex: "demographics", "preferences", "feedback")
            min_level: Nível mínimo para participar da pesquisa
            
        Returns:
            ID da pesquisa criada
        """
        now = datetime.utcnow()
        survey_data = {
            "title": title,
            "description": description,
            "questions": questions,
            "category": category,
            "requirements": {
                "min_level": min_level
            },
            "active": True,
            "responses_count": 0,
            "created_at": now,
            "updated_at": now
        }
        
        try:
            result = await self.collection.insert_one(survey_data)
            logger.info(f"Nova pesquisa criada: {title}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao criar pesquisa: {e}")
            raise
    
    async def get_survey(self, survey_id: str) -> Optional[Dict]:
        """
        Busca uma pesquisa pelo ID.
        
        Args:
            survey_id: ID da pesquisa
            
        Returns:
            Dados da pesquisa ou None se não encontrada
        """
        try:
            survey = await self.collection.find_one({"_id": ObjectId(survey_id)})
            return survey
        except Exception as e:
            logger.error(f"Erro ao buscar pesquisa {survey_id}: {e}")
            raise
    
    async def get_active_surveys(self, user_level: int) -> List[Dict]:
        """
        Busca pesquisas ativas disponíveis para o nível do usuário.
        
        Args:
            user_level: Nível do usuário
            
        Returns:
            Lista de pesquisas disponíveis
        """
        try:
            query = {
                "active": True,
                "requirements.min_level": {"$lte": user_level}
            }
            
            cursor = self.collection.find(query)
            surveys = await cursor.to_list(length=None)
            return surveys
        except Exception as e:
            logger.error(f"Erro ao buscar pesquisas ativas: {e}")
            raise
    
    async def record_survey_response(self, survey_id: str, user_id: int, responses: Dict) -> Dict:
        """
        Registra a resposta de um usuário a uma pesquisa.
        
        Args:
            survey_id: ID da pesquisa
            user_id: ID do usuário no Telegram
            responses: Respostas do usuário
            
        Returns:
            Resultado da operação
        """
        now = datetime.utcnow()
        response_data = {
            "survey_id": ObjectId(survey_id),
            "user_id": user_id,
            "responses": responses,
            "created_at": now
        }
        
        try:
            # Insere a resposta na coleção de respostas
            await self.db.db.survey_responses.insert_one(response_data)
            
            # Incrementa o contador de respostas na pesquisa
            await self.collection.update_one(
                {"_id": ObjectId(survey_id)},
                {"$inc": {"responses_count": 1}}
            )
            
            logger.info(f"Resposta à pesquisa {survey_id} registrada para usuário {user_id}")
            return {"success": True, "message": "Resposta registrada com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao registrar resposta à pesquisa {survey_id} de usuário {user_id}: {e}")
            raise
    
    async def deactivate_survey(self, survey_id: str) -> Dict:
        """
        Desativa uma pesquisa.
        
        Args:
            survey_id: ID da pesquisa
            
        Returns:
            Resultado da operação
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(survey_id)},
                {"$set": {"active": False, "updated_at": datetime.utcnow()}}
            )
            
            if result.modified_count:
                logger.info(f"Pesquisa {survey_id} desativada")
                return {"success": True, "message": "Pesquisa desativada com sucesso"}
            else:
                logger.warning(f"Pesquisa {survey_id} não encontrada ou já desativada")
                return {"success": False, "message": "Pesquisa não encontrada ou já desativada"}
        except Exception as e:
            logger.error(f"Erro ao desativar pesquisa {survey_id}: {e}")
            raise
    
    async def get_survey_results(self, survey_id: str) -> Dict:
        """
        Obtém os resultados agregados de uma pesquisa.
        
        Args:
            survey_id: ID da pesquisa
            
        Returns:
            Resultados agregados da pesquisa
        """
        try:
            # Busca a pesquisa
            survey = await self.get_survey(survey_id)
            if not survey:
                return {"error": "Pesquisa não encontrada"}
            
            # Busca as respostas
            responses_cursor = self.db.db.survey_responses.find({"survey_id": ObjectId(survey_id)})
            responses = await responses_cursor.to_list(length=None)
            
            # Prepara os resultados agregados
            results = {
                "survey_title": survey["title"],
                "total_responses": len(responses),
                "questions": []
            }
            
            # Processa cada pergunta
            for i, question in enumerate(survey["questions"]):
                question_type = question["type"]
                question_text = question["text"]
                
                question_results = {
                    "question": question_text,
                    "type": question_type
                }
                
                if question_type in ["multiple_choice", "single_choice"]:
                    # Contagem de respostas para perguntas de escolha
                    options = question.get("options", [])
                    option_counts = {option: 0 for option in options}
                    
                    for response in responses:
                        answer = response["responses"].get(str(i))
                        if isinstance(answer, list):  # multiple_choice
                            for selected in answer:
                                if selected in option_counts:
                                    option_counts[selected] += 1
                        elif answer in option_counts:  # single_choice
                            option_counts[answer] += 1
                    
                    question_results["option_counts"] = option_counts
                
                elif question_type == "text":
                    # Lista de respostas de texto
                    text_answers = []
                    for response in responses:
                        answer = response["responses"].get(str(i))
                        if answer:
                            text_answers.append(answer)
                    
                    question_results["text_answers"] = text_answers
                
                elif question_type == "scale":
                    # Estatísticas para perguntas de escala
                    scale_answers = []
                    for response in responses:
                        answer = response["responses"].get(str(i))
                        if answer is not None:
                            try:
                                scale_answers.append(int(answer))
                            except (ValueError, TypeError):
                                pass
                    
                    if scale_answers:
                        avg = sum(scale_answers) / len(scale_answers)
                        question_results["average"] = avg
                        question_results["min"] = min(scale_answers)
                        question_results["max"] = max(scale_answers)
                        question_results["distribution"] = {}
                        for value in scale_answers:
                            question_results["distribution"][value] = question_results["distribution"].get(value, 0) + 1
                
                results["questions"].append(question_results)
            
            return results
        except Exception as e:
            logger.error(f"Erro ao obter resultados da pesquisa {survey_id}: {e}")
            raise
    
    async def create_demographic_survey(self) -> str:
        """
        Cria uma pesquisa demográfica padrão.
        
        Returns:
            ID da pesquisa criada
        """
        title = "Conheça Nossos Fãs"
        description = "Ajude-nos a entender melhor quem são os fãs da FURIA! Responda a essas perguntas rápidas e ganhe XP."
        
        questions = [
            {
                "text": "Qual a sua idade?",
                "type": "single_choice",
                "options": ["Até 18", "19-24", "25-30", "31-40", "Acima de 40"]
            },
            {
                "text": "Com qual gênero você se identifica?",
                "type": "single_choice",
                "options": ["Masculino", "Feminino", "Não-binário", "Prefiro não informar"]
            },
            {
                "text": "Em qual região do Brasil você mora?",
                "type": "single_choice",
                "options": ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
            },
            {
                "text": "Há quanto tempo você acompanha a FURIA?",
                "type": "single_choice",
                "options": ["Menos de 6 meses", "6 meses a 1 ano", "1 a 2 anos", "2 a 3 anos", "Mais de 3 anos"]
            },
            {
                "text": "Quais jogos você mais gosta de acompanhar?",
                "type": "multiple_choice",
                "options": ["CS:GO/CS2", "Valorant", "Rainbow Six", "League of Legends", "Apex Legends", "Outros"]
            }
        ]
        
        return await self.create_survey(title, description, questions, "demographics", min_level=1)
    
    async def create_preferences_survey(self) -> str:
        """
        Cria uma pesquisa de preferências padrão.
        
        Returns:
            ID da pesquisa criada
        """
        title = "Suas Preferências no CS2"
        description = "Conte-nos sobre suas preferências no CS2 e ajude-nos a melhorar nossa comunidade!"
        
        questions = [
            {
                "text": "Qual o seu mapa favorito no CS2?",
                "type": "single_choice",
                "options": ["Dust 2", "Mirage", "Inferno", "Nuke", "Ancient", "Vertigo", "Anubis", "Overpass"]
            },
            {
                "text": "Quais armas você mais utiliza?",
                "type": "multiple_choice",
                "options": ["AK-47", "M4A1/M4A4", "AWP", "Desert Eagle", "USP/Glock", "MP9/MAC-10"]
            },
            {
                "text": "Qual função você mais gosta de desempenhar em uma equipe?",
                "type": "single_choice",
                "options": ["Entry Fragger", "Lurker", "Support", "AWPer", "IGL (In-Game Leader)"]
            },
            {
                "text": "Em uma escala de 1 a 10, como você avalia o desempenho atual da FURIA?",
                "type": "scale",
                "min": 1,
                "max": 10
            },
            {
                "text": "O que você gostaria de ver mais em nossos canais?",
                "type": "multiple_choice",
                "options": ["Análises táticas", "Conteúdo de bastidores", "Tutoriais e dicas", "Entrevistas com jogadores", "Torneios comunitários"]
            }
        ]
        
        return await self.create_survey(title, description, questions, "preferences", min_level=2)
    
    async def create_feedback_survey(self) -> str:
        """
        Cria uma pesquisa de feedback padrão.
        
        Returns:
            ID da pesquisa criada
        """
        title = "Feedback da Comunidade FURIA"
        description = "Sua opinião é importante! Ajude-nos a melhorar compartilhando seu feedback."
        
        questions = [
            {
                "text": "Como você avalia a comunicação da FURIA com os fãs?",
                "type": "scale",
                "min": 1,
                "max": 5
            },
            {
                "text": "Quais aspectos da FURIA você mais aprecia?",
                "type": "multiple_choice",
                "options": ["Habilidade dos jogadores", "Comunicação nas redes sociais", "Estilo de jogo", "Personalidade dos jogadores", "Interação com fãs"]
            },
            {
                "text": "O que você acha que poderia ser melhorado?",
                "type": "text"
            },
            {
                "text": "Quais tipos de eventos você gostaria que a FURIA organizasse?",
                "type": "multiple_choice",
                "options": ["Meet & Greet com jogadores", "Torneios comunitários", "Workshops e palestras", "Transmissões especiais", "Shows e festivais"]
            },
            {
                "text": "Quais outras equipes de esports você acompanha além da FURIA?",
                "type": "text"
            }
        ]
        
        return await self.create_survey(title, description, questions, "feedback", min_level=3) 
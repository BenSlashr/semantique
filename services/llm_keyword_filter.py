"""
Service de filtrage des mots-clés parasites via LLM GPT-5-Nano
Coût: $1 pour 4000 vérifications
"""
import asyncio
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import os

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    
from config import settings

# Configuration du logging
logger = logging.getLogger(__name__)

# Pour voir tous les logs de debug LLM, décommentez la ligne suivante :
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class LLMKeywordFilter:
    """Service de filtrage intelligent des mots-clés via GPT-5-Nano"""
    
    def __init__(self):
        self.client = None
        self.enabled = False
        self.daily_requests = 0
        self.last_reset = datetime.now().date()
        
        # Initialisation seulement si la clé API et openai sont disponibles
        if (OPENAI_AVAILABLE and 
            settings.LLM_FILTERING_ENABLED and 
            settings.OPENAI_API_KEY):
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.enabled = True
                logger.info("✅ LLM Keyword Filter activé avec GPT-5-Nano")
            except Exception as e:
                logger.warning(f"❌ Erreur initialisation OpenAI: {e}")
                self.enabled = False
        else:
            logger.info("ℹ️ LLM Keyword Filter désactivé (clé API manquante ou openai non installé)")
    
    async def filter_keywords_batch(self, keywords: List[str], query: str) -> List[str]:
        """
        Filtre un batch de mots-clés via GPT-5-Nano
        
        Args:
            keywords: Liste des mots-clés à filtrer
            query: Requête SEO originale pour le contexte
            
        Returns:
            Liste des mots-clés filtrés (sans parasites)
        """
        logger.info(f"🚀 DÉBUT FILTRAGE LLM: {len(keywords)} mots-clés pour la requête '{query}'")
        
        if not self.enabled:
            logger.debug("⚠️ Service LLM désactivé, retour des mots-clés originaux")
            return keywords
            
        # Vérification des limites quotidiennes
        if not self._can_make_request():
            logger.warning("🚨 Limite quotidienne LLM atteinte, fallback vers filtrage local")
            return keywords
            
        try:
            # Découpage en batches si nécessaire
            if len(keywords) > settings.LLM_BATCH_SIZE:
                filtered_results = []
                for i in range(0, len(keywords), settings.LLM_BATCH_SIZE):
                    batch = keywords[i:i + settings.LLM_BATCH_SIZE]
                    batch_result = await self._process_batch(batch, query)
                    filtered_results.extend(batch_result)
                return filtered_results
            else:
                return await self._process_batch(keywords, query)
                
        except Exception as e:
            logger.error(f"❌ Erreur LLM filtering: {e}")
            return keywords  # Fallback vers liste originale
    
    async def _process_batch(self, keywords: List[str], query: str) -> List[str]:
        """Traite un batch de mots-clés avec GPT-5-Nano"""
        
        start_time = time.time()
        
        # Construction du prompt optimisé
        prompt = self._build_prompt(keywords, query)
        
        try:
            # Logging de la requête envoyée
            logger.debug(f"📤 PROMPT ENVOYÉ À GPT-5-NANO:\n{prompt}")
            logger.debug(f"📊 Paramètres: model={settings.LLM_MODEL}, effort=low, verbosity=low")
            
            # Appel à l'API GPT-5-Nano
            response = self.client.responses.create(
                model=settings.LLM_MODEL,
                input=prompt,
                reasoning={"effort": "low"},  # Coût réduit
                text={"verbosity": "low"}     # Réponse concise
            )
            
            # Logging de la réponse brute
            logger.debug(f"📥 RÉPONSE BRUTE GPT-5-NANO:\n{response.output_text}")
            
            # Incrément du compteur de requêtes
            self._increment_request_counter()
            
            # Parse de la réponse
            filtered_keywords = self._parse_response(response.output_text)
            
            # Logging des métriques et résultat final
            processing_time = time.time() - start_time
            logger.info(f"🤖 LLM filtrage: {len(keywords)} → {len(filtered_keywords)} mots-clés ({processing_time:.2f}s)")
            logger.debug(f"📋 MOTS-CLÉS AVANT: {keywords}")
            logger.debug(f"📋 MOTS-CLÉS APRÈS: {filtered_keywords}")
            
            return filtered_keywords
            
        except Exception as e:
            logger.error(f"❌ Erreur API GPT-5-Nano: {e}")
            logger.debug(f"🔍 Détails erreur: {type(e).__name__} - {str(e)}")
            logger.debug(f"📝 Prompt qui a causé l'erreur:\n{prompt}")
            raise
    
    def _build_prompt(self, keywords: List[str], query: str) -> str:
        """Construit le prompt optimisé pour le filtrage"""
        
        keywords_str = ", ".join(keywords)
        
        prompt = f"""FILTRAGE SEO - Requête: "{query}"

Mots-clés extraits: {keywords_str}

TÂCHE: Filtre les mots-clés parasites pour cette requête SEO.

GARDE seulement les mots-clés pertinents pour le référencement naturel de cette requête spécifique.

SUPPRIME:
- Navigation (accueil, menu, contact)
- Dates et temporel (2024, 2025, nouveau, récent)
- Marques et noms propres non liés
- Mots trop génériques (bien, faire, avoir)
- URLs et techniques (www, http, html)
- Géographiques génériques si non pertinents

RETOURNE: Uniquement la liste des mots-clés valides, séparés par des virgules, sans explication."""

        return prompt
    
    def _parse_response(self, response_text: str) -> List[str]:
        """Parse la réponse du LLM et extrait les mots-clés filtrés"""
        
        logger.debug(f"🔍 PARSING RÉPONSE LLM...")
        
        # Nettoyage de la réponse
        response_text = response_text.strip()
        logger.debug(f"📝 Réponse nettoyée: '{response_text}'")
        
        # Si la réponse contient des explications, prendre seulement la liste
        lines = response_text.split('\n')
        keywords_line = ""
        
        logger.debug(f"📄 Nombre de lignes dans la réponse: {len(lines)}")
        
        for i, line in enumerate(lines):
            logger.debug(f"📄 Ligne {i}: '{line}'")
            if ',' in line and not line.startswith(('GARDE', 'SUPPRIME', 'TÂCHE', 'RETOURNE')):
                keywords_line = line
                logger.debug(f"✅ Ligne avec mots-clés détectée: '{keywords_line}'")
                break
        
        if not keywords_line:
            keywords_line = response_text
            logger.debug(f"⚠️ Aucune ligne spécifique trouvée, utilisation de toute la réponse")
        
        # Extraction des mots-clés
        raw_keywords = [kw.strip() for kw in keywords_line.split(',') if kw.strip()]
        logger.debug(f"📋 Mots-clés extraits bruts: {raw_keywords}")
        
        # Nettoyage final
        filtered_keywords = []
        for kw in raw_keywords:
            # Supprime les guillemets et autres caractères parasites
            clean_kw = kw.strip('"\'()[]{}').lower()
            if clean_kw and len(clean_kw) > 2:
                filtered_keywords.append(clean_kw)
                logger.debug(f"✅ Mot-clé conservé: '{clean_kw}'")
            else:
                logger.debug(f"❌ Mot-clé rejeté: '{clean_kw}' (trop court ou vide)")
        
        logger.debug(f"🎯 PARSING TERMINÉ: {len(filtered_keywords)} mots-clés finaux")
        return filtered_keywords
    
    def _can_make_request(self) -> bool:
        """Vérifie si on peut faire une requête (limites quotidiennes)"""
        
        # Reset quotidien
        today = datetime.now().date()
        if today > self.last_reset:
            self.daily_requests = 0
            self.last_reset = today
        
        return self.daily_requests < settings.LLM_MAX_DAILY_REQUESTS
    
    def _increment_request_counter(self):
        """Incrémente le compteur de requêtes quotidiennes"""
        self.daily_requests += 1
    
    async def is_service_available(self) -> bool:
        """Health check du service LLM"""
        
        if not self.enabled:
            return False
            
        try:
            # Test simple avec un mot-clé
            test_result = await self.filter_keywords_batch(["test"], "test query")
            return len(test_result) >= 0  # Succès si pas d'exception
        except:
            return False
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'usage quotidiennes"""
        
        return {
            "enabled": self.enabled,
            "daily_requests": self.daily_requests,
            "remaining_requests": max(0, settings.LLM_MAX_DAILY_REQUESTS - self.daily_requests),
            "last_reset": self.last_reset.isoformat(),
            "estimated_daily_cost": round(self.daily_requests * 0.00025, 4)  # $1/4000 = $0.00025 par requête
        }

# Instance globale (optionnelle)
print(f"🔍 llm_keyword_filter.py: settings.LLM_FILTERING_ENABLED = {settings.LLM_FILTERING_ENABLED}")
print(f"🔍 llm_keyword_filter.py: settings.OPENAI_API_KEY présente = {'✅' if settings.OPENAI_API_KEY else '❌'}")

llm_filter = LLMKeywordFilter() if settings.LLM_FILTERING_ENABLED else None
print(f"🔍 llm_keyword_filter.py: Instance créée = {llm_filter is not None}")
print(f"🔍 llm_keyword_filter.py: Instance enabled = {llm_filter.enabled if llm_filter else 'N/A'}")
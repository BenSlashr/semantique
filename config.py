"""
Configuration globale de l'application SEO Analyzer
"""
import os
from typing import Optional

# Charger le .env le plus tôt possible
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("🔧 Config: .env chargé avec succès")
except ImportError:
    print("⚠️ Config: python-dotenv non disponible")

class Settings:
    """Configuration globale de l'application"""

    # API ValueSERP
    VALUESERP_API_KEY: Optional[str] = None
    SERP_API_KEY: Optional[str] = None

    # Scraping
    DEFAULT_NUM_RESULTS: int = 20  # TOP 20 par défaut
    SCRAPING_TIMEOUT: int = 10  # Timeout par page en secondes
    SCRAPING_MAX_CONCURRENT: int = 20  # Nombre max de requêtes simultanées

    # Analyse SEO
    FOCUS_TOP_N: int = 10  # Pour stats min-max des mots-clés (sur TOP 20)
    TARGET_SCORE_TOP_N: int = 5  # Pour calcul score cible
    REQUIRED_WORDS_TOP_N: int = 8  # Pour calcul nombre de mots requis

    # Cache (activé - 7 jours pour tout)
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 7 * 24 * 3600  # 7 jours en secondes

    # LLM Keyword Filtering (optionnel)
    LLM_FILTERING_ENABLED: bool = False
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-5-nano"  # $1 pour 4000 vérifications
    LLM_TIMEOUT: int = 10          # Timeout par requête
    LLM_BATCH_SIZE: int = 50       # Mots-clés par batch
    LLM_MAX_DAILY_REQUESTS: int = 200  # Limite quotidienne

    def __init__(self):
        """Charge les variables d'environnement"""
        # Chargement des variables d'environnement
        self.VALUESERP_API_KEY = os.getenv("VALUESERP_API_KEY")
        self.SERP_API_KEY = os.getenv("SERP_API_KEY")

        # Configuration scraping depuis env (ou valeurs par défaut)
        self.DEFAULT_NUM_RESULTS = int(os.getenv("DEFAULT_NUM_RESULTS", "20"))
        self.SCRAPING_TIMEOUT = int(os.getenv("SCRAPING_TIMEOUT", "10"))
        self.SCRAPING_MAX_CONCURRENT = int(os.getenv("SCRAPING_MAX_CONCURRENT", "20"))

        # Configuration analyse SEO depuis env
        self.FOCUS_TOP_N = int(os.getenv("FOCUS_TOP_N", "10"))
        self.TARGET_SCORE_TOP_N = int(os.getenv("TARGET_SCORE_TOP_N", "5"))
        self.REQUIRED_WORDS_TOP_N = int(os.getenv("REQUIRED_WORDS_TOP_N", "8"))

        # Cache
        self.ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
        self.CACHE_TTL = int(os.getenv("CACHE_TTL", str(7 * 24 * 3600)))

        # LLM Filtering
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.LLM_FILTERING_ENABLED = os.getenv("LLM_FILTERING_ENABLED", "false").lower() == "true"
        self.LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5-nano")
        self.LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "10"))
        self.LLM_BATCH_SIZE = int(os.getenv("LLM_BATCH_SIZE", "50"))
        self.LLM_MAX_DAILY_REQUESTS = int(os.getenv("LLM_MAX_DAILY_REQUESTS", "200"))


# Instance globale
settings = Settings()

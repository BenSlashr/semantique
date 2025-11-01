#!/usr/bin/env python3
"""
Test du service LLM pour vérifier s'il fonctionne
"""
import asyncio
import os
import sys

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Charger le .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Fichier .env chargé")
except ImportError:
    print("⚠️ python-dotenv non disponible")

print("🔍 VÉRIFICATION SERVICE LLM")

# Test simple des variables d'environnement
valueserp_key = os.getenv('VALUESERP_API_KEY')
openai_key = os.getenv('OPENAI_API_KEY') 
llm_enabled = os.getenv('LLM_FILTERING_ENABLED')
llm_debug = os.getenv('LLM_DEBUG_ENABLED')

print(f"VALUESERP_API_KEY: {'✅' if valueserp_key else '❌'}")
print(f"OPENAI_API_KEY: {'✅' if openai_key else '❌'}")
print(f"LLM_FILTERING_ENABLED: {llm_enabled}")
print(f"LLM_DEBUG_ENABLED: {llm_debug}")

# Test de l'import de config
try:
    from config import settings
    print(f"✅ Config chargée")
    print(f"Settings LLM_FILTERING_ENABLED: {settings.LLM_FILTERING_ENABLED}")
    print(f"Settings OPENAI_API_KEY présente: {'✅' if settings.OPENAI_API_KEY else '❌'}")
except Exception as e:
    print(f"❌ Erreur config: {e}")

# Test de l'import openai
try:
    from openai import OpenAI
    print("✅ OpenAI importé")
except ImportError as e:
    print(f"❌ OpenAI non disponible: {e}")

# Test du service LLM
try:
    from services.llm_keyword_filter import llm_filter
    print(f"✅ Service LLM importé")
    
    if llm_filter:
        print(f"Service activé: {llm_filter.enabled}")
        print(f"Statistiques: {llm_filter.get_daily_stats()}")
    else:
        print("❌ llm_filter est None")
        
except ImportError as e:
    print(f"❌ Erreur import service LLM: {e}")
except Exception as e:
    print(f"❌ Erreur générale service LLM: {e}")

# Test simple si tout est OK
try:
    if 'llm_filter' in locals() and llm_filter and llm_filter.enabled:
        print("🧪 TEST FILTRAGE...")
        
        test_keywords = ["collier", "chien", "avis", "france", "2024", "anti", "aboiement"]
        test_query = "collier anti aboiement chien"
        
        async def test():
            try:
                result = await llm_filter.filter_keywords_batch(test_keywords, test_query)
                print(f"✅ Test réussi: {len(test_keywords)} → {len(result)} mots-clés")
                print(f"Avant: {test_keywords}")
                print(f"Après: {result}")
            except Exception as e:
                print(f"❌ Erreur test LLM: {e}")
                import traceback
                traceback.print_exc()
        
        asyncio.run(test())
    else:
        print("⚠️ Pas de test - service non disponible")
        
except Exception as e:
    print(f"❌ Erreur test final: {e}")
    import traceback
    traceback.print_exc()
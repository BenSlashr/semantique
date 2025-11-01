from fastapi import FastAPI, Request, Form, HTTPException, Query, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn
import os
import logging
from dotenv import load_dotenv
from services.valueserp_service import ValueSerpService
from services.seo_analyzer import SEOAnalyzer
from services.cache_service import cache_service
from typing import Optional, List, Dict, Any
import time
from config import settings

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging LLM pour debug (optionnel)
if os.getenv("LLM_DEBUG_ENABLED", "false").lower() == "true":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('llm_debug.log')
        ]
    )
    print("🐛 DEBUG LLM activé - Logs détaillés dans llm_debug.log")

# Debug: vérifier si les variables sont chargées
import sys
print(f"🔍 DEBUG - VALUESERP_API_KEY trouvée: {'✅' if os.getenv('VALUESERP_API_KEY') else '❌'}", file=sys.stderr)
print(f"🔍 DEBUG - OPENAI_API_KEY trouvée: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}", file=sys.stderr)

# Configuration du sous-chemin - Forcer à vide car reverse proxy gère le préfixe
ROOT_PATH = ""  # os.getenv("ROOT_PATH", "")

# Application principale
app = FastAPI(
    title="API d'Analyse Sémantique SEO",
    description="API complète pour l'analyse sémantique SEO - Compatible avec tous vos outils",
    version="2.0.0",
    docs_url=f"{ROOT_PATH}/docs",
    redoc_url=f"{ROOT_PATH}/redoc"
)

# Sous-router pour gérer le préfixe
seo_router = APIRouter(prefix=ROOT_PATH)

# Configuration des templates et fichiers statiques
templates = Jinja2Templates(directory="templates")
# Les fichiers statiques doivent être accessibles sans le root_path car Traefik le gère
app.mount("/static", StaticFiles(directory="static"), name="static")

# Injection du root_path dans tous les templates
@app.middleware("http")
async def add_root_path_to_templates(request: Request, call_next):
    # Utiliser le root_path d'uvicorn (depuis headers ou config) au lieu de ROOT_PATH
    request.state.root_path = request.scope.get("root_path", "")
    response = await call_next(request)
    return response

# Services
valueserp_service = ValueSerpService()
seo_analyzer = SEOAnalyzer()

# === MODELS PYDANTIC POUR L'API ===

class AnalysisRequest(BaseModel):
    query: str
    location: Optional[str] = "France"
    language: Optional[str] = "fr"

class KeywordData(BaseModel):
    keyword: str
    frequency: int
    importance: int
    min_freq: int
    max_freq: int

class CompetitorData(BaseModel):
    position: int
    domain: str
    url: str
    title: str
    seo_score: int
    overoptimization_score: int
    word_count: int
    h1: Optional[str] = None
    internal_links: Optional[int] = 0
    external_links: Optional[int] = 0

class AnalysisResponse(BaseModel):
    query: str
    analysis_timestamp: str
    target_seo_score: int
    recommended_words: int
    max_overoptimization: int
    competitors: List[CompetitorData]
    required_keywords: List[KeywordData]
    complementary_keywords: List[KeywordData]
    ngrams: List[Dict[str, Any]]
    market_analysis: Dict[str, Any]
    generated_questions: str

# === ROUTES WEB (EXISTANTES) ===

@seo_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Page d'accueil avec le formulaire d'analyse"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "root_path": request.scope.get("root_path", "")
    })

@seo_router.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    """Page d'aide pour comprendre les métriques"""
    return templates.TemplateResponse("help.html", {
        "request": request,
        "root_path": request.scope.get("root_path", "")
    })

@seo_router.post("/analyze")
async def analyze_query(
    request: Request,
    query: str = Form(...),
    location: str = Form(default="France"),
    language: str = Form(default="fr")
):
    """Endpoint principal pour l'analyse sémantique SEO (interface web)"""
    try:
        # Récupération des résultats SERP via ValueSERP (fixé à 20)
        serp_results = await valueserp_service.get_serp_data(query, location, language, 20)
        
        # Analyse sémantique complète
        analysis_results = await seo_analyzer.analyze_competition(query, serp_results)
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "results": analysis_results,
            "query": query,
            "root_path": request.scope.get("root_path", "")
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

# === ROUTES API JSON ===

@seo_router.post("/api/v1/analyze")
async def api_analyze_complete(request: AnalysisRequest):
    """
    🚀 ENDPOINT PRINCIPAL API - Analyse sémantique complète
    
    POST /api/v1/analyze
    Body: {"query": "votre requête", "location": "France", "language": "fr"}
    
    Retourne toutes les données d'analyse en JSON structuré.
    """
    try:
        serp_results = await valueserp_service.get_serp_data(
            request.query,
            request.location,
            request.language,
            20
        )
        
        analysis_results = await seo_analyzer.analyze_competition(request.query, serp_results)
        
        # Formatage des concurrents
        competitors = []
        for comp in analysis_results.get("concurrents", []):
            competitors.append({
                "position": comp.get("position"),
                "domain": comp.get("domaine"),
                "url": comp.get("url"),
                "title": comp.get("title"),
                "seo_score": comp.get("score"),
                "overoptimization_score": comp.get("suroptimisation"),
                "word_count": comp.get("words"),
                "h1": comp.get("h1"),
                "internal_links": comp.get("internal_links", 0),
                "external_links": comp.get("external_links", 0)
            })
        
        # Formatage des mots-clés
        required_keywords = [
            {
                "keyword": kw[0],
                "frequency": kw[1],
                "importance": kw[2],
                "min_freq": kw[3],
                "max_freq": kw[4]
            }
            for kw in analysis_results.get("KW_obligatoires", [])
        ]
        
        complementary_keywords = [
            {
                "keyword": kw[0],
                "frequency": kw[1],
                "importance": kw[2],
                "min_freq": kw[3], 
                "max_freq": kw[4]
            }
            for kw in analysis_results.get("KW_complementaires", [])
        ]
        
        # Formatage des n-grammes
        ngrams = [
            {
                "ngram": ng[0],
                "frequency": ng[1],
                "importance": ng[2]
            }
            for ng in analysis_results.get("ngrams", [])
        ]
        
        return {
            "query": request.query,
            "analysis_timestamp": str(int(time.time())),
            "target_seo_score": analysis_results.get("score_cible"),
            "recommended_words": analysis_results.get("mots_requis"),
            "max_overoptimization": analysis_results.get("max_suroptimisation"),
            "competitors": competitors,
            "required_keywords": required_keywords,
            "complementary_keywords": complementary_keywords,
            "ngrams": ngrams,
            "market_analysis": {
                "content_types": analysis_results.get("types_contenu", {}),
                "word_statistics": analysis_results.get("stats_mots", [])
            },
            "generated_questions": analysis_results.get("questions", "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse: {str(e)}")

@seo_router.get("/api/v1/analyze/{query}")
async def api_analyze_get(
    query: str,
    location: Optional[str] = Query("France", description="Localisation géographique"),
    language: Optional[str] = Query("fr", description="Code langue (fr, en, es, etc.)")
):
    """
    🔍 ENDPOINT GET - Analyse rapide par URL

    GET /api/v1/analyze/{query}?location=France&language=fr
    Pratique pour les tests rapides et intégrations simples.
    """
    request_data = AnalysisRequest(query=query, location=location, language=language)
    return await api_analyze_complete(request_data)

@seo_router.get("/api/v1/competitors/{query}")
async def api_get_competitors(
    query: str,
    location: Optional[str] = Query("France", max_length=50),
    language: Optional[str] = Query("fr", max_length=5),
    top_n: Optional[int] = Query(20, ge=1, le=20, description="Nombre de concurrents à retourner (1-20)")
):
    """
    🎯 ENDPOINT CONCURRENTS - Analyse uniquement les concurrents

    GET /api/v1/competitors/{query}?location=France&language=fr&top_n=20
    """
    # Validation de la requête
    if not query or len(query.strip()) < 2:
        raise HTTPException(status_code=400, detail="La requête doit contenir au moins 2 caractères")
    
    if len(query) > 100:
        raise HTTPException(status_code=400, detail="La requête ne peut pas dépasser 100 caractères")
    
    try:
        query = query.strip()
        serp_results = await valueserp_service.get_serp_data(query, location, language, 20)
        
        analysis_results = await seo_analyzer.analyze_competition(query, serp_results)
        
        competitors = []
        for comp in analysis_results.get("concurrence", [])[:top_n]:
            # Créer un preview du contenu (200 premiers caractères)
            content_full = comp.get("content", "")
            content_preview = content_full[:200] + "..." if len(content_full) > 200 else content_full
            
            competitors.append({
                "position": comp.get("position"),
                "domain": comp.get("domaine"),
                "url": comp.get("url"),
                "title": comp.get("title"),
                "seo_score": comp.get("score"),
                "overoptimization": comp.get("suroptimisation"),
                "word_count": comp.get("words"),
                "h1": comp.get("h1"),
                "h2": comp.get("h2", ""),
                "h3": comp.get("h3", ""),
                "content_preview": content_preview,
                "content_quality": comp.get("content_quality", "unknown"),
                "internal_links": comp.get("internal_links", 0),
                "external_links": comp.get("external_links", 0),
                "images": comp.get("images", 0),
                "titles": comp.get("titles", 0)
            })
        
        return {
            "query": query,
            "location": location,
            "language": language,
            "total_competitors": len(competitors),
            "analysis_timestamp": str(int(time.time())),
            "target_score": analysis_results.get("score_target", 0),
            "avg_score": round(sum(c["seo_score"] for c in competitors) / len(competitors), 1) if competitors else 0,
            "avg_word_count": round(sum(c["word_count"] for c in competitors) / len(competitors)) if competitors else 0,
            "competitors": competitors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@seo_router.get("/api/v1/keywords/{query}")
async def api_get_keywords(
    query: str,
    location: Optional[str] = Query("France"),
    language: Optional[str] = Query("fr"),
    keyword_type: Optional[str] = Query("all", description="Type: required, complementary, ngrams, all")
):
    """
    🔑 ENDPOINT MOTS-CLÉS - Analyse sémantique pure

    GET /api/v1/keywords/{query}?keyword_type=all
    """
    try:
        serp_results = await valueserp_service.get_serp_data(query, location, language, 20)
        analysis_results = await seo_analyzer.analyze_competition(query, serp_results)
        
        response = {
            "query": query,
            "analysis_timestamp": str(int(time.time()))
        }
        
        if keyword_type in ["required", "all"]:
            response["required_keywords"] = [
                {
                    "keyword": kw[0],
                    "frequency": kw[1], 
                    "importance": kw[2],
                    "min_freq": kw[3],
                    "max_freq": kw[4]
                }
                for kw in analysis_results.get("KW_obligatoires", [])
            ]
        
        if keyword_type in ["complementary", "all"]:
            response["complementary_keywords"] = [
                {
                    "keyword": kw[0],
                    "frequency": kw[1],
                    "importance": kw[2], 
                    "min_freq": kw[3],
                    "max_freq": kw[4]
                }
                for kw in analysis_results.get("KW_complementaires", [])
            ]
        
        if keyword_type in ["ngrams", "all"]:
            response["ngrams"] = [
                {
                    "ngram": ng[0],
                    "frequency": ng[1],
                    "importance": ng[2]
                }
                for ng in analysis_results.get("ngrams", [])
            ]
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@seo_router.get("/api/v1/metrics/{query}")
async def api_get_metrics(
    query: str,
    location: Optional[str] = Query("France"),
    language: Optional[str] = Query("fr")
):
    """
    📊 ENDPOINT MÉTRIQUES - Données de performance uniquement

    GET /api/v1/metrics/{query}
    """
    try:
        serp_results = await valueserp_service.get_serp_data(query, location, language, 20)
        analysis_results = await seo_analyzer.analyze_competition(query, serp_results)
        
        return {
            "query": query,
            "analysis_timestamp": str(int(time.time())),
            "target_seo_score": analysis_results.get("score_cible"),
            "recommended_words": analysis_results.get("mots_requis"),
            "max_overoptimization": analysis_results.get("max_suroptimisation"),
            "market_analysis": {
                "content_types": analysis_results.get("types_contenu", {}),
                "word_statistics": analysis_results.get("stats_mots", [])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@seo_router.get("/api/v1/health")
async def api_health():
    """🏥 Vérification de santé de l'API"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "message": "API d'analyse SEO opérationnelle",
        "endpoints": [
            "POST /api/v1/analyze",
            "GET /api/v1/analyze/{query}",
            "GET /api/v1/competitors/{query}",
            "GET /api/v1/keywords/{query}",
            "GET /api/v1/metrics/{query}",
            "GET /api/v1/health",
            "GET /api/v1/info"
        ]
    }

@seo_router.get("/api/v1/info")
async def api_info():
    """ℹ️ Informations sur l'API"""
    return {
        "name": "API d'Analyse Sémantique SEO",
        "version": "2.0.0",
        "description": "API complète pour l'analyse concurrentielle SEO",
        "features": [
            "Analyse sémantique complète",
            "Métriques de suroptimisation basées sur la concurrence",
            "Extraction de mots-clés intelligente",
            "Génération de questions PAA",
            "Analyse de la diversité sémantique"
        ],
        "documentation": "/docs",
        "redoc": "/redoc"
    }

# Ancien endpoint pour rétrocompatibilité
@seo_router.get("/api/analyze/{query}")
async def api_analyze_legacy(
    query: str,
    location: Optional[str] = "France",
    language: Optional[str] = "fr"
):
    """Endpoint legacy - utilisez /api/v1/analyze/{query} à la place"""
    request_data = AnalysisRequest(query=query, location=location, language=language)
    return await api_analyze_complete(request_data)

@seo_router.get("/health")
async def health_check():
    """Vérification de la santé de l'application"""
    return {"status": "healthy", "service": "SEO Analyzer API"}

@seo_router.get("/debug")
async def debug_config():
    """Endpoint de diagnostic pour vérifier la configuration"""
    import os
    
    # Récupération des variables d'environnement
    serp_key = os.getenv("SERP_API_KEY")
    valueserp_key = os.getenv("VALUESERP_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    root_path = os.getenv("ROOT_PATH", "")
    
    # Import du service LLM pour statistiques
    try:
        from services.llm_keyword_filter import llm_filter
        llm_stats = llm_filter.get_daily_stats() if llm_filter else {"error": "Service non initialisé"}
    except ImportError:
        llm_stats = {"error": "Service non disponible - OpenAI non installé"}
    
    config_status = {
        "root_path": root_path,
        "serp_api_configured": bool(serp_key),
        "valueserp_api_configured": bool(valueserp_key),
        "openai_api_configured": bool(openai_key),
        "api_key_length": len(serp_key) if serp_key else 0,
        "valueserp_key_length": len(valueserp_key) if valueserp_key else 0,
        "openai_key_length": len(openai_key) if openai_key else 0,
        "llm_filtering_stats": llm_stats,
        "environment_variables": {
            "ROOT_PATH": root_path,
            "SERP_API_KEY": f"{'✅ Configurée' if serp_key else '❌ Manquante'} ({len(serp_key) if serp_key else 0} caractères)",
            "VALUESERP_API_KEY": f"{'✅ Configurée' if valueserp_key else '❌ Manquante'} ({len(valueserp_key) if valueserp_key else 0} caractères)",
            "OPENAI_API_KEY": f"{'✅ Configurée' if openai_key else '❌ Manquante'} ({len(openai_key) if openai_key else 0} caractères)",
            "LLM_FILTERING_ENABLED": os.getenv("LLM_FILTERING_ENABLED", "false")
        }
    }
    
    return config_status

@seo_router.get("/cache/stats")
async def cache_stats():
    """Statistiques du cache pour monitoring"""
    stats = cache_service.get_stats()
    return {
        "cache": stats,
        "message": "Cache activé 7 jours pour SERP + contenu + analyses" if stats.get("enabled") else "Cache désactivé"
    }

@seo_router.post("/cache/clear")
async def clear_cache():
    """Vide tout le cache (admin)"""
    success = cache_service.clear_all()
    return {
        "success": success,
        "message": "Cache vidé avec succès" if success else "Erreur lors du vidage du cache"
    }

# Inclusion du sous-router dans l'application principale
app.include_router(seo_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
from fastapi import FastAPI, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv
from services.valueserp_service import ValueSerpService
from services.seo_analyzer import SEOAnalyzer
from typing import Optional, List, Dict, Any
import time

# Charger les variables d'environnement
load_dotenv()

# Configuration du sous-chemin
ROOT_PATH = os.getenv("ROOT_PATH", "/seo-analyzer")

app = FastAPI(
    title="API d'Analyse Sémantique SEO",
    description="API complète pour l'analyse sémantique SEO - Compatible avec tous vos outils",
    version="2.0.0",
    docs_url=f"{ROOT_PATH}/docs",
    redoc_url=f"{ROOT_PATH}/redoc",
    root_path=ROOT_PATH
)

# Configuration des templates et fichiers statiques
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Injection du root_path dans tous les templates
@app.middleware("http")
async def add_root_path_to_templates(request: Request, call_next):
    # Ajouter root_path aux variables globales du template
    request.state.root_path = ROOT_PATH
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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Page d'accueil avec le formulaire d'analyse"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "root_path": ROOT_PATH
    })

@app.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    """Page d'aide pour comprendre les métriques"""
    return templates.TemplateResponse("help.html", {
        "request": request,
        "root_path": ROOT_PATH
    })

@app.post("/analyze")
async def analyze_query(
    request: Request,
    query: str = Form(...),
    location: str = Form(default="France"),
    language: str = Form(default="fr")
):
    """Endpoint principal pour l'analyse sémantique SEO (interface web)"""
    try:
        # Récupération des résultats SERP via ValueSERP
        serp_results = await valueserp_service.get_serp_data(query, location, language)
        
        # Analyse sémantique complète
        analysis_results = await seo_analyzer.analyze_competition(query, serp_results)
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "results": analysis_results,
            "query": query,
            "root_path": ROOT_PATH
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

# === ROUTES API JSON ===

@app.post("/api/v1/analyze")
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
            request.language
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

@app.get("/api/v1/analyze/{query}")
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

@app.get("/api/v1/competitors/{query}")
async def api_get_competitors(
    query: str,
    location: Optional[str] = Query("France"),
    language: Optional[str] = Query("fr"),
    top_n: Optional[int] = Query(10, description="Nombre de concurrents (max 10)")
):
    """
    🎯 ENDPOINT CONCURRENTS - Analyse uniquement les concurrents
    
    GET /api/v1/competitors/{query}?location=France&language=fr&top_n=10
    """
    try:
        serp_results = await valueserp_service.get_serp_data(query, location, language)
        analysis_results = await seo_analyzer.analyze_competition(query, serp_results)
        
        competitors = []
        for comp in analysis_results.get("concurrents", [])[:top_n]:
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
        
        return {
            "query": query,
            "total_competitors": len(competitors),
            "analysis_timestamp": str(int(time.time())),
            "competitors": competitors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/keywords/{query}")
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
        serp_results = await valueserp_service.get_serp_data(query, location, language)
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

@app.get("/api/v1/metrics/{query}")
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
        serp_results = await valueserp_service.get_serp_data(query, location, language)
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

@app.get("/api/v1/health")
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

@app.get("/api/v1/info")
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
@app.get("/api/analyze/{query}")
async def api_analyze_legacy(query: str, location: Optional[str] = "France", language: Optional[str] = "fr"):
    """Endpoint legacy - utilisez /api/v1/analyze/{query} à la place"""
    return await api_analyze_get(query, location, language)

@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé (legacy)"""
    return {"status": "OK", "message": "L'outil d'analyse SEO fonctionne parfaitement"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 
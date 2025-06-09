from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
from services.valueserp_service import ValueSerpService
from services.seo_analyzer import SEOAnalyzer

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

# === FONCTIONS API ===

async def api_analyze_complete(request: AnalysisRequest) -> Dict[str, Any]:
    """
    🚀 ANALYSE COMPLÈTE - Retourne toutes les données en JSON
    
    Analyse une requête et retourne toutes les données structurées.
    Parfait pour intégration avec vos outils et automatisations.
    """
    try:
        # Récupération des données SERP
        serp_results = await valueserp_service.get_serp_data(
            request.query, 
            request.location, 
            request.language
        )
        
        # Analyse complète
        analysis_results = await seo_analyzer.analyze_competition(request.query, serp_results)
        
        # Formatage pour l'API
        response = _format_analysis_for_api(request.query, analysis_results)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse: {str(e)}")

async def api_get_competitors_only(
    query: str,
    location: str = "France",
    language: str = "fr",
    top_n: int = 10
) -> Dict[str, Any]:
    """
    🎯 CONCURRENTS UNIQUEMENT - Analyse des concurrents seulement
    
    Retourne la liste des concurrents avec leurs métriques SEO.
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

async def api_get_keywords_only(
    query: str,
    location: str = "France",
    language: str = "fr",
    keyword_type: str = "all"
) -> Dict[str, Any]:
    """
    🔑 MOTS-CLÉS UNIQUEMENT - Analyse sémantique pure
    
    Extrait uniquement les mots-clés et leur analyse sémantique.
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

async def api_get_metrics_only(
    query: str,
    location: str = "France", 
    language: str = "fr"
) -> Dict[str, Any]:
    """
    📊 MÉTRIQUES UNIQUEMENT - Données de performance
    
    Retourne les métriques cibles et recommandations sans les détails.
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

# === FONCTION UTILITAIRE ===

def _format_analysis_for_api(query: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Formate les résultats d'analyse pour l'API"""
    
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
        "query": query,
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
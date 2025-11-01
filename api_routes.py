# === NOUVELLES ROUTES API À AJOUTER À main.py ===

# Ajoutez ces imports au début du fichier main.py :
# from pydantic import BaseModel
# from typing import Optional, List, Dict, Any
# import time

# === MODELS PYDANTIC ===
class AnalysisRequest(BaseModel):
    query: str
    location: Optional[str] = "France"
    language: Optional[str] = "fr"

# === ROUTES API À AJOUTER ===

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
        "redoc": "/redoc",
        "github": "https://github.com/votre-repo",
        "contact": "contact@votre-domaine.com"
    } 
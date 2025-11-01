# 🚀 API d'Analyse Sémantique SEO - Documentation

## 📋 Vue d'ensemble

Cette API vous permet d'intégrer l'outil d'analyse sémantique SEO dans vos applications, scripts ou workflows. Elle fournit des données structurées en JSON pour l'analyse concurrentielle SEO.

**URL de base :** `http://localhost:8000` (ou votre domaine)

## 🔑 Endpoints disponibles

### 1. **Analyse complète** 
**Le plus utilisé - Recommandé pour débuter**

```bash
# POST (recommandé)
POST /api/v1/analyze
Content-Type: application/json

{
    "query": "créatine musculation",
    "location": "France", 
    "language": "fr"
}
```

```bash
# GET (plus simple pour tests)
GET /api/v1/analyze/créatine%20musculation?location=France&language=fr
```

**Réponse JSON :**
```json
{
    "query": "créatine musculation",
    "analysis_timestamp": "1703123456",
    "target_seo_score": 72,
    "recommended_words": 1200,
    "max_overoptimization": 15,
    "competitors": [
        {
            "position": 1,
            "domain": "example.com",
            "url": "https://example.com/article",
            "title": "Guide complet créatine musculation",
            "seo_score": 68,
            "overoptimization_score": 12,
            "word_count": 1450,
            "h1": "Tout savoir sur la créatine",
            "internal_links": 15,
            "external_links": 8
        }
    ],
    "required_keywords": [
        {
            "keyword": "créatine",
            "frequency": 2,
            "importance": 44,
            "min_freq": 3,
            "max_freq": 8
        }
    ],
    "complementary_keywords": [...],
    "ngrams": [...],
    "market_analysis": {...},
    "generated_questions": "Quelles sont les différences entre..."
}
```

### 2. **Concurrents uniquement**
**Pour l'analyse concurrentielle pure**

```bash
GET /api/v1/competitors/créatine%20musculation?top_n=5
```

**Réponse JSON :**
```json
{
    "query": "créatine musculation",
    "total_competitors": 5,
    "analysis_timestamp": "1703123456",
    "competitors": [
        {
            "position": 1,
            "domain": "example.com",
            "seo_score": 68,
            "overoptimization_score": 12,
            "word_count": 1450
        }
    ]
}
```

### 3. **Mots-clés uniquement**
**Pour l'extraction sémantique pure**

```bash
# Tous les mots-clés
GET /api/v1/keywords/créatine%20musculation

# Seulement les obligatoires
GET /api/v1/keywords/créatine%20musculation?keyword_type=required

# Seulement les complémentaires  
GET /api/v1/keywords/créatine%20musculation?keyword_type=complementary

# Seulement les n-grammes
GET /api/v1/keywords/créatine%20musculation?keyword_type=ngrams
```

### 4. **Métriques uniquement**
**Pour les KPIs et recommandations**

```bash
GET /api/v1/metrics/créatine%20musculation
```

**Réponse JSON :**
```json
{
    "query": "créatine musculation",
    "analysis_timestamp": "1703123456",
    "target_seo_score": 72,
    "recommended_words": 1200,
    "max_overoptimization": 15,
    "market_analysis": {
        "content_types": {"editorial": 80, "catalogue": 20},
        "word_statistics": [800, 2500, 1450]
    }
}
```

### 5. **Santé de l'API**

```bash
GET /api/v1/health
```

```bash
GET /api/v1/info
```

## 💻 Exemples d'utilisation

### Python (requests)
```python
import requests

# Analyse complète
response = requests.post("http://localhost:8000/api/v1/analyze", 
    json={
        "query": "créatine musculation",
        "location": "France",
        "language": "fr"
    }
)

data = response.json()
print(f"Score cible: {data['target_seo_score']}")
print(f"Nombre de concurrents: {len(data['competitors'])}")

# Concurrents uniquement
competitors = requests.get(
    "http://localhost:8000/api/v1/competitors/créatine%20musculation?top_n=5"
).json()

for comp in competitors['competitors']:
    print(f"{comp['position']}. {comp['domain']} - Score: {comp['seo_score']}")
```

### cURL
```bash
# Analyse complète
curl -X POST "http://localhost:8000/api/v1/analyze" \
     -H "Content-Type: application/json" \
     -d '{"query": "créatine musculation", "location": "France"}'

# Concurrents
curl "http://localhost:8000/api/v1/competitors/créatine%20musculation?top_n=3"

# Mots-clés
curl "http://localhost:8000/api/v1/keywords/créatine%20musculation?keyword_type=required"
```

### JavaScript (fetch)
```javascript
// Analyse complète
const response = await fetch('http://localhost:8000/api/v1/analyze', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        query: 'créatine musculation',
        location: 'France',
        language: 'fr'
    })
});

const data = await response.json();
console.log(`Score cible: ${data.target_seo_score}`);

// Concurrents uniquement  
const competitors = await fetch(
    'http://localhost:8000/api/v1/competitors/créatine%20musculation?top_n=5'
).then(r => r.json());

competitors.competitors.forEach(comp => {
    console.log(`${comp.position}. ${comp.domain} - Score: ${comp.seo_score}`);
});
```

### Node.js (axios)
```javascript
const axios = require('axios');

async function analyzeQuery(query) {
    try {
        const response = await axios.post('http://localhost:8000/api/v1/analyze', {
            query: query,
            location: 'France',
            language: 'fr'
        });
        
        return response.data;
    } catch (error) {
        console.error('Erreur:', error.response.data);
    }
}

// Usage
analyzeQuery('créatine musculation').then(data => {
    console.log('Analyse terminée:', data.query);
    console.log('Score cible:', data.target_seo_score);
});
```

## 📊 Structure des données

### Concurrent
```json
{
    "position": 1,
    "domain": "example.com",
    "url": "https://example.com/page",
    "title": "Titre de la page",
    "seo_score": 68,                    // 5-85 (nouveau système)
    "overoptimization_score": 12,       // 0-100 (0=optimal, 100=spam)
    "word_count": 1450,
    "h1": "Titre principal H1",
    "internal_links": 15,
    "external_links": 8
}
```

### Mot-clé
```json
{
    "keyword": "créatine",
    "frequency": 2,          // Fréquence moyenne chez les concurrents
    "importance": 44,        // Score d'importance (0-100)
    "min_freq": 3,          // Fréquence minimum observée
    "max_freq": 8           // Fréquence maximum observée
}
```

### N-gramme
```json
{
    "ngram": "créatine monohydrate prise masse",
    "frequency": 4,
    "importance": 85
}
```

## ⚡ Cas d'usage pratiques

### 1. **Monitoring concurrentiel automatisé**
```python
import requests
import time

queries = ["créatine musculation", "whey protéine", "bcaa"]

for query in queries:
    data = requests.get(f"http://localhost:8000/api/v1/competitors/{query}").json()
    
    print(f"\n=== {query.upper()} ===")
    for comp in data['competitors'][:3]:
        print(f"{comp['position']}. {comp['domain']} - Score: {comp['seo_score']}")
    
    time.sleep(2)  # Pause entre requêtes
```

### 2. **Extraction de mots-clés pour rédaction**
```python
def get_keywords_for_content(query):
    response = requests.get(f"http://localhost:8000/api/v1/keywords/{query}")
    data = response.json()
    
    # Mots-clés obligatoires
    required = [kw['keyword'] for kw in data['required_keywords']]
    
    # Mots-clés complémentaires les plus importants
    complementary = [kw['keyword'] for kw in data['complementary_keywords'][:10]]
    
    return {
        'obligatoires': required,
        'complementaires': complementary
    }

keywords = get_keywords_for_content("créatine musculation")
print("À utiliser obligatoirement:", keywords['obligatoires'])
print("À utiliser idéalement:", keywords['complementaires'])
```

### 3. **Analyse de performance relative**
```python
def compare_to_market(query, my_content_word_count, my_seo_score):
    metrics = requests.get(f"http://localhost:8000/api/v1/metrics/{query}").json()
    
    target_score = metrics['target_seo_score']
    recommended_words = metrics['recommended_words']
    
    print(f"Votre score: {my_seo_score} | Cible marché: {target_score}")
    print(f"Vos mots: {my_content_word_count} | Recommandé: {recommended_words}")
    
    if my_seo_score < target_score:
        print("🔥 Optimisation nécessaire!")
    else:
        print("✅ Dans la norme du marché")

compare_to_market("créatine musculation", 1200, 65)
```

## 🔧 Paramètres

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `query` | string | - | **Obligatoire.** Requête à analyser |
| `location` | string | "France" | Localisation géographique |
| `language` | string | "fr" | Code langue (fr, en, es, etc.) |
| `top_n` | integer | 10 | Nombre de concurrents (max 10) |
| `keyword_type` | string | "all" | Type de mots-clés (required, complementary, ngrams, all) |

## 📈 Codes de réponse

| Code | Description |
|------|-------------|
| 200 | Succès |
| 400 | Paramètres invalides |
| 500 | Erreur serveur (souvent problème API SERP) |

## 🚀 Pour aller plus loin

### Documentation interactive
Accédez à `/docs` pour l'interface Swagger interactive.

### Intégration avancée
L'API peut être intégrée dans :
- Scripts de monitoring SEO
- Outils de rédaction de contenu
- Tableaux de bord analytics
- Workflows automatisés
- Applications mobiles

### Performance
- Temps de réponse : 5-15 secondes par requête
- Rate limiting : Dépend de votre clé ValueSERP
- Cache recommandé pour éviter les doublons

---

**🎯 Besoin d'aide ?** Consultez `/api/v1/info` pour les informations techniques ou `/docs` pour l'interface interactive. 
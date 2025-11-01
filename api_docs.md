# 🚀 API d'Analyse Sémantique SEO - Documentation

## 📋 Vue d'ensemble

Cette API transforme votre outil d'analyse SEO en service utilisable par d'autres applications. Elle retourne des données JSON structurées pour l'analyse concurrentielle SEO.

**URL de base :** `http://localhost:8000`

## 🔑 Endpoints disponibles

### 1. **POST /api/v1/analyze** - Analyse complète
**Recommandé pour la plupart des cas d'usage**

```bash
POST /api/v1/analyze
Content-Type: application/json

{
    "query": "créatine musculation",
    "location": "France", 
    "language": "fr"
}
```

### 2. **GET /api/v1/analyze/{query}** - Analyse rapide
```bash
GET /api/v1/analyze/créatine%20musculation?location=France&language=fr
```

### 3. **GET /api/v1/competitors/{query}** - Concurrents uniquement
```bash
GET /api/v1/competitors/créatine%20musculation?top_n=5
```

### 4. **GET /api/v1/keywords/{query}** - Mots-clés uniquement
```bash
GET /api/v1/keywords/créatine%20musculation?keyword_type=all
```

### 5. **GET /api/v1/metrics/{query}** - Métriques uniquement
```bash
GET /api/v1/metrics/créatine%20musculation
```

## 💻 Exemples d'utilisation

### Python
```python
import requests

# Analyse complète
response = requests.post("http://localhost:8000/api/v1/analyze", 
    json={"query": "créatine musculation", "location": "France"}
)
data = response.json()

print(f"Score cible: {data['target_seo_score']}")
print(f"Concurrents analysés: {len(data['competitors'])}")

# Mots-clés obligatoires
for kw in data['required_keywords'][:5]:
    print(f"- {kw['keyword']} (importance: {kw['importance']})")
```

### JavaScript
```javascript
// Analyse complète
const response = await fetch('http://localhost:8000/api/v1/analyze', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        query: 'créatine musculation',
        location: 'France'
    })
});

const data = await response.json();
console.log(`Score cible: ${data.target_seo_score}`);
```

### cURL
```bash
# Analyse complète
curl -X POST "http://localhost:8000/api/v1/analyze" \
     -H "Content-Type: application/json" \
     -d '{"query": "créatine musculation"}'

# Concurrents uniquement
curl "http://localhost:8000/api/v1/competitors/créatine%20musculation"
```

## 📊 Structure des réponses

### Réponse complète (`/api/v1/analyze`)
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
            "title": "Guide créatine",
            "seo_score": 68,
            "overoptimization_score": 12,
            "word_count": 1450,
            "h1": "Tout sur la créatine",
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
    "market_analysis": {...}
}
```

## 🚀 Cas d'usage

### 1. Monitoring SEO automatisé
```python
queries = ["créatine", "whey protéine", "bcaa"]
for query in queries:
    competitors = requests.get(f"http://localhost:8000/api/v1/competitors/{query}").json()
    print(f"{query}: {len(competitors['competitors'])} concurrents analysés")
```

### 2. Extraction de mots-clés pour rédaction
```python
def get_keywords(query):
    data = requests.get(f"http://localhost:8000/api/v1/keywords/{query}").json()
    return [kw['keyword'] for kw in data['required_keywords']]

keywords = get_keywords("créatine musculation")
print("Mots-clés à utiliser:", keywords[:10])
```

### 3. Comparaison avec le marché
```python
def analyze_performance(query):
    metrics = requests.get(f"http://localhost:8000/api/v1/metrics/{query}").json()
    return {
        'target_score': metrics['target_seo_score'],
        'recommended_words': metrics['recommended_words']
    }
```

## 📈 Documentation interactive

Accédez à `http://localhost:8000/docs` pour tester l'API directement dans votre navigateur avec l'interface Swagger.

## ⚙️ Paramètres

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| query | string | - | Requête à analyser (obligatoire) |
| location | string | "France" | Localisation géographique |
| language | string | "fr" | Code langue |
| top_n | integer | 10 | Nombre de concurrents |
| keyword_type | string | "all" | Type de mots-clés |

## 🔒 Authentification

Aucune authentification requise pour l'instant. L'API utilise votre clé ValueSERP configurée dans les variables d'environnement.

---

**💡 Conseil :** Commencez par tester avec `/api/v1/analyze/{votre-requête}` pour voir toutes les données disponibles, puis utilisez les endpoints spécialisés selon vos besoins. 
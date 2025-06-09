# 🚀 Outil d'Analyse Sémantique SEO

Le meilleur outil d'analyse sémantique SEO du marché, développé avec FastAPI, HTML, CSS et JavaScript.

## ✨ Fonctionnalités

- **Analyse complète des SERP** : Récupération automatique des 10 premiers résultats Google
- **Extraction de mots-clés** : Identification des mots-clés obligatoires et complémentaires
- **Analyse de la concurrence** : Scores SEO, nombre de mots, structure technique
- **Recommandations précises** : Score cible, nombre de mots requis, seuil de suroptimisation
- **N-grammes intelligents** : Extraction des expressions clés importantes
- **Questions suggérées** : Génération automatique de questions pertinentes
- **Interface moderne** : Design professionnel et responsive
- **Export des données** : Téléchargement des résultats en JSON

## 🛠️ Technologies Utilisées

- **Backend** : FastAPI (Python)
- **Frontend** : HTML5, CSS3, JavaScript, Bootstrap 5
- **API SERP** : ValueSERP pour récupérer les données Google
- **Analyse sémantique** : NLTK, scikit-learn
- **Interface** : Templates Jinja2, Chart.js pour les graphiques

## 📋 Prérequis

- Python 3.8+
- Clé API ValueSERP (https://www.valueserp.com/)

## 🚀 Installation

1. **Cloner le projet**
```bash
git clone <votre-repo>
cd outil-seo-analyzer
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration de l'API**
Créer un fichier `.env` à la racine du projet :
```env
VALUESERP_API_KEY=votre_clé_api_valueserp
```

4. **Lancer l'application**
```bash
python main.py
```

L'application sera accessible sur : http://localhost:8000

## 📖 Utilisation

### Interface Web

1. **Accéder à l'application** : Ouvrez http://localhost:8000
2. **Saisir votre requête** : Entrez le mot-clé à analyser (ex: "whey ou créatine")
3. **Configurer les paramètres** : Choisissez la localisation et la langue
4. **Lancer l'analyse** : Cliquez sur "Lancer l'analyse"
5. **Consulter les résultats** : Visualisez toutes les métriques et recommandations

### API REST

#### Analyser une requête
```bash
GET /api/analyze/{query}?location=France&language=fr
```

Exemple :
```bash
curl "http://localhost:8000/api/analyze/whey%20ou%20créatine?location=France&language=fr"
```

#### Vérifier la santé de l'API
```bash
GET /health
```

## 📊 Structure des Résultats

L'analyse retourne un objet JSON complet avec :

```json
{
    "query": "whey ou creatine",
    "score_target": 54,
    "mots_requis": 1404,
    "KW_obligatoires": [["créatine", 2, 44], ["whey", 1, 35], ...],
    "KW_complementaires": [["pack", 2, 33], ["collation", 2, 17], ...],
    "ngrams": "grammes de créatine;lait de vache;synthèse des protéines...",
    "max_suroptimisation": 5,
    "questions": "Quel est le mieux entre la créatine et la whey ?;...",
    "type_editorial": 100,
    "type_catalogue": 0,
    "type_fiche_produit": 0,
    "mots_uniques_min_max_moyenne": [37, 57, 49],
    "concurrence": [...]
}
```

## 📈 Métriques Analysées

### Mots-clés
- **Obligatoires** : Mots-clés essentiels avec fréquence et importance
- **Complémentaires** : Mots-clés secondaires pour enrichir le contenu

### Analyse concurrentielle
- Score SEO de chaque concurrent
- Nombre de mots par page
- Structure technique (liens, images, tableaux)
- Positionnement dans les résultats

### Recommandations
- **Score cible** : Score SEO à atteindre pour être compétitif
- **Nombre de mots** : Longueur recommandée du contenu
- **Seuil de suroptimisation** : Limite à ne pas dépasser

## 🔧 Configuration Avancée

### Variables d'environnement

```env
# API ValueSERP (obligatoire)
VALUESERP_API_KEY=votre_clé_api

# Configuration optionnelle
PORT=8000
DEBUG=true
```

### Paramètres d'analyse

Les paramètres peuvent être ajustés dans `services/seo_analyzer.py` :
- Nombre de mots-clés extraits
- Seuils de fréquence
- Algorithmes d'importance

## 🎯 Exemples d'Utilisation

### Cas d'usage typiques

1. **Analyse de niche e-commerce**
```
Requête: "meilleure whey protéine"
→ Analyse des fiches produits et comparatifs
```

2. **Contenu informatif**
```
Requête: "comment prendre créatine"
→ Optimisation d'articles de blog
```

3. **Recherche locale**
```
Requête: "salle sport paris"
→ SEO local et géolocalisé
```

## 🚨 Limitations

- **Quota API** : Limité par votre plan ValueSERP
- **Langues** : Optimisé pour le français, supporte d'autres langues
- **Géolocalisation** : Dépend de la couverture ValueSERP

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/amelioration`)
3. Commit les changements (`git commit -m 'Ajout fonctionnalité'`)
4. Push la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour toute question ou problème :
- Créer une issue sur GitHub
- Consulter la documentation ValueSERP
- Vérifier les logs de l'application

## 🔮 Roadmap

### Prochaines fonctionnalités
- [ ] Export CSV des résultats
- [ ] Historique des analyses
- [ ] Comparaison multi-requêtes
- [ ] Alertes de changement SERP
- [ ] Intégration Google Analytics
- [ ] API GraphQL
- [ ] Mode batch pour analyses en masse

---

**Développé avec ❤️ pour dominer les SERPs !** 
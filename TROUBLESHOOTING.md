# 🔧 Guide de Diagnostic - Outil d'Analyse Sémantique SEO

## 🚨 Problème : L'outil affiche des données de test

### Symptômes
- L'outil est accessible à l'URL `https://outils.agence-slashr.fr/seo-analyzer/`
- Mais il affiche toujours les mots-clés "créatine", "whey", etc.
- Les analyses retournent les mêmes données de démonstration

### Diagnostic

#### 1. Vérifier la configuration API

Accédez à l'endpoint de diagnostic :
```bash
curl "https://outils.agence-slashr.fr/seo-analyzer/debug"
```

**Réponse attendue :**
```json
{
  "root_path": "/seo-analyzer",
  "serp_api_configured": true,
  "valueserp_api_configured": true,
  "api_key_length": 32,
  "environment_variables": {
    "ROOT_PATH": "/seo-analyzer",
    "SERP_API_KEY": "✅ Configurée (32 caractères)",
    "VALUESERP_API_KEY": "✅ Configurée (32 caractères)"
  }
}
```

**Si vous voyez ❌ Manquante :**

#### 2. Vérifier le fichier .env

```bash
# Se connecter au conteneur Docker
docker exec -it seo-analyzer bash

# Vérifier les variables d'environnement
env | grep -E "(SERP|ROOT)"

# Vérifier le fichier .env
cat .env
```

**Le fichier .env doit contenir :**
```bash
SERP_API_KEY=votre_cle_valueserp_ici
VALUESERP_API_KEY=votre_cle_valueserp_ici
ROOT_PATH=/seo-analyzer
```

#### 3. Vérifier la configuration Docker

```bash
# Vérifier les variables dans Docker Compose
docker-compose config | grep -A 10 -B 10 seo-analyzer

# Vérifier les logs du conteneur
docker logs seo-analyzer --tail 50
```

### Solutions

#### Solution 1: Reconfigurer les variables d'environnement

```bash
# Arrêter le conteneur
docker-compose stop seo-analyzer

# Éditer le fichier .env dans /seo-tools/seo-analyzer/
sudo nano /seo-tools/seo-analyzer/.env

# Ajouter/corriger les clés API
SERP_API_KEY=votre_vraie_cle_ici
VALUESERP_API_KEY=votre_vraie_cle_ici
ROOT_PATH=/seo-analyzer

# Redémarrer
docker-compose up -d seo-analyzer
```

#### Solution 2: Reconstruire complètement

```bash
cd /seo-tools

# Supprimer le conteneur
docker-compose stop seo-analyzer
docker-compose rm -f seo-analyzer

# Reconstruire
docker-compose build seo-analyzer
docker-compose up -d seo-analyzer
```

#### Solution 3: Vérifier la clé API ValueSERP

```bash
# Tester directement l'API ValueSERP
curl "https://api.valueserp.com/search?api_key=VOTRE_CLE&q=test&location=France&hl=fr&gl=fr"
```

**Réponse attendue :**
```json
{
  "search_metadata": {
    "status": "Success"
  },
  "organic_results": [...]
}
```

## 🔍 Tests de Validation

### Test 1: Configuration
```bash
curl "https://outils.agence-slashr.fr/seo-analyzer/debug"
```

### Test 2: Santé de l'application
```bash
curl "https://outils.agence-slashr.fr/seo-analyzer/health"
```

### Test 3: Analyse simple
```bash
curl "https://outils.agence-slashr.fr/seo-analyzer/api/analyze/test"
```

## 🐛 Autres Problèmes Courants

### Erreur 404 sur les sous-chemins

**Symptôme :** L'outil principal fonctionne mais `/help` donne 404

**Solution :**
1. Vérifier la configuration Traefik
2. Vérifier que `ROOT_PATH` est bien configuré
3. Vérifier les liens dans les templates

### Problème de certificat SSL

**Symptôme :** Erreur SSL ou certificat invalide

**Solution :**
```bash
# Vérifier les logs Traefik
docker logs traefik | grep seo-analyzer

# Forcer le renouvellement du certificat
docker exec traefik traefik cert update
```

### Problème de réseau Docker

**Symptôme :** Le conteneur démarre mais n'est pas accessible

**Solution :**
```bash
# Vérifier le réseau
docker network ls
docker network inspect seo-tools-network

# Vérifier la connectivité
docker exec seo-analyzer ping google.com
```

## 📝 Logs Utiles

### Logs de l'application
```bash
docker logs seo-analyzer --follow
```

### Logs Traefik
```bash
docker logs traefik --follow | grep seo-analyzer
```

### Logs des requêtes
```bash
# Activer le debug dans l'application
docker exec seo-analyzer env DEBUG=true
```

## ✅ Check-list de Validation

- [ ] L'endpoint `/debug` montre les APIs configurées
- [ ] L'endpoint `/health` retourne "healthy"
- [ ] Le test direct de l'API ValueSERP fonctionne
- [ ] Les logs ne montrent pas d'erreurs de clé API
- [ ] Une vraie requête ne retourne pas les données "créatine"

## 🆘 Support d'Urgence

Si le problème persiste :

1. **Collecte de logs complète :**
```bash
# Sauvegarder tous les logs
docker logs seo-analyzer > seo-analyzer.log 2>&1
docker logs traefik > traefik.log 2>&1
```

2. **Test de la clé API :**
```bash
# Vérifier le compte ValueSERP
curl "https://api.valueserp.com/account?api_key=VOTRE_CLE"
```

3. **Reset complet :**
```bash
# Sauvegarder la config
cp /seo-tools/seo-analyzer/.env /tmp/seo-analyzer.env.backup

# Reset complet
docker-compose stop seo-analyzer
docker-compose rm -f seo-analyzer
docker image rm seo-analyzer:latest
docker-compose build --no-cache seo-analyzer
docker-compose up -d seo-analyzer
```

---

**💡 Conseil :** Utilisez toujours l'endpoint `/debug` en premier pour identifier rapidement la cause du problème. 
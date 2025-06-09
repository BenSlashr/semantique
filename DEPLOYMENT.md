# 🚀 Guide de Déploiement Docker - Outil d'Analyse Sémantique SEO

## 📋 Prérequis

- Docker et Docker Compose installés
- Accès au serveur `/seo-tools/`
- Clé API ValueSERP configurée
- Traefik configuré pour le reverse proxy

## 🛠️ Configuration

### 1. Variables d'environnement

Créez un fichier `.env` avec vos clés API :

```bash
SERP_API_KEY=votre_cle_valueserp
VALUESERP_API_KEY=votre_cle_valueserp
ROOT_PATH=/seo-analyzer
```

### 2. Structure de déploiement

```
/seo-tools/
├── docker-compose.yml          # Compose principal
├── seo-analyzer/              # Votre outil
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── services/
│   ├── templates/
│   └── .env
```

## 🚀 Déploiement Automatique

### Option 1: Script automatisé

```bash
# Rendre le script exécutable
chmod +x deploy.sh

# Déployer avec le nom par défaut "seo-analyzer"
./deploy.sh

# Ou avec un nom personnalisé
./deploy.sh mon-outil-seo
```

### Option 2: Déploiement manuel

#### 1. Copie des fichiers

```bash
# Copier l'outil vers le serveur
sudo mkdir -p /seo-tools/seo-analyzer
sudo cp -r . /seo-tools/seo-analyzer/
sudo chown -R www-data:www-data /seo-tools/seo-analyzer
```

#### 2. Configuration Docker Compose

Ajoutez ce service à `/seo-tools/docker-compose.yml` :

```yaml
  seo-analyzer:
    build: ./seo-analyzer
    container_name: seo-analyzer
    restart: unless-stopped
    environment:
      - ROOT_PATH=/seo-analyzer
      - SERP_API_KEY=${SERP_API_KEY}
      - VALUESERP_API_KEY=${VALUESERP_API_KEY}
    networks:
      - seo-tools-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.seo-analyzer.rule=Host(`outils.agence-slashr.fr`) && PathPrefix(`/seo-analyzer`)"
      - "traefik.http.routers.seo-analyzer.entrypoints=websecure"
      - "traefik.http.routers.seo-analyzer.tls.certresolver=letsencrypt"
      - "traefik.http.middlewares.seo-analyzer-stripprefix.stripprefix.prefixes=/seo-analyzer"
      - "traefik.http.routers.seo-analyzer.middlewares=seo-analyzer-stripprefix"
```

#### 3. Build et démarrage

```bash
cd /seo-tools
sudo docker-compose build seo-analyzer
sudo docker-compose up -d seo-analyzer
```

## 🔍 Vérification

### URLs d'accès

- **Interface Web**: `https://outils.agence-slashr.fr/seo-analyzer/`
- **Documentation API**: `https://outils.agence-slashr.fr/seo-analyzer/docs`
- **API REST**: `https://outils.agence-slashr.fr/seo-analyzer/redoc`

### Tests

```bash
# Vérifier le conteneur
docker ps | grep seo-analyzer

# Tester l'API
curl "https://outils.agence-slashr.fr/seo-analyzer/health"

# Consulter les logs
docker logs seo-analyzer
```

## 🐛 Dépannage

### Problèmes courants

#### 1. Erreur 404 sur les sous-chemins

Vérifiez que `ROOT_PATH` est bien configuré :

```bash
docker exec seo-analyzer env | grep ROOT_PATH
```

#### 2. Problème de certificat SSL

Vérifiez la configuration Traefik :

```bash
docker logs traefik | grep seo-analyzer
```

#### 3. Erreur API ValueSERP

Vérifiez la clé API :

```bash
# Tester directement
curl "https://api.valueserp.com/search?api_key=VOTRE_CLE&q=test"
```

### Logs utiles

```bash
# Logs de l'application
docker logs seo-analyzer

# Logs Traefik
docker logs traefik

# Logs système
sudo journalctl -u docker
```

## 🔄 Mise à jour

### Redéploiement

```bash
cd /seo-tools
sudo docker-compose stop seo-analyzer
sudo docker-compose build seo-analyzer
sudo docker-compose up -d seo-analyzer
```

### Rolling update

```bash
# Rebuild sans downtime
sudo docker-compose up -d --build seo-analyzer
```

## 📊 Monitoring

### Métriques Docker

```bash
# Utilisation des ressources
docker stats seo-analyzer

# Espace disque
docker system df
```

### Health checks

L'application expose un endpoint `/health` pour les vérifications :

```bash
curl "https://outils.agence-slashr.fr/seo-analyzer/health"
```

## 🔐 Sécurité

### Bonnes pratiques

1. **Variables d'environnement** : Ne jamais commiter les clés API
2. **Réseau Docker** : Utiliser des réseaux isolés
3. **Certificats SSL** : Laisser Traefik gérer Let's Encrypt
4. **Logs** : Surveiller les tentatives d'accès malveillantes

### Restrictions d'accès

Pour limiter l'accès, ajoutez des labels Traefik :

```yaml
labels:
  - "traefik.http.middlewares.seo-auth.basicauth.users=user:$$2y$$10$$..."
  - "traefik.http.routers.seo-analyzer.middlewares=seo-analyzer-stripprefix,seo-auth"
```

## 📞 Support

En cas de problème :

1. Consultez les logs Docker
2. Vérifiez la configuration Traefik
3. Testez l'API ValueSERP directement
4. Vérifiez les certificats SSL

---

**🎉 Votre outil d'analyse sémantique SEO est maintenant déployé et accessible à l'adresse :**
`https://outils.agence-slashr.fr/seo-analyzer/` 
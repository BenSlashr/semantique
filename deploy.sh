#!/bin/bash

# Script de déploiement pour l'outil d'analyse sémantique SEO
# Usage: ./deploy.sh [nom-outil]

TOOL_NAME=${1:-seo-analyzer}
DEPLOY_PATH="/seo-tools/$TOOL_NAME"
COMPOSE_FILE="/seo-tools/docker-compose.yml"

echo "🚀 Déploiement de l'outil SEO: $TOOL_NAME"
echo "📍 Chemin de déploiement: $DEPLOY_PATH"

# Vérification de l'environnement
if [ ! -f ".env" ]; then
    echo "❌ Erreur: Fichier .env manquant"
    echo "Créez un fichier .env avec SERP_API_KEY=votre_clé"
    exit 1
fi

# Création du répertoire de déploiement
echo "📁 Création du répertoire de déploiement..."
sudo mkdir -p "$DEPLOY_PATH"

# Copie des fichiers
echo "📋 Copie des fichiers..."
sudo cp -r . "$DEPLOY_PATH/"
sudo chown -R www-data:www-data "$DEPLOY_PATH"

# Configuration de l'environnement
echo "⚙️ Configuration de l'environnement..."
echo "ROOT_PATH=/$TOOL_NAME" | sudo tee -a "$DEPLOY_PATH/.env"

# Mise à jour du docker-compose.yml
echo "🐳 Mise à jour de la configuration Docker..."
cat >> /tmp/seo-service.yml << EOF

  $TOOL_NAME:
    build: $DEPLOY_PATH
    container_name: $TOOL_NAME
    restart: unless-stopped
    environment:
      - ROOT_PATH=/$TOOL_NAME
      - SERP_API_KEY=\${SERP_API_KEY}
      - VALUESERP_API_KEY=\${VALUESERP_API_KEY}
    networks:
      - seo-tools-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.$TOOL_NAME.rule=Host(\`outils.agence-slashr.fr\`) && PathPrefix(\`/$TOOL_NAME\`)"
      - "traefik.http.routers.$TOOL_NAME.entrypoints=websecure"
      - "traefik.http.routers.$TOOL_NAME.tls.certresolver=letsencrypt"
      - "traefik.http.middlewares.$TOOL_NAME-stripprefix.stripprefix.prefixes=/$TOOL_NAME"
      - "traefik.http.routers.$TOOL_NAME.middlewares=$TOOL_NAME-stripprefix"
EOF

echo "🔄 Ajout au docker-compose principal..."
sudo cat /tmp/seo-service.yml >> "$COMPOSE_FILE"

# Build et démarrage
echo "🏗️ Build de l'image Docker..."
cd "$DEPLOY_PATH"
sudo docker-compose -f "$COMPOSE_FILE" build "$TOOL_NAME"

echo "🚀 Démarrage du service..."
sudo docker-compose -f "$COMPOSE_FILE" up -d "$TOOL_NAME"

# Vérification
echo "✅ Vérification du déploiement..."
sleep 5
if sudo docker ps | grep -q "$TOOL_NAME"; then
    echo "🎉 Déploiement réussi!"
    echo "🌐 URL: https://outils.agence-slashr.fr/$TOOL_NAME/"
    echo "📊 API: https://outils.agence-slashr.fr/$TOOL_NAME/docs"
else
    echo "❌ Erreur lors du déploiement"
    sudo docker logs "$TOOL_NAME"
    exit 1
fi

# Nettoyage
rm /tmp/seo-service.yml

echo "✨ Déploiement terminé avec succès!" 
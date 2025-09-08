FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de requirements
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Téléchargement des données NLTK nécessaires
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Copie du code source
COPY . .

# Exposition du port
EXPOSE 8000

# Variable d'environnement pour le sous-chemin (vide car --root-path uvicorn gère)
ENV ROOT_PATH=

# Commande de démarrage (--root-path pour les URLs des formulaires)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/semantique"]
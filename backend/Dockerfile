FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système (gcc pour certains packages)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements.txt d'abord (pour optimiser le cache Docker)
COPY requirements.txt .

# Installer les dépendances Python avec retry logic
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt || \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copier tout le code
COPY . .

# Exposer le port 5000
EXPOSE 5000

# Démarrer l'application
CMD ["python", "app.py"]
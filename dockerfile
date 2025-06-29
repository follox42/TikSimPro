# Dockerfile pour TikSimPro
FROM python:3.11-slim

# Variables d'environnement par défaut
ENV ACCOUNT_ID=viral_account_1
ENV PUBLISHER=tiktok
ENV DEBUG=false
ENV AUTO_PUBLISH=true
ENV PYTHONPATH=/app

# Installer les dépendances système pour vidéo/audio
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    chromium \
    chromium-driver \
    xvfb \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 tiksimpro
WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer des dépendances supplémentaires pour l'automation web
RUN pip install selenium webdriver-manager requests-oauthlib

# Copier le code source
COPY --chown=tiksimpro:tiksimpro . .

# Créer les dossiers nécessaires
RUN mkdir -p /app/output /app/temp /app/logs /app/config && \
    chown -R tiksimpro:tiksimpro /app

# Passer à l'utilisateur non-root
USER tiksimpro

# Point d'entrée avec gestion des variables d'environnement
CMD ["python", "main.py", "--docker-mode"]
#!/usr/bin/env python3
"""
Script d'installation pour TikSimPro
Installe les dépendances et configure l'environnement
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def check_python_version():
    """Vérifie que la version de Python est compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Erreur: Python 3.8 ou supérieur est requis")
        print(f"Version actuelle: {sys.version}")
        return False
    return True

def install_dependencies():
    """Installe les dépendances requises"""
    print("Installation des dépendances...")
    
    # Liste des packages requis
    packages = [
        "pygame",
        "numpy",
        "scipy",
        "moviepy",
        "librosa",
        "soundfile",
        "opencv-python",
        "selenium",
        "webdriver-manager",
        "requests",
        "schedule",
        "pymunk"
    ]
    
    # Installer chaque package
    for package in packages:
        print(f"Installation de {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            print(f"Erreur lors de l'installation de {package}")
            return False
    
    print("Toutes les dépendances ont été installées avec succès")
    return True

def create_directories():
    """Crée les répertoires nécessaires"""
    directories = [
        "output",
        "temp",
        "temp/frames",
        "temp/sounds",
        "tiktok_data",
        "trend_data",
        "logs",
        "videos"
    ]
    
    print("Création des répertoires...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  - {directory}")
    
    return True

def check_ffmpeg():
    """Vérifie si FFmpeg est installé"""
    try:
        subprocess.check_call(["ffmpeg", "-version"], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL)
        print("FFmpeg est déjà installé")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FFmpeg n'est pas installé ou n'est pas dans le PATH")
        
        # Suggestion d'installation selon le système d'exploitation
        system = platform.system()
        if system == "Windows":
            print("Vous pouvez télécharger FFmpeg depuis: https://ffmpeg.org/download.html")
            print("Ou l'installer via Chocolatey: choco install ffmpeg")
        elif system == "Darwin":  # macOS
            print("Vous pouvez installer FFmpeg via Homebrew: brew install ffmpeg")
        elif system == "Linux":
            print("Vous pouvez installer FFmpeg via votre gestionnaire de paquets.")
            print("Par exemple: sudo apt install ffmpeg (Ubuntu/Debian)")
            print("Ou: sudo yum install ffmpeg (CentOS/RHEL)")
        
        return False

def check_browser_drivers():
    """Vérifie si les pilotes de navigateur sont disponibles"""
    print("Les pilotes de navigateur seront téléchargés automatiquement par webdriver-manager")
    return True

def create_default_config():
    """Crée une configuration par défaut si elle n'existe pas"""
    config_path = "config.json"
    
    if os.path.exists(config_path):
        print(f"Le fichier de configuration {config_path} existe déjà")
        return True
    
    # Configuration par défaut (simplifiée)
    default_config = """{
    "simulator": {
        "type": "CircleSimulator",
        "params": {
            "width": 1080,
            "height": 1920,
            "fps": 60,
            "duration": 30
        }
    },
    "enhancer": {
        "type": "VideoEnhancer",
        "params": {
            "add_intro": true,
            "add_hashtags": true,
            "add_music": true
        }
    },
    "publishers": {
        "tiktok": {
            "type": "TikTokPublisher",
            "params": {
                "auto_close": true
            },
            "enabled": true
        }
    },
    "data_provider": {
        "type": "TikTokAnalyzer",
        "params": {
            "cache_dir": "trend_data"
        }
    },
    "output_dir": "videos",
    "auto_publish": false,
    "publishing": {
        "cross_platform": false,
        "default_platform": "tiktok"
    }
}"""
    
    with open(config_path, 'w') as f:
        f.write(default_config)
    
    print(f"Configuration par défaut créée: {config_path}")
    return True

def main():
    """Fonction principale"""
    print("=" * 80)
    print("Installation de TikSimPro")
    print("=" * 80)
    
    # Vérifications préalables
    if not check_python_version():
        return 1
    
    # Installation des dépendances
    if not install_dependencies():
        return 1
    
    # Création des répertoires
    if not create_directories():
        return 1
    
    # Vérification de FFmpeg
    check_ffmpeg()
    
    # Vérification des pilotes de navigateur
    check_browser_drivers()
    
    # Création de la configuration par défaut
    if not create_default_config():
        return 1
    
    print("-" * 80)
    print("Installation terminée avec succès!")
    print("Vous pouvez maintenant exécuter TikSimPro avec la commande:")
    print("  python main.py")
    print("-" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
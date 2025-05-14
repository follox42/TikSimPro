# TikSimPro - Générateur de contenu TikTok viral

TikSimPro est un système modulaire qui génère automatiquement des vidéos virales pour TikTok. Il utilise des simulations physiques satisfaisantes, analyse les tendances actuelles et peut publier directement sur les plateformes sociales.

## Architecture du système

TikSimPro utilise une architecture modulaire composée des composants suivants :

1. **Analyseur de tendances** : Analyse les tendances actuelles sur TikTok
2. **Générateur de vidéo** : Crée des simulations physiques visuellement satisfaisantes
3. **Générateur audio** : Génère des pistes audio synchronisées avec les vidéos
4. **Combineur de médias** : Fusionne la vidéo et l'audio
5. **Améliorateur de vidéo** : Ajoute des textes, effets et transitions
6. **Système de publication** : Publie le contenu sur diverses plateformes
7. **Pipeline central** : Coordonne tous les composants

![Architecture](docs/architecture.png)

## Installation

1. Clonez ce dépôt :
   ```
   git clone https://github.com/yourusername/tiksimpro.git
   cd tiksimpro
   ```

2. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```

3. Initialisez la configuration par défaut :
   ```
   python main.py --init
   ```

## Utilisation

### Configuration

Le système utilise un fichier de configuration JSON. Vous pouvez modifier le fichier `config.json` selon vos besoins ou utiliser les options de ligne de commande.

### Génération de vidéo

Pour générer une vidéo avec les paramètres par défaut :
```
python main.py
```

### Options de ligne de commande

- `--config, -c` : Spécifie le fichier de configuration à utiliser
- `--output, -o` : Définit le répertoire de sortie
- `--duration, -d` : Définit la durée de la vidéo en secondes
- `--resolution, -r` : Définit la résolution de la vidéo (format: largeur:hauteur)
- `--publish, -p` : Active la publication automatique
- `--init, -i` : Initialise la configuration par défaut

Exemple :
```
python main.py --duration 45 --resolution 1080:1920 --publish
```

### Publication sur TikTok

Pour publier automatiquement sur TikTok, assurez-vous que `auto_publish` est défini sur `true` dans votre configuration et que la plateforme TikTok est activée.

Lors de la première exécution avec publication activée, vous devrez vous connecter manuellement à votre compte TikTok dans le navigateur qui s'ouvrira.

## Dépendances

- Python 3.8+
- pygame
- moviepy
- numpy
- selenium (pour la publication)
- FFmpeg (pour le traitement vidéo)

## Structure du projet

```
tiksimpro/
├── core/               # Interfaces de base
├── trend_analyzers/    # Analyseurs de tendances
├── video_generators/   # Générateurs de vidéo
├── audio_generators/   # Générateurs audio
├── media/              # Outils de traitement média
├── video_enhancers/    # Améliorateurs de vidéo
├── publishers/         # Systèmes de publication
├── pipeline/           # Pipeline central
├── config.json         # Configuration par défaut
├── main.py             # Script principal
└── README.md           # Documentation
```

## Personnalisation

### Ajouter un nouveau générateur de vidéo

1. Créez une nouvelle classe dans le dossier `video_generators/` qui implémente l'interface `IVideoGenerator`
2. Mettez à jour votre configuration pour utiliser le nouveau générateur

### Ajouter une nouvelle plateforme de publication

1. Créez une nouvelle classe dans le dossier `publishers/` qui implémente l'interface `IContentPublisher`
2. Mettez à jour votre configuration pour activer la nouvelle plateforme

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
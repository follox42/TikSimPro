"""
Script pour publier directement la dernière vidéo générée sur TikTok
sans avoir à relancer la simulation.
"""

import os
import time
import random
from tiktok_publisher import TikTokPublisher

def get_latest_video(directory="videos"):
    """Trouve le fichier vidéo le plus récent dans le dossier spécifié"""
    if not os.path.exists(directory):
        print(f"Le dossier {directory} n'existe pas.")
        return None
        
    # Lister tous les fichiers mp4
    video_files = [f for f in os.listdir(directory) if f.endswith('.mp4')]
    
    if not video_files:
        print(f"Aucun fichier vidéo trouvé dans {directory}.")
        return None
        
    # Trouver le plus récent en se basant sur la date de modification
    latest_video = max(video_files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
    
    return os.path.join(directory, latest_video)

def post_latest_video():
    """Publie la dernière vidéo générée sur TikTok"""
    print("="*80)
    print("PUBLICATION DE LA DERNIÈRE VIDÉO SUR TIKTOK")
    print("="*80)
    
    # Trouver la dernière vidéo
    video_path = get_latest_video()
    
    if not video_path:
        print("Aucune vidéo disponible à publier.")
        return False
        
    print(f"Dernière vidéo trouvée: {video_path}")
    
    # Liste de hashtags populaires pour maximiser la portée
    hashtags = [
        "fyp", 
        "simulation", 
        "satisfying", 
        "oddlysatisfying",
        "physics",
        "viral",
        "foryou",
        "tiktoktrend",
        "ballsimulation",
        "satisfyingvideos"
    ]
    
    # Description de la vidéo (variez-la pour chaque publication)
    captions = [
        "Simulation de balles explosives 💥 Regardez jusqu'à la fin!",
        "Quand la physique rencontre l'art 🎨 #simulation",
        "Satisfaisant à regarder, non? ✨ Laissez un commentaire!",
        "Comment une simple simulation peut devenir si addictive 👀",
        "C'est tellement apaisant à regarder 😌 #oddlysatisfying",
        "La physique en action! 🔬 Vos interactions préférées?",
        "Une mélodie visuelle et sonore 🎵 Quel rebond vous a hypnotisé?",
        "Les couleurs, les sons, les explosions... 🎨 Votre partie préférée?",
        "Vidéo musicale générée par la physique 🎵 Vous aimez?",
        "Chaque rebond crée une note, chaque explosion une mélodie 🎹"
    ]
    
    caption = random.choice(captions)
    
    # Initialiser le gestionnaire de publication TikTok
    publisher = TikTokPublisher()
    
    # Publier la vidéo
    success = publisher.upload_video(
        video_path=video_path,
        caption=caption,
        hashtags=hashtags
    )
    
    if success:
        print("\n" + "="*80)
        print("VIDÉO PUBLIÉE AVEC SUCCÈS!")
        print(f"Légende: {caption}")
        print(f"Hashtags: {' '.join(['#' + tag for tag in hashtags])}")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("ÉCHEC DE LA PUBLICATION")
        print(f"La vidéo existe à: {video_path}")
        print("="*80)
    
    # Fermer proprement le navigateur
    publisher.close()
    
    return success

if __name__ == "__main__":
    post_latest_video()
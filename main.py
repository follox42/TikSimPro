"""
Script principal utilisant le lecteur de mélodies pour créer une vidéo TikTok
où chaque rebond joue une note d'une mélodie populaire.
"""

import os
import time
import random
from ball_simulation import Simulation
from melody_player import integrate_melody_player, MelodyPlayer
from video_enhancer import VideoEnhancer
from tiktok_publisher_semi_auto import TikTokPublisherSemiAuto

def main():
    # Créer le dossier de sortie si nécessaire
    output_dir = "videos"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Nom du fichier de sortie
    timestamp = int(time.time())
    output_filename = f"tiktok_melody_simulation_{timestamp}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    enhanced_output_path = os.path.join(output_dir, f"tiktok_melody_simulation_{timestamp}_enhanced.mp4")
    
    print("="*80)
    print("ÉTAPE 1: CHOIX DE LA MÉLODIE")
    print("="*80)
    
    # Créer le lecteur de mélodies
    melody_player = MelodyPlayer()
    
    # Afficher les mélodies disponibles
    melody_player.list_available_melodies()
    
    # Demander à l'utilisateur de choisir une mélodie
    melody_name = melody_player.choose_melody()
    
    # Jouer une démo de la mélodie
    print("\nVoici un aperçu de la mélodie choisie:")
    melody_player.demo_melody(melody_name)
    
    print("\n" + "="*80)
    print("ÉTAPE 2: GÉNÉRATION DE LA VIDÉO")
    print("="*80)
    
    # Créer la simulation
    sim = Simulation(output_path=output_path)
    
    # Intégrer le lecteur de mélodies
    integrate_melody_player(sim)
    
    # Définir la mélodie choisie
    sim.melody_player.set_current_melody(melody_name)
    
    # Exécuter la simulation pour créer la vidéo
    sim.run()
    
    print("\n" + "="*80)
    print("ÉTAPE 3: AMÉLIORATION VISUELLE")
    print("="*80)
    
    # Créer l'améliorateur de vidéo
    enhancer = VideoEnhancer()
    
    # Préparer les textes basés sur la mélodie choisie
    intro_text = f"Chaque rebond joue une note de '{melody_name}' 🎵"
    hashtags = [
        "fyp", 
        "music", 
        melody_name.replace(" ", ""),  # Nom de la mélodie sans espaces
        "satisfying", 
        "physics", 
        "viral",
        "musicalsimulation"
    ]
    cta_text = "Suivez pour plus de mélodies! 🎵"
    
    # Demander à l'utilisateur s'il souhaite ajouter du texte
    enhance = input("Voulez-vous ajouter du texte explicatif à la vidéo? (o/n): ").lower()
    
    if enhance.startswith('o') or enhance.startswith('y'):
        # Ajouter toutes les améliorations
        enhanced_video_path = enhancer.enhance_all(
            output_path,
            enhanced_output_path,
            intro_text,
            hashtags,
            cta_text
        )
        
        if enhanced_video_path:
            print(f"\nVidéo améliorée créée: {enhanced_video_path}")
            current_video_path = enhanced_video_path
        else:
            print("\nAucune amélioration appliquée ou erreur lors de l'amélioration.")
            current_video_path = output_path
    else:
        current_video_path = output_path
    
    print("\n" + "="*80)
    print(f"VIDÉO FINALE CRÉÉE: {current_video_path}")
    print(f"Mélodie utilisée: {melody_name}")
    print("="*80)
    
    # Description de la vidéo
    captions = [
        f"Chaque rebond joue une note de '{melody_name}' 🎵 Mettez le son!",
        f"La physique joue '{melody_name}' 🎵 Quelle mélodie voulez-vous voir ensuite?",
        f"Écoutez cette version physique de '{melody_name}' 🎧 Dites-moi ce que vous en pensez!",
        f"C'est '{melody_name}' joué par des rebonds de balles! 🎵 Vous reconnaissez?",
        f"Devinez cette mélodie! 🎵 (C'est '{melody_name}')"
    ]
    
    caption = random.choice(captions)
    
    # Hashtags pour la publication
    tiktok_hashtags = [
        "fyp", 
        "foryou", 
        "viral",
        "music", 
        melody_name.replace(" ", ""),  # Nom de la mélodie sans espaces
        "musicalsimulation", 
        "satisfying", 
        "oddlysatisfying",
        "physicssong",
        "songcover"
    ]
    
    # Demander à l'utilisateur s'il souhaite publier la vidéo
    publish = input("\nVoulez-vous publier cette vidéo sur TikTok? (o/n): ").lower()
    
    if publish.startswith('o') or publish.startswith('y'):
        print("\n" + "="*80)
        print("ÉTAPE 4: PUBLICATION SUR TIKTOK (MODE SEMI-AUTOMATIQUE)")
        print("="*80)
        
        # Initialiser le gestionnaire de publication TikTok semi-automatique
        publisher = TikTokPublisherSemiAuto()
        
        # Publier la vidéo en mode semi-automatique
        success = publisher.upload_video_semi_auto(
            video_path=current_video_path,
            caption=caption,
            hashtags=tiktok_hashtags
        )
        
        if success:
            print("\n" + "="*80)
            print("VIDÉO PUBLIÉE AVEC SUCCÈS!")
            print(f"Mélodie: {melody_name}")
            print(f"Légende: {caption}")
            print(f"Hashtags: {' '.join(['#' + tag for tag in tiktok_hashtags])}")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("ÉCHEC DE LA PUBLICATION")
            print(f"La vidéo a été générée et sauvegardée à: {current_video_path}")
            print("="*80)
    else:
        print("\n" + "="*80)
        print("PUBLICATION ANNULÉE")
        print(f"La vidéo a été générée et sauvegardée à: {current_video_path}")
        print("="*80)

if __name__ == "__main__":
    main()
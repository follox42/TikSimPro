"""
Module d'amélioration audio pour la simulation de balles explosives.
Télécharge et utilise des sons de haute qualité pour les rebonds et explosions.
"""

import os
import requests
import pygame
import random
import time

class SoundManager:
    """Gestionnaire de sons pour les simulations TikTok"""
    
    # Sources de sons gratuites et libres de droits
    SOUND_SOURCES = {
        "bounce": [
            "https://freesound.org/data/previews/400/400517_7669113-lq.mp3",  # Rebond léger
            "https://freesound.org/data/previews/416/416967_8079756-lq.mp3",  # Rebond moyen
            "https://freesound.org/data/previews/414/414837_5121236-lq.mp3",  # Rebond fort
        ],
        "explosion": [
            "https://freesound.org/data/previews/587/587183_7037-lq.mp3",     # Petite explosion
            "https://freesound.org/data/previews/111/111697_1975482-lq.mp3",  # Explosion moyenne
            "https://freesound.org/data/previews/536/536255_562492-lq.mp3",   # Grande explosion
        ],
        "musical": [
            "https://freesound.org/data/previews/324/324647_5260872-lq.mp3",  # Note Do
            "https://freesound.org/data/previews/324/324648_5260872-lq.mp3",  # Note Ré
            "https://freesound.org/data/previews/324/324649_5260872-lq.mp3",  # Note Mi
            "https://freesound.org/data/previews/324/324650_5260872-lq.mp3",  # Note Fa
            "https://freesound.org/data/previews/324/324651_5260872-lq.mp3",  # Note Sol
            "https://freesound.org/data/previews/324/324652_5260872-lq.mp3",  # Note La
            "https://freesound.org/data/previews/324/324653_5260872-lq.mp3",  # Note Si
        ],
        "ambience": [
            "https://freesound.org/data/previews/169/169257_2888453-lq.mp3",  # Ambiance électronique
        ]
    }
    
    def __init__(self):
        """Initialise le gestionnaire de sons"""
        # Initialiser pygame pour la lecture audio
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 512)
        
        # Répertoire de stockage des sons
        self.sounds_dir = "sounds"
        if not os.path.exists(self.sounds_dir):
            os.makedirs(self.sounds_dir)
        
        # Dictionnaires pour stocker les sons chargés
        self.bounce_sounds = []
        self.explosion_sounds = []
        self.musical_notes = []
        self.ambience_sound = None
        
        # Chargement des sons
        self.download_and_load_sounds()
        
        # Canaux audio
        self.channels = [pygame.mixer.Channel(i) for i in range(16)]  # 16 canaux pour jouer plusieurs sons simultanément
        self.current_channel = 0
        
    def download_sound(self, url, filename):
        """Télécharge un son depuis une URL si nécessaire"""
        filepath = os.path.join(self.sounds_dir, filename)
        
        # Ne télécharger que si le fichier n'existe pas déjà
        if not os.path.exists(filepath):
            try:
                print(f"Téléchargement du son: {url}")
                response = requests.get(url)
                response.raise_for_status()  # Lever une exception en cas d'erreur
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"Son téléchargé: {filepath}")
                return True
            except Exception as e:
                print(f"Erreur lors du téléchargement du son {url}: {e}")
                return False
        return True
    
    def download_and_load_sounds(self):
        """Télécharge et charge tous les sons nécessaires"""
        print("Téléchargement et chargement des sons...")
        
        # Télécharger et charger les sons de rebond
        for i, url in enumerate(self.SOUND_SOURCES["bounce"]):
            filename = f"bounce_{i}.mp3"
            if self.download_sound(url, filename):
                try:
                    sound = pygame.mixer.Sound(os.path.join(self.sounds_dir, filename))
                    sound.set_volume(0.6)  # Volume modéré pour les rebonds
                    self.bounce_sounds.append(sound)
                except Exception as e:
                    print(f"Erreur lors du chargement du son {filename}: {e}")
        
        # Télécharger et charger les sons d'explosion
        for i, url in enumerate(self.SOUND_SOURCES["explosion"]):
            filename = f"explosion_{i}.mp3"
            if self.download_sound(url, filename):
                try:
                    sound = pygame.mixer.Sound(os.path.join(self.sounds_dir, filename))
                    sound.set_volume(0.8)  # Volume plus élevé pour les explosions
                    self.explosion_sounds.append(sound)
                except Exception as e:
                    print(f"Erreur lors du chargement du son {filename}: {e}")
        
        # Télécharger et charger les notes musicales
        for i, url in enumerate(self.SOUND_SOURCES["musical"]):
            filename = f"note_{i}.mp3"
            if self.download_sound(url, filename):
                try:
                    sound = pygame.mixer.Sound(os.path.join(self.sounds_dir, filename))
                    sound.set_volume(0.5)  # Volume modéré pour les notes
                    self.musical_notes.append(sound)
                except Exception as e:
                    print(f"Erreur lors du chargement du son {filename}: {e}")
        
        # Télécharger et charger l'ambiance
        if self.SOUND_SOURCES["ambience"]:
            url = self.SOUND_SOURCES["ambience"][0]
            filename = "ambience.mp3"
            if self.download_sound(url, filename):
                try:
                    sound = pygame.mixer.Sound(os.path.join(self.sounds_dir, filename))
                    sound.set_volume(0.3)  # Volume bas pour l'ambiance
                    self.ambience_sound = sound
                except Exception as e:
                    print(f"Erreur lors du chargement du son {filename}: {e}")
        
        print(f"Sons chargés: {len(self.bounce_sounds)} rebonds, {len(self.explosion_sounds)} explosions, {len(self.musical_notes)} notes musicales")
    
    def play_bounce(self, velocity=1.0):
        """Joue un son de rebond basé sur la vitesse"""
        if not self.bounce_sounds:
            return
        
        # Sélectionner le son en fonction de la vitesse
        if velocity < 0.3:
            index = 0  # Rebond léger
        elif velocity < 0.7:
            index = 1  # Rebond moyen
        else:
            index = 2  # Rebond fort
        
        # S'assurer que l'index est valide
        index = min(index, len(self.bounce_sounds) - 1)
        
        # Utiliser le prochain canal disponible
        channel = self.channels[self.current_channel]
        self.current_channel = (self.current_channel + 1) % len(self.channels)
        
        # Jouer le son
        channel.play(self.bounce_sounds[index])
    
    def play_explosion(self, size=1.0):
        """Joue un son d'explosion basé sur la taille"""
        if not self.explosion_sounds:
            return
        
        # Sélectionner le son en fonction de la taille
        if size < 0.3:
            index = 0  # Petite explosion
        elif size < 0.7:
            index = 1  # Explosion moyenne
        else:
            index = 2  # Grande explosion
        
        # S'assurer que l'index est valide
        index = min(index, len(self.explosion_sounds) - 1)
        
        # Utiliser le prochain canal disponible
        channel = self.channels[self.current_channel]
        self.current_channel = (self.current_channel + 1) % len(self.channels)
        
        # Jouer le son
        channel.play(self.explosion_sounds[index])
    
    def play_note(self, note_index=None):
        """Joue une note musicale spécifique ou aléatoire"""
        if not self.musical_notes:
            return
        
        # Sélectionner une note aléatoire si aucune n'est spécifiée
        if note_index is None:
            note_index = random.randint(0, len(self.musical_notes) - 1)
        
        # S'assurer que l'index est valide
        note_index = note_index % len(self.musical_notes)
        
        # Utiliser le prochain canal disponible
        channel = self.channels[self.current_channel]
        self.current_channel = (self.current_channel + 1) % len(self.channels)
        
        # Jouer la note
        channel.play(self.musical_notes[note_index])
    
    def play_ambience(self, loop=True):
        """Joue le son d'ambiance en boucle"""
        if self.ambience_sound:
            # Utiliser le canal 0 pour l'ambiance
            self.channels[0].play(self.ambience_sound, loops=-1 if loop else 0)
    
    def stop_ambience(self):
        """Arrête le son d'ambiance"""
        if self.ambience_sound:
            self.channels[0].stop()


# Fonction pour intégrer le gestionnaire de sons dans la simulation
def integrate_sound_manager(simulation):
    """
    Intègre le gestionnaire de sons dans une simulation existante.
    
    Args:
        simulation: L'instance de la classe Simulation existante
    """
    # Créer le gestionnaire de sons
    sound_manager = SoundManager()
    
    # Associer le gestionnaire de sons à la simulation
    simulation.sound_manager = sound_manager
    
    # Remplacer les méthodes de gestion du son existantes
    
    # Méthode pour jouer une note
    original_play_note = simulation.play_note
    def enhanced_play_note(note_index=None):
        # Essayer d'utiliser le gestionnaire de sons amélioré
        try:
            simulation.sound_manager.play_note(note_index)
        except Exception as e:
            print(f"Erreur lors de la lecture de note: {e}")
            # Utiliser la méthode originale en cas d'erreur
            original_play_note(note_index)
    simulation.play_note = enhanced_play_note
    
    # Méthode pour jouer un son d'explosion
    original_play_explosion_sound = simulation.play_explosion_sound
    def enhanced_play_explosion_sound():
        # Essayer d'utiliser le gestionnaire de sons amélioré
        try:
            # Taille aléatoire pour varier les sons
            size = random.uniform(0.3, 1.0)
            simulation.sound_manager.play_explosion(size)
        except Exception as e:
            print(f"Erreur lors de la lecture du son d'explosion: {e}")
            # Utiliser la méthode originale en cas d'erreur
            original_play_explosion_sound()
    simulation.play_explosion_sound = enhanced_play_explosion_sound
    
    # Améliorer la méthode on_ball_hit_wall
    original_on_ball_hit_wall = simulation.on_ball_hit_wall
    def enhanced_on_ball_hit_wall(arbiter, space, data):
        result = original_on_ball_hit_wall(arbiter, space, data)
        
        # Ajouter un son de rebond basé sur la vitesse
        ball_shape = arbiter.shapes[0] if arbiter.shapes[0].collision_type == 1 else arbiter.shapes[1]
        for ball in simulation.balls:
            if ball.shape == ball_shape:
                velocity_magnitude = np.linalg.norm(ball.body.velocity)
                normalized_velocity = min(1.0, velocity_magnitude / 2000)
                
                # Jouer un son de rebond
                try:
                    simulation.sound_manager.play_bounce(normalized_velocity)
                except Exception as e:
                    print(f"Erreur lors de la lecture du son de rebond: {e}")
                
                break
        
        return result
    simulation.on_ball_hit_wall = enhanced_on_ball_hit_wall
    
    # Améliorer la méthode on_ball_hit_ball
    original_on_ball_hit_ball = simulation.on_ball_hit_ball
    def enhanced_on_ball_hit_ball(arbiter, space, data):
        result = original_on_ball_hit_ball(arbiter, space, data)
        
        # Ajouter un son de rebond basé sur la vitesse combinée
        shapes = arbiter.shapes
        total_velocity = 0
        
        for shape in shapes:
            for ball in simulation.balls:
                if ball.shape == shape:
                    velocity_magnitude = np.linalg.norm(ball.body.velocity)
                    total_velocity += velocity_magnitude
        
        # Normaliser la vitesse totale
        normalized_velocity = min(1.0, total_velocity / 4000)
        
        # Jouer un son de rebond
        try:
            simulation.sound_manager.play_bounce(normalized_velocity)
        except Exception as e:
            print(f"Erreur lors de la lecture du son de rebond: {e}")
        
        return result
    simulation.on_ball_hit_ball = enhanced_on_ball_hit_ball
    
    # Améliorer la méthode run pour démarrer la musique d'ambiance
    original_run = simulation.run
    def enhanced_run():
        # Démarrer la musique d'ambiance
        try:
            simulation.sound_manager.play_ambience(loop=True)
        except Exception as e:
            print(f"Erreur lors du démarrage de la musique d'ambiance: {e}")
        
        # Exécuter la méthode originale
        return original_run()
    simulation.run = enhanced_run
    
    print("Gestionnaire de sons intégré avec succès dans la simulation")
    return sound_manager


# Exemple d'utilisation
if __name__ == "__main__":
    from ball_simulation import Simulation
    
    # Créer la simulation
    sim = Simulation()
    
    # Intégrer le gestionnaire de sons
    integrate_sound_manager(sim)
    
    # Exécuter la simulation
    sim.run()
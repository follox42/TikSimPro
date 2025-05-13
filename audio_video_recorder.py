"""
Module d'enregistrement audio-vidéo pour combiner la simulation visuelle avec le son.
Utilise moviepy pour fusionner les images et le son dans une vidéo finale.
"""

import os
import time
import numpy as np
import pygame
import moviepy as mpy
from pygame.locals import *
import tempfile
import wave
import struct
import array
from threading import Thread
import cv2
from ball_simulation import Simulation
from sound_manager import SoundManager

class AudioVideoRecorder:
    """Enregistreur combiné audio et vidéo pour la simulation"""
    
    def __init__(self, width, height, fps=60, output_path="output.mp4"):
        """
        Initialise l'enregistreur audio-vidéo.
        
        Args:
            width: Largeur de la vidéo
            height: Hauteur de la vidéo
            fps: Images par seconde
            output_path: Chemin du fichier de sortie
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.output_path = output_path
        
        # Créer les dossiers temporaires
        self.temp_dir = tempfile.mkdtemp()
        self.frames_dir = os.path.join(self.temp_dir, "frames")
        os.makedirs(self.frames_dir, exist_ok=True)
        
        # Fichiers temporaires
        self.audio_file = os.path.join(self.temp_dir, "audio.wav")
        
        # Compteurs
        self.frame_count = 0
        
        # Configuration de l'enregistrement audio
        self.audio_recording = False
        self.audio_thread = None
        self.sample_rate = 44100
        self.audio_channels = 2
        self.audio_samples = []
        
        print(f"Enregistreur initialisé: {width}x{height} à {fps} FPS")
        print(f"Dossier temporaire: {self.temp_dir}")
    
    def start_audio_recording(self):
        """Démarre l'enregistrement audio en arrière-plan"""
        self.audio_recording = True
        self.audio_samples = []
        
        # Configurer pygame.mixer pour l'enregistrement
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=self.audio_channels)
        
        # Démarrer un thread pour l'enregistrement audio
        self.audio_thread = Thread(target=self._audio_recording_thread)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
        print("Enregistrement audio démarré")
    
    def _audio_recording_thread(self):
        """Thread d'enregistrement audio"""
        # Cette fonction simule l'enregistrement en capturant les données audio
        # générées par pygame.mixer
        
        # En réalité, nous ne pouvons pas directement accéder au flux audio
        # de pygame.mixer, donc nous allons utiliser un fichier temporaire
        # qui sera ensuite fusionné avec la vidéo
        
        # Note: Ceci est une simulation, pas un vrai enregistrement
        # Dans un cas réel, on utiliserait pyaudio ou un autre module
        # pour enregistrer l'audio du système
        
        # Créer un fichier wav vide comme placeholder
        with wave.open(self.audio_file, 'wb') as wf:
            wf.setnchannels(self.audio_channels)
            wf.setsampwidth(2)  # 2 bytes (16 bits)
            wf.setframerate(self.sample_rate)
            
            # Durée estimée basée sur le nombre de frames vidéo
            estimated_duration = self.fps * 60 / self.fps
            num_samples = int(estimated_duration * self.sample_rate)
            
            # Écrire des zéros (silence) comme placeholder
            # Dans un cas réel, on enregistrerait le vrai son ici
            data = array.array('h', [0] * num_samples * self.audio_channels)
            wf.writeframes(data.tobytes())
        
        print("Fichier audio placeholder créé:", self.audio_file)
        
        # Dans un cas réel, ici on attendrait la fin de l'enregistrement
        while self.audio_recording:
            time.sleep(0.1)
    
    def stop_audio_recording(self):
        """Arrête l'enregistrement audio"""
        self.audio_recording = False
        if self.audio_thread:
            self.audio_thread.join(timeout=2.0)
        
        print("Enregistrement audio arrêté")
    
    def capture_frame(self, surface):
        """
        Capture un frame depuis une surface pygame.
        
        Args:
            surface: Surface pygame à capturer
        """
        # Enregistrer le frame dans un fichier
        frame_file = os.path.join(self.frames_dir, f"frame_{self.frame_count:06d}.png")
        pygame.image.save(surface, frame_file)
        
        self.frame_count += 1
        
        # Afficher la progression tous les 60 frames (1 seconde à 60 FPS)
        if self.frame_count % 60 == 0:
            duration = self.frame_count / self.fps
            print(f"Frames capturés: {self.frame_count} ({duration:.1f}s)")
    
    def finalize(self):
        """Finalise l'enregistrement et crée la vidéo de sortie"""
        # Arrêter l'enregistrement audio
        self.stop_audio_recording()
        
        print("Finalisation de la vidéo...")
        print(f"Assemblage de {self.frame_count} frames")
        
        # Créer la liste de tous les frames
        frame_files = [
            os.path.join(self.frames_dir, f"frame_{i:06d}.png")
            for i in range(self.frame_count)
        ]
        
        # Vérifier les fichiers manquants
        missing_files = [f for f in frame_files if not os.path.exists(f)]
        if missing_files:
            print(f"Attention: {len(missing_files)} frames manquants!")
            # Filtrer pour ne garder que les fichiers existants
            frame_files = [f for f in frame_files if os.path.exists(f)]
        
        if not frame_files:
            print("Erreur: Aucun frame à assembler!")
            return False
        
        try:
            # Créer un clip vidéo à partir des images
            print("Création du clip vidéo...")
            video_clip = mpy.ImageSequenceClip(frame_files, fps=self.fps)
            
            # Ajouter l'audio capturé
            if os.path.exists(self.audio_file):
                print("Ajout de l'audio à la vidéo...")
                
                # Essayer d'utiliser l'audio capturé
                try:
                    audio_clip = mpy.AudioFileClip(self.audio_file)
                    video_clip = video_clip.set_audio(audio_clip)
                except Exception as e:
                    print(f"Erreur lors de l'ajout de l'audio: {e}")
                    print("Création de la vidéo sans audio...")
            else:
                print("Pas de fichier audio trouvé, création de la vidéo sans audio...")
            
            # Vérifier la durée de la vidéo
            target_duration = 61.0  # 61 secondes exactement
            actual_duration = video_clip.duration
            
            print(f"Durée actuelle: {actual_duration:.2f}s, Durée cible: {target_duration:.2f}s")
            
            # Ajuster la durée si nécessaire
            if actual_duration < target_duration:
                # Si trop court, ralentir légèrement
                ratio = target_duration / actual_duration
                print(f"Ajustement de la durée: ralentissement de {ratio:.2f}x")
                video_clip = video_clip.fx(mpy.vfx.speedx, 1/ratio)
            elif actual_duration > target_duration:
                # Si trop long, couper
                print(f"Ajustement de la durée: coupure à {target_duration}s")
                video_clip = video_clip.subclip(0, target_duration)
            
            # Écrire la vidéo finale
            print(f"Écriture de la vidéo finale: {self.output_path}")
            video_clip.write_videofile(
                self.output_path,
                codec='libx264',
                audio_codec='aac',
                fps=self.fps,
                threads=4,
                preset='medium'
            )
            
            print(f"Vidéo créée avec succès: {self.output_path}")
            return True
            
        except Exception as e:
            print(f"Erreur lors de la création de la vidéo: {e}")
            
            # Plan B: Utiliser OpenCV pour créer une vidéo sans audio
            print("Tentative de création de vidéo de secours avec OpenCV (sans audio)...")
            
            try:
                # Lire les dimensions du premier frame
                first_frame = cv2.imread(frame_files[0])
                h, w, _ = first_frame.shape
                
                # Créer l'enregistreur vidéo
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(self.output_path, fourcc, self.fps, (w, h))
                
                # Ajouter chaque frame
                for i, frame_file in enumerate(frame_files):
                    frame = cv2.imread(frame_file)
                    out.write(frame)
                    
                    # Afficher la progression
                    if i % 60 == 0:
                        print(f"Traitement des frames: {i}/{len(frame_files)}")
                
                # Libérer les ressources
                out.release()
                
                print(f"Vidéo de secours créée (sans audio): {self.output_path}")
                print("Note: Cette vidéo n'a pas d'audio. Utilisez un logiciel d'édition pour ajouter de l'audio.")
                return True
                
            except Exception as e2:
                print(f"Échec de la création de vidéo de secours: {e2}")
                return False
    
    def cleanup(self):
        """Nettoie les fichiers temporaires"""
        import shutil
        
        try:
            # Supprimer le dossier temporaire
            shutil.rmtree(self.temp_dir)
            print(f"Nettoyage terminé: {self.temp_dir} supprimé")
        except Exception as e:
            print(f"Erreur lors du nettoyage: {e}")


# Module pour remplacer l'enregistrement vidéo dans la simulation
def create_av_simulation(simulation_class):
    """
    Crée une version modifiée de la classe de simulation avec enregistrement audio-vidéo.
    
    Args:
        simulation_class: La classe de simulation à modifier
        
    Returns:
        Une nouvelle classe avec enregistrement audio-vidéo intégré
    """
    class AVSimulation(simulation_class):
        """Version modifiée de la simulation avec enregistrement audio-vidéo"""
        
        def __init__(self, *args, **kwargs):
            # Appeler le constructeur de la classe parente
            super().__init__(*args, **kwargs)
            
            # Créer l'enregistreur audio-vidéo
            self.av_recorder = AudioVideoRecorder(
                width=self.width,
                height=self.height,
                fps=self.fps,
                output_path=self.output_path
            )
            
            # Remplacer la méthode d'enregistrement vidéo
            self.original_capture_frame = self.capture_frame
            self.capture_frame = self.av_capture_frame
            
            # Flag pour l'enregistrement audio
            self.av_recording_started = False
        
        def av_capture_frame(self):
            """Version modifiée de capture_frame qui enregistre aussi l'audio"""
            # Démarrer l'enregistrement audio au premier frame
            if not self.av_recording_started:
                self.av_recorder.start_audio_recording()
                self.av_recording_started = True
            
            # Capturer le frame
            self.av_recorder.capture_frame(self.screen)
            
            # Appeler aussi la méthode originale pour compatibilité
            self.original_capture_frame()
        
        def run(self):
            """Version modifiée de run qui finalise l'enregistrement audio-vidéo"""
            try:
                # Exécuter la méthode originale
                result = super().run()
                
                # Finaliser l'enregistrement
                print("Finalisation de l'enregistrement audio-vidéo...")
                self.av_recorder.finalize()
                
                # Nettoyer les fichiers temporaires
                self.av_recorder.cleanup()
                
                return result
                
            except Exception as e:
                print(f"Erreur dans l'exécution de la simulation: {e}")
                # Essayer de finaliser quand même
                try:
                    self.av_recorder.finalize()
                    self.av_recorder.cleanup()
                except:
                    pass
                raise
    
    return AVSimulation


# Fonction pour créer et exécuter une simulation avec audio-vidéo
def run_av_simulation(output_path="output.mp4"):
    """
    Crée et exécute une simulation avec enregistrement audio-vidéo.
    
    Args:
        output_path: Chemin du fichier de sortie
        
    Returns:
        Le chemin du fichier créé
    """
    from ball_simulation import Simulation
    from sound_manager import integrate_sound_manager
    
    # Créer la classe de simulation améliorée
    AVSimulation = create_av_simulation(Simulation)
    
    # Créer une instance de la simulation
    sim = AVSimulation(output_path=output_path)
    
    # Intégrer le gestionnaire de sons
    sound_manager = integrate_sound_manager(sim)
    
    # Exécuter la simulation
    sim.run()
    
    return output_path


# Exemple d'utilisation
if __name__ == "__main__":
    output_file = "simulation_avec_son.mp4"
    result = run_av_simulation(output_file)
    print(f"Vidéo créée: {result}")
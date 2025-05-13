"""
Module pour télécharger et convertir automatiquement des mélodies MIDI
depuis des sites comme MuseScore pour les utiliser dans la simulation.
"""

import os
import io
import requests
import random
import time
import mido
import tempfile
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus

class MidiDownloader:
    """Télécharge et convertit des mélodies MIDI depuis diverses sources en ligne"""
    
    # Cache des mélodies téléchargées
    MIDI_CACHE_DIR = "midi_cache"
    
    # Liste des sites supportés pour le téléchargement
    SUPPORTED_SITES = ["musescore", "freemidi", "bitmidi"]
    
    def __init__(self):
        """Initialise le téléchargeur de MIDI"""
        # Créer le répertoire de cache si nécessaire
        if not os.path.exists(self.MIDI_CACHE_DIR):
            os.makedirs(self.MIDI_CACHE_DIR)
        
        # Dictionnaire pour stocker les mélodies convertie (titre -> séquence de notes)
        self.melodies = {}
        
        # Catalogue des mélodies disponibles
        self.catalog_file = os.path.join(self.MIDI_CACHE_DIR, "catalog.json")
        self.load_catalog()
        
        print(f"Téléchargeur MIDI initialisé. Dossier de cache: {self.MIDI_CACHE_DIR}")
        print(f"{len(self.catalog)} mélodies en cache")
    
    def load_catalog(self):
        """Charge le catalogue des mélodies disponibles"""
        if os.path.exists(self.catalog_file):
            try:
                with open(self.catalog_file, 'r') as f:
                    self.catalog = json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement du catalogue: {e}")
                self.catalog = {}
        else:
            self.catalog = {}
            
        # Mettre à jour le catalogue avec les fichiers existants
        self._scan_cache_folder()
    
    def save_catalog(self):
        """Sauvegarde le catalogue des mélodies disponibles"""
        try:
            with open(self.catalog_file, 'w') as f:
                json.dump(self.catalog, f, indent=2)
            print(f"Catalogue sauvegardé: {len(self.catalog)} mélodies")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du catalogue: {e}")
    
    def _scan_cache_folder(self):
        """Scanne le dossier de cache pour trouver les fichiers MIDI existants"""
        for filename in os.listdir(self.MIDI_CACHE_DIR):
            if filename.endswith('.mid') or filename.endswith('.midi'):
                # Extraire le titre de la mélodie du nom de fichier
                title = os.path.splitext(filename)[0]
                
                # Ajouter au catalogue si pas déjà présent
                if title not in self.catalog:
                    midi_path = os.path.join(self.MIDI_CACHE_DIR, filename)
                    # Extraire des informations de base
                    try:
                        midi_data = mido.MidiFile(midi_path)
                        self.catalog[title] = {
                            "filename": filename,
                            "path": midi_path,
                            "tracks": len(midi_data.tracks),
                            "type": midi_data.type,
                            "ticks_per_beat": midi_data.ticks_per_beat,
                            "source": "local",
                            "processed": False
                        }
                    except Exception as e:
                        print(f"Erreur lors de l'analyse du fichier MIDI {filename}: {e}")
    
    def search_musescore(self, query, limit=5):
        """
        Recherche des partitions sur MuseScore.
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats
            
        Returns:
            Liste de dictionnaires contenant les informations des partitions
        """
        print(f"Recherche sur MuseScore: {query}")
        
        # Construire l'URL de recherche
        search_url = f"https://musescore.com/sheetmusic?text={quote_plus(query)}"
        
        try:
            # Obtenir la page de résultats
            response = requests.get(search_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()
            
            # Analyser la page HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraire les résultats (cette partie peut nécessiter des ajustements en fonction de la structure HTML de MuseScore)
            results = []
            
            # Trouver les éléments de partition
            score_elements = soup.select('.OAIWc')
            
            for element in score_elements[:limit]:
                try:
                    # Extraire les informations
                    title_elem = element.select_one('.score-card__title')
                    title = title_elem.text.strip() if title_elem else "Titre inconnu"
                    
                    # Extraire l'URL
                    url_elem = element.select_one('a')
                    url = url_elem['href'] if url_elem and 'href' in url_elem.attrs else None
                    
                    if url and not url.startswith('http'):
                        url = 'https://musescore.com' + url
                    
                    # Extraire l'auteur
                    author_elem = element.select_one('.score-card__author')
                    author = author_elem.text.strip() if author_elem else "Auteur inconnu"
                    
                    # Ajouter aux résultats
                    results.append({
                        'title': title,
                        'url': url,
                        'author': author,
                        'source': 'musescore'
                    })
                except Exception as e:
                    print(f"Erreur lors de l'extraction d'un résultat: {e}")
            
            print(f"Résultats trouvés: {len(results)}")
            return results
            
        except Exception as e:
            print(f"Erreur lors de la recherche sur MuseScore: {e}")
            return []
    
    def search_freemidi(self, query, limit=5):
        """
        Recherche des fichiers MIDI sur FreeMIDI.org
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats
            
        Returns:
            Liste de dictionnaires contenant les informations des fichiers MIDI
        """
        print(f"Recherche sur FreeMIDI: {query}")
        
        # Construire l'URL de recherche
        search_url = f"https://freemidi.org/search?q={quote_plus(query)}"
        
        try:
            # Obtenir la page de résultats
            response = requests.get(search_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()
            
            # Analyser la page HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraire les résultats
            results = []
            
            # Trouver les éléments de résultat
            result_elements = soup.select('.search-results .artist-result')
            
            for element in result_elements[:limit]:
                try:
                    # Extraire les informations
                    title_elem = element.select_one('.artist-name a')
                    title = title_elem.text.strip() if title_elem else "Titre inconnu"
                    
                    # Extraire l'URL
                    url = title_elem['href'] if title_elem and 'href' in title_elem.attrs else None
                    
                    if url and not url.startswith('http'):
                        url = 'https://freemidi.org' + url
                    
                    # Extraire l'ID du fichier MIDI
                    midi_id = None
                    if url:
                        match = re.search(r'download(\d+)', url)
                        if match:
                            midi_id = match.group(1)
                    
                    # Ajouter aux résultats
                    results.append({
                        'title': title,
                        'url': url,
                        'midi_id': midi_id,
                        'source': 'freemidi'
                    })
                except Exception as e:
                    print(f"Erreur lors de l'extraction d'un résultat: {e}")
            
            print(f"Résultats trouvés: {len(results)}")
            return results
            
        except Exception as e:
            print(f"Erreur lors de la recherche sur FreeMIDI: {e}")
            return []
    
    def search_bitmidi(self, query, limit=5):
        """
        Recherche des fichiers MIDI sur BitMIDI
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats
            
        Returns:
            Liste de dictionnaires contenant les informations des fichiers MIDI
        """
        print(f"Recherche sur BitMIDI: {query}")
        
        # Construire l'URL de recherche
        search_url = f"https://bitmidi.com/search?q={quote_plus(query)}"
        
        try:
            # Obtenir la page de résultats
            response = requests.get(search_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()
            
            # Analyser la page HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraire les résultats
            results = []
            
            # Trouver les éléments de résultat
            result_elements = soup.select('.midi-file')
            
            for element in result_elements[:limit]:
                try:
                    # Extraire les informations
                    title_elem = element.select_one('h2.midi-file-title a')
                    title = title_elem.text.strip() if title_elem else "Titre inconnu"
                    
                    # Extraire l'URL
                    url = title_elem['href'] if title_elem and 'href' in title_elem.attrs else None
                    
                    if url and not url.startswith('http'):
                        url = 'https://bitmidi.com' + url
                    
                    # Extraire le lien de téléchargement direct
                    download_elem = element.select_one('a.midi-file-download')
                    download_url = download_elem['href'] if download_elem and 'href' in download_elem.attrs else None
                    
                    if download_url and not download_url.startswith('http'):
                        download_url = 'https://bitmidi.com' + download_url
                    
                    # Ajouter aux résultats
                    results.append({
                        'title': title,
                        'url': url,
                        'download_url': download_url,
                        'source': 'bitmidi'
                    })
                except Exception as e:
                    print(f"Erreur lors de l'extraction d'un résultat: {e}")
            
            print(f"Résultats trouvés: {len(results)}")
            return results
            
        except Exception as e:
            print(f"Erreur lors de la recherche sur BitMIDI: {e}")
            return []
    
    def search_melody(self, query, sites=None, limit=5):
        """
        Recherche une mélodie sur différents sites
        
        Args:
            query: Terme de recherche
            sites: Liste des sites à utiliser (None pour tous)
            limit: Nombre maximum de résultats par site
            
        Returns:
            Liste combinée de résultats de tous les sites
        """
        if sites is None:
            sites = self.SUPPORTED_SITES
        
        results = []
        
        # Parcourir chaque site
        for site in sites:
            if site.lower() == "musescore":
                site_results = self.search_musescore(query, limit)
            elif site.lower() == "freemidi":
                site_results = self.search_freemidi(query, limit)
            elif site.lower() == "bitmidi":
                site_results = self.search_bitmidi(query, limit)
            else:
                print(f"Site non supporté: {site}")
                continue
            
            # Ajouter les résultats du site
            results.extend(site_results)
        
        return results
    
    def download_midi(self, result_info):
        """
        Télécharge un fichier MIDI à partir des informations de résultat
        
        Args:
            result_info: Dictionnaire contenant les informations du résultat
            
        Returns:
            Le chemin du fichier MIDI téléchargé, ou None en cas d'erreur
        """
        source = result_info.get('source', '').lower()
        title = result_info.get('title', 'unknown')
        
        # Nettoyer le titre pour en faire un nom de fichier valide
        clean_title = re.sub(r'[^\w\s-]', '', title)
        clean_title = re.sub(r'[\s-]+', '_', clean_title)
        
        # Créer le chemin du fichier
        midi_path = os.path.join(self.MIDI_CACHE_DIR, f"{clean_title}.mid")
        
        # Vérifier si le fichier existe déjà
        if os.path.exists(midi_path):
            print(f"Le fichier MIDI existe déjà: {midi_path}")
            return midi_path
        
        print(f"Téléchargement du fichier MIDI depuis {source}: {title}")
        
        try:
            # Télécharger selon la source
            if source == "musescore":
                return self._download_from_musescore(result_info, midi_path)
            elif source == "freemidi":
                return self._download_from_freemidi(result_info, midi_path)
            elif source == "bitmidi":
                return self._download_from_bitmidi(result_info, midi_path)
            else:
                print(f"Source non supportée: {source}")
                return None
        except Exception as e:
            print(f"Erreur lors du téléchargement du fichier MIDI: {e}")
            return None
    
    def _download_from_musescore(self, result_info, midi_path):
        """Télécharge un fichier MIDI depuis MuseScore"""
        url = result_info.get('url')
        if not url:
            print("URL manquante pour le téléchargement depuis MuseScore")
            return None
        
        try:
            # Obtenir la page de la partition
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()
            
            # Analyser la page HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher le lien de téléchargement MIDI
            download_link = None
            # Le sélecteur exact dépend de la structure HTML de MuseScore
            download_elements = soup.select('a[href*=".mid"], a[href*=".midi"], a[href*="download"]')
            
            for elem in download_elements:
                href = elem.get('href', '')
                if '.mid' in href.lower() or '.midi' in href.lower():
                    download_link = href
                    break
            
            if not download_link:
                print("Lien de téléchargement MIDI non trouvé")
                return None
            
            # Construire l'URL complète si nécessaire
            if not download_link.startswith('http'):
                download_link = 'https://musescore.com' + download_link
            
            # Télécharger le fichier MIDI
            midi_response = requests.get(download_link, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            midi_response.raise_for_status()
            
            # Sauvegarder le fichier
            with open(midi_path, 'wb') as f:
                f.write(midi_response.content)
            
            print(f"Fichier MIDI téléchargé: {midi_path}")
            
            # Ajouter au catalogue
            title = result_info.get('title', os.path.basename(midi_path))
            self.catalog[title] = {
                "filename": os.path.basename(midi_path),
                "path": midi_path,
                "source": "musescore",
                "url": url,
                "processed": False
            }
            self.save_catalog()
            
            return midi_path
            
        except Exception as e:
            print(f"Erreur lors du téléchargement depuis MuseScore: {e}")
            return None
    
    def _download_from_freemidi(self, result_info, midi_path):
        """Télécharge un fichier MIDI depuis FreeMIDI"""
        url = result_info.get('url')
        midi_id = result_info.get('midi_id')
        
        if not url or not midi_id:
            print("URL ou ID MIDI manquant pour le téléchargement depuis FreeMIDI")
            return None
        
        try:
            # Construire l'URL de téléchargement
            download_url = f"https://freemidi.org/getter-{midi_id}"
            
            # Créer une session pour maintenir les cookies
            session = requests.Session()
            
            # Visiter d'abord la page de détails pour obtenir les cookies nécessaires
            session.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # Télécharger le fichier MIDI
            midi_response = session.get(download_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': url
            })
            
            # Vérifier le type de contenu
            if 'application/octet-stream' in midi_response.headers.get('Content-Type', ''):
                # Sauvegarder le fichier
                with open(midi_path, 'wb') as f:
                    f.write(midi_response.content)
                
                print(f"Fichier MIDI téléchargé: {midi_path}")
                
                # Ajouter au catalogue
                title = result_info.get('title', os.path.basename(midi_path))
                self.catalog[title] = {
                    "filename": os.path.basename(midi_path),
                    "path": midi_path,
                    "source": "freemidi",
                    "url": url,
                    "processed": False
                }
                self.save_catalog()
                
                return midi_path
            else:
                print("Le contenu téléchargé n'est pas un fichier MIDI valide")
                return None
            
        except Exception as e:
            print(f"Erreur lors du téléchargement depuis FreeMIDI: {e}")
            return None
    
    def _download_from_bitmidi(self, result_info, midi_path):
        """Télécharge un fichier MIDI depuis BitMIDI"""
        download_url = result_info.get('download_url')
        
        if not download_url:
            print("URL de téléchargement manquante pour BitMIDI")
            return None
        
        try:
            # Télécharger le fichier MIDI
            midi_response = requests.get(download_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            midi_response.raise_for_status()
            
            # Sauvegarder le fichier
            with open(midi_path, 'wb') as f:
                f.write(midi_response.content)
            
            print(f"Fichier MIDI téléchargé: {midi_path}")
            
            # Ajouter au catalogue
            title = result_info.get('title', os.path.basename(midi_path))
            self.catalog[title] = {
                "filename": os.path.basename(midi_path),
                "path": midi_path,
                "source": "bitmidi",
                "url": result_info.get('url', ''),
                "processed": False
            }
            self.save_catalog()
            
            return midi_path
            
        except Exception as e:
            print(f"Erreur lors du téléchargement depuis BitMIDI: {e}")
            return None
    
    def convert_midi_to_notes(self, midi_path):
        """
        Convertit un fichier MIDI en séquence de notes
        
        Args:
            midi_path: Chemin du fichier MIDI
            
        Returns:
            Liste d'indices de notes
        """
        if not os.path.exists(midi_path):
            print(f"Fichier MIDI introuvable: {midi_path}")
            return None
        
        try:
            # Charger le fichier MIDI
            midi_data = mido.MidiFile(midi_path)
            
            # Trouver la piste mélodique principale
            melody_track = None
            max_notes = 0
            
            for i, track in enumerate(midi_data.tracks):
                note_count = sum(1 for msg in track if msg.type == 'note_on')
                if note_count > max_notes:
                    max_notes = note_count
                    melody_track = i
            
            if melody_track is None:
                print("Aucune piste mélodique trouvée dans le fichier MIDI")
                return None
            
            # Extraire les notes de la piste mélodique
            notes = []
            
            for msg in midi_data.tracks[melody_track]:
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Convertir la note MIDI en indice de la gamme (Do, Ré, Mi, etc.)
                    # Note MIDI 60 = Do central (C4)
                    note_idx = (msg.note - 60) % 7  # Ramener à l'octave de base (0-6)
                    notes.append(note_idx)
            
            # Limiter le nombre de notes (prendre les 20 premières)
            if len(notes) > 20:
                notes = notes[:20]
            
            print(f"Notes extraites: {len(notes)}")
            return notes
            
        except Exception as e:
            print(f"Erreur lors de la conversion du fichier MIDI: {e}")
            return None
    
    def upload_local_midi(self, file_path):
        """
        Importe un fichier MIDI local dans le système
        
        Args:
            file_path: Chemin du fichier MIDI local
            
        Returns:
            Le chemin du fichier importé dans le cache
        """
        if not os.path.exists(file_path):
            print(f"Fichier MIDI local introuvable: {file_path}")
            return None
        
        try:
            # Extraire le titre du nom de fichier
            filename = os.path.basename(file_path)
            title = os.path.splitext(filename)[0]
            
            # Nettoyer le titre pour en faire un nom de fichier valide
            clean_title = re.sub(r'[^\w\s-]', '', title)
            clean_title = re.sub(r'[\s-]+', '_', clean_title)
            
            # Créer le chemin de destination
            dest_path = os.path.join(self.MIDI_CACHE_DIR, f"{clean_title}.mid")
            
            # Copier le fichier
            import shutil
            shutil.copy2(file_path, dest_path)
            
            print(f"Fichier MIDI importé: {dest_path}")
            
            # Ajouter au catalogue
            self.catalog[title] = {
                "filename": os.path.basename(dest_path),
                "path": dest_path,
                "source": "local",
                "processed": False
            }
            self.save_catalog()
            
            return dest_path
            
        except Exception as e:
            print(f"Erreur lors de l'importation du fichier MIDI local: {e}")
            return None
    
    def process_all_midi_files(self):
        """
        Traite tous les fichiers MIDI du cache pour extraire les séquences de notes
        
        Returns:
            Dictionnaire des mélodies (titre -> séquence de notes)
        """
        # Parcourir tous les fichiers MIDI du catalogue
        for title, info in self.catalog.items():
            # Vérifier si le fichier est déjà traité
            if info.get('processed', False) and 'notes' in info:
                self.melodies[title] = info['notes']
                continue
            
            # Récupérer le chemin du fichier
            midi_path = info.get('path')
            if not midi_path or not os.path.exists(midi_path):
                print(f"Fichier MIDI introuvable pour {title}: {midi_path}")
                continue
            
            # Convertir le fichier MIDI en séquence de notes
            notes = self.convert_midi_to_notes(midi_path)
            if notes:
                # Stocker les notes dans le catalogue
                info['notes'] = notes
                info['processed'] = True
                
                # Stocker également dans le dictionnaire des mélodies
                self.melodies[title] = notes
        
        # Sauvegarder le catalogue mis à jour
        self.save_catalog()
        
        return self.melodies
    
    def list_available_melodies(self):
        """Affiche la liste des mélodies disponibles"""
        melodies = list(self.catalog.keys())
        
        print("\nMélodies disponibles:")
        print("-" * 50)
        
        for i, title in enumerate(melodies):
            info = self.catalog[title]
            source = info.get('source', 'inconnu')
            print(f"{i+1}. {title} (Source: {source})")
        
        print("-" * 50)
        return melodies
    
    def choose_melody(self):
        """
        Permet à l'utilisateur de choisir une mélodie
        
        Returns:
            Tuple (titre de la mélodie, séquence de notes)
        """
        melodies = self.list_available_melodies()
        
        while True:
            try:
                choice = input("\nChoisissez une mélodie par numéro, 'r' pour aléatoire, ou 's' pour rechercher: ")
                
                if choice.lower() == 'r':
                    # Choix aléatoire
                    if not melodies:
                        print("Aucune mélodie disponible")
                        return None, None
                    
                    title = random.choice(melodies)
                    notes = self.get_notes_for_melody(title)
                    return title, notes
                
                elif choice.lower() == 's':
                    # Recherche d'une nouvelle mélodie
                    query = input("Entrez un terme de recherche: ")
                    results = self.search_melody(query)
                    
                    if not results:
                        print("Aucun résultat trouvé")
                        continue
                    
                    # Afficher les résultats
                    print("\nRésultats de recherche:")
                    print("-" * 50)
                    
                    for i, result in enumerate(results):
                        title = result.get('title', 'Titre inconnu')
                        source = result.get('source', 'inconnu')
                        print(f"{i+1}. {title} (Source: {source})")
                    
                    print("-" * 50)
                    
                    # Choisir un résultat
                    result_choice = input("\nChoisissez un résultat par numéro, ou 'c' pour annuler: ")
                    
                    if result_choice.lower() == 'c':
                        continue
                    
                    try:
                        result_idx = int(result_choice) - 1
                        if 0 <= result_idx < len(results):
                            selected_result = results[result_idx]
                            
                            # Télécharger le fichier MIDI
                            midi_path = self.download_midi(selected_result)
                            
                            if midi_path:
                                # Convertir en séquence de notes
                                title = selected_result.get('title', 'Titre inconnu')
                                notes = self.convert_midi_to_notes(midi_path)
                                
                                if notes:
                                    # Mettre à jour le catalogue
                                    self.catalog[title]['notes'] = notes
                                    self.catalog[title]['processed'] = True
                                    self.save_catalog()
                                    
                                    return title, notes
                            
                            print("Impossible de traiter la mélodie sélectionnée")
                    except ValueError:
                        print("Veuillez entrer un nombre valide")
                
                else:
                    # Choix par numéro
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(melodies):
                            title = melodies[idx]
                            notes = self.get_notes_for_melody(title)
                            return title, notes
                        else:
                            print(f"Veuillez entrer un nombre entre 1 et {len(melodies)}")
                    except ValueError:
                        print("Veuillez entrer un nombre valide")
            except Exception as e:
                print(f"Erreur lors du choix de la mélodie: {e}")
    
    def get_notes_for_melody(self, title):
        """
        Récupère la séquence de notes pour une mélodie donnée
        
        Args:
            title: Titre de la mélodie
            
        Returns:
            Séquence de notes
        """
        # Vérifier si la mélodie est dans le catalogue
        if title not in self.catalog:
            print(f"Mélodie inconnue: {title}")
            return None
        
        # Vérifier si les notes sont déjà extraites
        if 'notes' in self.catalog[title]:
            return self.catalog[title]['notes']
        
        # Sinon, traiter le fichier MIDI
        midi_path = self.catalog[title].get('path')
        if not midi_path or not os.path.exists(midi_path):
            print(f"Fichier MIDI introuvable pour {title}: {midi_path}")
            return None
        
        # Convertir le fichier MIDI en séquence de notes
        notes = self.convert_midi_to_notes(midi_path)
        if notes:
            # Mettre à jour le catalogue
            self.catalog[title]['notes'] = notes
            self.catalog[title]['processed'] = True
            self.save_catalog()
            
            return notes
        
        return None


# Fonction pour intégrer le système MIDI dans la simulation
def integrate_midi_downloader(simulation, melody_player):
    """
    Intègre le système de téléchargement MIDI dans la simulation et le lecteur de mélodies.
    
    Args:
        simulation: L'instance de la classe Simulation
        melody_player: L'instance de la classe MelodyPlayer
        
    Returns:
        Le téléchargeur MIDI intégré
    """
    # Créer le téléchargeur MIDI
    midi_downloader = MidiDownloader()
    
    # Associer le téléchargeur MIDI à la simulation
    simulation.midi_downloader = midi_downloader
    
    # Traiter tous les fichiers MIDI existants
    melodies = midi_downloader.process_all_midi_files()
    
    # Ajouter les mélodies au lecteur de mélodies
    for title, notes in melodies.items():
        melody_player.POPULAR_MELODIES[title] = notes
    
    print(f"Téléchargeur MIDI intégré avec succès. {len(melodies)} mélodies disponibles.")
    return midi_downloader


# Exemple d'utilisation
if __name__ == "__main__":
    downloader = MidiDownloader()
    
    # Afficher les mélodies déjà disponibles
    downloader.list_available_melodies()
    
    while True:
        print("\nOptions:")
        print("1. Rechercher une mélodie")
        print("2. Importer un fichier MIDI local")
        print("3. Choisir une mélodie existante")
        print("4. Quitter")
        
        choice = input("\nChoisissez une option (1-4): ")
        
        if choice == "1":
            query = input("Entrez un terme de recherche: ")
            results = downloader.search_melody(query)
            
            if not results:
                print("Aucun résultat trouvé")
                continue
            
            # Afficher les résultats
            print("\nRésultats de recherche:")
            print("-" * 50)
            
            for i, result in enumerate(results):
                title = result.get('title', 'Titre inconnu')
                source = result.get('source', 'inconnu')
                print(f"{i+1}. {title} (Source: {source})")
            
            print("-" * 50)
            
            # Choisir un résultat à télécharger
            result_choice = input("\nChoisissez un résultat à télécharger (numéro) ou 'c' pour annuler: ")
            
            if result_choice.lower() == 'c':
                continue
            
            try:
                result_idx = int(result_choice) - 1
                if 0 <= result_idx < len(results):
                    selected_result = results[result_idx]
                    
                    # Télécharger le fichier MIDI
                    midi_path = downloader.download_midi(selected_result)
                    
                    if midi_path:
                        # Convertir en séquence de notes
                        notes = downloader.convert_midi_to_notes(midi_path)
                        print(f"Notes extraites: {notes}")
            except ValueError:
                print("Veuillez entrer un nombre valide")
        
        elif choice == "2":
            file_path = input("Entrez le chemin du fichier MIDI local: ")
            midi_path = downloader.upload_local_midi(file_path)
            
            if midi_path:
                # Convertir en séquence de notes
                notes = downloader.convert_midi_to_notes(midi_path)
                print(f"Notes extraites: {notes}")
        
        elif choice == "3":
            title, notes = downloader.choose_melody()
            
            if title and notes:
                print(f"Mélodie choisie: {title}")
                print(f"Notes: {notes}")
        
        elif choice == "4":
            print("Au revoir!")
            break
        
        else:
            print("Option invalide")
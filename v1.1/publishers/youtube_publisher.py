"""
Module de publication automatique pour YouTube utilisant Selenium
----------------------------------------------------------------
Ce module permet de:
1. Se connecter à un compte YouTube
2. Publier automatiquement des vidéos
3. Gérer les titres, descriptions et mots-clés

Requiert:
pip install selenium webdriver-manager
"""

import os
import time
import pickle
import logging
import traceback
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from publishers.base_publisher import BasePublisher

logger = logging.getLogger("TikSimPro")

class YouTubePublisher(BasePublisher):
    """
    Gestionnaire de publication YouTube utilisant Selenium
    """
    
    def __init__(self, credentials_file=None, auto_close=True):
        """
        Initialise le gestionnaire de publication YouTube
        
        Args:
            credentials_file: Fichier pour sauvegarder les cookies (optionnel)
            auto_close: Fermer automatiquement le navigateur après utilisation
        """
        self.cookies_file = credentials_file or "youtube_cookies.pkl"
        self.is_authenticated = False
        self.driver = None
        self.auto_close = auto_close
        
        # Ne pas initialiser le navigateur tout de suite
        # L'initialisation se fera à la demande
    
    def setup_browser(self):
        """Configure le navigateur Chrome avec Selenium"""
        try:
            # Vérifier si le driver existe déjà
            if self.driver is not None:
                # Essayer de faire une opération simple pour vérifier si le driver est encore valide
                try:
                    # Si on peut récupérer l'URL, le driver est toujours valide
                    self.driver.current_url
                    logger.info("Réutilisation du driver existant")
                    return True
                except:
                    # Si une erreur se produit, le driver n'est plus valide, il faut le recréer
                    logger.info("Driver existant non valide, création d'un nouveau")
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
            
            chrome_options = Options()
            
            # Options de base
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Agent utilisateur normal
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
            
            # Désactiver les notifications
            chrome_options.add_argument("--disable-notifications")
            
            # Options pour éviter la détection comme bot
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            logger.info("Initialisation du webdriver Chrome...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Définir une taille d'écran raisonnable
            self.driver.set_window_size(1280, 800)
            
            # Modifier les propriétés webdriver pour contourner la détection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Navigateur configuré pour YouTube")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du navigateur: {e}")
            logger.error(traceback.format_exc())
            self.driver = None
            return False
    
    def save_cookies(self):
        """Sauvegarde les cookies pour les futures sessions"""
        if self.driver:
            try:
                cookies = self.driver.get_cookies()
                with open(self.cookies_file, 'wb') as file:
                    pickle.dump(cookies, file)
                logger.info(f"Cookies YouTube sauvegardés dans {self.cookies_file}")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde des cookies: {e}")
    
    def load_cookies(self):
        """Charge les cookies d'une session précédente si disponibles"""
        # Vérifier que le driver est initialisé
        if not self.driver:
            if not self.setup_browser():
                return False
        
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, 'rb') as file:
                    cookies = pickle.load(file)
                
                # Ouvrir d'abord YouTube pour pouvoir ajouter les cookies
                self.driver.get("https://www.youtube.com")
                time.sleep(2)
                
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'ajout du cookie: {e}")
                
                # Rafraîchir pour appliquer les cookies
                self.driver.refresh()
                time.sleep(3)
                
                # Vérifier si connecté
                if self.is_logged_in():
                    logger.info("Session YouTube restaurée avec succès via les cookies")
                    self.is_authenticated = True
                    return True
                else:
                    logger.info("Les cookies sauvegardés ne sont plus valides pour YouTube")
                    return False
                    
            except Exception as e:
                logger.error(f"Erreur lors du chargement des cookies: {e}")
                return False
        else:
            logger.info("Aucun cookie YouTube sauvegardé trouvé")
            return False
    
    def is_logged_in(self):
        """Vérifie si l'utilisateur est connecté à YouTube"""
        # Vérifier que le driver est initialisé
        if not self.driver:
            return False
            
        try:
            # Méthode simplifiée pour éviter les faux positifs
            
            # Vérifier si le bouton de connexion est présent (si visible, alors non connecté)
            login_buttons = self.driver.find_elements(By.XPATH, 
                "//a[contains(@href, 'accounts.google.com/ServiceLogin')]")
            
            if login_buttons and any(btn.is_displayed() for btn in login_buttons):
                return False
            
            # Vérifier la présence de l'avatar (méthode la plus fiable)
            avatar = self.driver.find_elements(By.CSS_SELECTOR, "#avatar-btn")
            if avatar and avatar[0].is_displayed():
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de connexion YouTube: {e}")
            return False
    
    def authenticate(self):
        """
        Se connecte à YouTube, soit automatiquement via cookies, soit manuellement
        
        Returns:
            bool: True si l'authentification a réussi, False sinon
        """
        # Initialiser le navigateur si nécessaire
        if not self.driver:
            logger.info("Initialisation du navigateur pour l'authentification...")
            if not self.setup_browser():
                logger.error("Impossible d'initialiser le navigateur")
                return False
        
        # Vérifier d'abord si nous pouvons nous connecter avec des cookies existants
        if self.load_cookies():
            return True
        
        # Si pas de cookies ou cookies invalides, procéder à la connexion manuelle
        try:
            logger.info("Ouverture de la page de connexion YouTube...")
            self.driver.get("https://www.youtube.com")
            time.sleep(3)
            
            # Vérifier si nous sommes déjà connectés
            if self.is_logged_in():
                logger.info("Déjà connecté à YouTube")
                self.is_authenticated = True
                self.save_cookies()
                return True
            
            # Cliquer sur le bouton de connexion
            try:
                login_buttons = self.driver.find_elements(By.XPATH, 
                    "//a[contains(@href, 'accounts.google.com/ServiceLogin')]")
                
                if login_buttons and login_buttons[0].is_displayed():
                    login_buttons[0].click()
                    time.sleep(3)
            except Exception as e:
                logger.warning(f"Impossible de cliquer sur le bouton de connexion: {e}")
                # Essayer d'accéder directement à la page de connexion
                self.driver.get("https://accounts.google.com/ServiceLogin?service=youtube")
                time.sleep(3)
            
            # Attendre que l'utilisateur se connecte manuellement
            print("\n" + "="*80)
            print("VEUILLEZ VOUS CONNECTER MANUELLEMENT À YOUTUBE DANS LA FENÊTRE DU NAVIGATEUR")
            print("Le programme va vérifier régulièrement si vous êtes connecté")
            print("="*80 + "\n")
            
            # Vérifier régulièrement si l'utilisateur s'est connecté
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            check_interval = 5  # vérifier toutes les 5 secondes
            
            while time.time() - start_time < max_wait_time:
                current_url = self.driver.current_url
                
                # Si nous sommes sur YouTube, vérifier si connecté
                if "youtube.com" in current_url:
                    if self.is_logged_in():
                        logger.info("Connexion à YouTube réussie!")
                        self.is_authenticated = True
                        self.save_cookies()
                        return True
                
                time.sleep(check_interval)
                print(f"Vérification de connexion YouTube... URL: {current_url}")
            
            # Si le temps d'attente est dépassé
            print("Temps d'attente dépassé. Confirmez-vous être connecté? (o/n)")
            response = input().strip().lower()
            if response in ['o', 'oui', 'y', 'yes']:
                self.is_authenticated = True
                self.save_cookies()
                return True
            
            return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification YouTube: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def navigate_to_upload(self):
        """
        Navigue vers la page de téléchargement YouTube
        
        Returns:
            bool: True si la navigation a réussi, False sinon
        """
        # Vérifier que le driver est initialisé
        if not self.driver:
            if not self.setup_browser():
                return False
                
        try:
            # Aller d'abord à la page principale de YouTube
            self.driver.get("https://www.youtube.com")
            time.sleep(3)
            
            # Méthode directe : accès direct à l'URL d'upload
            logger.info("Accès direct à la page d'upload YouTube...")
            self.driver.get("https://www.youtube.com/upload")
            time.sleep(5)
            
            # Vérifier qu'on est bien sur la page d'upload
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
                logger.info("Navigation directe vers la page d'upload YouTube réussie")
                return True
            except TimeoutException:
                # Si la page d'upload n'est pas chargée, essayer la méthode par l'interface
                logger.warning("Navigation directe échouée, tentative via l'interface...")
                
                # Revenir à YouTube
                self.driver.get("https://www.youtube.com")
                time.sleep(3)
                
                # Essayer de cliquer sur le bouton de création
                try:
                    create_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "create-icon"))
                    )
                    create_button.click()
                    time.sleep(1)
                    
                    # Chercher l'option d'upload
                    upload_option = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//yt-formatted-string[contains(text(), 'Upload') or contains(text(), 'Importer')]"))
                    )
                    upload_option.click()
                    time.sleep(3)
                    
                    # Vérifier qu'on est sur la page d'upload
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                    )
                    logger.info("Navigation via l'interface vers la page d'upload réussie")
                    return True
                    
                except Exception as e:
                    logger.error(f"Erreur navigation via l'interface: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erreur lors de la navigation vers la page d'upload: {e}")
            return False
    
    def upload_video(self, video_path, caption="", hashtags=None, title=None, privacy="public", is_short=True):
        """
        Publie une vidéo sur YouTube, avec option pour les Shorts
        
        Args:
            video_path: Chemin vers le fichier vidéo
            caption: Description de la vidéo
            hashtags: Liste de hashtags (sans #)
            title: Titre de la vidéo (optionnel)
            privacy: 'public', 'unlisted' ou 'private'
            is_short: Si True, publie en tant que Short YouTube
        """
        # Vérifier l'authentification
        if not self.is_authenticated:
            logger.info("Authentification YouTube requise")
            if not self.authenticate():
                return False
        
        # Vérifier que le fichier vidéo existe
        if not os.path.exists(video_path):
            logger.error(f"Le fichier vidéo {video_path} n'existe pas")
            return False
        
        # Formater le titre
        if not title:
            file_name = os.path.basename(video_path)
            title = os.path.splitext(file_name)[0]
            title = title.replace("_", " ").title()
        
        # Ajouter #Shorts si c'est un Short
        if is_short:
            hashtags = hashtags or []
            if "shorts" not in [tag.lower() for tag in hashtags]:
                hashtags.insert(0, "Shorts")
        
        # Formater les hashtags et la description
        hashtag_text = " ".join([f"#{tag}" for tag in hashtags]) if hashtags else ""
        description = caption
        if hashtag_text:
            description += f"\n\n{hashtag_text}"
        
        try:
            # Naviguer vers la page d'upload
            if not self.navigate_to_upload():
                logger.error("Échec de navigation vers la page d'upload YouTube")
                return False
            
            logger.info(f"Publication de la vidéo sur YouTube: {video_path}")
            
            # 1. Sélectionner le fichier
            try:
                file_input = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
                file_input.send_keys(os.path.abspath(video_path))
                logger.info("Fichier vidéo sélectionné avec succès")
                
                # Attendre que le chargement commence
                time.sleep(5)
                
                # Attendre que la page d'édition apparaisse
                WebDriverWait(self.driver, 60).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "ytcp-form-input-container"))
                )
                logger.info("Formulaire d'édition détecté")
                
                # Pause supplémentaire pour s'assurer que tout est chargé
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Erreur lors de la sélection du fichier: {e}")
                return False
            
            # 2. Entrer le titre avec JavaScript (au lieu de la méthode standard)
            try:
                # Attendre que l'élément de titre soit présent
                title_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#title-textarea #textbox"))
                )
                
                # Méthode 1: Simuler une frappe humaine
                title_field.click()  # S'assurer que le champ est sélectionné
                title_field.clear()  # Effacer tout texte existant
                # Ajouter la description principale
                title_field.send_keys(title)

                logger.info(f"Titre saisi: {title}")
                
            except Exception as e:
                logger.error(f"Erreur lors de la saisie du titre: {e}")
                
            # 3. Entrer la description 
            try:
                # Attendre que l'élément de description soit présent
                description_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#description-textarea #textbox"))
                )
                
                # Méthode 1: Simuler une frappe humaine
                description_field.click()  # S'assurer que le champ est sélectionné
                description_field.clear()  # Effacer tout texte existant
                # Ajouter la description principale
                description_field.send_keys(description)

                logger.info("Description saisie")
                
            except Exception as e:
                logger.error(f"Erreur lors de la saisie de la description: {e}")
            
            # 4. Marquer comme "Non destiné aux enfants"
            try:
                self.driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(1)
                
                # Attendre que le widget 'Made for Kids' soit présent
                not_mfk_radio = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MFK"))
                )
                not_mfk_radio.click()
                logger.info("Option 'Non destiné aux enfants' sélectionnée")
                
            except Exception as e:
                logger.error(f"Erreur lors du paramétrage 'Non destiné aux enfants': {e}")
            
            # 5. Cliquer sur les boutons "Suivant"
            try:
                # Faire défiler pour voir le bouton
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Cliquer sur "Suivant" pour aller aux options de visibilité
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#next-button"))
                )
                next_button.click()
                time.sleep(2)
                
                # Cliquer encore sur "Suivant" pour aller aux éléments de la vidéo (si nécessaire)
                try:
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#next-button"))
                    )
                    next_button.click()
                    time.sleep(2)
                except:
                    pass
                
                # Cliquer sur "Suivant" une dernière fois (si nécessaire)
                try:
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#next-button"))
                    )
                    next_button.click()
                    time.sleep(2)
                except:
                    pass
                
            except Exception as e:
                logger.error(f"Erreur lors de la navigation dans les étapes: {e}")
            
            # 6. Définir la visibilité (public, unlisted, private)
            try:
                visibility_option = None
                
                # Chercher l'option de visibilité par son nom
                visibility_options = {
                    "public": "PUBLIC",
                    "unlisted": "UNLISTED", 
                    "private": "PRIVATE"
                }
                
                option_name = visibility_options.get(privacy.lower(), "PUBLIC")
                
                # Attendre que les options de visibilité soient présentes
                visibility_option = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f'tp-yt-paper-radio-button[name="{option_name}"]'))
                )
                
                # Cliquer sur l'option de visibilité
                visibility_option.click()
                logger.info(f"Visibilité définie: {privacy}")
                
            except Exception as e:
                logger.error(f"Erreur lors de la définition de la visibilité: {e}")
            
            # 7. Publier la vidéo
            try:
                # Cliquer sur le bouton publier/terminé
                publish_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#done-button"))
                )
                publish_button.click()
                logger.info("Bouton de publication cliqué")
                
                # Attendre la confirmation (dialogue de traitement)
                try:
                    WebDriverWait(self.driver, 60).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "ytcp-uploads-still-processing-dialog"))
                    )
                    logger.info("Dialogue de traitement détecté, publication réussie")
                    return True
                except:
                    # Vérification alternative - redirection vers le studio
                    current_url = self.driver.current_url
                    if "studio.youtube.com" in current_url:
                        logger.info(f"Redirection vers YouTube Studio: {current_url}")
                        return True
                    else:
                        logger.warning(f"Pas de confirmation claire, URL actuelle: {current_url}")
                        # On considère quand même comme un succès
                        return True
                
            except Exception as e:
                logger.error(f"Erreur lors de la publication finale: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur YouTube: {e}")
            logger.error(traceback.format_exc())
            return False
        finally:
            # Fermer le navigateur si auto_close est activé
            if self.auto_close:
                self.close()
                
    def close(self):
        """Ferme le navigateur et nettoie les ressources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Navigateur YouTube fermé")
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture du navigateur: {e}")
            finally:
                self.driver = None
    
    def __del__(self):
        """Destructeur pour assurer que le navigateur est fermé"""
        if hasattr(self, 'auto_close') and self.auto_close:
            self.close()
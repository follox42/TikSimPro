# publishers/youtube_publisher.py
"""
Système de publication YouTube utilisant Selenium
"""

import os
import time
import pickle
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import random
from pathlib import Path

from core.interfaces import IContentPublisher

logger = logging.getLogger("TikSimPro")

class YouTubePublisher(IContentPublisher):
    """
    Publie du contenu sur YouTube en utilisant Selenium
    """
    
    def __init__(self, 
                credentials_file: Optional[str] = None, 
                auto_close: bool = True,
                headless: bool = False):
        """
        Initialise le système de publication YouTube
        
        Args:
            credentials_file: Fichier pour sauvegarder les cookies
            auto_close: Fermer automatiquement le navigateur après utilisation
            headless: Exécuter le navigateur en mode headless
        """
        self.cookies_file = credentials_file or "youtube_cookies.pkl"
        self.auto_close = auto_close
        self.headless = headless
        self.is_authenticated = False
        self.driver = None
        
        # Vérifier que Selenium est disponible
        self._check_selenium()
        
        logger.info("YouTubePublisher initialisé")
    
    def _check_selenium(self) -> bool:
        """
        Vérifie si Selenium est disponible
        
        Returns:
            True si Selenium est disponible, False sinon
        """
        try:
            import selenium
            from selenium import webdriver
            return True
        except ImportError:
            logger.error("Selenium non disponible, certaines fonctionnalités seront limitées")
            return False
    
    def _setup_browser(self) -> bool:
        """
        Configure le navigateur Chrome avec Selenium
        
        Returns:
            True si la configuration a réussi, False sinon
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
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
            
            # Mode headless si demandé
            if self.headless:
                chrome_options.add_argument("--headless")
            
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
            self.driver = None
            return False
    
    def _save_cookies(self) -> bool:
        """
        Sauvegarde les cookies pour les futures sessions
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        if not self.driver:
            return False
            
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as file:
                pickle.dump(cookies, file)
            logger.info(f"Cookies YouTube sauvegardés dans {self.cookies_file}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des cookies: {e}")
            return False
    
    def _load_cookies(self) -> bool:
        """
        Charge les cookies d'une session précédente si disponibles
        
        Returns:
            True si le chargement a réussi, False sinon
        """
        # Vérifier que le driver est initialisé
        if not self.driver:
            if not self._setup_browser():
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
                if self._is_logged_in():
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
    
    def _is_logged_in(self) -> bool:
        """
        Vérifie si l'utilisateur est connecté à YouTube
        
        Returns:
            True si connecté, False sinon
        """
        from selenium.webdriver.common.by import By
        
        # Vérifier que le driver est initialisé
        if not self.driver:
            return False
            
        try:
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
    
    def authenticate(self) -> bool:
        """
        Authentifie le système de publication
        
        Returns:
            True si l'authentification a réussi, False sinon
        """
        # Initialiser le navigateur si nécessaire
        if not self.driver:
            logger.info("Initialisation du navigateur pour l'authentification YouTube...")
            if not self._setup_browser():
                logger.error("Impossible d'initialiser le navigateur")
                return False
        
        # Vérifier d'abord si nous pouvons nous connecter avec des cookies existants
        if self._load_cookies():
            return True
        
        # Si pas de cookies ou cookies invalides, procéder à la connexion manuelle
        try:
            logger.info("Ouverture de la page YouTube...")
            self.driver.get("https://www.youtube.com")
            time.sleep(3)
            
            # Vérifier si nous sommes déjà connectés
            if self._is_logged_in():
                logger.info("Déjà connecté à YouTube")
                self.is_authenticated = True
                self._save_cookies()
                return True
            
            # Cliquer sur le bouton de connexion
            from selenium.webdriver.common.by import By
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
                    if self._is_logged_in():
                        logger.info("Connexion à YouTube réussie!")
                        self.is_authenticated = True
                        self._save_cookies()
                        return True
                
                time.sleep(check_interval)
                print(f"Vérification de connexion YouTube... URL: {current_url}")
            
            # Si le temps d'attente est dépassé
            print("Temps d'attente dépassé. Confirmez-vous être connecté? (o/n)")
            response = input().strip().lower()
            if response in ['o', 'oui', 'y', 'yes']:
                self.is_authenticated = True
                self._save_cookies()
                return True
            
            return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification YouTube: {e}")
            return False
    
    def publish(self, video_path: str, caption: str, hashtags: List[str], **kwargs) -> bool:
        """
        Publie une vidéo sur YouTube
        
        Args:
            video_path: Chemin de la vidéo à publier
            caption: Description de la vidéo
            hashtags: Liste de hashtags à utiliser
            **kwargs: Paramètres supplémentaires
                - title: Titre de la vidéo (par défaut: nom du fichier)
                - is_short: Publier comme un Short YouTube (True/False)
                - privacy: Niveau de confidentialité ('public', 'unlisted', 'private')
            
        Returns:
            True si la publication a réussi, False sinon
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        from selenium.webdriver.common.keys import Keys
        
        # Extraire les paramètres supplémentaires
        title = kwargs.get('title', None)
        is_short = kwargs.get('is_short', True)
        privacy = kwargs.get('privacy', 'public')
        
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
            if "shorts" not in [tag.lower() for tag in hashtags]:
                hashtags.insert(0, "Shorts")
        
        # Formater la description
        hashtag_text = " ".join([f"#{tag}" for tag in hashtags]) if hashtags else ""
        full_description = caption
        if hashtag_text:
            full_description += f"\n\n{hashtag_text}"
        
        try:
            # Naviguer vers la page d'upload
            logger.info("Navigation vers la page d'upload YouTube...")
            self.driver.get("https://www.youtube.com/upload")
            time.sleep(5)
            
            # Vérifier si nous sommes sur la page d'upload
            try:
                file_input = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
            except TimeoutException:
                logger.error("Page d'upload YouTube non chargée")
                return False
            
            # Télécharger la vidéo
            logger.info(f"Téléchargement de la vidéo: {video_path}")
            file_input.send_keys(os.path.abspath(video_path))
            
            # Attendre que la page d'édition apparaisse
            try:
                WebDriverWait(self.driver, 60).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "#title-textarea #textbox"))
                )
                logger.info("Formulaire d'édition détecté")
                time.sleep(3)
            except TimeoutException:
                logger.error("Formulaire d'édition non chargé")
                return False
            
            # Saisir le titre
            try:
                title_field = self.driver.find_element(By.CSS_SELECTOR, "#title-textarea #textbox")
                title_field.click()
                title_field.clear()
                title_field.send_keys(title)
                logger.info(f"Titre saisi: {title}")
            except Exception as e:
                logger.error(f"Erreur lors de la saisie du titre: {e}")
            
            # Saisir la description
            try:
                description_field = self.driver.find_element(By.CSS_SELECTOR, "#description-textarea #textbox")
                description_field.click()
                description_field.clear()
                description_field.send_keys(full_description)
                logger.info("Description saisie")
            except Exception as e:
                logger.error(f"Erreur lors de la saisie de la description: {e}")
            
            # Marquer comme "Non destiné aux enfants"
            try:
                self.driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(1)
                
                not_for_kids_radio = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MFK"))
                )
                not_for_kids_radio.click()
                logger.info("Option 'Non destiné aux enfants' sélectionnée")
            except Exception as e:
                logger.error(f"Erreur lors du paramétrage 'Non destiné aux enfants': {e}")
            
            # Navigation à travers les étapes
            try:
                # Défiler vers le bas pour voir le bouton
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Cliquer sur "Suivant" pour aller aux options de visibilité
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#next-button"))
                )
                next_button.click()
                time.sleep(2)
                
                # Cliquer sur "Suivant" pour les étapes suivantes si nécessaire
                for _ in range(2):
                    try:
                        next_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "#next-button"))
                        )
                        next_button.click()
                        time.sleep(2)
                    except:
                        break
                
            except Exception as e:
                logger.error(f"Erreur lors de la navigation dans les étapes: {e}")
            
            # Définir la visibilité
            try:
                visibility_options = {
                    "public": "PUBLIC",
                    "unlisted": "UNLISTED", 
                    "private": "PRIVATE"
                }
                
                option_name = visibility_options.get(privacy.lower(), "PUBLIC")
                
                visibility_option = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f'tp-yt-paper-radio-button[name="{option_name}"]'))
                )
                
                visibility_option.click()
                logger.info(f"Visibilité définie: {privacy}")
                
            except Exception as e:
                logger.error(f"Erreur lors de la définition de la visibilité: {e}")
            
            # Publier la vidéo
            try:
                publish_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#done-button"))
                )
                publish_button.click()
                logger.info("Bouton de publication cliqué")
                
                # Attendre la confirmation
                time.sleep(10)
                
                try:
                    # Vérifier si une boîte de dialogue de traitement est affichée
                    processing_dialog = self.driver.find_elements(By.CSS_SELECTOR, "ytcp-uploads-still-processing-dialog")
                    if processing_dialog and processing_dialog[0].is_displayed():
                        logger.info("Dialogue de traitement détecté, publication réussie")
                        return True
                except:
                    pass
                
                # Vérification alternative - redirection vers le studio
                current_url = self.driver.current_url
                if "studio.youtube.com" in current_url:
                    logger.info(f"Redirection vers YouTube Studio: {current_url}")
                    return True
                
                # En cas de doute, considérer comme un succès
                logger.info("Aucune erreur détectée, publication probablement réussie")
                return True
                
            except Exception as e:
                logger.error(f"Erreur lors de la publication finale: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur YouTube: {e}")
            import traceback
            traceback.print_exc()
            
            # Capturer une capture d'écran pour le diagnostic
            if self.driver:
                self.driver.save_screenshot("youtube_error.png")
                logger.info("Une capture d'écran a été enregistrée dans 'youtube_error.png'")
            
            return False
        finally:
            # Fermer le navigateur si demandé
            if self.auto_close and self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except:
                    pass
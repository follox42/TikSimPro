# publishers/instagram_publisher.py
"""
Système de publication Instagram utilisant Selenium
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

class InstagramPublisher(IContentPublisher):
    """
    Publie du contenu sur Instagram en utilisant Selenium
    """
    
    def __init__(self, 
                credentials_file: Optional[str] = None, 
                auto_close: bool = True,
                mobile_emulation: bool = True):
        """
        Initialise le système de publication Instagram
        
        Args:
            credentials_file: Fichier pour sauvegarder les cookies
            auto_close: Fermer automatiquement le navigateur après utilisation
            mobile_emulation: Activer l'émulation mobile (recommandé pour Instagram)
        """
        self.cookies_file = credentials_file or "instagram_cookies.pkl"
        self.auto_close = auto_close
        self.mobile_emulation = mobile_emulation
        self.is_authenticated = False
        self.driver = None
        
        # Vérifier que Selenium est disponible
        self._check_selenium()
        
        logger.info("InstagramPublisher initialisé")
    
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
            
            # Émulation mobile (recommandée pour Instagram)
            if self.mobile_emulation:
                mobile_emulation = {
                    "deviceName": "iPhone X"
                }
                chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
            
            # Désactiver les notifications
            chrome_options.add_argument("--disable-notifications")
            
            # Options pour éviter la détection comme bot
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            logger.info("Initialisation du webdriver Chrome...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Définir une taille d'écran raisonnable si pas d'émulation mobile
            if not self.mobile_emulation:
                self.driver.set_window_size(1280, 800)
            
            # Modifier les propriétés webdriver pour contourner la détection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Navigateur configuré pour Instagram")
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
            logger.info(f"Cookies Instagram sauvegardés dans {self.cookies_file}")
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
                
                # Ouvrir d'abord Instagram pour pouvoir ajouter les cookies
                self.driver.get("https://www.instagram.com")
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
                    logger.info("Session Instagram restaurée avec succès via les cookies")
                    self.is_authenticated = True
                    return True
                else:
                    logger.info("Les cookies sauvegardés ne sont plus valides pour Instagram")
                    return False
                    
            except Exception as e:
                logger.error(f"Erreur lors du chargement des cookies: {e}")
                return False
        else:
            logger.info("Aucun cookie Instagram sauvegardé trouvé")
            return False
    
    def _is_logged_in(self) -> bool:
        """
        Vérifie si l'utilisateur est connecté à Instagram
        
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
                "//button[contains(text(), 'Log in') or contains(text(), 'Log In') or contains(text(), 'Connexion')]")
            
            if login_buttons and any(btn.is_displayed() for btn in login_buttons):
                return False
            
            # Sur version mobile
            if self.mobile_emulation:
                # Vérifier les icônes de la barre inférieure (home, search, etc)
                nav_items = self.driver.find_elements(By.XPATH, 
                    "//div[@role='tablist']/div")
                if nav_items and len(nav_items) >= 3:
                    return True
            # Sur version desktop
            else:
                profile_links = self.driver.find_elements(By.XPATH, 
                    "//a[contains(@href, '/profile/') or contains(@href, '/_u/')]")
                if profile_links and any(link.is_displayed() for link in profile_links):
                    return True
            
            # Si nous sommes sur la page d'accueil, probablement connecté
            if "instagram.com/accounts/login" not in self.driver.current_url:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de connexion Instagram: {e}")
            return False
    
    def authenticate(self) -> bool:
        """
        Authentifie le système de publication
        
        Returns:
            True si l'authentification a réussi, False sinon
        """
        # Initialiser le navigateur si nécessaire
        if not self.driver:
            logger.info("Initialisation du navigateur pour l'authentification Instagram...")
            if not self._setup_browser():
                logger.error("Impossible d'initialiser le navigateur")
                return False
        
        # Vérifier d'abord si nous pouvons nous connecter avec des cookies existants
        if self._load_cookies():
            return True
        
        # Si pas de cookies ou cookies invalides, procéder à la connexion manuelle
        try:
            logger.info("Ouverture de la page Instagram...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)
            
            # Accepter les cookies si nécessaire
            from selenium.webdriver.common.by import By
            try:
                cookie_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Accept') or contains(text(), 'Accept All') or contains(text(), 'Accepter')]")
                
                if cookie_buttons:
                    for button in cookie_buttons:
                        if button.is_displayed():
                            button.click()
                            time.sleep(1)
                            break
            except:
                pass
            
            # Vérifier si nous sommes déjà connectés
            if self._is_logged_in():
                logger.info("Déjà connecté à Instagram")
                self.is_authenticated = True
                self._save_cookies()
                return True
            
            # Attendre que l'utilisateur se connecte manuellement
            print("\n" + "="*80)
            print("VEUILLEZ VOUS CONNECTER MANUELLEMENT À INSTAGRAM DANS LA FENÊTRE DU NAVIGATEUR")
            print("Le programme va vérifier régulièrement si vous êtes connecté")
            print("="*80 + "\n")
            
            # Vérifier régulièrement si l'utilisateur s'est connecté
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            check_interval = 5  # vérifier toutes les 5 secondes
            
            while time.time() - start_time < max_wait_time:
                if self._is_logged_in():
                    logger.info("Connexion à Instagram réussie!")
                    self.is_authenticated = True
                    self._save_cookies()
                    return True
                
                time.sleep(check_interval)
                print(f"Vérification de connexion Instagram... URL: {self.driver.current_url}")
            
            # Si le temps d'attente est dépassé
            print("Temps d'attente dépassé. Confirmez-vous être connecté? (o/n)")
            response = input().strip().lower()
            if response in ['o', 'oui', 'y', 'yes']:
                self.is_authenticated = True
                self._save_cookies()
                return True
            
            return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification Instagram: {e}")
            return False
    
    def _navigate_to_upload(self) -> bool:
        """
        Navigue vers la page de création/téléchargement
        
        Returns:
            True si la navigation a réussi, False sinon
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Vérifier que le driver est initialisé
        if not self.driver:
            if not self._setup_browser():
                return False
                
        try:
            # Aller à la page principale d'Instagram
            self.driver.get("https://www.instagram.com")
            time.sleep(3)
            
            # En fonction du mode d'affichage (mobile ou desktop)
            if self.mobile_emulation:
                # Version mobile - cliquer sur le bouton "+"
                try:
                    # Chercher le bouton "+" (création)
                    create_buttons = self.driver.find_elements(By.XPATH, 
                        "//div[@role='tablist']//a[contains(@href, '/create')] | //div[contains(@class, 'createKeyCommandWrapper')]//div[@role='button']")
                    
                    if not create_buttons:
                        # Autre méthode : chercher par la position dans la barre
                        buttons = self.driver.find_elements(By.XPATH, "//div[@role='tablist']/div")
                        if len(buttons) >= 3:  # Généralement le 3ème bouton
                            create_buttons = [buttons[2]]
                    
                    if create_buttons and create_buttons[0].is_displayed():
                        create_buttons[0].click()
                        logger.info("Bouton de création cliqué (mobile)")
                        time.sleep(2)
                        return True
                    else:
                        logger.error("Bouton de création non trouvé (mobile)")
                        return False
                        
                except Exception as e:
                    logger.error(f"Erreur lors de la recherche du bouton de création (mobile): {e}")
                    return False
            else:
                # Version desktop - cliquer sur le bouton "+"
                try:
                    # Chercher le bouton "+" (création)
                    create_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, 
                            "//div[contains(@class, 'createKeyCommandWrapper')]//div[@role='button'] | //div[@aria-label='New post' or @aria-label='Nouvelle publication']"))
                    )
                    create_button.click()
                    logger.info("Bouton de création cliqué (desktop)")
                    time.sleep(2)
                    return True
                    
                except Exception as e:
                    logger.error(f"Erreur lors du clic sur le bouton de création (desktop): {e}")
                    return False
        
        except Exception as e:
            logger.error(f"Erreur lors de la navigation vers la création: {e}")
            return False
    
    def publish(self, video_path: str, caption: str, hashtags: List[str], **kwargs) -> bool:
        """
        Publie une vidéo sur Instagram
        
        Args:
            video_path: Chemin de la vidéo à publier
            caption: Légende de la vidéo
            hashtags: Liste de hashtags à utiliser
            **kwargs: Paramètres supplémentaires
                - is_reel: Publier comme un Reel (True) ou post standard (False)
            
        Returns:
            True si la publication a réussi, False sinon
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        from selenium.webdriver.common.keys import Keys
        
        # Extraire les paramètres supplémentaires
        is_reel = kwargs.get('is_reel', True)
        
        # Vérifier l'authentification
        if not self.is_authenticated:
            logger.info("Authentification Instagram requise")
            if not self.authenticate():
                return False
        
        # Vérifier que le fichier vidéo existe
        if not os.path.exists(video_path):
            logger.error(f"Le fichier vidéo {video_path} n'existe pas")
            return False
        
        # Formater les hashtags
        hashtag_text = " ".join([f"#{tag}" for tag in hashtags]) if hashtags else ""
        
        # Formater la légende complète
        full_caption = caption
        if hashtag_text:
            if full_caption:
                full_caption += "\n\n" + hashtag_text
            else:
                full_caption = hashtag_text
        
        try:
            # Naviguer vers l'interface de création
            if not self._navigate_to_upload():
                logger.error("Échec de navigation vers l'interface de création Instagram")
                return False
            
            logger.info(f"Publication de la vidéo sur Instagram: {video_path}")
            
            # Gestion différente selon interface mobile ou desktop
            if self.mobile_emulation:
                # Version mobile
                
                # 1. Sélectionner le fichier vidéo
                try:
                    file_input = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                    )
                    
                    file_input.send_keys(os.path.abspath(video_path))
                    logger.info("Fichier vidéo sélectionné")
                    time.sleep(3)
                    
                    # Attendre le bouton "Next" ou "Suivant"
                    next_button = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, 
                            "//button[contains(text(), 'Next') or contains(text(), 'Suivant')]"))
                    )
                    next_button.click()
                    logger.info("Premier bouton Suivant cliqué")
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la sélection du fichier: {e}")
                    return False
                
                # 2. Passer l'étape des filtres/édition
                try:
                    next_button = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, 
                            "//button[contains(text(), 'Next') or contains(text(), 'Suivant')]"))
                    )
                    next_button.click()
                    logger.info("Deuxième bouton Suivant cliqué")
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Erreur lors du clic sur le deuxième bouton Suivant: {e}")
                    # Continuer quand même, car certaines versions peuvent sauter cette étape
                
                # 3. Saisir la légende et publier
                try:
                    caption_field = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, 
                            "//textarea[@aria-label='Write a caption…' or @aria-label='Écrire une légende...']"))
                    )
                    
                    caption_field.clear()
                    caption_field.send_keys(full_caption)
                    logger.info("Légende saisie")
                    time.sleep(1)
                    
                    # Cliquer sur le bouton "Share" ou "Partager"
                    share_button = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, 
                            "//button[contains(text(), 'Share') or contains(text(), 'Partager')]"))
                    )
                    share_button.click()
                    logger.info("Bouton Partager cliqué")
                    
                    # Attendre la fin du processus de publication
                    time.sleep(10)
                    
                    # Vérifier si la publication a réussi
                    if "instagram.com/create" not in self.driver.current_url:
                        logger.info("Publication Instagram réussie!")
                        return True
                    else:
                        logger.error("La publication n'a pas abouti")
                        return False
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la publication finale: {e}")
                    return False
                    
            else:
                # Version desktop
                
                # 1. Sélectionner le fichier
                try:
                    file_input = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                    )
                    
                    file_input.send_keys(os.path.abspath(video_path))
                    logger.info("Fichier vidéo sélectionné")
                    time.sleep(3)
                except Exception as e:
                    logger.error(f"Erreur lors de la sélection du fichier: {e}")
                    return False
                
                # 2. Sélectionner le type de contenu si c'est un Reel
                if is_reel:
                    try:
                        reel_option = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, 
                                "//span[contains(text(), 'Reel')] | //button[contains(text(), 'Reel')]"))
                        )
                        reel_option.click()
                        logger.info("Option Reel sélectionnée")
                        time.sleep(1)
                    except Exception as e:
                        logger.warning(f"Impossible de sélectionner l'option Reel: {e}")
                
                # 3. Cliquer sur "Next" pour passer à l'étape suivante
                try:
                    next_button = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, 
                            "//button[contains(text(), 'Next') or contains(text(), 'Suivant')]"))
                    )
                    next_button.click()
                    logger.info("Premier bouton Suivant cliqué")
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Erreur lors du clic sur le premier bouton Suivant: {e}")
                    return False
                
                # 4. Passer l'étape des filtres/édition
                try:
                    next_button = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, 
                            "//button[contains(text(), 'Next') or contains(text(), 'Suivant')]"))
                    )
                    next_button.click()
                    logger.info("Deuxième bouton Suivant cliqué")
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Erreur lors du clic sur le deuxième bouton Suivant: {e}")
                
                # 5. Saisir la légende et publier
                try:
                    caption_field = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, 
                            "//textarea[@aria-label='Write a caption…' or @aria-label='Écrire une légende...']"))
                    )
                    
                    caption_field.clear()
                    caption_field.send_keys(full_caption)
                    logger.info("Légende saisie")
                    time.sleep(1)
                    
                    # Cliquer sur le bouton "Share" ou "Partager"
                    share_button = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, 
                            "//button[contains(text(), 'Share') or contains(text(), 'Partager')]"))
                    )
                    share_button.click()
                    logger.info("Bouton Partager cliqué")
                    
                    # Attendre la fin du processus de publication
                    time.sleep(15)
                    
                    # Vérifier si la publication a réussi
                    success_elements = self.driver.find_elements(By.XPATH, 
                        "//span[contains(text(), 'shared') or contains(text(), 'partagé')]")
                    
                    if success_elements and any(elem.is_displayed() for elem in success_elements):
                        logger.info("Publication Instagram réussie!")
                        return True
                        
                    # Vérification alternative
                    if "instagram.com/create" not in self.driver.current_url:
                        logger.info("Publication Instagram probablement réussie")
                        return True
                    else:
                        logger.error("La publication n'a pas abouti")
                        return False
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la publication finale: {e}")
                    return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur Instagram: {e}")
            import traceback
            traceback.print_exc()
            
            # Capturer une capture d'écran pour le diagnostic
            if self.driver:
                self.driver.save_screenshot("instagram_error.png")
                logger.info("Une capture d'écran a été enregistrée dans 'instagram_error.png'")
            
            return False
        finally:
            # Fermer le navigateur si demandé
            if self.auto_close and self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except:
                    pass
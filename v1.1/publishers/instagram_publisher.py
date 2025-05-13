"""
Module de publication automatique pour Instagram utilisant Selenium
-----------------------------------------------------------------
Ce module permet de:
1. Se connecter à un compte Instagram
2. Publier automatiquement des vidéos (Posts ou Reels)
3. Gérer les légendes, hashtags et mentions

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
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from publishers.base_publisher import BasePublisher

logger = logging.getLogger("TikSimPro")

class InstagramPublisherSelenium(BasePublisher):
    """
    Gestionnaire de publication Instagram utilisant Selenium
    """
    
    def __init__(self, credentials_file=None, auto_close=True, mobile_emulation=True):
        """
        Initialise le gestionnaire de publication Instagram
        
        Args:
            credentials_file: Fichier pour sauvegarder les cookies (optionnel)
            auto_close: Fermer automatiquement le navigateur après utilisation
            mobile_emulation: Émuler un appareil mobile (recommandé pour Instagram)
        """
        self.cookies_file = credentials_file or "instagram_cookies.pkl"
        self.is_authenticated = False
        self.driver = None
        self.auto_close = auto_close
        self.mobile_emulation = mobile_emulation
        
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
            
            # Émulation mobile (recommandée pour Instagram)
            if self.mobile_emulation:
                mobile_emulation = {
                    "deviceName": "iPhone X"
                }
                chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
            
            # Agent utilisateur normal
            if not self.mobile_emulation:
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
            
            # Définir une taille d'écran raisonnable si pas d'émulation mobile
            if not self.mobile_emulation:
                self.driver.set_window_size(1280, 800)
            
            # Modifier les propriétés webdriver pour contourner la détection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Navigateur configuré pour Instagram")
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
                logger.info(f"Cookies Instagram sauvegardés dans {self.cookies_file}")
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
                if self.is_logged_in():
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
    
    def is_logged_in(self):
        """Vérifie si l'utilisateur est connecté à Instagram"""
        # Vérifier que le driver est initialisé
        if not self.driver:
            return False
            
        try:
            # Vérifier si le bouton de connexion est présent (si visible, alors non connecté)
            login_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Log in') or contains(text(), 'Log In') or contains(text(), 'Connexion')]")
            
            if login_buttons and any(btn.is_displayed() for btn in login_buttons):
                return False
            
            # Vérifier la présence d'éléments qui indiquent qu'on est connecté
            
            # Sur version desktop
            if not self.mobile_emulation:
                profile_links = self.driver.find_elements(By.XPATH, 
                    "//a[contains(@href, '/profile/') or contains(@href, '/_u/')]")
                if profile_links and any(link.is_displayed() for link in profile_links):
                    return True
            
            # Sur version mobile
            else:
                # Vérifier les icônes de la barre inférieure (home, search, etc)
                nav_items = self.driver.find_elements(By.XPATH, 
                    "//div[@role='tablist']/div")
                if nav_items and len(nav_items) >= 3:
                    return True
            
            # Vérifier si la page d'accueil est chargée
            if "instagram.com/accounts/login" not in self.driver.current_url:
                # Essayer de cliquer sur une zone vide pour voir s'il y a un popup non-authentifié
                try:
                    ActionChains(self.driver).move_by_offset(10, 10).click().perform()
                    time.sleep(1)
                    
                    # Après le clic, vérifier à nouveau si des boutons de connexion apparaissent
                    login_buttons = self.driver.find_elements(By.XPATH, 
                        "//button[contains(text(), 'Log in') or contains(text(), 'Log In') or contains(text(), 'Connexion')]")
                    
                    if login_buttons and any(btn.is_displayed() for btn in login_buttons):
                        return False
                    
                    # Si aucun bouton n'apparaît, on est probablement connecté
                    return True
                except:
                    # Si une erreur se produit, continuer la vérification
                    pass
            
            # Par défaut, considérer qu'on n'est pas connecté
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de connexion Instagram: {e}")
            return False
    
    def authenticate(self):
        """
        Se connecte à Instagram, soit automatiquement via cookies, soit manuellement
        
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
            logger.info("Ouverture de la page de connexion Instagram...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)
            
            # Accepter les cookies si nécessaire
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
            if self.is_logged_in():
                logger.info("Déjà connecté à Instagram")
                self.is_authenticated = True
                self.save_cookies()
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
                if self.is_logged_in():
                    logger.info("Connexion à Instagram réussie!")
                    self.is_authenticated = True
                    self.save_cookies()
                    return True
                
                time.sleep(check_interval)
                print(f"Vérification de connexion Instagram... URL: {self.driver.current_url}")
            
            # Si le temps d'attente est dépassé
            print("Temps d'attente dépassé. Confirmez-vous être connecté? (o/n)")
            response = input().strip().lower()
            if response in ['o', 'oui', 'y', 'yes']:
                self.is_authenticated = True
                self.save_cookies()
                return True
            
            return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification Instagram: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def navigate_to_upload(self):
        """
        Navigue vers la page de téléchargement/création Instagram
        
        Returns:
            bool: True si la navigation a réussi, False sinon
        """
        # Vérifier que le driver est initialisé
        if not self.driver:
            if not self.setup_browser():
                return False
                
        try:
            # Aller d'abord à la page principale d'Instagram
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
    
    def upload_video(self, video_path, caption="", hashtags=None, is_reel=True):
        """
        Publie une vidéo sur Instagram, en Reel ou en post normal
        
        Args:
            video_path: Chemin vers le fichier vidéo
            caption: Légende de la vidéo
            hashtags: Liste de hashtags (sans #)
            is_reel: Poster comme un Reel (True) ou post standard (False)
            
        Returns:
            bool: True si la publication a réussi, False sinon
        """
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
        hashtag_text = ""
        if hashtags:
            hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
        
        # Formater la légende complète
        full_caption = caption
        if hashtag_text:
            if full_caption:
                full_caption += "\n\n" + hashtag_text
            else:
                full_caption = hashtag_text
        
        try:
            # Naviguer vers l'interface de création
            if not self.navigate_to_upload():
                logger.error("Échec de navigation vers l'interface de création Instagram")
                return False
            
            logger.info(f"Publication de la vidéo sur Instagram: {video_path}")
            
            # Gestion différente selon interface mobile ou desktop
            if self.mobile_emulation:
                return self._upload_mobile(video_path, full_caption, is_reel)
            else:
                return self._upload_desktop(video_path, full_caption, is_reel)
                
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur Instagram: {e}")
            logger.error(traceback.format_exc())
            return False
        finally:
            if self.auto_close:
                self.close()
    
    def _upload_mobile(self, video_path, caption, is_reel):
        """Méthode pour télécharger via l'interface mobile"""
        try:
            # 1. Sélectionner le type de contenu (Reel ou Post)
            # Pour l'interface mobile, cette étape est souvent gérée directement dans l'écran de création
            
            # 2. Sélectionner le fichier vidéo
            try:
                # Attendre l'apparition de l'input file
                file_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
                
                # Envoyer le chemin du fichier vidéo
                file_input.send_keys(os.path.abspath(video_path))
                logger.info("Fichier vidéo sélectionné")
                time.sleep(3)
                
                # Attendre que le téléchargement soit terminé
                try:
                    # Rechercher le bouton "Next" ou "Suivant"
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
                
            except Exception as e:
                logger.error(f"Erreur lors de la sélection du fichier: {e}")
                return False
            
            # 3. Ajuster les options de filtres/édition (passer à l'étape suivante)
            try:
                # Rechercher le bouton "Next" ou "Suivant" à l'étape des filtres
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
            
            # 4. Saisir la légende et publier
            try:
                # Attendre l'apparition du champ de légende
                caption_field = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//textarea[@aria-label='Write a caption…' or @aria-label='Écrire une légende...']"))
                )
                
                # Effacer tout texte existant
                caption_field.clear()
                
                # Saisir la légende
                caption_field.send_keys(caption)
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
                
                # Vérifier si la publication a réussi (retour à la page principale)
                if "instagram.com/create" not in self.driver.current_url:
                    logger.info("Publication Instagram réussie!")
                    return True
                else:
                    # Vérifier s'il y a des messages d'erreur
                    error_messages = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'error') or contains(@class, 'Error')]")
                    
                    if error_messages:
                        for msg in error_messages:
                            if msg.is_displayed():
                                logger.error(f"Message d'erreur Instagram: {msg.text}")
                    
                    logger.error("La publication n'a pas abouti")
                    return False
                
            except Exception as e:
                logger.error(f"Erreur lors de la publication finale: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur générale lors de l'upload mobile: {e}")
            return False
    
    def _upload_desktop(self, video_path, caption, is_reel):
        """Méthode pour télécharger via l'interface desktop"""
        try:
            # 1. Dans l'interface desktop, on doit d'abord sélectionner le fichier
            try:
                # Attendre l'apparition de l'input file
                file_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
                
                # Envoyer le chemin du fichier vidéo
                file_input.send_keys(os.path.abspath(video_path))
                logger.info("Fichier vidéo sélectionné")
                time.sleep(3)
            except Exception as e:
                logger.error(f"Erreur lors de la sélection du fichier: {e}")
                return False
            
            # 2. Sélectionner le type de contenu si c'est un Reel
            if is_reel:
                try:
                    # Chercher l'option Reel dans le menu déroulant ou bouton
                    reel_option = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, 
                            "//span[contains(text(), 'Reel')] | //button[contains(text(), 'Reel')]"))
                    )
                    reel_option.click()
                    logger.info("Option Reel sélectionnée")
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"Impossible de sélectionner l'option Reel: {e}")
                    # Continuer quand même, Instagram peut déterminer automatiquement
            
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
                # Continuer quand même, car certaines versions peuvent sauter cette étape
            
            # 5. Saisir la légende et publier
            try:
                # Attendre l'apparition du champ de légende
                caption_field = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//textarea[@aria-label='Write a caption…' or @aria-label='Écrire une légende...']"))
                )
                
                # Effacer tout texte existant
                caption_field.clear()
                
                # Saisir la légende
                caption_field.send_keys(caption)
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
                    # Vérifier s'il y a des messages d'erreur
                    error_messages = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'error') or contains(@class, 'Error')]")
                    
                    if error_messages:
                        for msg in error_messages:
                            if msg.is_displayed():
                                logger.error(f"Message d'erreur Instagram: {msg.text}")
                    
                    logger.error("La publication n'a pas abouti")
                    return False
                
            except Exception as e:
                logger.error(f"Erreur lors de la publication finale: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur générale lors de l'upload desktop: {e}")
            return False
    
    def close(self):
        """Ferme le navigateur et nettoie les ressources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Navigateur Instagram fermé")
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture du navigateur: {e}")
            finally:
                self.driver = None
    
    def __del__(self):
        """Destructeur pour assurer que le navigateur est fermé"""
        if hasattr(self, 'auto_close') and self.auto_close:
            self.close()
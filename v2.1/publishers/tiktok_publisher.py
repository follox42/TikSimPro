# publishers/tiktok_publisher.py
"""
Système de publication TikTok utilisant Selenium
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

class TikTokPublisher(IContentPublisher):
    """
    Publie du contenu sur TikTok en utilisant Selenium
    """
    
    def __init__(self, 
                credentials_file: Optional[str] = None, 
                auto_close: bool = True,
                headless: bool = False):
        """
        Initialise le système de publication TikTok
        
        Args:
            credentials_file: Fichier pour sauvegarder les cookies
            auto_close: Fermer automatiquement le navigateur après utilisation
            headless: Exécuter le navigateur en mode headless
        """
        self.cookies_file = credentials_file or "tiktok_cookies.pkl"
        self.auto_close = auto_close
        self.headless = headless
        self.is_authenticated = False
        self.driver = None
        
        # Vérifier que Selenium est disponible
        self._check_selenium()
        
        logger.info("TikTokPublisher initialisé")
    
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
            
            # Agent utilisateur mobile pour meilleure compatibilité
            mobile_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/85.0.4183.109 Mobile/15E148 Safari/604.1"
            chrome_options.add_argument(f"--user-agent={mobile_user_agent}")
            
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
            
            logger.info("Navigateur configuré pour TikTok")
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
            logger.info(f"Cookies TikTok sauvegardés dans {self.cookies_file}")
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
                
                # Ouvrir d'abord TikTok pour pouvoir ajouter les cookies
                self.driver.get("https://www.tiktok.com")
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
                    logger.info("Session TikTok restaurée avec succès via les cookies")
                    self.is_authenticated = True
                    return True
                else:
                    logger.info("Les cookies sauvegardés ne sont plus valides pour TikTok")
                    return False
                    
            except Exception as e:
                logger.error(f"Erreur lors du chargement des cookies: {e}")
                return False
        else:
            logger.info("Aucun cookie TikTok sauvegardé trouvé")
            return False
    
    def _is_logged_in(self) -> bool:
        """
        Vérifie si l'utilisateur est connecté à TikTok
        
        Returns:
            True si connecté, False sinon
        """
        from selenium.webdriver.common.by import By
        
        # Vérifier que le driver est initialisé
        if not self.driver:
            return False
            
        try:
            current_url = self.driver.current_url
            
            # Vérifier si nous sommes sur TikTok Studio ou sur creator-center/upload
            if ("tiktok.com/tiktokstudio" in current_url and "login" not in current_url) or "creator-center/upload" in current_url:
                return True
            
            # Vérifier la présence du bouton de connexion (si visible, alors non connecté)
            login_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Log in') or contains(text(), 'Login') or contains(text(), 'Sign in') or contains(text(), 'Connexion')]")
            
            if login_buttons and any(btn.is_displayed() for btn in login_buttons):
                return False
            
            # Vérifier la présence d'éléments qui indiquent qu'on est connecté
            profile_elements = self.driver.find_elements(By.XPATH, 
                "//a[contains(@href, '/profile') or contains(@href, '/@')]")
            
            if profile_elements and any(elem.is_displayed() for elem in profile_elements):
                return True
            
            # Vérifier la présence du bouton upload
            upload_buttons = self.driver.find_elements(By.XPATH, 
                "//a[contains(@href, '/create')] | //button[contains(@class, 'upload')] | //div[contains(@class, 'upload')]")
            
            if upload_buttons and any(btn.is_displayed() for btn in upload_buttons):
                return True
            
            # Par défaut, considérer qu'on n'est pas connecté
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de connexion TikTok: {e}")
            return False
    
    def authenticate(self) -> bool:
        """
        Authentifie le système de publication
        
        Returns:
            True si l'authentification a réussi, False sinon
        """
        # Initialiser le navigateur si nécessaire
        if not self.driver:
            logger.info("Initialisation du navigateur pour l'authentification TikTok...")
            if not self._setup_browser():
                logger.error("Impossible d'initialiser le navigateur")
                return False
        
        # Vérifier d'abord si nous pouvons nous connecter avec des cookies existants
        if self._load_cookies():
            return True
        
        # Si pas de cookies ou cookies invalides, procéder à la connexion manuelle
        try:
            logger.info("Ouverture de la page TikTok...")
            self.driver.get("https://www.tiktok.com/tiktokstudio")
            time.sleep(5)
            
            # Vérifier si nous sommes déjà connectés
            if self._is_logged_in():
                logger.info("Déjà connecté à TikTok")
                self.is_authenticated = True
                self._save_cookies()
                return True
            
            # Attendre que l'utilisateur se connecte manuellement
            print("\n" + "="*80)
            print("VEUILLEZ VOUS CONNECTER MANUELLEMENT À TIKTOK DANS LA FENÊTRE DU NAVIGATEUR")
            print("Le programme va vérifier régulièrement si vous êtes connecté")
            print("IMPORTANT: Assurez-vous de vous connecter avec un compte CRÉATEUR")
            print("="*80 + "\n")
            
            # Vérifier régulièrement si l'utilisateur s'est connecté
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            check_interval = 5  # vérifier toutes les 5 secondes
            
            while time.time() - start_time < max_wait_time:
                if self._is_logged_in():
                    logger.info("Connexion à TikTok réussie!")
                    self.is_authenticated = True
                    self._save_cookies()
                    return True
                
                time.sleep(check_interval)
                print(f"Vérification de connexion TikTok... URL: {self.driver.current_url}")
            
            # Si le temps d'attente est dépassé
            print("Temps d'attente dépassé. Confirmez-vous être connecté? (o/n)")
            response = input().strip().lower()
            if response in ['o', 'oui', 'y', 'yes']:
                self.is_authenticated = True
                self._save_cookies()
                return True
            
            return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification TikTok: {e}")
            return False
    
    def publish(self, video_path: str, caption: str, hashtags: List[str], **kwargs) -> bool:
        """
        Publie une vidéo sur TikTok
        
        Args:
            video_path: Chemin de la vidéo à publier
            caption: Légende de la vidéo
            hashtags: Liste de hashtags à utiliser
            kwargs: Paramètres supplémentaires spécifiques à la plateforme
            
        Returns:
            True si la publication a réussi, False sinon
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        from selenium.webdriver.common.keys import Keys
        
        # Vérifier l'authentification
        if not self.is_authenticated:
            logger.info("Authentification TikTok requise")
            if not self.authenticate():
                return False
        
        # Vérifier que le fichier vidéo existe
        if not os.path.exists(video_path):
            logger.error(f"Le fichier vidéo {video_path} n'existe pas")
            return False
        
        # Formater les hashtags
        hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
        
        # Formater la légende complète
        full_caption = caption
        if hashtag_text:
            if full_caption:
                full_caption += "\n\n" + hashtag_text
            else:
                full_caption = hashtag_text
        
        try:
            # Aller directement à TikTok Studio
            logger.info("Navigation vers TikTok Studio...")
            self.driver.get("https://www.tiktok.com/creator-center/upload")
            time.sleep(5)
            
            # Vérifier si nous sommes bien connecté au studio ou redirigé vers la connexion
            current_url = self.driver.current_url
            if "login" in current_url:
                logger.info("Redirection vers la page de connexion détectée. Connexion nécessaire.")
                if not self.authenticate():
                    return False
                # Après connexion, retourner au studio
                self.driver.get("https://www.tiktok.com/creator-center/upload")
                time.sleep(5)
            
            # Attendre que l'input file apparaisse
            logger.info("Recherche du champ de téléchargement...")
            try:
                upload_input = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
            except TimeoutException:
                # Si l'élément spécifique n'est pas trouvé, chercher tous les inputs de type file
                upload_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
                if upload_inputs:
                    upload_input = upload_inputs[0]
                else:
                    logger.error("Aucun champ d'upload trouvé!")
                    self.driver.save_screenshot("upload_error.png")
                    logger.info("Une capture d'écran a été enregistrée dans 'upload_error.png'")
                    return False
            
            # Télécharger la vidéo
            logger.info(f"Téléchargement de la vidéo: {video_path}")
            upload_input.send_keys(os.path.abspath(video_path))
            
            # Attendre que la vidéo soit traitée
            logger.info("Traitement de la vidéo en cours...")
            time.sleep(15)  # Attente initiale plus longue
            
            # Attendre que le champ de description soit activé (cela indique que la vidéo est prête)
            try:
                caption_field = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
                )
            except:
                logger.error("Champ de description non trouvé")
                return False
            
            # Saisir la description
            logger.info(f"Ajout de la description et des hashtags: {full_caption}")

            # Méthode 1: Simuler une frappe humaine
            caption_field.click()  # S'assurer que le champ est sélectionné
            caption_field.clear()  # Effacer tout texte existant

            # Simuler un Ctrl+A pour tout sélectionner
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()

            # Ensuite, simuler un appui sur la touche Backspace pour effacer
            caption_field.send_keys(Keys.BACKSPACE)

            # Ajouter la description principale
            caption_field.send_keys(caption)
            caption_field.send_keys(Keys.ENTER)
            caption_field.send_keys(Keys.ENTER)
            caption_field.send_keys(hashtag_text)

            # Attendre un moment pour que TikTok traite les hashtags
            time.sleep(2)
            
            # Rechercher et cliquer sur le bouton de publication
            logger.info("Recherche du bouton de publication...")
            post_button_xpaths = [
                "//button[contains(text(), 'Post') or contains(text(), 'Publier')]",
                "//button[contains(@class, 'submit') or contains(@class, 'publish') or contains(@class, 'post')]",
                "//div[contains(text(), 'Post') or contains(text(), 'Publier')]",
                "//span[contains(text(), 'Post') or contains(text(), 'Publier')]",
                "//button[contains(@data-e2e, 'post') or contains(@data-e2e, 'publish')]"
            ]
            
            post_button = None
            for xpath in post_button_xpaths:
                buttons = self.driver.find_elements(By.XPATH, xpath)
                if buttons:
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            post_button = button
                            break
                if post_button:
                    break
            
            if not post_button:
                logger.error("Aucun bouton de publication trouvé")
                return False
            
            # Cliquer sur le bouton de publication
            logger.info("Publication de la vidéo...")
            post_button.click()
            
            # Attendre la confirmation de publication
            logger.info("Attente de la confirmation de publication...")
            time.sleep(10)  # Attendre que la publication commence
            
            # Vérifier si nous sommes redirigés vers une autre page (signe de succès)
            tries = 0
            max_tries = 12  # Attendre jusqu'à 2 minutes (12 x 10 secondes)
            success = False
            
            while tries < max_tries:
                # Vérifier si nous sommes redirigés vers la page de contenu
                current_url = self.driver.current_url
                if "/content" in current_url:
                    logger.info("Redirection vers la page de contenu détectée : Publication réussie !")
                    success = True
                    break
                
                # Vérifier s'il y a un message de succès
                success_elements = self.driver.find_elements(By.XPATH, 
                    "//div[contains(text(), 'Your video is') or contains(text(), 'Votre vidéo') or contains(text(), 'success')]")
                if success_elements:
                    logger.info("Message de succès détecté!")
                    success = True
                    break
                
                time.sleep(10)
                tries += 1
                logger.info(f"Toujours en attente de confirmation... ({tries}/{max_tries})")
            
            # Si nous arrivons ici sans confirmation, demander à l'utilisateur
            if not success:
                print("\nLa confirmation automatique a échoué. Veuillez vérifier manuellement.")
                print("La vidéo a-t-elle été publiée avec succès? (o/n)")
                
                response = input("Votre réponse (o/n): ").strip().lower()
                success = response == 'o' or response == 'oui' or response == 'y' or response == 'yes'
            
            if self.auto_close:
                logger.info("Fermeture du navigateur...")
                self.driver.quit()
                self.driver = None
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur TikTok: {e}")
            import traceback
            traceback.print_exc()
            
            # Capturer une capture d'écran pour le diagnostic
            if self.driver:
                self.driver.save_screenshot("tiktok_error.png")
                logger.info("Une capture d'écran a été enregistrée dans 'tiktok_error.png'")
            
            return False
        finally:
            # Fermer le navigateur si demandé
            if self.auto_close and self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except:
                    pass
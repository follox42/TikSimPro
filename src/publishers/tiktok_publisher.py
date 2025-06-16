# publishers/tiktok_publisher.py
"""
Publisher for tiktok:

"""

import os
import time
import pickle
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import random
from pathlib import Path

from src.publishers.base_publisher import IPublisher
from src.utils.connectors.tiktok_connector import TikTokConnector

logger = logging.getLogger("TikSimPro")

class TikTokPublisher(IPublisher):
    """
    Publisher for tiktok
    """
    def __init__(self, 
                credentials_file: Optional[str] = None, 
                auto_close: bool = True,
                headless: bool = False):
        """
        Init the tiktok publicher system
        
        Args:
            credentials_file: File to save cookies
            auto_close: Auto close the browser after the user's done
            headless: Use selenium in headless mode ( enable if you encounter any problem )
        """
        self.auto_close = auto_close
        self.headless = headless

        self.connector = TikTokConnector(credentials_file or "tiktok_cookies.pkl", headless=headless)

        logger.info("TikTokPublisher initialized")

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
        if not self.connector.is_authenticated:
            logger.info("Authentification TikTok requise")
            if not self.connector.authenticate():
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
            self.connector.driver.get("https://www.tiktok.com/creator-center/upload")
            time.sleep(5)
            
            # Vérifier si nous sommes bien connecté au studio ou redirigé vers la connexion
            current_url = self.connector.driver.current_url
            if "login" in current_url:
                logger.info("Redirection vers la page de connexion détectée. Connexion nécessaire.")
                if not self.connector.authenticate():
                    return False
                # Après connexion, retourner au studio
                self.connector.driver.get("https://www.tiktok.com/creator-center/upload")
                time.sleep(5)
            
            # Attendre que l'input file apparaisse
            logger.info("Recherche du champ de téléchargement...")
            try:
                upload_input = WebDriverWait(self.connector.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
            except TimeoutException:
                # Si l'élément spécifique n'est pas trouvé, chercher tous les inputs de type file
                upload_inputs = self.connector.driver.find_elements(By.XPATH, "//input[@type='file']")
                if upload_inputs:
                    upload_input = upload_inputs[0]
                else:
                    logger.error("Aucun champ d'upload trouvé!")
                    self.connector.driver.save_screenshot("upload_error.png")
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
                caption_field = WebDriverWait(self.connector.driver, 20).until(
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
            actions = ActionChains(self.connector.driver)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()

            # Ensuite, simuler un appui sur la touche Backspace pour effacer
            caption_field.send_keys(Keys.BACKSPACE)
            time.sleep(2)

            # Simuler un Ctrl+A pour tout sélectionner
            actions = ActionChains(self.connector.driver)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            
            # Ajouter la description principale
            caption_field.send_keys(caption)
            caption_field.send_keys(Keys.ENTER)
            caption_field.send_keys(Keys.ENTER)
            caption_field.send_keys(hashtag_text)

            # Attendre un moment pour que TikTok traite les hashtags
            time.sleep(5)
            
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
                buttons = self.connector.driver.find_elements(By.XPATH, xpath)
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
                current_url = self.connector.driver.current_url
                if "/content" in current_url:
                    logger.info("Redirection vers la page de contenu détectée : Publication réussie !")
                    success = True
                    break
                
                # Vérifier s'il y a un message de succès
                success_elements = self.connector.driver.find_elements(By.XPATH, 
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
                self.connector.driver.quit()
                self.connector.driver = None
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur TikTok: {e}")
            import traceback
            traceback.print_exc()
            
            # Capturer une capture d'écran pour le diagnostic
            if self.connector.driver:
                self.connector.driver.save_screenshot("tiktok_error.png")
                logger.info("Une capture d'écran a été enregistrée dans 'tiktok_error.png'")
            
            return False
        finally:
            # Fermer le navigateur si demandé
            if self.auto_close and self.connector.driver:
                try:
                    self.connector.driver.quit()
                    self.connector.driver = None
                except:
                    pass
"""
Module de publication automatique pour TikTok avec détection de connexion améliorée
----------------------------------------------------------------------------------
Ce module permet de:
1. Se connecter à un compte TikTok
2. Publier automatiquement des vidéos
3. Gérer les hashtags et descriptions

Requiert:
pip install selenium webdriver-manager
"""

import os
import time
import json
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from publishers.base_publisher import BasePublisher

class TikTokPublisher(BasePublisher):
    def __init__(self, credentials_file=None, auto_close=True):
        """
        Initialise le gestionnaire de publication TikTok
        
        Args:
            credentials_file (str): Chemin vers un fichier de sauvegarde des cookies (optionnel)
        """
        self.credentials_file = credentials_file
        self.cookies_file = "tiktok_cookies.pkl"
        self.is_authenticated = False
        self.driver = None
        self.auto_close = auto_close  # Par défaut, on ferme le navigateur
        self.setup_browser()
    
    def setup_browser(self):
        """Configure le navigateur Chrome avec Selenium"""
        chrome_options = Options()
        
        # Options pour améliorer la stabilité
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-extensions")
        
        # Décommenter pour exécuter en arrière-plan (sans interface visible)
        # chrome_options.add_argument("--headless")
        
        # Option pour éviter la détection comme bot
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # User agent mobile pour meilleure compatibilité avec TikTok
        mobile_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/85.0.4183.109 Mobile/15E148 Safari/604.1"
        chrome_options.add_argument(f'user-agent={mobile_user_agent}')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Modifier les propriétés webdriver pour contourner la détection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Navigateur configuré avec succès")
    
    def save_cookies(self):
        """Sauvegarde les cookies pour les futures sessions"""
        if self.driver:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as file:
                pickle.dump(cookies, file)
            print(f"Cookies sauvegardés dans {self.cookies_file}")
    
    def load_cookies(self):
        """Charge les cookies d'une session précédente si disponibles"""
        if os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'rb') as file:
                cookies = pickle.load(file)
            
            # Ouvrir d'abord TikTok Studio pour pouvoir ajouter les cookies
            self.driver.get("https://www.tiktok.com/tiktokstudio")
            time.sleep(2)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Erreur lors de l'ajout du cookie: {e}")
            
            # Rafraîchir pour appliquer les cookies
            self.driver.refresh()
            time.sleep(3)
            
            # Vérifier si connecté à TikTok Studio
            try:
                # Vérifier si nous sommes sur la page TikTok Studio ou center-creator/upload (pas sur la page de connexion)
                current_url = self.driver.current_url
                print(f"URL après chargement des cookies: {current_url}")
                
                if (("tiktokstudio" in current_url and "login" not in current_url) or 
                    "creator-center/upload" in current_url):
                    print("Session TikTok Studio restaurée avec succès via les cookies")
                    self.is_authenticated = True
                    return True
                else:
                    print("Les cookies sauvegardés ne sont plus valides pour TikTok Studio")
                    print(f"URL actuelle après tentative de restauration: {current_url}")
                    return False
            except Exception as e:
                print(f"Erreur lors de la vérification des cookies: {e}")
                return False
        else:
            print("Aucun cookie sauvegardé trouvé")
            return False
    
    def is_logged_in(self):
        """
        Vérifie si l'utilisateur est connecté en cherchant différents éléments de l'interface
        """
        try:
            # Examiner différents éléments qui indiquent une connexion réussie
            # 1. Vérifier la présence d'un avatar (méthode principale)
            try:
                avatar_elements = self.driver.find_elements(By.XPATH, 
                    "//span[contains(@class, 'avatar')] | //div[contains(@class, 'avatar')] | //img[contains(@class, 'avatar')]")
                if avatar_elements:
                    return True
            except:
                pass
                
            # 2. Vérifier la présence du bouton de création de vidéo
            try:
                upload_buttons = self.driver.find_elements(By.XPATH, 
                    "//a[contains(@href, '/create')] | //button[contains(@class, 'upload')] | //div[contains(@class, 'upload')]")
                if upload_buttons:
                    return True
            except:
                pass
                
            # 3. Vérifier l'absence du bouton de connexion
            try:
                login_buttons = self.driver.find_elements(By.XPATH, 
                    "//a[contains(@href, '/login')] | //button[contains(text(), 'Log in')] | //button[contains(text(), 'Sign in')]")
                if not login_buttons:
                    return True
            except:
                pass
                
            # 4. Vérifier l'URL qui peut contenir des indicateurs de profil
            current_url = self.driver.current_url
            if "/profile" in current_url or "/me" in current_url:
                return True
                
            return False
            
        except Exception as e:
            print(f"Erreur lors de la vérification de connexion: {e}")
            return False
    
    def manual_check_login(self):
        """Demande à l'utilisateur de confirmer manuellement s'il est connecté à TikTok Studio"""
        print("\n" + "="*80)
        print("VÉRIFICATION MANUELLE DE CONNEXION À TIKTOK STUDIO")
        print("Êtes-vous connecté à TikTok Studio dans la fenêtre du navigateur? (o/n)")
        print("="*80)
        
        response = input("Votre réponse (o/n): ").strip().lower()
        if response == 'o' or response == 'oui' or response == 'y' or response == 'yes':
            self.is_authenticated = True
            self.save_cookies()
            return True
        return False
    
    def authenticate(self):
        """
        Ouvre la page de connexion TikTok Studio et attend que l'utilisateur se connecte manuellement.
        Sauvegarde ensuite les cookies pour les futures sessions.
        """
        # Vérifier d'abord si nous pouvons nous connecter avec des cookies existants
        if self.load_cookies():
            return True
        
        # Si pas de cookies ou cookies invalides, procéder à la connexion manuelle
        try:
            print("Ouverture de la page TikTok Studio...")
            # URL directe de TikTok Studio qui mène au portail de connexion créateur
            self.driver.get("https://www.tiktok.com/tiktokstudio")
            time.sleep(5)
            
            current_url = self.driver.current_url
            print(f"URL actuelle: {current_url}")
            
            # Vérifier si nous sommes redirigés vers la page de connexion spécifique à TikTok Studio
            studio_login_indicators = [
                "login?redirect_url=", 
                "creator-center", 
                "enter_from=tiktokstudio"
            ]
            
            is_on_studio_login = all(indicator in current_url for indicator in studio_login_indicators)
            
            if is_on_studio_login or "login" in current_url or not self.is_logged_in():
                print("Page de connexion TikTok Studio détectée.")
                
                # Attendre que l'utilisateur se connecte manuellement
                print("\n" + "="*80)
                print("VEUILLEZ VOUS CONNECTER MANUELLEMENT DANS LA FENÊTRE DU NAVIGATEUR")
                print("IMPORTANT: Assurez-vous de vous connecter avec un compte CRÉATEUR")
                print("Le programme va vérifier régulièrement si vous êtes connecté")
                print("="*80 + "\n")
                
                # Vérifier régulièrement si l'utilisateur s'est connecté
                max_wait_time = 300  # 5 minutes
                start_time = time.time()
                check_interval = 5  # vérifier toutes les 5 secondes
                
                while time.time() - start_time < max_wait_time:
                    # Vérifier si nous sommes sur TikTok Studio après connexion réussie
                    current_url = self.driver.current_url
                    print(f"Vérification URL: {current_url}")
                    
                    # Vérifier si nous sommes sur TikTok Studio ou sur creator-center/upload
                    if ("tiktokstudio" in current_url and "login" not in current_url) or "creator-center/upload" in current_url:
                        print("Connexion à TikTok Studio réussie!")
                        self.is_authenticated = True
                        self.save_cookies()
                        return True
                    
                    time.sleep(check_interval)
                    print("Vérification de connexion à TikTok Studio... (Ctrl+C pour interrompre)")
                
                # Si le temps d'attente est dépassé, demander à l'utilisateur
                print("Temps d'attente dépassé pour la détection automatique.")
                return self.manual_check_login()
            else:
                # Déjà connecté à TikTok Studio
                print("Déjà connecté à TikTok Studio!")
                self.is_authenticated = True
                self.save_cookies()
                return True
                
        except Exception as e:
            print(f"Erreur lors de l'authentification à TikTok Studio: {e}")
            # Essayer la vérification manuelle en dernier recours
            return self.manual_check_login()
    
    def upload_video(self, video_path, caption="", hashtags=None):
        """
        Publie une vidéo sur TikTok avec une légende et des hashtags
        
        Args:
            video_path (str): Chemin vers le fichier vidéo à publier
            caption (str): Texte de la description
            hashtags (list): Liste de hashtags à ajouter (sans le symbole #)
        
        Returns:
            bool: True si la publication a réussi, False sinon
        """
        if not self.is_authenticated:
            print("Vous devez vous authentifier avant de publier")
            if not self.authenticate():
                return False
        
        if not os.path.exists(video_path):
            print(f"Le fichier vidéo {video_path} n'existe pas")
            return False
        
        self.auto_close = False  # Désactiver la fermeture automatique
        
        try:
            # Formater la description avec les hashtags
            if hashtags:
                hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
                full_caption = f"{caption}\n\n{hashtag_text}"
            else:
                full_caption = caption
            
            # Aller directement à TikTok Studio
            print("Navigation vers TikTok Studio...")
            self.driver.get("https://www.tiktok.com/tiktokstudio")
            time.sleep(5)
            
            # Vérifier si nous sommes bien connecté au studio ou redirigé vers la connexion
            current_url = self.driver.current_url
            if "login" in current_url:
                print("Redirection vers la page de connexion détectée. Connexion nécessaire.")
                if not self.authenticate():
                    return False
                # Après connexion, retourner au studio
                self.driver.get("https://www.tiktok.com/tiktokstudio")
                time.sleep(5)
            
            # Rechercher et cliquer sur le bouton "Télécharger" ou "Upload" dans le studio
            print("Recherche du bouton de téléchargement dans TikTok Studio...")
            upload_button_xpaths = [
                "//button[contains(text(), 'Upload') or contains(text(), 'Télécharger')]",
                "//a[contains(text(), 'Upload') or contains(text(), 'Télécharger')]",
                "//div[contains(text(), 'Upload') or contains(text(), 'Télécharger')]",
                "//span[contains(text(), 'Upload') or contains(text(), 'Télécharger')]",
                "//button[contains(@class, 'upload')]",
                "//div[contains(@class, 'upload')]",
                "//a[contains(@href, '/creator-center/upload')]",
                "//a[contains(@href, '/upload')]"
            ]
            
            upload_button = None
            for xpath in upload_button_xpaths:
                buttons = self.driver.find_elements(By.XPATH, xpath)
                if buttons:
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            upload_button = button
                            break
                if upload_button:
                    break
            
            if upload_button:
                print("Bouton de téléchargement trouvé. Clic...")
                upload_button.click()
                time.sleep(5)
            else:
                # Si aucun bouton trouvé, essayer d'aller directement à la page d'upload
                print("Aucun bouton de téléchargement trouvé. Accès direct à la page d'upload...")
                self.driver.get("https://www.tiktok.com/creator-center/upload")
                time.sleep(5)
            
            # Maintenant, chercher l'élément input file pour télécharger la vidéo
            print("Recherche du champ de téléchargement...")
            
            try:
                # Attendre que l'input file apparaisse
                upload_input = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
            except TimeoutException:
                # Si l'élément spécifique n'est pas trouvé, chercher tous les inputs de type file
                upload_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
                if upload_inputs:
                    upload_input = upload_inputs[0]
                else:
                    print("Aucun champ d'upload trouvé! Capture d'écran pour diagnostic...")
                    self.driver.save_screenshot("upload_error.png")
                    print(f"Une capture d'écran a été enregistrée dans 'upload_error.png'")
                    return False
            
            # Télécharger la vidéo
            print(f"Téléchargement de la vidéo: {video_path}")
            upload_input.send_keys(os.path.abspath(video_path))
            
            # Attendre que la vidéo soit traitée
            print("Traitement de la vidéo en cours...")
            time.sleep(15)  # Attente initiale plus longue
            
            # Attendre que le champ de description soit activé (cela indique que la vidéo est prête)
            try:
                # Essayer différents sélecteurs pour le champ de description
                caption_field = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
                )
            except:
                print("Champ de description non trouvé")
            
            # Saisir la description
            print(f"Ajout de la description et des hashtags: {full_caption}")

            # Méthode 1: Simuler une frappe humaine
            caption_field.click()  # S'assurer que le champ est sélectionné
            caption_field.clear()  # Effacer tout texte existant

            # Simuler un Ctrl+A pour tout sélectionner (Cmd+A sur Mac si besoin)
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

            # Vérification que le texte a été saisi correctement
            try:
                actual_text = caption_field.get_attribute("innerText") or caption_field.text
                print(f"Texte actuellement présent dans le champ: '{actual_text}'")
                
                if not actual_text or actual_text.strip() == "":
                    print("ATTENTION: La description semble vide!")
                elif not all(f"#{tag}" in actual_text for tag in hashtags):
                    print("ATTENTION: Certains hashtags semblent manquants!")
            except Exception as e:
                print(f"Erreur lors de la vérification du texte: {e}")

            print("Description et hashtags ajoutés")

            
            # Attendre le chargement de l'image de couverture
            try:
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//img[contains(@class, 'cover-image')]")
                    )
                )
                print("Image de couverture chargée.")
            except:
                print("Erreur : L'image de couverture n'a pas été trouvée après 60 secondes.")
            
            # Cliquer sur le bouton de publication (essayer plusieurs variantes)
            print("Recherche du bouton de publication...")
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
                        print(f"Bouton trouvé: {button.text}, Classe: {button.get_attribute('class')}, Visible: {button.is_displayed()}, Activé: {button.is_enabled()}")
                        
                        try:
                            # Faire défiler vers le bouton pour qu'il soit visible
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(2)  # Attendre que le défilement soit terminé
                            
                            # Attendre explicitement que le bouton soit cliquable
                            try:
                                WebDriverWait(self.driver, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, f"//*[contains(@class, '{button.get_attribute('class')}')]"))
                                )
                            except:
                                print("Attente du bouton cliquable échouée, tentative quand même...")
                            
                            # Si le bouton est visible et activé
                            if button.is_displayed() and button.is_enabled():
                                post_button = button
                                break
                        except Exception as e:
                            print(f"Erreur lors de la vérification du bouton: {e}")
                            continue
                            
                if post_button:
                    break
                    
            if not post_button:
                
                # Tentative de recherche alternative - boutons quelconques
                print("Tentative de recherche alternative de boutons...")
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    try:
                        btn_text = btn.text.lower()
                        btn_class = btn.get_attribute("class").lower()
                        if ("post" in btn_text or "publish" in btn_text or "publier" in btn_text or 
                            "post" in btn_class or "publish" in btn_class or "submit" in btn_class):
                            print(f"Bouton alternatif trouvé: {btn_text}, Classe: {btn_class}")
                            post_button = btn
                            break
                    except:
                        continue
                
                # Si toujours pas de bouton trouvé
                if not post_button:
                    print("Aucun bouton de publication trouvé après recherche étendue.")
                    return False
                
            print("Publication de la vidéo...")
            try:
                # Essayer d'abord avec le clic Selenium standard
                try:
                    post_button.click()
                    print("Clic Selenium standard réussi")
                except Exception as e:
                    print(f"Clic standard échoué: {e}")
                    # Essayer avec JavaScript si le clic standard échoue
                    try:
                        self.driver.execute_script("arguments[0].click();", post_button)
                        print("Clic JavaScript réussi")
                    except Exception as js_e:
                        print(f"Clic JavaScript échoué: {js_e}")
                        # Dernier recours: ActionChains
                        try:
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(self.driver)
                            actions.move_to_element(post_button).click().perform()
                            print("Clic ActionChains réussi")
                        except Exception as ac_e:
                            print(f"Clic ActionChains échoué: {ac_e}")
                            print("Tous les types de clics ont échoué")
                            
                            # Suggestion à l'utilisateur
                            print("\nVeuillez essayer de cliquer manuellement sur le bouton de publication.")
                            print("Le navigateur est maintenant sous votre contrôle.")
                            self.auto_close = False
                            return False
            except Exception as e:
                print(f"Erreur générale lors du clic: {e}")
                return False
            
            # Attendre la confirmation de publication
            print("Attente de la confirmation de publication...")
            time.sleep(10)  # Attendre que la publication commence
            
            # Vérifier si nous sommes redirigés vers une autre page (signe potentiel de succès)
            tries = 0
            max_tries = 12  # Attendre jusqu'à 2 minutes (12 x 10 secondes)
            success = False
            
            while tries < max_tries:
                # Chercher des messages de succès
                # ✅ 1. Vérification d'une redirection vers /content (TikTok Studio success page)
                current_url = self.driver.current_url
                if "/content" in current_url:
                    print("Redirection vers la page de contenu détectée : Publication réussie !")
                    success = True
                    break

                # ✅ 2. (Optionnel) Maintien de l'ancienne détection textuelle pour sécurité
                success_elements = self.driver.find_elements(By.XPATH, 
                    "//div[contains(text(), 'Your video is') or contains(text(), 'Votre vidéo') or contains(text(), 'success')]")
                if success_elements:
                    print("Message de succès détecté!")
                    success = True
                    break

                    
                time.sleep(10)
                tries += 1
                print(f"Toujours en attente de confirmation... ({tries}/{max_tries})")
            
            # Si nous arrivons ici, demander à l'utilisateur si la publication a réussi
            if not success:
                print("\nLa confirmation automatique a échoué. Veuillez vérifier manuellement.")
                print("La vidéo a-t-elle été publiée avec succès? (o/n)")
                
                response = input("Votre réponse (o/n): ").strip().lower()
                success = response == 'o' or response == 'oui' or response == 'y' or response == 'yes'
            
            # Attendre explicitement avant de fermer
            print("\nPublication terminée. Attente avant de fermer le navigateur...")
            print("Appuyez sur Entrée pour fermer le navigateur ou tapez 'garder' pour le garder ouvert.")
            
            user_input = input("Votre choix (Entrée/garder): ").strip().lower()
            if user_input == "garder":
                print("Le navigateur restera ouvert. Vous pouvez le fermer manuellement plus tard.")
                self.auto_close = False
                return success
            else:
                self.auto_close = True
                return success
            
        except TimeoutException as e:
            print(f"Timeout lors de la publication: {e}")
            self.driver.save_screenshot("timeout_error.png")
            print(f"Une capture d'écran a été enregistrée dans 'timeout_error.png'")
            return False
        except Exception as e:
            print(f"Erreur lors de la publication: {e}")
            self.driver.save_screenshot("general_error.png")
            print(f"Une capture d'écran a été enregistrée dans 'general_error.png'")
            return False
    
    def close(self):
        """Ferme le navigateur et nettoie les ressources"""
        if hasattr(self, 'auto_close') and not self.auto_close:
            print("Navigateur laissé ouvert à la demande de l'utilisateur.")
            return
            
        if self.driver:
            self.driver.quit()
            print("Navigateur fermé")
    
    def __del__(self):
        """Destructeur pour assurer que le navigateur est fermé"""
        if hasattr(self, 'auto_close') and not self.auto_close:
            return
        self.close()


# Exemple d'utilisation
if __name__ == "__main__":
    # Tester la connexion
    publisher = TikTokPublisher()
    if publisher.authenticate():
        print("Connexion réussie!")
    else:
        print("Échec de la connexion.")
    publisher.close()
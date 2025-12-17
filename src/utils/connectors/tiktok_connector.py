# publishers/tiktok_connector.py
import os
import time
import pickle
import logging
import uuid
import fcntl
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

logger = logging.getLogger("TikSimPro.Connector")

# Global lock file to prevent concurrent Chrome sessions
CHROME_LOCK_FILE = "/tmp/tiksimpro_chrome.lock"

class TikTokConnector:
    """Gère l’authentification à TikTok via Selenium & cookies."""

    def __init__(self, cookies_file: str = "tiktok_cookies.pkl", headless: bool = False):
        self.cookies_file = cookies_file
        self.headless = headless
        self.driver = None
        self.is_authenticated = False

        # Chrome profile isolation
        self._lock_file = None
        self._profile_path = None

        # Clean up stale Chrome artifacts on init
        self._cleanup_stale_chrome_artifacts()

    def _cleanup_stale_chrome_artifacts(self):
        """Clean up stale Chrome temp files that can cause conflicts"""
        import glob
        patterns = [
            "/tmp/.com.google.Chrome.*",
            "/tmp/tiksimpro_chrome_tiktok_*",
            "/tmp/scoped_dir*",
            os.path.expanduser("~/.tiksimpro/chrome_tiktok_*")
        ]
        for pattern in patterns:
            for path in glob.glob(pattern):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        os.remove(path)
                except:
                    pass

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

    def _acquire_chrome_lock(self) -> bool:
        """Acquire global lock to prevent concurrent Chrome sessions"""
        try:
            self._lock_file = open(CHROME_LOCK_FILE, 'w')
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX)
            logger.debug("Chrome lock acquired")
            return True
        except Exception as e:
            logger.error(f"Failed to acquire Chrome lock: {e}")
            return False

    def _release_chrome_lock(self):
        """Release the global Chrome lock"""
        try:
            if self._lock_file:
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
                self._lock_file.close()
                self._lock_file = None
                logger.debug("Chrome lock released")
        except Exception as e:
            logger.warning(f"Error releasing Chrome lock: {e}")

    def _cleanup_profile(self):
        """Clean up the temporary Chrome profile directory"""
        try:
            if self._profile_path and os.path.exists(self._profile_path):
                shutil.rmtree(self._profile_path, ignore_errors=True)
                logger.debug(f"Cleaned up Chrome profile: {self._profile_path}")
                self._profile_path = None
        except Exception as e:
            logger.warning(f"Error cleaning up Chrome profile: {e}")

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

            # Clean up any stale Chrome artifacts before starting
            self._cleanup_stale_chrome_artifacts()

            # Check if we should use remote Selenium (Docker)
            use_remote = os.environ.get("USE_SELENIUM_DOCKER", "false").lower() == "true"

            if not use_remote:
                # Create a unique profile directory in home to avoid /tmp conflicts with Docker
                unique_id = str(uuid.uuid4())[:8]
                self._profile_path = os.path.expanduser(f"~/.tiksimpro/chrome_tiktok_{unique_id}")
                os.makedirs(self._profile_path, exist_ok=True)
                chrome_options.add_argument(f"--user-data-dir={self._profile_path}")
                logger.info(f"Using isolated Chrome profile: {self._profile_path}")
            else:
                self._profile_path = None
                logger.info("Using Selenium Docker - no custom profile")

            # Options de base pour Linux
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--ignore-certificate-errors-spki-list")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI,VizDisplayCompositor")
            
            # Mode headless si demandé
            if self.headless:
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
            
            # Agent utilisateur mobile pour meilleure compatibilité
            mobile_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/85.0.4183.109 Mobile/15E148 Safari/604.1"
            chrome_options.add_argument(f"--user-agent={mobile_user_agent}")
            
            # Désactiver les notifications
            chrome_options.add_argument("--disable-notifications")
            
            # Options pour éviter la détection comme bot
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Spécifier le chemin du binaire Google Chrome
            chrome_options.binary_location = "/usr/bin/google-chrome-stable"
            
            # Check if we should use remote Selenium (Docker)
            use_remote = os.environ.get("USE_SELENIUM_DOCKER", "false").lower() == "true"

            if use_remote:
                logger.info("Connexion au Selenium Docker (noVNC disponible sur port 7900)...")
                self.driver = webdriver.Remote(
                    command_executor="http://localhost:4444/wd/hub",
                    options=chrome_options
                )
            else:
                logger.info("Initialisation du webdriver Chrome local...")
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
            self._cleanup_profile()
            self._release_chrome_lock()
            self.driver = None
            return False

    def close(self):
        """Close browser and cleanup resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except:
            pass
        self._cleanup_profile()
        self._release_chrome_lock()

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
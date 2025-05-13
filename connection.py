"""
Script simple pour se connecter à TikTok et sauvegarder les cookies.
À utiliser avant de poster des vidéos.
"""

from tiktok_publisher import TikTokPublisher

def connect_to_tiktok():
    """Se connecte à TikTok et sauvegarde les cookies pour une utilisation future"""
    print("="*80)
    print("CONNEXION À TIKTOK")
    print("="*80)
    print("Ce script va ouvrir une fenêtre de navigateur pour vous permettre de vous connecter à TikTok.")
    print("Une fois connecté, les cookies seront sauvegardés pour les futures utilisations.")
    
    publisher = TikTokPublisher()
    
    if publisher.authenticate():
        print("\n" + "="*80)
        print("CONNEXION RÉUSSIE!")
        print("Vos cookies ont été sauvegardés dans 'tiktok_cookies.pkl'")
        print("Vous pouvez maintenant utiliser les scripts de publication sans vous reconnecter.")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("ÉCHEC DE LA CONNEXION")
        print("Veuillez vérifier votre connexion Internet et réessayer.")
        print("="*80)
    
    publisher.close()

if __name__ == "__main__":
    connect_to_tiktok()
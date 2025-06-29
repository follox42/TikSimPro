# cookie-api/app.py
"""
API Simple de Gestion des Cookies pour TikSimPro
Gère les cookies d'authentification pour TikTok, YouTube, Instagram
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import os
import sqlite3
from datetime import datetime, timedelta
import hashlib
import base64

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_PATH = '/app/data/cookies.db'
DATA_DIR = '/app/data'

# Créer le dossier data si nécessaire
os.makedirs(DATA_DIR, exist_ok=True)

# ========================================
# BASE DE DONNÉES SQLITE SIMPLE
# ========================================

def init_database():
    """Initialise la base de données SQLite"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Table des comptes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            platform TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table des cookies
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cookies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            cookie_data TEXT NOT NULL,
            expires_at TIMESTAMP,
            is_valid BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')
    
    # Table des stats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS upload_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            video_path TEXT,
            upload_status TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Connexion à la base de données"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ========================================
# ROUTES API
# ========================================

@app.route('/')
def index():
    """Page d'accueil avec interface simple"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>TikSimPro Cookie Manager</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .account { display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #eee; }
        .status-active { color: green; font-weight: bold; }
        .status-expired { color: red; font-weight: bold; }
        button { background: #007cba; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #005fa3; }
        input, textarea { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍪 TikSimPro Cookie Manager</h1>
            <p>Gestion des cookies d'authentification pour vos comptes</p>
        </div>
        
        <div class="section">
            <h2>📱 Comptes Configurés</h2>
            <div id="accounts"></div>
        </div>
        
        <div class="section">
            <h2>➕ Ajouter un Compte</h2>
            <input type="text" id="accountName" placeholder="Nom du compte (ex: viral_account_1)">
            <select id="platform">
                <option value="tiktok">TikTok</option>
                <option value="youtube">YouTube</option>
                <option value="instagram">Instagram</option>
            </select>
            <button onclick="addAccount()">Ajouter</button>
        </div>
        
        <div class="section">
            <h2>🍪 Upload Cookies</h2>
            <select id="cookieAccount"></select>
            <select id="cookiePlatform">
                <option value="tiktok">TikTok</option>
                <option value="youtube">YouTube</option>
                <option value="instagram">Instagram</option>
            </select>
            <textarea id="cookieData" placeholder="Collez vos cookies ici (format JSON)"></textarea>
            <button onclick="uploadCookies()">Upload Cookies</button>
        </div>
        
        <div class="section">
            <h2>📊 Statistiques</h2>
            <div id="stats"></div>
        </div>
    </div>

    <script>
        // Charger les comptes au démarrage
        loadAccounts();
        loadStats();
        
        async function loadAccounts() {
            try {
                const response = await fetch('/api/accounts');
                const accounts = await response.json();
                
                const accountsDiv = document.getElementById('accounts');
                const cookieAccountSelect = document.getElementById('cookieAccount');
                
                accountsDiv.innerHTML = '';
                cookieAccountSelect.innerHTML = '';
                
                accounts.forEach(account => {
                    const statusClass = account.cookie_valid ? 'status-active' : 'status-expired';
                    const statusText = account.cookie_valid ? 'Cookie OK' : 'Cookie Expiré';
                    
                    accountsDiv.innerHTML += `
                        <div class="account">
                            <span><strong>${account.name}</strong> - ${account.platform}</span>
                            <span class="${statusClass}">${statusText}</span>
                        </div>
                    `;
                    
                    cookieAccountSelect.innerHTML += `<option value="${account.id}">${account.name} - ${account.platform}</option>`;
                });
            } catch (error) {
                console.error('Erreur:', error);
            }
        }
        
        async function addAccount() {
            const name = document.getElementById('accountName').value;
            const platform = document.getElementById('platform').value;
            
            try {
                const response = await fetch('/api/accounts', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name, platform})
                });
                
                if (response.ok) {
                    alert('Compte ajouté avec succès!');
                    loadAccounts();
                    document.getElementById('accountName').value = '';
                } else {
                    alert('Erreur lors de l\\'ajout du compte');
                }
            } catch (error) {
                alert('Erreur: ' + error.message);
            }
        }
        
        async function uploadCookies() {
            const accountId = document.getElementById('cookieAccount').value;
            const platform = document.getElementById('cookiePlatform').value;
            const cookieData = document.getElementById('cookieData').value;
            
            try {
                const cookies = JSON.parse(cookieData);
                
                const response = await fetch(`/api/accounts/${accountId}/cookies`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        platform: platform,
                        cookie_data: cookies
                    })
                });
                
                if (response.ok) {
                    alert('Cookies uploadés avec succès!');
                    loadAccounts();
                    document.getElementById('cookieData').value = '';
                } else {
                    alert('Erreur lors de l\\'upload des cookies');
                }
            } catch (error) {
                alert('Erreur format JSON: ' + error.message);
            }
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats/dashboard');
                const stats = await response.json();
                
                document.getElementById('stats').innerHTML = `
                    <p><strong>Comptes totaux:</strong> ${stats.total_accounts || 0}</p>
                    <p><strong>Comptes actifs:</strong> ${stats.active_accounts || 0}</p>
                    <p><strong>Uploads récents:</strong> ${stats.recent_uploads || 0}</p>
                    <p><strong>Cookies expirés:</strong> ${stats.expired_cookies || 0}</p>
                `;
            } catch (error) {
                console.error('Erreur stats:', error);
            }
        }
        
        // Refresh automatique toutes les 30 secondes
        setInterval(() => {
            loadAccounts();
            loadStats();
        }, 30000);
    </script>
</body>
</html>
    ''')

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Récupère tous les comptes"""
    conn = get_db_connection()
    accounts = conn.execute('''
        SELECT a.*, 
               CASE WHEN c.is_valid = 1 AND (c.expires_at IS NULL OR c.expires_at > datetime('now')) 
                    THEN 1 ELSE 0 END as cookie_valid
        FROM accounts a
        LEFT JOIN cookies c ON a.id = c.account_id AND c.platform = a.platform
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(account) for account in accounts])

@app.route('/api/accounts', methods=['POST'])
def create_account():
    """Crée un nouveau compte"""
    data = request.json
    
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO accounts (name, platform) VALUES (?, ?)',
            (data['name'], data['platform'])
        )
        conn.commit()
        account_id = conn.lastrowid
        conn.close()
        
        return jsonify({'message': 'Compte créé', 'id': account_id}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Compte déjà existant'}), 400

@app.route('/api/accounts/<int:account_id>/cookies', methods=['GET'])
def get_cookies(account_id):
    """Récupère les cookies d'un compte"""
    conn = get_db_connection()
    cookies = conn.execute(
        'SELECT platform, expires_at, is_valid, created_at FROM cookies WHERE account_id = ? AND is_valid = 1',
        (account_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(cookie) for cookie in cookies])

@app.route('/api/accounts/<int:account_id>/cookies', methods=['POST'])
def upload_cookies(account_id):
    """Upload des nouveaux cookies pour un compte"""
    data = request.json
    
    conn = get_db_connection()
    
    # Désactiver les anciens cookies
    conn.execute(
        'UPDATE cookies SET is_valid = 0 WHERE account_id = ? AND platform = ?',
        (account_id, data['platform'])
    )
    
    # Ajouter les nouveaux cookies
    cookie_json = json.dumps(data['cookie_data'])
    expires_at = data.get('expires_at')
    
    conn.execute('''
        INSERT INTO cookies (account_id, platform, cookie_data, expires_at) 
        VALUES (?, ?, ?, ?)
    ''', (account_id, data['platform'], cookie_json, expires_at))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Cookies mis à jour'}), 200

@app.route('/api/accounts/<int:account_id>/cookies/get', methods=['GET'])
def get_account_cookies_for_use(account_id):
    """Récupère les cookies valides pour utilisation par TikSimPro"""
    platform = request.args.get('platform', 'tiktok')
    
    conn = get_db_connection()
    cookie_row = conn.execute('''
        SELECT cookie_data FROM cookies 
        WHERE account_id = ? AND platform = ? AND is_valid = 1
        AND (expires_at IS NULL OR expires_at > datetime('now'))
        ORDER BY created_at DESC LIMIT 1
    ''', (account_id, platform)).fetchone()
    conn.close()
    
    if cookie_row:
        cookie_data = json.loads(cookie_row['cookie_data'])
        return jsonify({'cookies': cookie_data, 'valid': True})
    else:
        return jsonify({'cookies': None, 'valid': False}), 404

@app.route('/api/stats/dashboard', methods=['GET'])
def dashboard_stats():
    """Statistiques pour le dashboard"""
    conn = get_db_connection()
    
    total_accounts = conn.execute('SELECT COUNT(*) as count FROM accounts').fetchone()['count']
    active_accounts = conn.execute('SELECT COUNT(*) as count FROM accounts WHERE status = "active"').fetchone()['count']
    
    # Uploads récents (24h)
    recent_uploads = conn.execute('''
        SELECT COUNT(*) as count FROM upload_stats 
        WHERE uploaded_at > datetime('now', '-1 day')
    ''').fetchone()['count']
    
    # Cookies expirés
    expired_cookies = conn.execute('''
        SELECT COUNT(*) as count FROM cookies 
        WHERE is_valid = 1 AND expires_at < datetime('now')
    ''').fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'total_accounts': total_accounts,
        'active_accounts': active_accounts,
        'recent_uploads': recent_uploads,
        'expired_cookies': expired_cookies,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/upload/log', methods=['POST'])
def log_upload():
    """Log un upload de vidéo"""
    data = request.json
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO upload_stats (account_id, platform, video_path, upload_status, views, likes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.get('account_id'),
        data.get('platform'),
        data.get('video_path'),
        data.get('upload_status', 'success'),
        data.get('views', 0),
        data.get('likes', 0)
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Upload logged'}), 200

# ========================================
# UTILITAIRES
# ========================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check de santé de l'API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if os.path.exists(DATABASE_PATH) else 'disconnected'
    })

@app.route('/api/backup', methods=['POST'])
def backup_cookies():
    """Sauvegarde des cookies"""
    backup_dir = '/app/data/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'{backup_dir}/cookies_backup_{timestamp}.json'
    
    conn = get_db_connection()
    accounts = conn.execute('SELECT * FROM accounts').fetchall()
    cookies = conn.execute('SELECT * FROM cookies WHERE is_valid = 1').fetchall()
    conn.close()
    
    backup_data = {
        'timestamp': timestamp,
        'accounts': [dict(account) for account in accounts],
        'cookies': [dict(cookie) for cookie in cookies]
    }
    
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    return jsonify({'message': 'Backup created', 'file': backup_file})

if __name__ == '__main__':
    init_database()
    app.run(host='0.0.0.0', port=5000, debug=True)


# ========================================
# cookie-api/Dockerfile
# ========================================

FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances
RUN pip install flask flask-cors

# Créer les dossiers
RUN mkdir -p /app/data /app/logs

# Copier l'application
COPY cookie-api/app.py .

# Exposer le port
EXPOSE 5000

# Commande de démarrage
CMD ["python", "app.py"]
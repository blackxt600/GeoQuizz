# Guide de Déploiement - GeoQuizz

Ce guide explique comment déployer GeoQuizz sur différentes plateformes.

## Déploiement Local

### Méthode 1 : Exécution directe
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python app.py
```

Accéder à : http://localhost:5000

### Méthode 2 : Script automatique (Windows)
```bash
start.bat
```

## Déploiement avec Docker

### Build et Run simple
```bash
# Build l'image
docker build -t geoquizz .

# Run le conteneur
docker run -d -p 5000:5000 -v $(pwd)/data:/app/data geoquizz
```

### Avec Docker Compose (recommandé)
```bash
# Définir le chemin de vos photos
export PHOTOS_PATH=/chemin/vers/vos/photos  # Linux/Mac
set PHOTOS_PATH=C:\Photos  # Windows

# Démarrer
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

## Déploiement sur serveur Linux

### Avec systemd

1. Créer le fichier `/etc/systemd/system/geoquizz.service` :

```ini
[Unit]
Description=GeoQuizz Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/geoquizz
Environment="PATH=/var/www/geoquizz/venv/bin"
ExecStart=/var/www/geoquizz/venv/bin/python app.py

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Activer et démarrer :
```bash
sudo systemctl daemon-reload
sudo systemctl enable geoquizz
sudo systemctl start geoquizz
sudo systemctl status geoquizz
```

### Avec Nginx (reverse proxy)

1. Installer Nginx :
```bash
sudo apt update
sudo apt install nginx
```

2. Configurer `/etc/nginx/sites-available/geoquizz` :
```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Pour les gros fichiers photos
    client_max_body_size 50M;
}
```

3. Activer :
```bash
sudo ln -s /etc/nginx/sites-available/geoquizz /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Avec Gunicorn (production)

1. Installer Gunicorn :
```bash
pip install gunicorn
```

2. Créer `gunicorn_config.py` :
```python
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
```

3. Lancer :
```bash
gunicorn -c gunicorn_config.py app:app
```

4. Modifier le service systemd :
```ini
ExecStart=/var/www/geoquizz/venv/bin/gunicorn -c gunicorn_config.py app:app
```

## Déploiement Cloud

### Heroku

1. Créer `Procfile` :
```
web: gunicorn app:app
```

2. Créer `runtime.txt` :
```
python-3.13.0
```

3. Déployer :
```bash
heroku login
heroku create votre-app-geoquizz
git push heroku main
heroku open
```

### Railway.app

1. Connecter votre repo GitHub
2. Railway détecte automatiquement Python
3. Ajouter les variables d'environnement si nécessaire
4. Déploiement automatique

### Render.com

1. Connecter le repo GitHub
2. Type de service : Web Service
3. Build Command : `pip install -r requirements.txt`
4. Start Command : `gunicorn app:app`
5. Déployer

### DigitalOcean App Platform

1. Connecter le repo GitHub
2. Sélectionner Python
3. Configurer :
   - Build Command : `pip install -r requirements.txt`
   - Run Command : `gunicorn --workers 2 --bind 0.0.0.0:$PORT app:app`
4. Déployer

### VPS (Serveur dédié)

Pour un VPS Ubuntu/Debian :

```bash
# Installer les dépendances
sudo apt update
sudo apt install python3.13 python3-pip python3-venv nginx

# Cloner le projet
cd /var/www
sudo git clone https://github.com/VOTRE_USERNAME/GeoQuizz.git geoquizz
cd geoquizz

# Configurer l'environnement
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Configurer systemd et nginx (voir sections ci-dessus)

# Configurer le firewall
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Configuration SSL/HTTPS

### Avec Let's Encrypt (gratuit)

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir un certificat
sudo certbot --nginx -d votre-domaine.com

# Renouvellement automatique (déjà configuré)
sudo certbot renew --dry-run
```

## Variables d'environnement

Pour la production, créer un fichier `.env` :

```bash
FLASK_ENV=production
SECRET_KEY=votre-cle-secrete-aleatoire
MAX_PHOTOS=1000
ALLOWED_PHOTO_EXTENSIONS=jpg,jpeg,png,tiff
```

Charger avec python-dotenv :
```bash
pip install python-dotenv
```

## Performance et Optimisation

### Cache des photos
Ajouter un cache pour les miniatures des photos.

### CDN
Utiliser un CDN (Cloudflare, AWS CloudFront) pour servir les photos.

### Base de données
Si vous avez beaucoup d'utilisateurs, migrer de JSON vers PostgreSQL ou MongoDB.

### Load Balancing
Pour une grande échelle, utiliser plusieurs instances avec un load balancer.

## Monitoring

### Logs
```bash
# Voir les logs en temps réel
journalctl -u geoquizz -f

# Logs Docker
docker-compose logs -f geoquizz
```

### Uptime Monitoring
- UptimeRobot (gratuit)
- Pingdom
- StatusCake

### Application Monitoring
- Sentry pour le tracking d'erreurs
- New Relic pour les performances
- Prometheus + Grafana

## Backup

### Backup automatique des données

Script `backup.sh` :
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/geoquizz"
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/
# Garder seulement les 7 derniers backups
find $BACKUP_DIR -name "data_*.tar.gz" -mtime +7 -delete
```

Ajouter au cron :
```bash
crontab -e
# Backup quotidien à 2h du matin
0 2 * * * /chemin/vers/backup.sh
```

## Sécurité

### Bonnes pratiques

1. **Changer la SECRET_KEY** en production
2. **Désactiver le mode DEBUG** (FLASK_ENV=production)
3. **Limiter l'accès aux fichiers** (vérifier les permissions)
4. **Rate limiting** (Flask-Limiter)
5. **CORS** configuré correctement
6. **Validation des entrées** utilisateur
7. **HTTPS** obligatoire en production
8. **Firewall** configuré (ufw, iptables)

### Rate Limiting

Installer Flask-Limiter :
```bash
pip install Flask-Limiter
```

Ajouter dans `app.py` :
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

## Troubleshooting

### L'application ne démarre pas
```bash
# Vérifier les logs
journalctl -u geoquizz -n 50

# Vérifier le port
sudo netstat -tulpn | grep 5000

# Vérifier les permissions
ls -la /var/www/geoquizz
```

### Erreur de permission pour les photos
```bash
# Donner les bonnes permissions
sudo chown -R www-data:www-data /var/www/geoquizz
sudo chmod -R 755 /var/www/geoquizz
```

### Problème de mémoire
```bash
# Augmenter la mémoire du serveur
# Ou réduire le nombre de workers Gunicorn
```

## Mise à jour

Pour mettre à jour l'application en production :

```bash
cd /var/www/geoquizz
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart geoquizz
```

## Support

Pour toute question sur le déploiement, ouvrez une issue sur GitHub.

# Production Deployment

This deploys FlashOfThought as two Docker services on one server:

- `api`: FastAPI on port `8000` inside Docker
- `ui`: Streamlit on `127.0.0.1:8501`

User data is persisted on the host:

- `prod-data/users.sqlite3`
- `prod-data/chroma_db/`
- `prod-static/uploads/` for local static fallback

## Server Setup

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin nginx certbot python3-certbot-nginx
sudo systemctl enable docker
sudo systemctl start docker
```

## Deploy

```bash
cd /opt
git clone https://github.com/MaddieMo1/Flash-Of-Thought.git
cd Flash-Of-Thought

cp .env.production.example .env
nano .env

mkdir -p prod-data/chroma_db prod-static/uploads
docker compose up -d --build
docker compose ps
```

## Nginx

Copy `deploy/nginx.conf.example` and replace `your-domain.com`.

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/flashofthought
sudo nano /etc/nginx/sites-available/flashofthought
sudo ln -s /etc/nginx/sites-available/flashofthought /etc/nginx/sites-enabled/flashofthought
sudo nginx -t
sudo systemctl reload nginx
```

Enable HTTPS:

```bash
sudo certbot --nginx -d your-domain.com
```

## Logs and Updates

```bash
docker compose logs -f
git pull
docker compose up -d --build
```

## Backup

Back up `prod-data/` regularly:

```bash
tar -czf flashofthought-backup-$(date +%F).tar.gz prod-data
```

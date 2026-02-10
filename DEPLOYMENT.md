# 🚀 Deployment Guide

This guide covers how to host the **HiTek OSINT** API on a VPS and the frontend on **Cloudflare Pages**.

---

## 🛠 Prerequisites

1.  **VPS** (Ubuntu 20.04+ recommended) with Python 3.10+ installed.
2.  **Domain Name** (e.g., `hitek-osint.com`) pointing to your VPS IP.
3.  **Cloudflare Account** for hosting the frontend.
4.  **GitHub Account** to fork this repository.

---

## 🏗 Part 1: API Setup (VPS)

### 1. Connect to VPS
SSH into your server:
```bash
ssh root@your-vps-ip
```

### 2. Prepare System & Database
Make sure you have your 1.78B row `users.db` file ready. Let's assume it's at `/data/users.db`.

```bash
# Update system
apt update && apt upgrade -y
apt install python3-pip python3-venv git nginx -y

# Create directory for DB (if not exists)
mkdir -p /data
# (Upload your users.db to /data/users.db using SCP or SFTP)
```

### 3. Clone Repository
```bash
cd /opt
git clone https://github.com/Unknown-2829/Hitek_db_api-web.git
cd Hitek_db_api-web
```

### 4. Setup Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Test the API
Run manually to check if it works:
```bash
export DB_PATH="/data/users.db"
export API_PORT=8000
python -m api.main
```
If it says "Application startup complete", press `Ctrl+C` to stop.

### 6. Setup Systemd Service (Keep it running)
Create a service file:
```bash
nano /etc/systemd/system/hitek-api.service
```

Paste this content (adjust paths if needed):
```ini
[Unit]
Description=HiTek OSINT API
After=network.target

[Service]
User=root
WorkingDirectory=/opt/Hitek_db_api-web
Environment="DB_PATH=/data/users.db"
Environment="API_PORT=8000"
Environment="PATH=/opt/Hitek_db_api-web/venv/bin"
ExecStart=/opt/Hitek_db_api-web/venv/bin/python -m api.main
Restart=always

[Install]
WantedBy=multi-user.target
```

Start and enable the service:
```bash
systemctl daemon-reload
systemctl start hitek-api
systemctl enable hitek-api
```

### 7. Setup Nginx (Reverse Proxy & SSL)
Allow Nginx to forward requests to port 8000.

```bash
nano /etc/nginx/sites-available/hitek_api
```

Paste this configuration:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;  # Replace with your API domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and restart Nginx:
```bash
ln -s /etc/nginx/sites-available/hitek_api /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

**🔒 Optional: Free SSL (HTTPS) with Certbot**
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d api.yourdomain.com
```

✅ **Your API is now live at:** `https://api.yourdomain.com`

---

## 🌐 Part 2: Frontend Setup (Cloudflare Pages)

### 1. Prepare Configuration
1.  Open `website/app.js` in your local repo.
2.  Find this line at the top:
    ```javascript
    const API_BASE = window.location.hostname === 'localhost' ...
        ? 'http://localhost:8000'
        : 'https://your-api-domain.com';  // <-- CHANGE THIS
    ```
3.  Replace `'https://your-api-domain.com'` with your actual API URL (e.g., `'https://api.hitek-osint.com'`).
4.  Commit and push this change to GitHub.

### 2. Deploy on Cloudflare
1.  Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/).
2.  Go to **Compute (Workers & Pages)** > **Create Application**.
3.  Select **Pages** > **Connect to Git**.
4.  Select your repo (`Hitek_db_api-web`).
5.  **Build Settings:**
    *   **Framework Preset:** `None` (it's a static HTML site)
    *   **Build Command:** (Leave empty)
    *   **Build Output Directory:** `website`  <-- IMPORTANT!
6.  Click **Save and Deploy**.

Cloudflare will build and deploy your site in seconds.

✅ **Your Website is live at:** `https://hitek-db-api-web.pages.dev` (or add your custom domain in Cloudflare settings).

---

## 🔄 Updates

To update the frontend:
- Just push changes to GitHub. Cloudflare updates automatically.

To update the API:
```bash
cd /opt/Hitek_db_api-web
git pull
systemctl restart hitek-api
```

# 🚀 Deployment Guide

This guide covers how to host the **Phantom OSINT** API on a VPS and the frontend on **Cloudflare Pages**.

---

## 🛠 Prerequisites

1.  **VPS** (Ubuntu 20.04+ recommended) with Python 3.10+ installed.
2.  **Cloudflare Account** for hosting the frontend.
3.  **GitHub Account** to fork this repository.

---

## 🏗 Part 1: API Setup (VPS)

### 1. Connect to VPS
SSH into your server (using the IP from your screenshot):
```bash
ssh root@20.204.232.146
```

### 2. Setup Code & Env
```bash
# Clone the repo
git clone https://github.com/Unknown-2829/Hitek_db_api-web.git
cd Hitek_db_api-web

# Setup Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Start the API (Easiest Way)
We included a helper script `run.sh`:

```bash
chmod +x run.sh
./run.sh
```
*Make sure your `users.db` is at `/data/users.db`. If not, edit `run.sh`.*

### 4. Expose to Web (Nginx)
Since you opened Port 80, let's use Nginx to safely forward traffic to the API.

```bash
# Install Nginx
apt install nginx -y

# Configure using our example
cp nginx.conf.example /etc/nginx/sites-available/hitek_api
nano /etc/nginx/sites-available/hitek_api
# CHANGE 'server_name' to: 20.204.232.146
```

Enable it:
```bash
ln -s /etc/nginx/sites-available/hitek_api /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
systemctl restart nginx
```

✅ **API is live at:** `http://20.204.232.146`

---

## 🌐 Part 2: Frontend Setup (Cloudflare Pages)

### 1. Update Frontend Config (IMPORTANT)
Since your API is HTTP (IP only), you must tell the frontend where to look.

1.  Edit `website/app.js` locally.
2.  Change `API_BASE` to your IP:
    ```javascript
    const API_BASE = 'http://20.204.232.146';
    ```
3.  **Commit and push** this change to GitHub.

### 2. Cloudflare Build Settings
1.  Go to **Cloudflare Dashboard** > **Pages** > **Connect to Git**.
2.  Select `Hitek_db_api-web`.
3.  **Use these settings:**
    *   **Framework Preset:** `None`
    *   **Build Command:** `(Leave Empty)`
    *   **Build Output Directory:** `website`
    *   **Root Directory:** `(Leave Empty)`

4.  Click **Save and Deploy**.

---

## 🌐 Part 3: Domain Setup (unknowns.app)

Since you own **unknowns.app**, let's set it up properly for HTTPS.

### 1. Cloudflare DNS Settings
Go to Cloudflare Dashboard > **DNS** for `unknowns.app`. Add these records:

| Type | Name | Content (Value) | Proxy Status | Purpose |
|------|------|-----------------|--------------|---------|
| **A** | `api` | `20.204.232.146` | **DNS Only** (Grey Cloud) | For API (VPS) |
| **CNAME**| `osint` | `hitek-osint.pages.dev` | **Proxied** (Orange Cloud) | For Website |

*(Replace `hitek-osint.pages.dev` with your actual Cloudflare Pages URL)*

### 2. Setup SSL on VPS (for API)
Now that `api.unknowns.app` points to your VPS, let's enable HTTPS.

SSH into VPS:
```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Edit Nginx setup
nano /etc/nginx/sites-available/hitek_api
# Change 'server_name' to: api.unknowns.app
```

Get the certificate:
```bash
certbot --nginx -d api.unknowns.app
systemctl restart nginx
```

✅ **API is now SECURE:** `https://api.unknowns.app`

### 3. Final Frontend Update
Now update `website/app.js` to use the secure domain:

```javascript
const API_BASE = 'https://api.unknowns.app';
```

Commit and push. Cloudflare will redeploy automatically.
🚀 **Result:**
- Website: `https://unknowns.app`
- API: `https://api.unknowns.app`
- **No Mixed Content Errors!**

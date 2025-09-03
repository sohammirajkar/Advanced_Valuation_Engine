# 🚀 Quick Start - Railway Deployment

## TL;DR - Deploy in 5 Steps

### 1️⃣ Generate Configs

```bash
cd deployment/scripts
python deploy_helper.py config
```

### 2️⃣ Deploy Redis

- Railway Dashboard → New Service → Database → Redis
- Copy `REDIS_URL`

### 3️⃣ Deploy Backend  

- New Service → GitHub → Your repo
- Copy `deployment/configs/railway-backend.json` → `railway.json`
- Set env: `REDIS_URL = <redis-url-from-step-2>`
- Copy generated backend URL

### 4️⃣ Deploy Worker

- New Service → GitHub → Same repo  
- Copy `deployment/configs/railway-worker.json` → `railway.json`
- Set env: `REDIS_URL = <same-redis-url>`

### 5️⃣ Update Frontend

- Go to existing frontend service
- Copy `deployment/configs/railway-frontend.json` → `railway.json`  
- Set env: `API_URL = <backend-url-from-step-3>`

## ✅ Done

Visit your frontend URL - you should see:

- ✅ "Connected to API" message
- Working valuation calculations

---

**Need help?** See full guide: [`deployment/README.md`](README.md)

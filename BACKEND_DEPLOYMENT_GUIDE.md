# 🚀 Backend Deployment Guide for Railway

## Overview

Your valuation engine backend consists of three services that need to be deployed:
1. **Redis** - Message broker and cache
2. **FastAPI Backend** - Main API server
3. **Celery Worker** - Background task processor

## 📋 Step-by-Step Deployment

### Step 1: Deploy Redis Service

1. **Go to Railway**: https://railway.app
2. **Create New Project** or use existing one
3. **Add Redis Service**:
   - Click "New Service"
   - Select "Database" → "Redis"
   - Wait for deployment

4. **Get Redis Connection URL**:
   - Go to Redis service → Variables tab
   - Copy the `REDIS_URL` (looks like: `redis://default:password@host:port`)

### Step 2: Deploy FastAPI Backend

1. **Create New Service**:
   - Click "New Service" → "GitHub Repo"
   - Select your repository: `sohammirajkar/Advanced_Valuation_Engine`

2. **Configure Backend Service**:
   - **Service Name**: `valuation-backend` (or similar)
   - **Root Directory**: Keep as root (empty)
   - **Build Command**: Leave empty (auto-detected)
   - **Start Command**: `python start_backend.py`

3. **Set Environment Variables**:
   ```
   REDIS_URL=redis://default:password@host:port
   ```
   (Use the URL from Step 1)

4. **Deploy**:
   - Railway will automatically build and deploy
   - Note the generated URL (e.g., `https://valuation-backend-production.up.railway.app`)

### Step 3: Deploy Celery Worker

1. **Create Another Service**:
   - Click "New Service" → "GitHub Repo"
   - Select the same repository: `sohammirajkar/Advanced_Valuation_Engine`

2. **Configure Worker Service**:
   - **Service Name**: `valuation-worker` (or similar)
   - **Root Directory**: Keep as root (empty)
   - **Build Command**: Leave empty (auto-detected)
   - **Start Command**: `python start_worker.py`

3. **Set Environment Variables**:
   ```
   REDIS_URL=redis://default:password@host:port
   ```
   (Same URL from Step 1)

4. **Deploy**:
   - Railway will build and start the worker
   - Check logs to ensure it connects to Redis successfully

### Step 4: Update Frontend

1. **Go to Your Frontend Service**
2. **Update Environment Variables**:
   ```
   API_URL=https://your-backend-service-url.up.railway.app
   ```
   (Use the URL from Step 2, WITHOUT trailing slash)

3. **Redeploy Frontend**:
   - Railway will automatically redeploy with new API_URL

## ✅ Verification Steps

### 1. Check Redis Service
- Go to Redis service logs
- Should show successful startup

### 2. Check Backend Service  
- Go to backend service logs
- Should show: `Uvicorn running on http://0.0.0.0:8000`
- Visit the backend URL in browser - should show: `{"message":"Valuation Engine API Running"}`

### 3. Check Worker Service
- Go to worker service logs  
- Should show: `celery@hostname ready`
- Should see Redis connection successful

### 4. Check Frontend
- Visit your frontend URL
- Should show: ✅ "Connected to API: https://your-backend-url"
- Try running a valuation to test end-to-end functionality

## 🔧 Troubleshooting

### Backend shows "Connection refused" to Redis
- **Issue**: `REDIS_URL` is incorrect or Redis service is down
- **Solution**: Check Redis service URL and status

### Worker shows "Cannot connect to broker"
- **Issue**: Same as above, worker can't reach Redis
- **Solution**: Verify `REDIS_URL` is set correctly in worker service

### Frontend shows "Cannot connect to API"
- **Issue**: `API_URL` is incorrect or backend is down
- **Solution**: Check backend service status and URL

### Backend shows "Module not found" errors
- **Issue**: Dependencies not installed properly
- **Solution**: Check that `requirements.txt` includes all dependencies

## 📁 File Reference

The following files are configured for Railway deployment:

- **Backend**: `start_backend.py` + `Procfile.backend`
- **Worker**: `start_worker.py` + `Procfile.worker`  
- **Frontend**: `start_streamlit.py` + `Procfile.frontend`

## 🌐 Final Architecture

After deployment, you'll have:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   Celery        │
│   Frontend      │────│   Backend       │────│   Worker        │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                └───────┐   ┌───────────┘
                                        │   │
                                ┌─────────────────┐
                                │     Redis       │
                                │   (Message      │
                                │   Broker +      │
                                │   Cache)        │
                                └─────────────────┘
```

## 💡 Tips

- **Use the same Redis URL** for both backend and worker services
- **Don't include trailing slashes** in API_URL
- **Check service logs** if something isn't working
- **Start with Redis**, then backend, then worker, finally frontend
- **Environment variables** are case-sensitive

Once all services are deployed and connected, your valuation engine will be fully operational on Railway! 🎉
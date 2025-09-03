# 🚀 Railway Deployment Guide

## 📋 Overview

This guide provides step-by-step instructions for deploying the Valuation Engine to Railway. The application consists of multiple services that work together to provide a complete financial valuation platform.

## 🏗️ Architecture

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
                                │   Database      │
                                └─────────────────┘
```

## 📁 Deployment Structure

```
deployment/
├── railway/
│   ├── services.yml      # Service configurations
│   └── environment.yml   # Environment variables
├── scripts/
│   ├── start_frontend.py # Frontend startup script
│   ├── start_backend.py  # Backend startup script
│   ├── start_worker.py   # Worker startup script
│   └── deploy_helper.py  # Deployment utilities
└── configs/
    └── (generated Railway configs)
```

## 🚀 Deployment Steps

### Step 1: Prepare Railway Configuration

1. **Generate configuration files**:

   ```bash
   python deployment/scripts/deploy_helper.py config
   ```

2. **Check deployment status**:

   ```bash
   python deployment/scripts/deploy_helper.py status
   ```

### Step 2: Deploy Services (in order)

#### 2.1 Deploy Redis Database

1. Go to [Railway Dashboard](https://railway.app)
2. Create new service → **Database** → **Redis**
3. Wait for deployment
4. Copy the `REDIS_URL` from Variables tab

#### 2.2 Deploy Backend API

1. Create new service → **GitHub Repo** → Your repository
2. **Service Settings**:
   - Name: `valuation-backend`
   - Root Directory: `/` (root)
3. **Upload Configuration**:
   - Copy `deployment/configs/railway-backend.json` to root as `railway.json`
4. **Environment Variables**:

   ```
   REDIS_URL = redis://default:password@host:port
   ```

5. **Deploy** and wait for completion
6. **Copy the generated URL** (e.g., `https://valuation-backend-production.up.railway.app`)

#### 2.3 Deploy Celery Worker

1. Create new service → **GitHub Repo** → Same repository
2. **Service Settings**:
   - Name: `valuation-worker`
   - Root Directory: `/` (root)
3. **Upload Configuration**:
   - Copy `deployment/configs/railway-worker.json` to root as `railway.json`
4. **Environment Variables**:

   ```
   REDIS_URL = redis://default:password@host:port
   ```

   (Same as backend)
5. **Deploy**

#### 2.4 Update Frontend

1. Go to your existing frontend service
2. **Upload Configuration**:
   - Copy `deployment/configs/railway-frontend.json` to root as `railway.json`
3. **Environment Variables**:

   ```
   API_URL = https://valuation-backend-production.up.railway.app
   ```

   (Use URL from Step 2.2, NO trailing slash)
4. **Redeploy**

## ✅ Verification

### Check Service Status

1. **Redis**: Should show "Running" status
2. **Backend**:
   - Logs should show: `🚀 Starting Valuation Engine Backend API`
   - Visit URL: Should return `{"message": "Valuation Engine API Running"}`
3. **Worker**:
   - Logs should show: `🔄 Starting Valuation Engine Worker`
   - Should see: `celery@hostname ready`
4. **Frontend**:
   - Should show: `✅ Connected to API: https://your-backend-url`
   - Try running a calculation to test end-to-end

### Test Complete Flow

1. Visit your frontend URL
2. Go to "Basic Valuation" tab
3. Enter cash flows: `100, 200, 300`
4. Click "Calculate NPV"
5. Should see result and visualization

## 🔧 Troubleshooting

### Frontend shows "Cannot connect to API"

**Cause**: API_URL not set or incorrect
**Solution**:

1. Check backend service URL is correct
2. Ensure no trailing slash in API_URL
3. Verify backend service is running

### Backend fails to start

**Cause**: Missing REDIS_URL
**Solution**:

1. Verify Redis service is running
2. Copy correct REDIS_URL from Redis service
3. Add to backend environment variables

### Worker shows connection errors

**Cause**: Cannot connect to Redis
**Solution**:

1. Use same REDIS_URL as backend
2. Verify Redis service is accessible

### Build failures

**Cause**: Missing dependencies or config
**Solution**:

1. Check Dockerfile exists in root
2. Verify requirements.txt is complete
3. Ensure startup scripts have correct paths

## 🎯 Quick Commands

```bash
# Check deployment status
python deployment/scripts/deploy_helper.py status

# Generate configs for Railway
python deployment/scripts/deploy_helper.py config

# Test startup scripts locally
python deployment/scripts/start_frontend.py
python deployment/scripts/start_backend.py
python deployment/scripts/start_worker.py
```

## 📞 Support

If you encounter issues:

1. **Check service logs** in Railway dashboard
2. **Verify environment variables** are set correctly
3. **Ensure correct deployment order** (Redis → Backend → Worker → Frontend)
4. **Test individual components** using the startup scripts

## 🎉 Success Criteria

Your deployment is successful when:

- ✅ All 4 services show "Running" status
- ✅ Frontend shows "Connected to API"
- ✅ NPV calculation works end-to-end
- ✅ No error logs in any service

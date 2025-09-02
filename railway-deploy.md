# Railway Deployment Guide

## Quick Deploy to Railway (No Code Changes Required)

### Prerequisites
1. GitHub account
2. Railway account (free at railway.app)

### Deployment Steps

#### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit for Railway deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/valuation-engine.git
git push -u origin main
```

#### 2. Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will automatically detect the services

#### 3. Add Redis Service
1. In your Railway project dashboard
2. Click "New" → "Database" → "Add Redis"
3. Railway will automatically set the `REDIS_URL` environment variable

#### 4. Configure Services

Railway will create 3 services automatically:
- **API Service** (FastAPI backend)
- **Worker Service** (Celery workers) 
- **Web Service** (Streamlit frontend)

#### 5. Environment Variables

Railway will auto-configure most variables, but verify these:
- `REDIS_URL` - Auto-configured by Railway Redis
- `API_BASE_URL` - Set to your API service URL
- `PORT` - Auto-configured by Railway

#### 6. Custom Domains (Optional)
- Each service gets a railway.app subdomain
- You can add custom domains in the service settings

### Access Your App
After deployment:
- **Streamlit UI**: `https://your-app-web.up.railway.app`
- **API Docs**: `https://your-app-api.up.railway.app/docs`
- **API Health**: `https://your-app-api.up.railway.app/health`

### Monitoring
- View logs in Railway dashboard
- Monitor resource usage
- Set up alerts

### Scaling
- Adjust replicas in service settings
- Railway auto-scales based on traffic
- Upgrade plan for higher limits

### Cost Estimation
- Free tier: $5 credit/month
- After free tier: ~$0.001/minute per vCPU
- Typical cost: $10-30/month for production use

## Alternative: One-Click Deploy

Click this button for instant deployment:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/YOUR_TEMPLATE_ID)

## Troubleshooting

### Common Issues
1. **Redis Connection**: Ensure REDIS_URL is set correctly
2. **Port Binding**: Services must bind to `0.0.0.0:$PORT`
3. **Dependencies**: Check requirements.txt is complete

### Health Checks
```bash
# Check API health
curl https://your-app-api.up.railway.app/health

# Check Redis connection
curl https://your-app-api.up.railway.app/tasks/cache-stats
```

### Support
- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: Create issues in your repo
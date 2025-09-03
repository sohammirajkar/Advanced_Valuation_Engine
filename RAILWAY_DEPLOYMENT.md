# Railway Deployment Guide

## 🚀 Quick Setup for Frontend Deployment

Your backend is already running on Railway. Now let's connect the frontend!

## 📋 Required Environment Variables

### In Railway Frontend Service

1. **API_URL** (Required): Your backend service URL

   ```
   https://your-backend-service-name.up.railway.app
   ```

   **⚠️ Important Notes:**
   - Replace `your-backend-service-name` with your actual backend service name
   - Do NOT include trailing slash
   - Use `https://` (not `http://`)

## 🔧 How to Set Environment Variables in Railway

1. **Go to Railway Dashboard**: <https://railway.app>
2. **Select Your Frontend Project**
3. **Navigate to Variables Tab**
4. **Add Environment Variable**:
   - **Name**: `API_URL`
   - **Value**: `https://your-backend-service.up.railway.app`
5. **Save Changes**
6. **Redeploy**: Railway will automatically redeploy with new variables

## 🔍 Finding Your Backend URL

### Method 1: Railway Dashboard

1. Go to your backend service in Railway
2. Look for the "Domains" section
3. Copy the generated URL (e.g., `https://web-production-1234.up.railway.app`)

### Method 2: Railway CLI

```bash
railway status
```

### Method 3: Check Deployments

1. Go to your backend service
2. Click on "Deployments"
3. Look for the public URL

## ✅ Verification Steps

After setting the API_URL:

1. **Check Startup Logs**: Look for these messages in Railway logs:

   ```
   🚀 Starting Streamlit Frontend
   ===============================
   PORT: 8080
   API_URL: https://your-backend-service.up.railway.app
   ```

2. **Check Frontend**: Open your frontend URL and look for:
   - ✅ Green "Connected to API" message
   - No connection errors

3. **Test Functionality**: Try using any valuation feature to confirm API connectivity

## 🐛 Troubleshooting

### Frontend shows "Cannot connect to API: <http://localhost:8000>"

- **Cause**: API_URL environment variable not set or incorrect
- **Solution**: Set API_URL to your Railway backend URL

### Frontend shows "API Connection Failed (Status: 404)"

- **Cause**: Backend URL is incorrect
- **Solution**: Verify your backend URL is accessible

### Frontend shows "Connection Timeout"

- **Cause**: Backend service is down or URL is wrong
- **Solution**: Check backend service status in Railway

### Still using localhost in production?

- **Cause**: API_URL environment variable not set
- **Solution**: Add API_URL variable in Railway dashboard

## 📱 Example Configuration

For a backend deployed as `web-production-1234.up.railway.app`:

```
API_URL=https://web-production-1234.up.railway.app
```

## 🔄 After Setting Variables

1. Railway will automatically redeploy your frontend
2. Check the deployment logs for confirmation
3. Visit your frontend URL to verify connection
4. You should see ✅ "Connected to API" message

## 📞 Support

If you're still having issues:

1. Check Railway service logs for both frontend and backend
2. Verify backend is responding at the URL
3. Ensure no trailing slashes in API_URL
4. Try a manual curl test: `curl https://your-backend-url/`

#!/bin/bash

echo "🚀 Deploying Streamlit Frontend to Railway"
echo "========================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial frontend commit for Railway deployment"
else
    echo "📁 Git repository exists, adding new changes..."
    git add .
    git commit -m "Update frontend for Railway deployment - $(date)"
fi

echo ""
echo "✅ Frontend code prepared for deployment!"
echo ""
echo "🔗 Next steps for Railway deployment:"
echo "1. Go to https://railway.app and create a new project"
echo "2. Connect your GitHub repository"
echo "3. Railway will auto-detect the Streamlit app"
echo "4. Set the environment variable API_URL to your backend URL"
echo "   Example: API_URL=https://your-backend-production.up.railway.app"
echo "5. Deploy!"
echo ""
echo "📋 Important Environment Variables to set in Railway:"
echo "• API_URL: Your backend API URL (without trailing slash)"
echo "• PORT: Railway will set this automatically"
echo ""
echo "🌐 Your frontend will be live at:"
echo "• https://your-frontend-production.up.railway.app"
echo ""
echo "💡 Tips:"
echo "• Railway will automatically use the Procfile for deployment"
echo "• The .streamlit/config.toml configures Streamlit for production"
echo "• Health checks are configured at /_stcore/health"
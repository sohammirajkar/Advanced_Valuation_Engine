#!/bin/bash

echo "🚀 Deploying Valuation Engine to Railway"
echo "========================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for Railway deployment"
else
    echo "📁 Git repository exists, adding new changes..."
    git add .
    git commit -m "Update for Railway deployment - $(date)"
fi

echo ""
echo "✅ Code prepared for deployment!"
echo ""
echo "🔗 Next steps:"
echo "1. Create GitHub repository: https://github.com/new"
echo "2. Add remote: git remote add origin https://github.com/YOUR_USERNAME/valuation-engine.git"
echo "3. Push code: git push -u origin main"
echo "4. Deploy on Railway: https://railway.app"
echo "5. Connect GitHub repo and add Redis service"
echo ""
echo "🌐 Your app will be live at:"
echo "• Frontend: https://valuation-frontend-production.up.railway.app"
echo "• API: https://valuation-api-production.up.railway.app/docs"
echo ""
echo "💡 Tip: Railway will auto-detect all services from your Procfile and railway.json"
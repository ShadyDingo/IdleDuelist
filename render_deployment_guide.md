# 🚀 Render Deployment Guide for IdleDuelist

## Why Render?
- ✅ **750 hours/month free** (vs Fly.io's 160 hours)
- ✅ **Very stable** - Excellent uptime
- ✅ **Great for Python** - Optimized for Python apps
- ✅ **Easy setup** - Connect GitHub and deploy
- ✅ **No timeout issues** - Better than Fly.io

## Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Click "Get Started for Free"
3. Sign up with GitHub

## Step 2: Deploy Your App
1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Select "IdleDuelist" repository
4. Configure:
   - **Name**: `idleduelist-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements_railway.txt`
   - **Start Command**: `python simple_deployment.py`
5. Click "Create Web Service"

## Step 3: Environment Variables
Render will automatically set:
- ✅ `PORT` - Automatically set by Render
- ✅ `PYTHON_VERSION` - Set to Python 3

## Step 4: Get Your Live URL
After deployment (2-3 minutes), you'll get:
```
https://idleduelist-backend.onrender.com
```

## Step 5: Test Your App
Visit your Render URL:
```
https://idleduelist-backend.onrender.com/health
```

Should see:
```json
{"status":"healthy","simple":true}
```

## Render Advantages:
- **750 hours/month free** - More than Railway (500h) or Fly.io (160h)
- **No deployment timeouts** - Render handles Python apps excellently
- **Auto-deploy** - Deploys automatically when you push to GitHub
- **Custom domains** - Free custom domain support
- **SSL certificates** - Automatic HTTPS
- **Great logging** - Clear error messages and logs

## Monitoring:
1. Go to your Render dashboard
2. Click on your web service
3. View logs, metrics, and deployments
4. Monitor resource usage

## Scaling:
- **Starter Plan**: $7/month for unlimited hours
- **Standard Plan**: $25/month for production features

## Troubleshooting:
- **Check logs** in Render dashboard
- **Verify build command** is correct
- **Check start command** matches your file
- **Redeploy** if needed

Render is excellent for Python apps and has the most generous free tier!

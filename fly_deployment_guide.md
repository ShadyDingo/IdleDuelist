# 🚀 Fly.io Deployment Guide for Windows

## 📋 **Prerequisites**
- GitHub account
- Fly.io account (free)

## 🚀 **Step 1: Create Fly.io Account**
1. Go to [fly.io](https://fly.io)
2. Click "Sign Up" 
3. Sign up with GitHub (recommended)
4. Verify your email

## 🔧 **Step 2: Prepare Your Repository**
Your repository is already ready with the `fly.toml` configuration file!

## 📱 **Step 3: Deploy via Web Interface**

### **Option A: Deploy from GitHub (Recommended)**
1. **Go to [Fly.io Dashboard](https://fly.io/dashboard)**
2. **Click "Launch App"**
3. **Select "Deploy from GitHub"**
4. **Authorize Fly.io to access your GitHub repositories**
5. **Select your IdleDuelist repository**
6. **Fly.io will automatically detect the `fly.toml` file**
7. **Click "Deploy"**
8. **Wait 2-3 minutes for deployment**

### **Option B: Manual Deploy**
1. **Go to [Fly.io Dashboard](https://fly.io/dashboard)**
2. **Click "Launch App"**
3. **Select "Deploy from Source"**
4. **Choose your region** (closest to you)
5. **Select "Python" as the runtime**
6. **Upload your project files**
7. **Click "Deploy"**

## 🎯 **Step 4: Get Your Live URL**
After deployment, you'll get a URL like:
```
https://your-app-name.fly.dev
```

## ✅ **Step 5: Test Your Deployment**
```bash
# Test health endpoint
curl https://your-app-name.fly.dev/health

# Test stats endpoint  
curl https://your-app-name.fly.dev/stats
```

## 📱 **Step 6: Update Your Mobile App**
```python
# In your mobile app, update the server URL
self.network_manager = NetworkManager("https://your-app-name.fly.dev")
```

## 🔧 **Configuration Details**

### **fly.toml Configuration**
```toml
app = "idle-duelist-backend"
primary_region = "sjc"

[build]

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256

[env]
  PORT = "8000"
```

### **What This Configuration Does:**
- **App Name**: `idle-duelist-backend`
- **Region**: San Jose, California (change to closest to you)
- **Port**: 8000 (internal)
- **Memory**: 256MB (free tier)
- **CPU**: 1 shared CPU (free tier)
- **Auto-stop**: Machines stop when idle (saves money)
- **Auto-start**: Machines start when needed
- **HTTPS**: Automatic SSL certificate

## 🆓 **Free Tier Limits**
- **3 shared-cpu-1x VMs** with 256MB RAM each
- **160GB-hours per month** (about 5 hours/day)
- **Automatic HTTPS** and global deployment
- **No credit card required**

## 🔍 **Monitoring Your App**
1. **Go to [Fly.io Dashboard](https://fly.io/dashboard)**
2. **Click on your app**
3. **View logs, metrics, and status**
4. **Monitor resource usage**

## 🚀 **Scaling Up (When Ready)**
- **Paid Plans**: Start at $1.94/month
- **More VMs**: Add more instances
- **More Memory**: Upgrade to 512MB or 1GB
- **Better Performance**: Dedicated CPUs

## 🐛 **Troubleshooting**

### **Deployment Fails**
- Check that `fly.toml` is in your repository root
- Verify `requirements_free.txt` exists
- Check build logs in Fly.io dashboard

### **App Won't Start**
- Check that `free_deployment.py` exists
- Verify all dependencies are in `requirements_free.txt`
- Check app logs in Fly.io dashboard

### **Connection Issues**
- Verify your app URL is correct
- Check that the app is running (green status)
- Test with curl or browser

## 📊 **Expected Performance**
- **Startup Time**: 10-30 seconds (first request)
- **Response Time**: 100-500ms (after warmup)
- **Concurrent Users**: 50-100 (free tier)
- **Uptime**: 99%+ (with auto-restart)

## 🎉 **Success!**
Once deployed, your IdleDuelist backend will be:
- ✅ **Live and accessible** worldwide
- ✅ **Handling player data** and duels
- ✅ **Ready for mobile app integration**
- ✅ **Completely free** to run

Your game will be accessible to players worldwide, and you can start testing the online multiplayer experience immediately!

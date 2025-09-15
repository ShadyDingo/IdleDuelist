# 🌐 IdleDuelist Public Deployment Guide

## 🎯 **Get Your Game Online for Everyone to Play!**

### **✅ What's New:**
- ✅ **Account System**: Players can now login/logout and save their progress
- ✅ **Persistent Characters**: Your character is saved even after refreshing the page
- ✅ **Public URLs**: Deploy to get a shareable link anyone can use
- ✅ **Auto-Login**: Returns to your character when you visit again

---

## 🚀 **Deploy to Railway (Recommended)**

### **Step 1: Setup Railway**
1. **Go to**: [Railway.app](https://railway.app)
2. **Sign up** with GitHub
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**

### **Step 2: Connect Repository**
1. **Select your IdleDuelist repository**
2. **Railway will auto-detect** Python and requirements
3. **Click "Deploy"**

### **Step 3: Configure Settings**
1. **In Railway dashboard**, go to your project
2. **Go to Settings → Environment**
3. **Add these environment variables:**
   ```
   PORT=8001
   ```
4. **Save and redeploy**

### **Step 4: Get Your Public URL**
1. **Go to "Deployments" tab**
2. **Copy the public URL** (e.g., `https://your-app.up.railway.app`)
3. **Share with friends!**

---

## 🚀 **Deploy to Render (Alternative)**

### **Step 1: Setup Render**
1. **Go to**: [Render.com](https://render.com)
2. **Sign up** with GitHub
3. **Click "New +" → "Web Service"**

### **Step 2: Connect Repository**
1. **Connect your GitHub repository**
2. **Select the IdleDuelist repo**
3. **Configure:**
   - **Name**: `idleduelist-web`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements_web.txt`
   - **Start Command**: `python simple_web_server.py`

### **Step 3: Deploy**
1. **Click "Create Web Service"**
2. **Wait for deployment** (5-10 minutes)
3. **Get your public URL**

---

## 🎮 **How the Account System Works**

### **For Players:**
1. **First Visit**: Choose "Create New Character"
2. **Character Creation**: Fill out the form and submit
3. **Auto-Save**: Your character is saved locally and on server
4. **Refresh Page**: You'll automatically return to your character
5. **Logout**: Click logout to switch accounts

### **For You (Developer):**
- **Local Storage**: Saves player data in browser
- **Server Database**: Stores all player data permanently
- **Login System**: Players can login with their username
- **Persistent Progress**: Wins/losses/rating saved forever

---

## 🔗 **Sharing Your Game**

### **Option 1: Direct Link**
```
https://your-app.up.railway.app
```

### **Option 2: QR Code**
- Generate QR code for your URL
- Share on social media, forums, etc.

### **Option 3: Embed in Website**
```html
<iframe src="https://your-app.up.railway.app" width="100%" height="600"></iframe>
```

---

## 📱 **Mobile-Friendly Features**

- ✅ **Responsive Design**: Works on phones, tablets, desktops
- ✅ **Touch-Friendly**: Buttons and forms work great on mobile
- ✅ **Fast Loading**: Optimized for mobile networks
- ✅ **No Downloads**: Just open in browser and play

---

## 🎯 **Features Available Online**

### **✅ Working Features:**
- Character creation with factions, weapons, armor
- Real-time dueling against other players
- Leaderboard with rankings
- Account system with login/logout
- Persistent character data
- Rating system with wins/losses

### **🔄 Differences from Main App:**
- **Simplified UI**: Web-optimized interface
- **Basic Combat**: Streamlined for web performance
- **No Art Assets**: Uses CSS styling instead of game images
- **Limited Features**: Focuses on core dueling gameplay

---

## 🛠 **Customization Options**

### **Easy Changes:**
1. **Modify `static/index.html`** for UI changes
2. **Edit `simple_web_server.py`** for game logic
3. **Update CSS** for different styling
4. **Add new weapons/factions** in the data structures

### **Advanced Features:**
- Add more complex combat mechanics
- Implement real-time multiplayer
- Add chat system
- Create tournaments
- Add achievements

---

## 🚨 **Important Notes**

### **Free Tier Limits:**
- **Railway**: 500 hours/month, sleeps after inactivity
- **Render**: 750 hours/month, sleeps after 15 minutes
- **Both**: Wake up automatically when someone visits

### **Database:**
- Uses SQLite (file-based database)
- Data persists between deployments
- No external database needed for free tier

### **Scaling:**
- Can upgrade to paid tiers for more resources
- Add PostgreSQL for production use
- Implement Redis for session management

---

## 🎉 **Ready to Share!**

Your IdleDuelist game is now ready for the world! 

1. **Deploy to Railway/Render**
2. **Get your public URL**
3. **Share with friends**
4. **Watch players duel and compete!**

**The game will automatically save all player progress and work on any device with a web browser!** 🌐🎮

# 🚀 SatQuery AI - Streamlit Community Cloud Hosting Guide

This guide explains how to host **SatQuery AI** for **100% free** on **[Streamlit Community Cloud](https://share.streamlit.io/)** with continuous automated deployments, SSL HTTPS certificates, and zero server maintenance.

---

## 📋 Prerequisites
1. A GitHub account with the SatQuery AI repository pushed.
2. A free [Streamlit Community Cloud account](https://share.streamlit.io/) (signs in with GitHub).
3. Your MongoDB Atlas connection URI (from `backend/.env`).

---

## Step 1: Ensure Large Raster Files are Excluded from Git
To avoid GitHub file size limits (files >100 MB), ensure `.gitignore` excludes heavy raster directories:
```gitignore
uploads/
evidence/
sample_data/
node_modules/
backend/venv/
cloudflared.exe
```
*(This is already pre-configured in your project `.gitignore`)*

---

## Step 2: Push Repository to GitHub
From your project directory:
```bash
git add requirements.txt streamlit_app.py .streamlit/ backend/ requirements.txt .gitignore README.md
git commit -m "Add Streamlit application and configuration for cloud deployment"
git push -u origin main
```

---

## Step 3: Deploy on Streamlit Community Cloud

1. Log into **[share.streamlit.io](https://share.streamlit.io/)** using your GitHub account.
2. Click **"New app"** (or **"Create app"**).
3. Fill in the deployment details:
   - **Repository:** `your-username/SatQueryAI-Deployment` (or your repo name)
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
   - **App URL:** (Optional custom subdomain, e.g. `satquery-ai.streamlit.app`)
4. Click **"Advanced settings..."** before deploying to add your MongoDB Atlas credentials:
   - Under **Secrets**, paste:
     ```toml
     MONGODB_URI = "mongodb+srv://anushkayadave2_db_user:YOUR_PASSWORD@satqueryai.4ycva2p.mongodb.net/?appName=SatQueryAI"
     DATABASE_NAME = "satquery_ai"
     ```
5. Click **"Save"**, then click **"Deploy!"**

---

## Step 4: Access Your Live Application
Streamlit Cloud will automatically:
* Provision a high-performance Python environment.
* Install all dependencies from `requirements.txt`.
* Connect securely to your MongoDB Atlas database via Secrets.
* Assign your app a permanent HTTPS domain:
  `https://satquery-ai.streamlit.app`

---

## 🛠️ Running Locally Anytime
To test or run locally at any time:
```powershell
# Option A: Run the batch launcher
.\run_streamlit.bat

# Option B: Run directly via CLI
streamlit run streamlit_app.py --server.port 8501
```
Open **`http://localhost:8501`** in your browser.

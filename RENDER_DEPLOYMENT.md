# SatQuery AI - Render Deployment Guide

This guide details how to deploy **SatQuery AI** to [Render.com](https://render.com) using the decoupled architecture:
1. **FastAPI Backend Web Service** (`satquery-backend`)
2. **React Frontend Static Site** (`satquery-frontend`)
3. Connected to your live **MongoDB Atlas** database.

---

## Method 1: 1-Click Automated Blueprint Deployment (Recommended)

Render Blueprints use the [`render.yaml`](file:///c:/Users/giris/Downloads/SatQueryAI/render.yaml) file to automatically provision and link both services simultaneously.

### Step 1: Push Repository to GitHub or GitLab
Push your project to a remote Git repository:
```bash
git add .
git commit -m "Configure Render Web Service and Static Site deployment"
git push origin main
```

### Step 2: Create Blueprint Instance on Render
1. Log in to [dashboard.render.com](https://dashboard.render.com).
2. Click the **New +** button in the top navigation bar and select **Blueprint**.
3. Connect your GitHub/GitLab account and select your `SatQueryAI` repository.
4. Render will read `render.yaml` and display the blueprint plan:
   - **`satquery-backend`** (Python Web Service)
   - **`satquery-frontend`** (Static Site)
5. Under Environment Variables for `satquery-backend`, enter your MongoDB Atlas URI:
   - **Key**: `MONGODB_URI`
   - **Value**: `mongodb+srv://anushkayadave2_db_user:<your_password>@satqueryai.4ycva2p.mongodb.net/?appName=SatQueryAI`
6. Click **Apply**.
7. Render will build and launch both services automatically:
   - Render automatically injects `VITE_API_BASE_URL` into the frontend with the live URL of `satquery-backend`.

---

## Method 2: Manual Dashboard Setup on Render

If you prefer to configure the services manually in the Render dashboard:

### Service 1: Deploy FastAPI Backend as a Web Service
1. In Render Dashboard, click **New +** -> **Web Service**.
2. Select your `SatQueryAI` repository.
3. Configure the settings:
   - **Name**: `satquery-backend`
   - **Language**: `Python 3`
   - **Region**: Oregon (or your preferred region)
   - **Branch**: `main`
   - **Root Directory**: *(leave blank or set to project root)*
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
4. Under **Environment Variables**, click **Add Environment Variable**:
   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `PYTHON_VERSION` | `3.12.0` | Ensures Python 3.12 runtime |
   | `MONGODB_URI` | `mongodb+srv://anushkayadave2_db_user:<password>@satqueryai.4ycva2p.mongodb.net/?appName=SatQueryAI` | Your Atlas connection string |
   | `DATABASE_NAME` | `satquery_ai` | Target MongoDB database |
5. Click **Create Web Service**. Wait for the build to finish.
6. Copy your backend URL (e.g. `https://satquery-backend.onrender.com`).

---

### Service 2: Deploy React Frontend as a Static Site
1. In Render Dashboard, click **New +** -> **Static Site**.
2. Select your `SatQueryAI` repository.
3. Configure the settings:
   - **Name**: `satquery-frontend`
   - **Branch**: `main`
   - **Root Directory**: *(leave blank or `frontend`)*
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
4. Under **Redirects / Rewrites**, add a rewrite rule for client-side routing:
   - **Type**: `Rewrite`
   - **Source**: `/*`
   - **Destination**: `/index.html`
5. Under **Environment Variables**, add:
   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `VITE_API_BASE_URL` | `https://satquery-backend.onrender.com` | Live backend URL from Service 1 |
6. Click **Create Static Site**. Wait for the build to finish.

---

## MongoDB Atlas Network Access Configuration

To allow Render services to connect to MongoDB Atlas:
1. Open your [MongoDB Atlas Console](https://cloud.mongodb.com).
2. Go to **Security** -> **Network Access**.
3. Click **+ Add IP Address**.
4. Select **Allow Access from Anywhere** (`0.0.0.0/0`) or enter Render's outbound IP addresses.
5. Click **Confirm**.

---

## Verification & Health Check

1. **Verify Backend Health**:
   Visit `https://satquery-backend.onrender.com/health/db` in your browser. Expected output:
   ```json
   {
     "status": "connected",
     "database": "satquery_ai",
     "uri": "mongodb+srv://anushkayadave2_db_user:****@satqueryai.4ycva2p.mongodb.net/?appName=SatQueryAI",
     "fallback_active": false,
     "message": "Connected to MongoDB Atlas database 'satquery_ai'"
   }
   ```
2. **Verify Frontend Application**:
   Visit `https://satquery-frontend.onrender.com`. Check the bottom of the sidebar to see the green **MongoDB Atlas: Connected** status pill!

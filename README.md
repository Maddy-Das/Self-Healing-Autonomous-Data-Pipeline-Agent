# 🚀 Self-Healing Autonomous Data Pipeline Agent

An AI-powered platform designed for Enterprise scale that builds, simulates, and **self-heals** data pipelines from a CSV file and a plain English description. Powered by **GLM 5.1** (Zhipu AI).

## ✨ Features

- **📊 Smart Data Profiling** — Automatic CSV analysis (types, nulls, duplicates, stats)
- **🛡️ Data Quality & PII Engine** — 8-category validation detecting schema drift, outliers, and PII
- **🏗️ AI Pipeline Builder** — Generates ETL code, SQL schema, Airflow DAG from natural language
- **🧪 3-Layer Simulation** — Tests ETL logic, DAG structure, and SQL correctness without Airflow
- **🔧 Self-Healing Loop** — AI detects issues and auto-fixes code (up to 3 iterations)
- **🔄 Resilience Engine** — Circuit Breakers, Checkpointing, and Exponential Backoff
- **📈 Observability Logs** — Built-in JSON structured logs, latency timing, and lineage tracking
- **📦 ZIP Export** — Download production-ready package with docker-compose

---

## 📋 Prerequisites

Before running the project, make sure you have installed:
- **Python 3.10+** (For the FastAPI Backend)
- **Node.js 18+** (For the Next.js Frontend)
- **Zhipu AI API Key** (Get one at [Zhipu AI](https://open.bigmodel.cn/))
- *(Optional)* Docker to run in containers

---

## 🛠️ How to Run Locally (Manual Setup)

### 1. Start the Backend

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Virtual Environment (Optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your API key:
   - Create or edit the `.env` file in the `backend` folder:
   ```
   ZHIPUAI_API_KEY=your_actual_api_key_here
   ```
5. Run the server:
   ```bash
   python main.py
   ```
   *The backend will now be running at `http://localhost:8000`*

### 2. Start the Frontend

1. Open a **new terminal tab** and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install Node modules:
   ```bash
   npm install
   ```
3. Run the Next.js development server:
   ```bash
   npm run dev
   # If port 3000 is taken, it will try another or you can specify:
   npx next dev -p 3001
   ```
   *The frontend will now be accessible at `http://localhost:3000` (or whichever port is assigned).*

---

## 🐳 How to Run via Docker

You can containerize the application using the multi-stage Dockerfiles provided in the repositories.

1. Build the images:
   ```bash
   docker build -t pipeline-backend ./backend
   docker build -t pipeline-frontend ./frontend
   ```

2. Run the backend container:
   ```bash
   docker run -d -p 8000:8000 -e ZHIPUAI_API_KEY="your_api_key" --name pipeline-backend pipeline-backend
   ```

3. Run the frontend container:
   ```bash
   docker run -d -p 3000:3000 --name pipeline-frontend pipeline-frontend
   ```

*(Alternatively, use `docker-compose` if you have packaged a solution!)*

---

## 🌐 Production + Vercel Deployment

This project is deployed as:
- **Frontend (Next.js)** on **Vercel**
- **Backend (FastAPI)** on a Python host (Render/Railway/Fly.io/VM)

### 1) Deploy Backend (FastAPI)

Set environment variables on your backend host (Render):
- `ZHIPUAI_API_KEY=your_actual_api_key`
- `CORS_ORIGINS=https://your-frontend-domain.vercel.app`
  - If you use multiple frontend domains, separate them with commas.
  - The origin must exactly match your frontend URL (including `https` and domain).

Start command:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```
(Run from the `backend` directory.)

### 2) Deploy Frontend to Vercel

In Vercel:
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Install Command**: `npm ci`
- **Output**: default Next.js output

Set frontend environment variable in Vercel:
- `NEXT_PUBLIC_API_URL=https://self-healing-autonomousdata-pipeline.onrender.com`

Save it for Production (and Preview/Development if needed), then redeploy the frontend.

Then deploy.

### 3) Validate Production

After deploy:
- Open Vercel URL
- Upload sample CSV from `sample_data/`
- Generate pipeline and verify status reaches `complete`
- Verify artifact download works
- If you still get a CORS error, check that `CORS_ORIGINS` exactly matches the Vercel frontend origin.

---

## 🧪 Running the Test Suite

The backend comes with a comprehensive suite of **28 passing unit tests** validating the AI modules, quality validation, resilience layers, and circuit breakers.

1. Go to the `backend` directory:
   ```bash
   cd backend
   ```
2. Ensure you have installed the testing packages:
   ```bash
   pip install pytest pytest-asyncio
   ```
3. Run the tests:
   ```bash
   python -m pytest tests/ -v
   ```

---

## 📖 How to Use the UI

1. Open your browser and go to the Frontend URL (usually `http://localhost:3000`).
2. **Upload a dataset:** Drag and drop a sample CSV (e.g., sample store sales data or `sample_data/sales_data.csv`).
3. **Describe the flow:** Provide an English prompt describing your ETL requirements. Example:
   > *"Ingest daily sales data, clean duplicates & nulls, calculate total revenue per region, and format dates. Store results in SQLite."*
4. **Click "Generate Pipeline":** Let the agent take over. 
5. The UI will stream generation phases:
   - **Data Quality Alerts** (PII detected, schema anomalies, high cardinality)
   - **Simulation Output** (whether it crashed natively)
   - **Reasoning Traces** (the exact decisions the LLM made for building and patching bugs)
6. Once healed and completely stabilized, your **Readiness Score** will glow "Production Ready". 
7. **Download** the generated ZIP package containing your `etl.py`, Airflow `dag.py`, and Docker architecture.

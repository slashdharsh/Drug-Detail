# 💊 Drug Detail Aid Generator

Structured FDA prescribing information — type a drug name, get a full detail aid instantly.  
Powered by the **free OpenFDA API** (no API key required).

---

## 🚀 Run Locally

### 1. Clone / download this folder

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
streamlit run app.py
```
Opens at → `http://localhost:8501`

---

## ☁️ Deploy on Streamlit Community Cloud (Free)

1. Push this folder to a **GitHub repo** (public or private)
2. Go to → [share.streamlit.io](https://share.streamlit.io)
3. Click **"New app"**
4. Select your repo, branch (`main`), and set **Main file path** to `app.py`
5. Click **Deploy** — live in ~2 minutes ✅

No secrets or API keys needed — OpenFDA is completely public.

---

## 📁 Project Structure

```
drug-detail-aid/
├── app.py            ← Main Streamlit app
├── requirements.txt  ← Python dependencies
└── README.md
```

---

## 📦 Data Source

- **OpenFDA Drug Label API** — `https://api.fda.gov/drug/label.json`
- Free, no authentication required
- Sourced from FDA-approved drug labeling (DailyMed)

---

## 🛠 Possible Extensions

- [ ] PDF export of the detail aid
- [ ] Compare two drugs side by side
- [ ] Drug interaction checker
- [ ] Branded template with custom logo
- [ ] Search history / favourites

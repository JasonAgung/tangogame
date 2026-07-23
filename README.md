# ☀️ Tango Game & Solver 🌑

Aplikasi web interaktif untuk bermain dan menyelesaikan game **Tango Puzzle 6x6** yang dikembangkan menggunakan **FastAPI (Backend)** dan **React + Vite + TailwindCSS (Frontend)**. 

Project ini mendukung penyelesaian puzzle secara otomatis menggunakan dua pendekatan algoritma:
1. **Backtracking** (dengan dan tanpa heuristik)
2. **Simulated Annealing (SA)**

---

## 🌟 Fitur Utama

- **Mode USER (Interaktif)**:
  - Bermain puzzle secara manual (klik petak untuk mengubah menjadi ☀️ Sun / 🌑 Moon).
  - Fitur **Highlight Violations** real-time untuk menandai petak yang melanggar aturan game.
  - Fitur **Cara Bermain (How to Play)** modal pop-up interaktif.
  - Opsi **SOLVE PUZZLE** instan menggunakan algoritma Backtracking.

- **Mode EXPERT (Analisis Performa)**:
  - Pemilihan tingkat kesulitan (**Easy**, **Medium**, **Hard**) dan nomor puzzle (1 - 100).
  - Perbandingan performa antara **Backtracking (BT)** (opsi Heuristic Toggle) dan **Simulated Annealing (SA)**.
  - Menampilkan **Metrics Analysis**: Jumlah iterasi, waktu eksekusi, dan *final cost*.

---

## 📂 Struktur Project

```text
tango-project/
├── app/                  # Source code Backend Python (FastAPI)
│   ├── main.py           # Entry point API & endpoints
│   ├── models.py         # Data model Puzzle & Constraint
│   └── solvers.py        # Implementation Backtracking & Simulated Annealing
├── data_puzzle/          # Database kumpulan soal puzzle (JSON)
│   ├── easy/             # Soal tingkat Easy (001 - 100)
│   ├── medium/           # Soal tingkat Medium (001 - 100)
│   └── hard/             # Soal tingkat Hard (001 - 100)
├── frontend/             # Source code Frontend React + Vite
│   ├── src/
│   │   ├── TangoGame.jsx # Main UI Component
│   │   └── ...
│   ├── public/
│   │   └── favicon.svg   # Favicon game
│   ├── index.html        # Main HTML
│   └── package.json      # Dependencies Frontend
├── requirements.txt      # Dependencies Python Backend
└── README.md
```

---

## 💻 Cara Menjalankan Project (Lokal)

### 1. Jalankan Backend (API)

Buka terminal di root folder project (`tango-project`):

Buat dan aktifkan virtual environment Python:
- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- **Windows**:
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  ```

Install dependencies Backend:
```bash
pip install -r requirements.txt
```

Jalankan server FastAPI:
```bash
uvicorn app.main:app --reload --port 8000
```
Backend akan berjalan di: `http://localhost:8000`

---

### 2. Jalankan Frontend (UI)

Buka terminal baru, lalu masuk ke folder `frontend`:
```bash
cd frontend
```

Install dependencies Node.js:
```bash
npm install
```

Jalankan server dev Frontend:
```bash
npm run dev
```
Buka alamat yang muncul di terminal (biasanya `http://localhost:5173`) di browser Anda.

---

## ☁️ Deployment

- **Backend**: Di-deploy ke [Render.com](https://render.com) (Python 3 Web Service via Uvicorn).
- **Frontend**: Di-deploy ke [Vercel](https://vercel.com) (Vite Frontend + Environment Variable `VITE_API_BASE_URL`).

---

## 👤 Author & Credits

- **Developer**: Jason Kelvin Agung
- **Sumber Data Puzzle**: `tangounlimitedgame.com` *(inactive)*

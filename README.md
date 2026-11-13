# ☀️ Tango Game & Solver 🌑

Aplikasi web interaktif untuk bermain dan menyelesaikan game **Tango Puzzle 6x6** yang dikembangkan menggunakan **FastAPI (Backend)** dan **React + Vite + TailwindCSS (Frontend)**. 

Project ini mendukung penyelesaian puzzle secara otomatis menggunakan dua pendekatan algoritma:
1. **Backtracking** (dengan dan tanpa heuristik)
2. **Simulated Annealing (SA)**

---

## Fitur Utama

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

## Struktur Project

```text
tango-project/
├── app/                  # Source code Backend Python (FastAPI)
│   ├── main.py           # Entry point API & endpoints
│   ├── models.py         # Data model Puzzle & Constraint
│   ├── solvers.py        # Implementation Backtracking & Simulated Annealing
│   └── linkedin_daily.py # Scraper puzzle harian LinkedIn Tango
├── deploy/               # systemd, Caddy, & script setup VPS
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

## Cara Menjalankan Project (Lokal)

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

## Today's Tango Challenge

Puzzle Tango harian dari LinkedIn Games ditampilkan di atas papan dan langsung dimuat saat web dibuka.

- `app/linkedin_daily.py` membuka halaman game LinkedIn (tanpa login) pakai Playwright, mengambil data puzzle, lalu menyimpannya ke `data_puzzle/daily/latest.json` (format sama dengan `data_puzzle/<difficulty>/`).
- Scraper juga menjalankan solver Backtracking dan mencocokkannya dengan kunci jawaban resmi (`solver_verified`).
- Dijalankan tiap jam oleh systemd timer. Kalau puzzle hari ini (patokan tengah malam waktu Pacific) sudah ada, scraper langsung skip.
- Endpoint: `GET /api/daily`. Kalau belum ada puzzle harian, frontend fallback ke puzzle Easy #1.

Jalankan manual di lokal (pakai Google Chrome yang terpasang):
```bash
TANGO_BROWSER_CHANNEL=chrome python -m app.linkedin_daily --force
```

---

## Deployment

- **Backend**: VPS Oracle Cloud (Ubuntu, aarch64). Caddy (HTTPS otomatis) → Uvicorn (systemd), plus systemd timer untuk scraper harian.
- **Frontend**: [Vercel](https://vercel.com) (Vite Frontend + Environment Variable `VITE_API_BASE_URL`).

### Setup VPS (sekali saja)

1. Di Oracle Cloud Console: **Networking → VCN → Security List**, tambah Ingress Rule TCP port **80** dan **443** dari `0.0.0.0/0`.
2. SSH ke VPS, lalu:
   ```bash
   git clone https://github.com/JasonAgung/tangogame.git ~/tangogame
   cd ~/tangogame
   ./deploy/setup.sh 168-110-212-220.sslip.io   # atau domain sendiri yang A record-nya ke IP VPS
   ```
3. Di Vercel, set `VITE_API_BASE_URL=https://168-110-212-220.sslip.io`, lalu redeploy.

### Update kode

```bash
cd ~/tangogame && git pull
venv/bin/pip install -r requirements.txt
sudo systemctl restart tango-api
```

### Cek status

```bash
systemctl status tango-api
systemctl list-timers tango-daily.timer
journalctl -u tango-daily.service -n 20
```

---

## Author & Credits

- **Developer**: Jason Kelvin Agung
- **Sumber Data Puzzle**: `tangounlimitedgame.com` *(inactive)*
- **Puzzle Harian**: LinkedIn Games (Tango). Project ini tidak berafiliasi dengan LinkedIn.

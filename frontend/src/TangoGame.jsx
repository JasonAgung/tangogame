import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Komponen Cell untuk menampilkan kotak individu (matahari atau bulan)
function Cell({ value, isGiven, isViolating, onClick }) {
  let content = "";
  if (value === "Sun") {
    content = "☀️";
  } else if (value === "Moon") {
    content = "🌑";
  }

  let className = "w-14 h-14 border-2 flex items-center justify-center text-2xl cursor-pointer transition-all select-none ";
  
  // logika warna border (Garis Tepi)
  if (isViolating) {
    className += "border-red-600 z-10 "; // Merah jika melanggar
  } else if (isGiven) {
    className += "border-gray-500 ";     // Abu-abu gelap jika soal asli
  } else {
    className += "border-gray-400 ";     // Abu-abu terang jika sel kosong/biasa
  }

  // logika warna bg (Latar Belakang)
  if (isGiven) {
    className += "bg-gray-200 cursor-not-allowed "; // Tetap abu-abu jika soal asli
  } else if (isViolating) {
    className += "bg-red-100 hover:bg-red-200 ";    // Merah muda jika user salah isi
  } else {
    className += "bg-white hover:bg-gray-50 ";      // Putih jika sel biasa
  }

  return (
    <div 
      onClick={isGiven ? null : onClick} 
      className={className}
      style={{ WebkitTapHighlightColor: 'transparent' }}
    >
      {content}
    </div>
  );
}

// Komponen utama GameUI 
export default function GameUI() {
  const [mode, setModeState] = useState("user");
  const [grid, setGrid] = useState([
    ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""],
    ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""]
  ]);

  const [constraints, setConstraints] = useState([]);
  const [givens, setGivens] = useState([]);
  const [statusBar, setStatusBar] = useState("Sistem Siap.");
  const [evaluationMetrics, setEvaluationMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Fitur Highlight Violations
  const [violatingCells, setViolatingCells] = useState([]);
  const [highlightViolations, setHighlightViolations] = useState(true);

  // Fitur Heuristic Toggle (EXPERT)
  const [useHeuristic, setUseHeuristic] = useState(false);

  // State untuk pemilihan puzzle
  const [selectedDifficulty, setSelectedDifficulty] = useState("easy");
  const [selectedPuzzleNumber, setSelectedPuzzleNumber] = useState("1");

  // State Modal Cara Bermain
  const [showRulesModal, setShowRulesModal] = useState(false);

  useEffect(function() {
    start();
  }, []);

  // Effect: Jalankan validasi otomatis jika grid terisi penuh & Cek Pelanggaran Real-time
  useEffect(function() {
    let emptyCount = 0;
    for (let r = 0; r < 6; r++) {
      for (let c = 0; c < 6; c++) {
        if (grid[r][c] === "") emptyCount++;
      }
    }
    
    //givens ga 0 mastiin puzzle udh ke load
    if (!loading && givens.length > 0) {
      onCheckViolationsRequest();
    }

    //kalau papan penuh
    if (emptyCount === 0 && !loading && givens.length > 0) {
      onValidateRequest();
    }
  }, [grid]);

  async function onCheckViolationsRequest() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/check_violations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          grid: grid,
          constraints: constraints
        }),
      });
      const data = await response.json();
      if (data.status === "success") {
        setViolatingCells(data.violating_cells);
      }
    } catch (e) {
      console.error("Gagal cek pelanggaran:", e);
    }
  }

  async function onValidateRequest() {
    showStatus("Memvalidasi...");
    try {
      const response = await fetch(`${API_BASE_URL}/api/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          grid: grid,
          constraints: constraints
        }),
      });
      const data = await response.json();
      if (data.status === "success") {
        showStatus("🎉 " + data.message);
      } else {
        showStatus("❌ " + data.message);
      }
    } catch (e) {
      console.error(e);
      showStatus("Gagal validasi.");
    }
  }

  function start() {
    showStatus("Selamat datang!");
    onLoadPuzzle("easy", "1");
  }

  function setMode(m) {
    setModeState(m);
    showStatus("Mode: " + m.toUpperCase());
  }

  function showStatus(msg) {
    setStatusBar(msg);
  }

  function updateCell(row, col) {
    for (let i = 0; i < givens.length; i++) {
      if (givens[i][0] === row && givens[i][1] === col) return;
    }
    const newGrid = [];
    for (let i = 0; i < 6; i++) {
      newGrid.push([...grid[i]]);
    }
    const val = newGrid[row][col];
    if (val === "") newGrid[row][col] = "Sun";
    else if (val === "Sun") newGrid[row][col] = "Moon";
    else newGrid[row][col] = "";
    setGrid(newGrid);
  }

  function resetBoard() {
    const newGrid = [];
    for (let r = 0; r < 6; r++) {
      const newRow = [];
      for (let c = 0; c < 6; c++) {
        let isGiven = false;
        for (let i = 0; i < givens.length; i++) {
          if (givens[i][0] === r && givens[i][1] === c) isGiven = true;
        }
        if (isGiven) newRow.push(grid[r][c]);
        else newRow.push("");
      }
      newGrid.push(newRow);
    }
    setGrid(newGrid);
    setViolatingCells([]);
    showStatus("Papan telah di-reset ke soal awal.");
  }

  function showSolution(solutionGrid) {
    setGrid(solutionGrid);
    showStatus("Puzzle Berhasil Dipecahkan!");
  }

  function showEvaluation(metrics) {
    setEvaluationMetrics(metrics);
  }

  //penamaan aja, kalau di json itu S, diubah jadi Sun
  function konversiGrid(jsonGrid) {
    const hasil = [];
    for (let r = 0; r < 6; r++) {
      const baris = [];
      for (let c = 0; c < 6; c++) {
        const item = jsonGrid[r][c];
        if (item === "S") baris.push("Sun");
        else if (item === "M") baris.push("Moon");
        else baris.push("");
      }
      hasil.push(baris);
    }
    return hasil;
  }

  //saat manggil solver, puzzle dikirimkan ke backend melalui fungsi ini menghapus input user
  function bersihkanGridUntukSolver() {
    const cleanGrid = [
      ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""],
      ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""]
    ];
    for (let i = 0; i < givens.length; i++) {
      const r = givens[i][0];
      const c = givens[i][1];
      cleanGrid[r][c] = grid[r][c];
    }
    return cleanGrid;
  }

  async function onLoadPuzzle(diff, num) {
    setLoading(true);
    showStatus("Menghubungi server...");
    try {
      const response = await fetch(`${API_BASE_URL}/api/puzzle?difficulty=${diff}&number=${num}`);
      if (!response.ok) throw new Error("Puzzle tidak ditemukan");
      const data = await response.json();
      setGrid(konversiGrid(data.grid));
      setGivens(data.givens);
      setConstraints(data.constraints);
      setEvaluationMetrics(null);
      setViolatingCells([]);
      showStatus(`Puzzle ${diff} #${num} dimuat.`);
    } catch (error) {
      showStatus("Gagal memuat puzzle.");
    } finally {
      setLoading(false);
    }
  }

  function handleDifficultyChange(e) {
    const newDiff = e.target.value;
    setSelectedDifficulty(newDiff);
    onLoadPuzzle(newDiff, selectedPuzzleNumber);
  }

  function handlePuzzleNumberChange(e) {
    const newNum = e.target.value;
    setSelectedPuzzleNumber(newNum);
    onLoadPuzzle(selectedDifficulty, newNum);
  }
  
  // Fungsi untuk memilih puzzle secara acak (1-100)
  function handleRandomPuzzle() {
    const randomNum = Math.floor(Math.random() * 100) + 1;
    setSelectedPuzzleNumber(randomNum.toString());
    onLoadPuzzle(selectedDifficulty, randomNum);
  }

  async function onSolveRequest(solverType) {
    setLoading(true);
    showStatus("Menghitung solusi (" + solverType + ")...");
    const cleanGrid = bersihkanGridUntukSolver();
    try {
      const response = await fetch(`${API_BASE_URL}/api/solve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          grid: cleanGrid,
          constraints: constraints,
          solver_type: solverType,
          use_heuristic: useHeuristic 
        }),
      });
      const data = await response.json();
      if (data.status === "success") {
        showSolution(data.solution);
        if (mode === "expert") showEvaluation(data.stats);
      } else {
        showStatus("Gagal: " + data.message);
      }
    } catch (e) {
      showStatus("Server Error (Port 8000).");
    } finally {
      setLoading(false);
    }
  }

  function renderRelation(c, index) {
    const r1 = c.cells[0][0]; const c1 = c.cells[0][1];
    const r2 = c.cells[1][0]; const c2 = c.cells[1][1];
    //56 itu panjang kotak plus 4 jarak gap = 60 , 36 posisi titik tengah kotak pertama kiri atas
    const top = 36 + ((r1 + r2) / 2) * 60;
    const left = 36 + ((c1 + c2) / 2) * 60;
    let warnaTeks = c.relationValue === "x" ? "text-red-500" : "text-blue-600";
    return (
      <div key={"const-" + index} className="absolute z-10 pointer-events-none transform -translate-x-1/2 -translate-y-1/2 select-none" style={{ top: top + "px", left: left + "px" }}>
        <div className="w-6 h-6 bg-white rounded-full border border-gray-200 shadow-md flex items-center justify-center">
          <span className={"text-xs font-bold " + warnaTeks}>{c.relationValue}</span>
        </div>
      </div>
    );
  }

  const puzzleNumbers = [];
  for (let i = 1; i <= 101; i++) {
    puzzleNumbers.push(<option key={i} value={i}>No. {i}</option>);
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen w-screen bg-slate-50 font-sans text-slate-900 select-none overflow-hidden">
      <div className="mb-4 text-center flex flex-col items-center">
        <h1 className="text-3xl font-black tracking-tight mb-1">TANGO GAME</h1>
        
        {/* Tombol Cara Bermain */}
        <button 
          onClick={() => setShowRulesModal(true)}
          className="mb-2 bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 font-bold px-3 py-1 rounded-full text-xs transition-all shadow-sm flex items-center gap-1.5 cursor-pointer active:scale-95"
        >
          <span>📖</span> Cara Bermain
        </button>

        <div className="bg-slate-800 text-white px-4 py-1 rounded text-xs uppercase tracking-widest">{statusBar}</div>
      </div>
      <div className="flex items-center gap-2 mb-6">
        <div className="flex gap-2 bg-slate-200 p-1 rounded-lg">
          <button onClick={() => setMode("user")} className={"px-4 py-1 rounded-md text-sm font-bold " + (mode === "user" ? "bg-white shadow" : "")}>USER</button>
          <button onClick={() => setMode("expert")} className={"px-4 py-1 rounded-md text-sm font-bold " + (mode === "expert" ? "bg-white shadow" : "")}>EXPERT</button>
        </div>

        {/* Petunjuk Mode */}
        <div className="relative group cursor-help flex items-center justify-center">
          <div className="w-5 h-5 rounded-full border border-slate-400 text-slate-500 hover:border-slate-600 hover:text-slate-700 hover:bg-slate-100 flex items-center justify-center text-xs font-bold transition-all select-none">
            ?
          </div>
          {/* Tooltip Box */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-64 bg-slate-800 text-slate-100 text-xs rounded-lg p-3 shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 pointer-events-none">
            <p className="font-bold border-b border-slate-700 pb-1 mb-1 text-white">Panduan Mode</p>
            <div className="space-y-1.5 text-[11px] leading-relaxed">
              <p>
                <span className="text-blue-400 font-bold">USER:</span> Mode interaktif bermain puzzle. Hanya terdapat opsi penyelesaian otomatis menggunakan Backtracking.
              </p>
              <p>
                <span className="text-emerald-400 font-bold">EXPERT:</span> Mode analisis kinerja. Menampilkan metrik evaluasi (waktu & iterasi) serta membandingkan solver Backtracking vs Simulated Annealing.
              </p>
            </div>
            {/* Segitiga panah tooltip pointing up */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800"></div>
          </div>
        </div>
      </div>
      <div className="relative bg-slate-300 p-2 rounded-lg shadow-xl border-4 border-slate-800">
        <div className="grid grid-cols-6 gap-1">
          {/* untuk setiap baris, dan untuk setiap kolom */}
          {grid.map((row, rIdx) => row.map((val, cIdx) => {
            let isGiven = false;
            //ngecek kalau cell ini masuk ga dalam givens, (nanti stylingnya beda)
            for(let g of givens) if(g[0] === rIdx && g[1] === cIdx) isGiven = true;
            let isViolating = false;
            //ngecek juga kalau cell nya itu termasuk ke salah satu daftar cell melangagr atau ngga
            if (highlightViolations) {
              for (let v of violatingCells) if (v[0] === rIdx && v[1] === cIdx) isViolating = true;
            }
            return <Cell key={rIdx+"-"+cIdx} value={val} isGiven={isGiven} isViolating={isViolating} onClick={() => updateCell(rIdx, cIdx)} />;
          }))}
        </div>
        {/* render simbol relasi */}
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
          {constraints.map((c, i) => renderRelation(c, i))}
        </div>
      </div>
      <div className="mt-6 flex flex-col gap-4 w-full max-w-sm">
        
        {/* Kontrol Checkbox (Highlight & Heuristic), Heuristic kalau di mode expert */}
        <div className="flex items-center justify-center gap-4 mb-1">
          <div className="flex items-center gap-1">
            <input type="checkbox" id="highlight" checked={highlightViolations} onChange={(e) => setHighlightViolations(e.target.checked)} className="w-4 h-4 cursor-pointer" />
            <label htmlFor="highlight" className="text-[10px] font-bold cursor-pointer text-slate-600 uppercase tracking-tighter">Highlight Violations</label>
          </div>

          {mode === "expert" && (
            <div className="flex items-center gap-1">
              <input type="checkbox" id="useHeuristic" checked={useHeuristic} onChange={(e) => setUseHeuristic(e.target.checked)} className="w-4 h-4 cursor-pointer" />
              <label htmlFor="useHeuristic" className="text-[10px] font-bold cursor-pointer text-blue-600 uppercase tracking-tighter underline">Use Heuristic (BT)</label>
            </div>
          )}
        </div>

        {/* kalau user cuman ada tombol solve, expert ada dua */}       
        {mode === "user" ? (
          <button onClick={() => onSolveRequest("backtracking")} disabled={loading} className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all shadow-[0_4px_0_0_rgba(29,78,216,1)] active:shadow-none active:translate-y-1">
            {loading ? "MENGHITUNG..." : "SOLVE PUZZLE"}
          </button>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            <button onClick={() => onSolveRequest("backtracking")} disabled={loading} className="bg-blue-600 text-white font-bold py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all shadow-[0_4px_0_0_rgba(29,78,216,1)] active:shadow-none active:translate-y-1">
              {loading ? "..." : "SOLVE: BT"}
            </button>
            <button onClick={() => onSolveRequest("sa")} disabled={loading} className="bg-emerald-600 text-white font-bold py-3 rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-[0_4px_0_0_rgba(5,150,105,1)] active:shadow-none active:translate-y-1">
              {loading ? "..." : "SOLVE: SA"}
            </button>
          </div>
        )}
        <div className="flex gap-2">
          {/* Dropdown Difficulty tetap ada di kedua mode */}
          <select value={selectedDifficulty} onChange={handleDifficultyChange} className="flex-1 bg-white border-2 border-slate-800 px-2 py-2 rounded-lg font-bold text-xs outline-none cursor-pointer">
            <option value="easy">EASY</option>
            <option value="medium">MEDIUM</option>
            <option value="hard">HARD</option>
          </select>

          {/* Conditional Rendering: new puzzle (user) vs dropdown (expert) */}
          {mode === "user" ? (
            <button 
              onClick={handleRandomPuzzle}
              className="flex-[1.5] bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-2 py-2 rounded-lg text-[10px] transition-all shadow-[0_4px_0_0_rgba(67,56,202,1)] active:shadow-none active:translate-y-1"
            >
              NEW PUZZLE
            </button>
          ) : (
            <select value={selectedPuzzleNumber} onChange={handlePuzzleNumberChange} className="flex-1 bg-white border-2 border-slate-800 px-2 py-2 rounded-lg font-bold text-xs outline-none cursor-pointer">
              {puzzleNumbers}
            </select>
          )}

          <button onClick={resetBoard} className="flex-1 bg-orange-500 hover:bg-orange-600 text-white font-bold px-4 py-2 rounded-lg text-xs transition-all shadow-[0_4px_0_0_rgba(194,65,12,1)] active:shadow-none active:translate-y-1">RESET</button>
        </div>
      </div>
      {mode === "expert" && evaluationMetrics && (
        <div className="mt-4 p-3 bg-white border-2 border-slate-800 rounded-lg shadow-md w-full max-w-sm">
          <h2 className="font-bold border-b pb-1 mb-1 text-slate-700 text-sm">Metrics Analysis</h2>
          <div className="text-xs space-y-1">
            <div className="flex justify-between"><span>Iterations:</span> <b className="text-blue-600">{evaluationMetrics.iterations}</b></div>
            <div className="flex justify-between"><span>Execution Time:</span> <b className="text-blue-600">{evaluationMetrics.time}</b></div>
            <div className="flex justify-between"><span>Final Cost:</span> <b className="text-blue-600">{evaluationMetrics.final_cost}</b></div>
          </div>
        </div>
      )}

      {/* Notice sumber data & credit */}
      <div className="mt-4 text-[10px] text-slate-400 text-center select-text space-y-1">
        <div>
          Sumber data puzzle:{" "}
          <a 
            href="https://www.tangounlimitedgame.com/" 
            target="_blank" 
            rel="noopener noreferrer" 
            className="underline hover:text-slate-500 transition-colors font-semibold"
          >
            tangounlimitedgame.com
          </a>
        </div>
        <div className="font-medium text-slate-500">
          Made by <span className="font-semibold text-slate-700">Jason Kelvin Agung</span>
        </div>
      </div>

      {/* Modal Cara Bermain / Game Rules */}
      {showRulesModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border-2 border-slate-800 rounded-xl p-5 max-w-md w-full shadow-2xl space-y-4 relative text-left animate-in fade-in zoom-in duration-200">
            {/* Header Modal */}
            <div className="border-b pb-2">
              <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                <span>📖</span> Cara Bermain Tango Puzzle
              </h3>
            </div>

            {/* Isi Aturan */}
            <div className="space-y-3 text-xs text-slate-600 leading-relaxed max-h-[60vh] overflow-y-auto pr-1">
              <div className="p-2.5 bg-slate-50 border rounded-lg space-y-1">
                <p className="font-bold text-slate-800 flex items-center gap-1.5">
                  <span>1️⃣</span> Keseimbangan Simbol (3☀️ & 3🌑)
                </p>
                <p>Setiap baris dan kolom pada papan 6x6 harus berisi <b>tepat 3 Matahari (☀️)</b> dan <b>3 Bulan (🌑)</b>.</p>
              </div>

              <div className="p-2.5 bg-slate-50 border rounded-lg space-y-1">
                <p className="font-bold text-slate-800 flex items-center gap-1.5">
                  <span>2️⃣</span> Maksimal 2 Simbol Berurutan
                </p>
                <p>Dilarang menempatkan 3 simbol yang sama secara berturut-turut dalam satu baris atau kolom (misal: ☀️☀️☀️ atau 🌑🌑🌑 itu <b>salah</b>).</p>
              </div>

              <div className="p-2.5 bg-slate-50 border rounded-lg space-y-1">
                <p className="font-bold text-slate-800 flex items-center gap-1.5">
                  <span>3️⃣</span> Simbol Relasi Petunjuk
                </p>
                <ul className="list-disc list-inside space-y-1 pl-1">
                  <li><span className="font-bold text-blue-600 border px-1.5 py-0.5 rounded bg-blue-50 text-[11px]">=</span> : Dua petak bersebelahan harus ber-simbol <b>SAMA</b>.</li>
                  <li><span className="font-bold text-red-500 border px-1.5 py-0.5 rounded bg-red-50 text-[11px]">x</span> : Dua petak bersebelahan harus ber-simbol <b>BERBEDA</b>.</li>
                </ul>
              </div>

              <div className="p-2.5 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-[11px]">
                💡 <b>Tips:</b> Aktifkan opsi <i>Highlight Violations</i> di bawah papan untuk langsung melihat petak mana yang melanggar aturan.
              </div>
            </div>

            {/* Footer Modal / Tombol Tutup */}
            <button 
              onClick={() => setShowRulesModal(false)}
              className="w-full bg-slate-800 hover:bg-slate-900 text-white font-bold py-2.5 rounded-lg text-xs transition-all shadow-md active:translate-y-0.5 cursor-pointer"
            >
              Mengerti & Mulai Bermain
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

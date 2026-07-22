import random
import math
import copy
import time
from typing import Tuple, Optional, Dict
from .models import Puzzle

class BacktrackingSolver:
    def __init__(self, useHeuristic: bool = True, maxNodes: int = 10000):
        self.useHeuristic = useHeuristic
        self.maxNodes = maxNodes
        self.nodesExplored = 0 

    def solve(self, p: Puzzle) -> Optional[Puzzle]:
        self.nodesExplored += 1
        
        # 1. kalau semua sel udah terisi
        if p.isComplete():
            return p

        # 2. pilih sel kosong berikutnya
        row, col = self.selectVariable(p)

        # 3. iterasi domain: Coba nilai 'Sun' terus 'Moon'
        for value in ["Sun", "Moon"]:
            
            # 4. cek konsistensi: 
            if self.isConsistent(row, col, value, p):
                
                # 5. masukkan nilai
                p.applyMove(row, col, value)

                # 6. rekursi
                result = self.solve(p)
                
                # kalau hasil rekursi bukan None, berarti solusi ditemukan
                if result is not None:
                    return result

                # 7. backtrack: Batalkan pilihan kalau jalan ini buntu
                p.undoMove(row, col)

        # 8. Failure: kalau tidak ada nilai yang cocok di sel ini
        return None

    def selectVariable(self, p: Puzzle) -> Tuple[int, int]:
        # tanpa heuristik
        if not self.useHeuristic:
            for r in range(6):
                for c in range(6):
                    if p.grid[r][c] == "":
                        return (r, c)
            return (-1, -1)

        # pakai heuristik
        best_row, best_col = -1, -1
        highest_priority = -1

        for r in range(6):
            for c in range(6):
                if p.grid[r][c] == "":
                    priority = 1 # prioritas dasar
                    
                    #  HEURISTIK RELASI
                    for cons in p.constraints:
                        if cons.type == "relation" and (r, c) in cons.cells:
                            priority = 2
                    
                    # HEURISTIK ADJACENCY (XX_, _XX, X_X)
                    # Horizontal
                    if (c >= 2 and p.grid[r][c-1] != "" and p.grid[r][c-1] == p.grid[r][c-2]) or \
                       (c <= 3 and p.grid[r][c+1] != "" and p.grid[r][c+1] == p.grid[r][c+2]) or \
                       (c >= 1 and c <= 4 and p.grid[r][c-1] != "" and p.grid[r][c-1] == p.grid[r][c+1]):
                        priority = 3
                    
                    # Vertikal
                    if (r >= 2 and p.grid[r-1][c] != "" and p.grid[r-1][c] == p.grid[r-2][c]) or \
                       (r <= 3 and p.grid[r+1][c] != "" and p.grid[r+1][c] == p.grid[r+2][c]) or \
                       (r >= 1 and r <= 4 and p.grid[r-1][c] != "" and p.grid[r-1][c] == p.grid[r+1][c]):
                        priority = 3

                    # (c) HEURISTIK BALANCE (3:3)
                    if [p.grid[r][i] for i in range(6)].count("Sun") == 3 or \
                       [p.grid[r][i] for i in range(6)].count("Moon") == 3 or \
                       [p.grid[i][c] for i in range(6)].count("Sun") == 3 or \
                       [p.grid[i][c] for i in range(6)].count("Moon") == 3:
                        priority = 3

                    if priority > highest_priority:
                        highest_priority = priority
                        best_row, best_col = r, c
                    
                    if highest_priority == 3:
                        return (best_row, best_col)

        return (best_row, best_col)

    def isConsistent(self, row: int, col: int, value: str, p: Puzzle) -> bool:
        # hanya cek aturan yang melibatkan sel ini saja.
        p.applyMove(row, col, value)
        
        consistent = True
        for c in p.constraints:
            # jika sel yang baru diisi (row, col) ada dalam daftar sel yang dipantau aturan ini
            if (row, col) in c.cells:
                # cek apakah aturan ini dilanggar
                if not c.isSatisfied(p):
                    consistent = False
                    break
        
        p.undoMove(row, col)
        return consistent

class SimulatedAnnealingSolver:
    def __init__(self, initialTemperature: float = 1.0, coolingRate: float = 0.9999, maxIterations: int = 5000):
        self.initialTemperature = initialTemperature
        self.coolingRate = coolingRate
        self.maxIterations = maxIterations
        # simpan sel yang bisa diubah, dikelompokkan per baris
        self.cells_per_row = [[] for _ in range(6)] 

    def solve(self, p: Puzzle) -> Tuple[Puzzle, Dict]:
        start_time = time.time()
        
        # 1. inisialisasi state awal (Semi-Greedy: Baris Seimbang)
        current_state = self.initialState(p)
        current_cost = self.cost(current_state)
        
        best_state = copy.deepcopy(current_state)
        best_cost = current_cost
        
        temperature = self.initialTemperature
        stats = {"iterations": 0, "final_cost": 0, "time": 0}

        for i in range(self.maxIterations):
            stats["iterations"] = i + 1
            if current_cost == 0:
                break
            
            # 2. generate tetangga (Tukar dua sel dalam satu baris)
            next_state = self.neighbor(current_state)
            next_cost = self.cost(next_state)
            
            delta_E = next_cost - current_cost
            
            if delta_E < 0:
                accept = True
            else:
                prob = math.exp(-delta_E / temperature)
                accept = random.random() < prob
            
            if accept:
                current_state = next_state
                current_cost = next_cost
                if current_cost < best_cost:
                    best_state = copy.deepcopy(current_state)
                    best_cost = current_cost
            
            temperature *= self.coolingRate

        end_time = time.time()
        stats["final_cost"] = best_cost
        stats["time"] = f"{round(end_time - start_time, 4)}s"
        
        return (best_state, stats)

    def initialState(self, p: Puzzle) -> Puzzle:
        #  isi sel kosong tiap baris agar jumlah Sun dan Moon tepat 3:3.

        new_p = copy.deepcopy(p)
        self.cells_per_row = [[] for _ in range(6)]
        
        for r in range(6):
            # 1. hitung berapa Sun dan Moon yang udah ada (soal asli)
            suns_ada = new_p.grid[r].count("Sun")
            moons_ada = new_p.grid[r].count("Moon")
            
            # 2. hitung berapa sisanya yang dibutuhkan agar jadi 3:3
            suns_butuh = 3 - suns_ada
            moons_butuh = 3 - moons_ada
            
            # 3. buat daftar simbol yang akan dimasukkan
            pool = (["Sun"] * suns_butuh) + (["Moon"] * moons_butuh)
            random.shuffle(pool)
            
            # 4. isi kotak kosong di baris ini dengan pool tersebut
            pool_idx = 0
            for c in range(6):
                if new_p.grid[r][c] == "":
                    new_p.grid[r][c] = pool[pool_idx]
                    self.cells_per_row[r].append(c) # Catat kolom yang bisa di-swap
                    pool_idx += 1
                    
        return new_p

    def neighbor(self, state: Puzzle) -> Puzzle:
        # pilih satu baris acak, lalu menukar isi dua sel (bukan soal asli).
        new_state = copy.deepcopy(state)
        
        # pilih baris yang punya minimal 2 sel bebas untuk ditukar
        possible_rows = []
        for r in range(6):
            if len(self.cells_per_row[r]) >= 2:
                possible_rows.append(r)
        
        if not possible_rows:
            return new_state

        r = random.choice(possible_rows)
        
        # pilih dua kolom acak dari daftar sel bebas di baris r
        c1, c2 = random.sample(self.cells_per_row[r], 2)
        
        # lakukan penukaran (Swap)
        temp = new_state.grid[r][c1]
        new_state.grid[r][c1] = new_state.grid[r][c2]
        new_state.grid[r][c2] = temp
            
        return new_state

    def cost(self, state: Puzzle) -> int:
        total_violations = 0
        for c in state.constraints:
            total_violations += c.violationCount(state)
        return total_violations

from typing import List, Tuple, Optional

class Constraint:
    def __init__(self, constraint_type: str, cells: List[Tuple[int, int]], relation_value: str = ""):
        # 'relation', 'noThree', atau 'count'
        self.type = constraint_type
        # daftar koordinat (row, col) yang terlibat dalam aturan ini
        self.cells = cells
        # dipake kalau type adalah 'relation' ('=' atau 'x')
        self.relation_value = relation_value

    def getViolations(self, p: 'Puzzle') -> List[Tuple[int, int]]:
        # Mengembalikan daftar koordinat yang terlibat dalam pelanggaran aturan ini. Untuk UI
        
        # 1. Pelanggaran Relasi (= atau x)
        if self.type == "relation":
            r1, c1 = self.cells[0]
            r2, c2 = self.cells[1]
            val1 = p.grid[r1][c1]
            val2 = p.grid[r2][c2]
            if val1 == "" or val2 == "": return []
            
            if self.relation_value == "=" and val1 != val2:
                return [(r1, c1), (r2, c2)]
            if self.relation_value == "x" and val1 == val2:
                return [(r1, c1), (r2, c2)]

        # 2. Pelanggaran 3 Berurutan (noThree)
        elif self.type == "noThree":
            vals = [p.grid[r][c] for r, c in self.cells]
            if "" not in vals and vals[0] == vals[1] == vals[2]:
                return self.cells # Ketiga sel terlibat pelanggaran

        # 3. Pelanggaran Jumlah (count: maksimal 3 Sun/Moon)
        elif self.type == "count":
            vals = [p.grid[r][c] for r, c in self.cells]
            suns = vals.count("Sun")
            moons = vals.count("Moon")
            
            if suns > 3 or moons > 3:
                # Jika lebih dari 3, tandai semua sel dengan simbol yang berlebih di baris/kolom itu
                violated_symbol = "Sun" if suns > 3 else "Moon"
                return [(r, c) for r, c in self.cells if p.grid[r][c] == violated_symbol]
        
        return []

    def isSatisfied(self, p: 'Puzzle') -> bool:
        # cek apakah aturan ini terpenuhi berdasarkan kondisi grid saat ini.

        # relasi (= atau x)
        if self.type == "relation":
            r1, c1 = self.cells[0]
            r2, c2 = self.cells[1]
            val1 = p.grid[r1][c1]
            val2 = p.grid[r2][c2]
            if val1 == "" or val2 == "": return True # kalau belum lengkap, skip
            if self.relation_value == "=": return val1 == val2
            if self.relation_value == "x": return val1 != val2

        # tidak boleh ada 3 berurutan
        elif self.type == "noThree":
            vals = [p.grid[r][c] for r, c in self.cells]
            # kalau ada yang kosong, tidak mungkin melanggar aturan 3 berurutan
            if "" in vals: return True
            # Melanggar kalau ketiga sel isinya sama
            return not (vals[0] == vals[1] == vals[2])

        # jumlah seimbang
        elif self.type == "count":
            vals = [p.grid[r][c] for r, c in self.cells]
            suns = vals.count("Sun")
            moons = vals.count("Moon")
            # Tidak boleh ada yang lebih dari 3
            if suns > 3 or moons > 3:
                return False
            return True
        
        return True

    def violationCount(self, p: 'Puzzle') -> int:
        # Menghitung skor pelanggaran.
        # Semakin besar angkanya, semakin buruk kondisi papan bagi Simulated Annealing.

        # untuk tipe 'count', dihitung seberapa banyak simbol yang melebihi batas
        if self.type == "count":
            vals = [p.grid[r][c] for r, c in self.cells]
            suns = vals.count("Sun")
            moons = vals.count("Moon")
            
            # Hitung lebihnya brp
            surplus_sun = max(0, suns - 3)
            surplus_moon = max(0, moons - 3)
            
            return surplus_sun + surplus_moon

        # tipe lain (noThree, relation), skor tetap: 0 atau 1
        return 0 if self.isSatisfied(p) else 1

class Puzzle:
    def __init__(self):
        self.grid = [["" for _ in range(6)] for _ in range(6)]
        self.constraints: List[Constraint] = []
        
        # tambahkan aturan global secara otomatis saat objek dibuat
        self._add_global_constraints()

    def _add_global_constraints(self):
        # tempel aturan standar Tango (NoThree dan Count) untuk seluruh papan.

        # tambahkan Aturan 'count' (3 Sun, 3 Moon per Baris & Kolom)
        for i in range(6):
            # Baris i
            self.constraints.append(Constraint("count", [(i, j) for j in range(6)]))
            # Kolom i
            self.constraints.append(Constraint("count", [(j, i) for j in range(6)]))

        # tambahkan Aturan 'noThree' (Horizontal & Vertikal)
        for r in range(6):
            for c in range(4):
                # Horizontal: (r,c), (r,c+1), (r,c+2)
                self.constraints.append(Constraint("noThree", [(r, c), (r, c+1), (r, c+2)]))
        for c in range(6):
            for r in range(4):
                # Vertikal: (r,c), (r+1,c), (r+2,c)
                self.constraints.append(Constraint("noThree", [(r, c), (r+1, c), (r+2, c)]))

    def isComplete(self) -> bool:
        for r in range(6):
            for c in range(6):
                if self.grid[r][c] == "": return False
        return True

    def isValid(self) -> bool:
        # Cek semua objek constraint.
        for c in self.constraints:
            if not c.isSatisfied(self):
                return False
        return True

    def applyMove(self, row: int, col: int, value: str):
        self.grid[row][col] = value

    def undoMove(self, row: int, col: int):
        self.grid[row][col] = ""

    def getViolatingCells(self) -> List[Tuple[int, int]]:
        # Mengumpulkan semua koordinat sel yang melanggar dari seluruh constraint. Untuk UI
        all_violations = set()
        for c in self.constraints:
            v_cells = c.getViolations(self)
            for cell in v_cells:
                all_violations.add(cell)
        return list(all_violations)

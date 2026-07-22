import json
import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from .models import Puzzle, Constraint
from .solvers import BacktrackingSolver, SimulatedAnnealingSolver

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SolverRequest(BaseModel):
    grid: List[List[str]]
    constraints: List[dict] 
    solver_type: Optional[str] = "backtracking"
    use_heuristic: Optional[bool] = False

@app.get("/")
def read_root():
    return {"message": "Tango Puzzle Solver API"}

@app.get("/api/puzzle")
def get_puzzle(difficulty: str, number: int):
    file_number = str(number).zfill(3)
    file_name = f"{difficulty}_{file_number}.json"
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data_puzzle", difficulty, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Puzzle tidak ditemukan")
    
    with open(file_path, "r") as f:
        data = json.load(f)
    return data

@app.post("/api/solve")
def solve_puzzle(request: SolverRequest):
    my_puzzle = Puzzle()
    my_puzzle.grid = request.grid
    
    for c_data in request.constraints:
        new_c = Constraint(
            constraint_type=c_data["type"],
            cells=[(cell[0], cell[1]) for cell in c_data["cells"]],
            relation_value=c_data.get("relationValue", "")
        )
        my_puzzle.constraints.append(new_c)
    
    if request.solver_type == "backtracking":
        # Teruskan nilai use_heuristic dari request ke dalam solver
        solver = BacktrackingSolver(useHeuristic=request.use_heuristic)
        start_t = time.time()
        result_puzzle = solver.solve(my_puzzle)
        end_t = time.time()
        
        if result_puzzle:
            stats = {
                "iterations": solver.nodesExplored,
                "time": f"{round(end_t - start_t, 4)}s",
                "final_cost": 0
            }
            return {
                "status": "success", 
                "message": "Solusi ditemukan (Backtracking)", 
                "solution": result_puzzle.grid, 
                "stats": stats
            }
        else:
            return {"status": "error", "message": "Tidak ditemukan solusi"}
        
    elif request.solver_type == "sa":
        solver = SimulatedAnnealingSolver()
        result_puzzle, stats = solver.solve(my_puzzle)
        return {
            "status": "success", 
            "message": "Solusi ditemukan (Simulated Annealing)", 
            "solution": result_puzzle.grid, 
            "stats": stats
        }
    
    return {"status": "error", "message": "Unknown solver type"}

@app.post("/api/validate")
def validate_puzzle(request: SolverRequest):
    my_puzzle = Puzzle()
    my_puzzle.grid = request.grid
    
    for c_data in request.constraints:
        new_c = Constraint(
            constraint_type=c_data["type"],
            cells=[(cell[0], cell[1]) for cell in c_data["cells"]],
            relation_value=c_data.get("relationValue", "")
        )
        my_puzzle.constraints.append(new_c)
    
    if my_puzzle.isComplete() and my_puzzle.isValid():
        return {"status": "success", "message": "PUZZLE SOLVED!"}
    
    return {"status": "error", "message": "Belum tepat."}

@app.post("/api/check_violations")
def check_violations(request: SolverRequest):
    my_puzzle = Puzzle()
    my_puzzle.grid = request.grid
    
    for c_data in request.constraints:
        new_c = Constraint(
            constraint_type=c_data["type"],
            cells=[(cell[0], cell[1]) for cell in c_data["cells"]],
            relation_value=c_data.get("relationValue", "")
        )
        my_puzzle.constraints.append(new_c)
    
    violating_cells = my_puzzle.getViolatingCells()
    return {"status": "success", "violating_cells": violating_cells}

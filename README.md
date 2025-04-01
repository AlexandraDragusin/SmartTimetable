# Schedule Optimization using Hill-Climbing and A* Algorithms

## 📘 Overview

This project tackles the **timetable generation problem**, aiming to build class schedules that minimize or completely eliminate conflicts. Conflicts are categorized as:

- **Mandatory constraint violations** (must not occur in a valid schedule)
- **Optional constraint violations** (preferably avoided, but allowed)

Two search-based optimization algorithms are implemented:
- **Hill-Climbing with Random Restart**
- **A\* (A-Star) Search**

---

## 📁 Project Structure

- `orar.py` — Entry point script; accepts `astar` or `hc` as arguments along with the input filename.
- `hill_climbing.py` — Implementation of the Hill-Climbing algorithm.
- `astar.py` — Implementation of the A* algorithm.
- `check_constraints.py` — Defines and checks both mandatory and optional constraints.
- `utils.py` — Helper functions.
- `inputs/` — Contains input YAML files describing scheduling requirements.
- `outputs/` — Stores results of each algorithm.
- `refs/` — Reference outputs for comparison.
- `plot_results_hc/` — Contains graphs and logs from Hill-Climbing runs.

---

## 🧠 Algorithms

### Hill-Climbing (HC)

- Starts from a state satisfying all **mandatory constraints**
- Improves solution by selecting neighboring states with **fewer conflicts**
- Implements **Random Restart** to avoid local minima
- Limits:
  - `MAX_RESTARTS = 50`
  - `MAX_ITERATIONS = 100`
  - `MAX_GENERATED_NEIGHBORS = 10`

### A\* Search

- Starts from an **empty schedule**
- Uses a heuristic based on:
  - Current number of conflicts
  - Number of uncovered subjects
  - Number of empty classrooms
- Timeout after 240 seconds if no solution is found

---

## 📊 Performance Summary

| Test File                  | Algorithm       | Avg Time | Avg Conflicts | Avg States Generated |
|---------------------------|------------------|----------|----------------|------------------------|
| `dummy.yaml`              | Hill-Climbing    | 0.23s    | 0              | 474                    |
|                           | A*               | 0.0092s  | 0              | 159                    |
| `orar_mic_exact.yaml`     | Hill-Climbing    | 28.5s    | 2.3            | 11,718                 |
|                           | A*               | 1.1s     | 0              | 4,058                  |
| `orar_mediu_relaxat.yaml` | Hill-Climbing    | 20.1s    | 0              | 5,735                  |
|                           | A*               | 23.9s    | 0              | 61,419                 |
| `orar_mare_relaxat.yaml`  | Hill-Climbing    | 182s     | 5.95           | 32,433                 |
|                           | A*               | 69.6s    | 0              | 102,686                |

---

## 🧪 How to Run

```bash
python orar.py hc inputs/dummy.yaml
python orar.py astar inputs/orar_mediu_relaxat.yaml
```


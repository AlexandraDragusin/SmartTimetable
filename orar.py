import sys
import yaml
import astar
import hill_climbing

def main():
    if len(sys.argv) != 3:
        print("Mod de folosire: python orar.py <algorithm> <input_file>")
        return

    algorithm = sys.argv[1]
    input_file = sys.argv[2]

    # Extrag datele de intrare
    with open(input_file, 'r') as file:
        input_data = yaml.safe_load(file)

    if algorithm == "astar":
        astar.start(input_data, input_file)
    elif algorithm == "hc":
        hill_climbing.start(input_data, input_file)
    else:
        print("Algoritmul nu exista. Algoritmi: astar, hc")

if __name__ == "__main__":
    main()

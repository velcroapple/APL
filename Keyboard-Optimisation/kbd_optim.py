#!/usr/bin/env python3
"""
Keyboard Layout Optimization via Simulated Annealing


Notes:
- Cost is total Euclidean distance between consecutive characters.
- Coordinates are fixed (QWERTY-staggered grid). Optimization swaps assignments.

This base code uses Python "types" - these are optional, but very helpful
for debugging and to help with editing.

"""

import argparse
import math
import os
import random
#import string
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt  # type: ignore

Point = Tuple[float, float]
Layout = Dict[str, Point]

random.seed(42)  

def qwerty_coordinates(chars: str) -> Layout:
    """Return QWERTY grid coordinates for the provided character set.

    The grid is a simple staggered layout (units are arbitrary):
    - Row 0: qwertyuiop at y=0, x in [0..9]
    - Row 1: asdfghjkl at y=1, x in [0.5..8.5]
    - Row 2: zxcvbnm at y=2, x in [1..6]
    - Space at (4.5, 3)
    Characters not present in the grid default to the space position.
    """
    row0 = "qwertyuiop"
    row1 = "asdfghjkl"
    row2 = "zxcvbnm"

    coords: Layout = {}
    for i, c in enumerate(row0):
        coords[c] = (float(i), 0.0)
    for i, c in enumerate(row1):
        coords[c] = (0.5 + float(i), 1.0)
    for i, c in enumerate(row2):
        coords[c] = (1.0 + float(i), 2.0)
    coords[" "] = (4.5, 3.0)

    # Backfill for requested chars; unknowns get space position.
    space_xy = coords[" "]
    for ch in chars:
        if ch not in coords:
            coords[ch] = space_xy
    return coords


def initial_layout() -> Layout:
    """Create an initial layout mapping chars to some arbitrary positions of letters."""

    # Start with identity for letters and space; others mapped to space.
    base_keys = "abcdefghijklmnopqrstuvwxyz "

    # Get coords - or use coords of space as default
    layout = qwerty_coordinates(base_keys)

    # Randomize a bit to avoid local minima
    for _ in range(500):
        layout= get_neighbour(layout,list(base_keys))
    return layout


def preprocess_text(text: str, chars: str) -> str:
    """Lowercase and filter to the allowed character set; map others to space."""
    for i in range(len(text)):
        if text[i].lower() not in chars:
            # just replace with space
            text=text[:i]+' '+text[i+1:]
    #lowercase everything
    text = text.lower()
    return text
    

def path_length_cost(text: str, layout: Layout) -> float:
    """Sum Euclidean distances across consecutive characters in text."""
    dist=0
    for i in range(len(text)):
        #skip dist between first char and last char
        if i==0:
            continue
        x1,y1=layout[text[i-1]] 
        x2,y2=layout[text[i]] 
        dist+=math.sqrt((x2-x1)**2+(y2-y1)**2)
    return dist


######
# Define any other useful functions, such as to create new layout etc.
######
def get_neighbour(layout: Layout, chars: List[str]) -> Layout:
    """Create a new layout by swapping two random characters."""
    new_route = layout.copy()
    i, j = random.sample(range(len(layout)), 2)
    i=chars[i]
    j=chars[j]  
    new_route[i], new_route[j] = new_route[j], new_route[i]
    return new_route

# Dataclass is like a C struct - you can use it just to store data if you wish
# It provides some convenience functions for assignments, printing etc.
@dataclass
class SAParams:
    iters: int = 21000
    t0: float = 300.0  # Initial temperature setting
    alpha: float = 0.993  # geometric decay per iteration
    epoch: int = 100  # iterations per temperature step (1 = per-iter decay)


def simulated_annealing(
    text: str,
    layout: Layout,
    params: SAParams,
    chars: List[str],
) -> Tuple[Layout, float, List[float], List[float]]:
    """Simulated annealing to minimize path-length cost over character swaps.

    Returns best layout, best cost, and two lists:
    - best cost up to now (monotonically decreasing)
    - cost of current solution (may occasionally go up)
    These will be used for plotting
    """
    #parameters
    num_iterations, initial_temp, cooling_rate, epoch= params.iters, params.t0, params.alpha, params.epoch
    print(f"params : iters = {num_iterations}, intial temp = {initial_temp}, cooling rate = {cooling_rate}, epoch = {epoch}")
    current_layout = layout.copy()
    current_distance = path_length_cost(text,current_layout)
    
    best_layout = current_layout.copy()
    best_distance = current_distance
    
    temp = initial_temp
    distances = [current_distance]
    best_routes = [best_layout.copy()]
    best_distances = [best_distance] 
    
    for i in range(num_iterations):
        #get a neighbour layout and its distance
        neighbour_layout = get_neighbour(current_layout,chars)
        neighbour_distance = path_length_cost(text,neighbour_layout)
        
        #accept or reject the neighbour layout
        #as temp decreases (number of epochs increases), less likely to accept worse solutions
        p = math.exp((current_distance - neighbour_distance) / temp)
        # print(f"Prob[{i} = {p}")
        if neighbour_distance < current_distance or random.random() < p:
            current_layout = neighbour_layout.copy()
            current_distance = neighbour_distance
            
            if current_distance < best_distance:
                best_layout = current_layout.copy()
                best_distance = current_distance
        
        # every "epoch" iterations, reduce temp
        if (i+1)%epoch==0:
            temp *= cooling_rate
        
        #for logging purposes
        if (i+1)%1000==0:
            print(f"Iter {i+1}/{num_iterations} Current Cost: {current_distance:.4f} Best Cost: {best_distance:.4f} Temp: {temp:.4f}")
        distances.append(current_distance)
        best_routes.append(best_layout.copy())
        best_distances.append(best_distance)

    return best_routes[-1], best_distances[-1], best_distances, distances

def plot_costs(
    layout: Layout, best_trace: List[float], current_trace: List[float]
) -> None:

    # Plot cost trace
    out_dir = "."
    plt.figure(figsize=(6, 3))
    plt.plot(best_trace, lw=1.5)
    plt.plot(current_trace, lw=1.5)
    plt.xlabel("Iteration")
    plt.ylabel("Best Cost")
    plt.title("Best Cost vs Iteration")
    plt.tight_layout()
    path = os.path.join(out_dir, f"cost_trace.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")

    # Plot layout scatter
    xs, ys, labels = [], [], []
    for ch, (x, y) in layout.items():
        xs.append(x)
        ys.append(y)
        labels.append(ch)

    plt.figure(figsize=(6, 3))
    plt.scatter(xs, ys, s=250, c="#1f77b4")
    for x, y, ch in zip(xs, ys, labels):
        plt.text(
            x,
            y,
            ch,
            ha="center",
            va="center",
            color="white",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.15", fc="#1f77b4", ec="none", alpha=0.9),
        )
    plt.gca().invert_yaxis()
    plt.title("Optimized Layout")
    plt.axis("equal")
    plt.tight_layout()
    path = os.path.join(out_dir, f"layout.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


def load_text(filename) -> str:
    if filename is not None:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    # Fallback demo text
    return (
        "the quick brown fox jumps over the lazy dog\n"
        "APL is the best course ever\n"
    )


def main(filename: str | None = None, args=None) -> None:

    chars = "abcdefghijklmnopqrstuvwxyz "

    # Initial assignment - QWERTY
    layout0 = initial_layout()
    
    # Prepare text and evaluate baseline
    raw_text = load_text(filename)
    text = preprocess_text(raw_text, chars)
    baseline_cost = path_length_cost(text, layout0)
    print(f"Baseline (QWERTY assignment) cost: {baseline_cost:.4f}")

    # Annealing - give parameter values
    params = SAParams(
        iters=args.iters,
        t0=args.temp,
        alpha=args.alpha,
        epoch=args.epoch,
    )
    start = time.time()
    best_layout, best_cost, best_trace, current_trace = simulated_annealing(text, layout0, params, list(chars))
    dur = time.time() - start
    print(f"Optimized cost: {best_cost:.4f}  (improvement {(baseline_cost - best_cost):.4f})")
    print(f"Runtime: {dur:.2f}s over {params.iters} iterations")

    plot_costs(best_layout, best_trace, current_trace)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keyboard Layout Optimization")
    #parse the arguments from the command line
    parser.add_argument("filename", nargs="?", default=None, help="Input text file")
    parser.add_argument("--iters", type=int, default=21000, help="Number of iterations")
    parser.add_argument("--temp", type=float, default=600.0, help="Initial temperature")
    parser.add_argument("--alpha", type=float, default=0.993, help="Cooling rate")
    parser.add_argument("--epoch", type=int, default=100, help="Iterations per cooling step")
    args = parser.parse_args()

    main(args.filename, args)

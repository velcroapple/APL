"""
Tiny combinational logic simulator producing WaveDrom JSON.

Usage:
  python digitalsim.py path/to/circuit.net [--out out.json]

Input format sections (fixed order): INPUTS, OUTPUTS, GATES, STIMULUS.
Gates: OUT = AND(A, B) | OR(A, B) | XOR(A, B) | NOT(A)
"""

import sys
import argparse
from pathlib import Path
from typing import List


def parse_netlist(text: str):
    
    # delete empty lines and strip whitespace
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # check if the sections are there in order
    if not lines[0].startswith("INPUTS:"):
        raise ValueError("Expected 'INPUTS:' section in line 1")
    if not lines[1].startswith("OUTPUTS:"):
        raise ValueError("Expected 'OUTPUTS:' section in line 2")

    # names of inputs and outputs
    inputs = lines[0].split()[1:]
    outputs = lines[1].split()[1:]

    i = 2
    if lines[i] != "GATES:":
        raise ValueError("Expected 'GATES:' section")
    i += 1

    # Parse gates 
    all_gates = []
    while i < len(lines) and lines[i] != "STIMULUS:":
        lhs, rhs = lines[i].split("=")
        out = lhs.strip()
        type_part, args_part = rhs.strip().split("(")
        gate_type = type_part.strip()
        args = [a.strip().strip(")") for a in args_part.split(",")]
        all_gates.append({"out": out, "type": gate_type, "args": args})
        i += 1

    # Stimuli
    if i == len(lines) or lines[i] != "STIMULUS:":
        raise ValueError("Expected STIMULUS section")
    i += 1

    stimulus = []
    while i < len(lines):
        values = lines[i].split()[1:]
        if len(values) != len(inputs):
            raise ValueError("Stimulus length does not match number of inputs")
        stimulus.append(values)
        i += 1

    # order gates by dependency so we don't have to recursively evaluate each timestep
    # elborated in report 
    known = set(inputs)
    ordered_gates = []
    remaining = all_gates
    for gate in remaining:
        if gate["args"] not in known or gate["args"] not in all_gates:
            raise ValueError("Gate has unknown inputs")
    while remaining:
        progress = False
        for gate in remaining[:]:
            if all(arg in known for arg in gate["args"]):
                ordered_gates.append([gate["out"], gate["type"], gate["args"]])
                known.add(gate["out"])
                remaining.remove(gate)
                progress = True
        if not progress:
            raise ValueError("Unresolvable gate dependencies")

    return [inputs, outputs, ordered_gates, stimulus]


def eval_gate(state: dict, gate: list) -> int:
    # logic evaluation
    _, gate_type, input_names = gate
    # Gather evaluated inputs
    inputs = [state[name] for name in input_names]

    if gate_type == "AND":
        for input in inputs:
            if not input:
                return 0
        return 1
    elif gate_type == "OR":
        for input in inputs:
            if input:
                return 1
        return 0
    elif gate_type == "XOR":
        res = 0
        for inp in inputs:
            res ^= inp
        return res
    elif gate_type == "NOT":
        if len(inputs) != 1:
            raise ValueError("NOT gate must have exactly one input")
        return 1 - inputs[0]
    else:
        raise ValueError(f"Unknown gate type: {gate_type}")


def simulate(nl):
    """Simulate circuit over all stimulus vectors."""
    inputs, outputs, gates, stimulus = nl
    waves = []  # One string per timestep

    for inputs_at_timestep in stimulus:
        # Initialize state with current input values
        state = {inp: int(val) for inp, val in zip(inputs, inputs_at_timestep)}

        # Evaluate each gate in order
        for gate in gates:
            out, _, _ = gate
            state[out] = eval_gate(state, gate)

        # Record output values for this timestep
        wave_step = ''.join(str(state[out]) for out in outputs)
        waves.append(wave_step)
    return waves


def to_wavedrom_json(nl, waves):
    """Convert simulation results to WaveDrom JSON format (manual string build)."""
    inputs, outputs, _, stimulus = nl
    lines = []
    lines.append("{")
    lines.append('  "signal": [')

    # Inputs
    for idx, inp in enumerate(inputs):
        wave = ''.join(str(int(stim[idx])) for stim in stimulus)
        lines.append("    {")
        lines.append(f'      "name": "{inp}",')
        lines.append(f'      "wave": "{wave}"')
        lines.append("    },")

    # Outputs
    for j, out in enumerate(outputs):
        wave = ''.join(step[j] for step in waves)
        comma = "," if j != len(outputs) - 1 else ""
        lines.append("    {")
        lines.append(f'      "name": "{out}",')
        lines.append(f'      "wave": "{wave}"')
        lines.append("    }" + comma)

    lines.append("  ]")
    lines.append("}")
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    
    ap = argparse.ArgumentParser()
    ap.add_argument("netlist", help=".net file path")
    ap.add_argument("--out", "-o", help="output JSON path")
    args = ap.parse_args(argv)

    text = Path(args.netlist).read_text()
    nl = parse_netlist(text)
    waves = simulate(nl)
    js = to_wavedrom_json(nl, waves)

    # in case output path is not explicitly provided, use same name as netlist with .json extension
    out_path = args.out or str(Path(args.netlist).with_suffix(".json"))
    Path(out_path).write_text(js + "\n")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

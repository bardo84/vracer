"""
Verilog-AMS Parser for Race Detection

Parses a subset of Verilog-AMS (digital, no analog blocks) using pycomby
pattern matching. Converts to IRDesign for race detection.

Supported constructs:
- Module declarations
- Signal declarations: logic, real, wreal, reg, wire, input, output, inout
- Always blocks with sensitivity lists
- Assignments: blocking (=), nonblocking (<=), continuous (assign)
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass

from pycomby import pycomby

from vracer_core import (
    IRSignal, IRAssignment, IRProcess, IRDesign,
)


# =============================================================================
# Signal Kind Mapping
# =============================================================================

SIGNAL_KINDS_ORDERED = [
    ("wreal", "wreal"),
    ("logic", "logic"),
    ("reg", "logic"),
    ("wire", "wire"),
    ("input", "wire"),
    ("output", "wire"),
    ("inout", "wire"),
    ("real", "real"),
]

REGISTER_TYPES = {"reg", "logic"}


# =============================================================================
# Parsing Helpers
# =============================================================================

def _clean_text(text):
    """Remove comments from source text."""
    text = re.sub(r"//.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def _extract_always_blocks(text):
    """
    Extract always blocks with their sensitivity lists and bodies.
    Handles both 'begin...end' and single-statement forms.
    Returns list of (sensitivity_str, body_str).
    """
    blocks = []
    
    pattern = re.compile(
        r"always\s*@\s*\(([^)]+)\)\s*"
        r"(?:begin\s*(.*?)\s*end|([^;]+;))",
        re.DOTALL | re.IGNORECASE
    )
    
    for m in pattern.finditer(text):
        sens = m.group(1).strip()
        body = m.group(2) if m.group(2) is not None else m.group(3)
        body = body.strip() if body else ""
        blocks.append((sens, body))
    
    return blocks


def _parse_sensitivity_list(sens_str):
    """
    Parse sensitivity list like 'posedge clk or negedge rst or a or b'.
    Returns (signal_names, edge_kinds).
    """
    signals = []
    kinds = []
    
    sens_str = sens_str.strip()
    if sens_str == "*":
        return ["*"], ["combinational"]
    
    parts = re.split(r"\s+or\s+|\s*,\s*", sens_str, flags=re.IGNORECASE)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if part.lower().startswith("posedge "):
            sig = part[8:].strip()
            signals.append(sig)
            kinds.append("posedge")
        elif part.lower().startswith("negedge "):
            sig = part[8:].strip()
            signals.append(sig)
            kinds.append("negedge")
        else:
            signals.append(part)
            kinds.append("level")
    
    return signals, kinds


def _parse_assignments_in_block(body, src_location):
    """
    Extract assignments from an always block body.
    Handles both blocking (=) and nonblocking (<=) assignments.
    """
    assignments = []
    
    nb_pattern = ":[dst:word] <= :[src];"
    nb_matches = pycomby(body, nb_pattern)
    for m in nb_matches:
        dst = m.get("dst", "")
        src_expr = m.get("src", "")
        src_signals = _extract_signal_refs(src_expr)
        assignments.append(IRAssignment(
            src_signals=src_signals,
            dst_signal=dst,
            kind="nonblocking",
            src_location=src_location,
        ))
    
    body_no_nb = re.sub(r"\w+\s*<=\s*[^;]+;", "", body)
    
    b_pattern = ":[dst:word] = :[src];"
    b_matches = pycomby(body_no_nb, b_pattern)
    for m in b_matches:
        dst = m.get("dst", "")
        src_expr = m.get("src", "")
        if dst in ("begin", "end", "if", "else", "case", "endcase"):
            continue
        src_signals = _extract_signal_refs(src_expr)
        assignments.append(IRAssignment(
            src_signals=src_signals,
            dst_signal=dst,
            kind="blocking",
            src_location=src_location,
        ))
    
    return assignments


def _extract_signal_refs(expr):
    """
    Extract signal references from an expression.
    Finds all word tokens that look like identifiers.
    Excludes numeric literals, Verilog literals, and common keywords.
    """
    keywords = {
        "begin", "end", "if", "else", "case", "endcase", "for", "while",
        "assign", "always", "initial", "posedge", "negedge", "or", "and",
        "not", "xor", "nand", "nor", "xnor", "module", "endmodule",
    }
    
    expr_clean = re.sub(r"\d+'[bBhHdDoO][0-9a-fA-FxXzZ_]+", "", expr)
    expr_clean = re.sub(r"\d+\.\d+", "", expr_clean)
    
    tokens = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", expr_clean)
    signals = []
    for t in tokens:
        if t.lower() not in keywords and not t.isdigit():
            if t not in signals:
                signals.append(t)
    return signals


# =============================================================================
# Main Parser
# =============================================================================

def parse_vams(source, filename="<string>"):
    """
    Parse Verilog-AMS source into IRDesign.
    
    Args:
        source: Verilog-AMS source code
        filename: Source filename for error reporting
        
    Returns:
        IRDesign with signals and processes
    """
    text = _clean_text(source)
    
    signals = {}
    processes = []
    
    # --- Parse module header ---
    mod_matches = pycomby(text, "module :[name:word]")
    module_name = mod_matches[0]["name"] if mod_matches else "unknown"
    
    # --- Parse signal declarations ---
    for kind_keyword, kind_value in SIGNAL_KINDS_ORDERED:
        pattern = kind_keyword + " :[names];"
        matches = pycomby(text, pattern)
        for m in matches:
            names_str = m.get("names", "")
            for name in re.split(r"\s*,\s*", names_str):
                name = name.strip()
                name = re.sub(r"\[.*?\]", "", name).strip()
                if name and name not in signals:
                    signals[name] = IRSignal(
                        name=name,
                        kind=kind_value,
                        is_register=(kind_keyword in REGISTER_TYPES),
                    )
    
    # --- Parse always blocks ---
    always_blocks = _extract_always_blocks(text)
    
    for idx, (sens_str, body) in enumerate(always_blocks):
        
        triggers, trigger_kinds = _parse_sensitivity_list(sens_str)
        
        for sig in triggers:
            if sig != "*" and sig not in signals:
                signals[sig] = IRSignal(name=sig, kind="logic", is_register=False)
        
        src_loc = f"{filename}:always_{idx}"
        assignments = _parse_assignments_in_block(body, src_loc)
        
        for assign in assignments:
            if assign.dst_signal not in signals:
                signals[assign.dst_signal] = IRSignal(
                    name=assign.dst_signal,
                    kind="logic",
                    is_register=True,
                )
            for src in assign.src_signals:
                if src not in signals:
                    signals[src] = IRSignal(name=src, kind="logic", is_register=False)
        
        proc_name = f"always_{idx}@{','.join(triggers)}"
        processes.append(IRProcess(
            name=proc_name,
            triggers=triggers,
            trigger_kinds=trigger_kinds,
            assignments=assignments,
            src_location=src_loc,
        ))
    
    # --- Parse continuous assignments ---
    assign_pattern = r"assign :[dst:word] = :[src];"
    assign_matches = pycomby(text, assign_pattern)
    
    for idx, m in enumerate(assign_matches):
        dst = m.get("dst", "")
        src_expr = m.get("src", "")
        src_signals = _extract_signal_refs(src_expr)
        
        if dst not in signals:
            signals[dst] = IRSignal(name=dst, kind="wire", is_register=False)
        for src in src_signals:
            if src not in signals:
                signals[src] = IRSignal(name=src, kind="wire", is_register=False)
        
        proc_name = f"assign_{idx}_{dst}"
        processes.append(IRProcess(
            name=proc_name,
            triggers=src_signals,
            trigger_kinds=["level"] * len(src_signals),
            assignments=[IRAssignment(
                src_signals=src_signals,
                dst_signal=dst,
                kind="continuous",
                src_location=f"{filename}:assign_{idx}",
            )],
            src_location=f"{filename}:assign_{idx}",
        ))
    
    return IRDesign(
        signals=list(signals.values()),
        processes=processes,
    )


def parse_vams_file(filepath):
    """Parse a Verilog-AMS file."""
    path = Path(filepath)
    source = path.read_text(encoding="utf-8")
    return parse_vams(source, filename=str(path))


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python vparser.py <file.vams>")
        sys.exit(1)
    
    design = parse_vams_file(sys.argv[1])
    
    print(f"Signals ({len(design.signals)}):")
    for sig in design.signals:
        reg_str = " [reg]" if sig.is_register else ""
        print(f"  {sig.name}: {sig.kind}{reg_str}")
    
    print(f"\nProcesses ({len(design.processes)}):")
    for proc in design.processes:
        print(f"  {proc.name}")
        print(f"    triggers: {proc.triggers}")
        print(f"    assignments: {len(proc.assignments)}")
        for a in proc.assignments:
            print(f"      {a.dst_signal} {('<=' if a.kind == 'nonblocking' else '=')} f({a.src_signals})")

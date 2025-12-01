#!/usr/bin/env python3
"""
VRacer - Race Condition Detection Tool for Verilog/Verilog-AMS

Analyzes all signals uniformly regardless of their kind.
"""

import argparse
import sys
from pathlib import Path

from vparser import parse_vams_file
from vracer_core import (
    build_design_graph,
    detect_all_races,
    RaceType,
    DetectionConfig,
    RaceGraph,
)


def format_race(race, verbose=False):
    """Format a race for display."""
    kind_names = {
        RaceType.WRITE_WRITE: "WRITE-WRITE",
        RaceType.READ_WRITE: "READ-WRITE",
        RaceType.TRIGGER: "TRIGGER",
    }
    
    lines = []
    lines.append(f"  [{kind_names[race.race_type]}] target: {race.target_id}")
    lines.append(f"    source: {race.source_id}")
    lines.append(f"    anchor1: {race.anchor1_id}")
    lines.append(f"    anchor2: {race.anchor2_id}")
    
    if verbose:
        lines.append(f"    path1: {' -> '.join(race.path1.nodes)}")
        lines.append(f"    path2: {' -> '.join(race.path2.nodes)}")
        if race.path1.conditions:
            lines.append(f"    conditions1: {race.path1.conditions}")
        if race.path2.conditions:
            lines.append(f"    conditions2: {race.path2.conditions}")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Detect race conditions in Verilog/Verilog-AMS designs",
        epilog="Analysis treats all signals uniformly"
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Verilog/Verilog-AMS files to analyze",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed race paths",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show only race counts",
    )
    parser.add_argument(
        "--no-ww",
        action="store_true",
        help="Disable write-write race detection",
    )
    parser.add_argument(
        "--no-rw",
        action="store_true",
        help="Disable read-write race detection",
    )
    parser.add_argument(
        "--no-trigger",
        action="store_true",
        help="Disable trigger race detection",
    )
    
    args = parser.parse_args()
    
    enabled_types = set()
    if not args.no_ww:
        enabled_types.add(RaceType.WRITE_WRITE)
    if not args.no_rw:
        enabled_types.add(RaceType.READ_WRITE)
    if not args.no_trigger:
        enabled_types.add(RaceType.TRIGGER)
    
    config = DetectionConfig()
    
    total_races = 0
    
    for filepath in args.files:
        path = Path(filepath)
        if not path.exists():
            print(f"Error: File not found: {filepath}", file=sys.stderr)
            continue
        
        print(f"\n{'='*60}")
        print(f"Analyzing: {filepath}")
        print(f"{'='*60}")
        
        try:
            design = parse_vams_file(path)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}", file=sys.stderr)
            continue
        
        if args.verbose:
            print(f"\nDesign Statistics:")
            print(f"  Signals:    {len(design.signals)}")
            print(f"  Processes:  {len(design.processes)}")
        
        graph = build_design_graph(design)
        races = detect_all_races(graph, enabled_types, config)
        
        total_races += len(races)
        
        if args.summary:
            ww = sum(1 for r in races if r.race_type == RaceType.WRITE_WRITE)
            rw = sum(1 for r in races if r.race_type == RaceType.READ_WRITE)
            tr = sum(1 for r in races if r.race_type == RaceType.TRIGGER)
            print(f"Races found: {len(races)} (WW:{ww}, RW:{rw}, TR:{tr})")
        else:
            if races:
                print(f"\nRaces found: {len(races)}")
                for race in races:
                    print(format_race(race, args.verbose))
            else:
                print("\nNo races detected.")
    
    print(f"\n{'='*60}")
    print(f"Total races: {total_races}")
    print(f"{'='*60}")
    
    return 0 if total_races == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

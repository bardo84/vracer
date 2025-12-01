# VRacer

**Verilog Race Condition Detection Tool**

Static analysis tool for detecting race conditions in Verilog and Verilog-AMS designs.

VRacer analyzes Verilog/Verilog-AMS source files to detect potential race conditions that can cause non-deterministic simulation behavior.  It follows the static race analysis approach of Ouyang [US7017129B2, expired 2020].

## Features

- **Write-Write Race Detection**: Multiple processes writing to the same signal
- **Read-Write Race Detection**: Process reading a signal while another writes to it
- **Trigger Race Detection**: Concurrent processes triggered by the same signals

## Installation

Requires Python 3.10+ and [pycomby](https://github.com/bardo84/pycomby).

### Setup

1. Clone and install pycomby:

```bash
git clone https://github.com/bardo84/pycomby.git
cd pycomby
pip install -e .
cd ..
```

2. Clone and install vracer:

```bash
git clone https://github.com/bardo84/vracer.git
cd vracer
pip install -e .
```

3. Run vracer:

```bash
python vracer.py examples/example_1.v
```

Or use the command directly:

```bash
vracer examples/example_1.v
```

## Usage

```bash
# Analyze a single file
python vracer.py examples/example_1.v

# Analyze multiple files
python vracer.py examples/example_1.v examples/example_5.v

# Verbose output with detailed paths
python vracer.py examples/example_1.v -v

# Summary only (counts)
python vracer.py examples/example_1.v --summary

# Disable specific race types
python vracer.py examples/example_1.v --no-ww     # No write-write detection
python vracer.py examples/example_1.v --no-rw     # No read-write detection
python vracer.py examples/example_1.v --no-trigger # No trigger race detection
```

## Example Output

```
============================================================
Analyzing: examples/example_1.v
============================================================

Races found: 3
  [WRITE-WRITE] target: d_count1
    source: d_count1
    anchor1: c_always_0@clk
    anchor2: c_always_1@clk
  [READ-WRITE] target: d_count1
    source: d_count1
    anchor1: c_always_0@clk
    anchor2: c_always_1@clk
...
```

## Project Structure

```
vracer/
├── vracer.py          # Main CLI tool
├── vracer_core.py     # Detection algorithms and data structures
├── vparser.py         # Verilog-AMS parser
├── test_vracer.py     # Test suite
├── examples/          # Example Verilog files
│   ├── example_1.v    # Race condition example
│   ├── example_8.v    # Fixed version
│   └── ...
└── README.md
```

## Testing

```bash
python test_vracer.py
```

## Race Condition Types

| Type | Description | Example |
|------|-------------|---------|
| Write-Write (WW) | Multiple processes write to the same signal | Two `always @(posedge clk)` blocks both assign to `count` |
| Read-Write (RW) | One process reads while another writes | Monitor reads `data` while driver writes to it |
| Trigger (TR) | Processes with same triggers write to overlapping signals | Two processes triggered by `clk` both write to `result` |

## License

MIT License

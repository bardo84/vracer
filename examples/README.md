# Race Condition Examples

This directory contains 9 Verilog examples demonstrating race conditions and their solutions, extracted from the article "Race Conditions: The Root of All Verilog Evil".

## Examples Overview

### Problematic Examples (Have Race Conditions)

**Example 1: Race Condition with Blocking Assignments**
- File: `example_1.v`
- Description: Two counters synchronized to clock edge using blocking assignments
- Issue: Assertion failures depend on simulator's arbitrary process execution order
- Race Type: Write-Write race on `count1` signal

**Example 2: Race Condition with Initial Blocks**
- File: `example_2.v`
- Description: Semantically equivalent to Example 1 but using initial blocks instead of always block
- Issue: Different simulation order produces different results
- Race Type: Write-Write race on `count1` signal

**Example 3: Debug Version with Display Statements**
- File: `example_3.v`
- Description: Example 2 with $display statements to show actual simulation order
- Purpose: Demonstrates how simulation order changes during execution
- Race Type: Write-Write race on `count1` signal

**Example 5: Accumulator Testbench with Race Conditions**
- File: `example_5.v`
- Description: Real-world testbench scenario with multiple blocking assignments to DUT inputs
- Issues: 
  - Data input updated before monitor reads old value
  - Enable cleared before monitor processes condition
  - Reset state inconsistency across multiple always_ff blocks
- Race Types: Write-Write and Read-Write races

### Support Modules (No Races)

**Example 4: Accumulator Module (DUT)**
- File: `example_4.v`
- Description: Reference design used in testbench examples
- Features: Enable, reset, data input/output
- Status: No races (proper synthesizable design)

### Corrected Examples (Race-Free)

**Example 6: Non-Blocking Assignment Behavior**
- File: `example_6.v`
- Description: Demonstrates current vs. future values with non-blocking assignments
- Purpose: Educational - shows how non-blocking assignments decouple timing
- Status: No races

**Example 7: Order Independence with Non-Blocking Assignments**
- File: `example_7.v`
- Description: Multiple tests showing assignment order doesn't matter
- Key Insight: Assertions pass regardless of execution order
- Status: No races

**Example 8: Fixed Race Condition**
- File: `example_8.v`
- Description: Solution to Examples 1-2 using non-blocking assignment for `count1`
- Fix: Changed blocking `count1++` to non-blocking `count1 <=`
- Status: No races

**Example 9: Fixed Accumulator Testbench**
- File: `example_9.v`
- Description: Solution to Example 5 using non-blocking assignments throughout
- Fixes:
  - Clock generation uses non-blocking assignment
  - All DUT inputs use non-blocking assignments
  - Model updates use non-blocking assignments
- Status: No races

## Testing

Run tests with:
```bash
python test_vracer.py
```

To analyze a specific example with detailed output:
```bash
python vracer.py examples/example_1.v -v
```

## Key Lessons

1. **Blocking vs Non-Blocking**: Always use non-blocking assignments for signals shared across synchronous processes
2. **Simulation Order Independence**: Code should behave identically regardless of arbitrary execution order
3. **DUT Input Handling**: All testbench-to-DUT connections should use non-blocking assignments
4. **Current vs Future Values**: Non-blocking assignments update at end of timestep, blocking assignments update immediately
5. **Testing**: Test designs with multiple simulators to expose order-dependent bugs

## Race Condition Types

- **Write-Write (WW)**: Multiple processes writing to same signal
- **Read-Write (RW)**: Process reading signal being written by another process
- **Trigger (TR)**: Process triggered by signals modified by other processes triggered same way

## Related Files

- `race_detection.py`: Race detection algorithms
- `vams_parser.py`: Verilog-AMS parser
- `vracer.py`: Command-line analysis tool
- `test_vracer.py`: Test suite

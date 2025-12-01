"""
Test suite for vracer.py - Race detection tool

Tests the race detection functionality.
"""

import subprocess
import sys
from pathlib import Path


def run_vracer(files, verbose=False, summary=False, skip_types=None):
    """Run vracer.py with given options and return results."""
    if skip_types is None:
        skip_types = []
    
    cmd = [sys.executable, "vracer.py"] + files
    if verbose:
        cmd.append("-v")
    if summary:
        cmd.append("--summary")
    if "ww" in skip_types:
        cmd.append("--no-ww")
    if "rw" in skip_types:
        cmd.append("--no-rw")
    if "trigger" in skip_types:
        cmd.append("--no-trigger")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def test_single_file():
    """Test analyzing a single file."""
    print("\n" + "="*70)
    print("TEST: Single File Analysis")
    print("="*70)
    
    returncode, stdout, stderr = run_vracer(["examples/example_1.v"], summary=True)
    
    assert "Races found" in stdout, "Should report races found"
    assert returncode == 0, "Should exit successfully"
    print("[PASS] Single file analysis works")


def test_multiple_files():
    """Test analyzing multiple files at once."""
    print("\n" + "="*70)
    print("TEST: Multiple File Analysis")
    print("="*70)
    
    files = ["examples/example_1.v", "examples/example_5.v", "examples/example_8.v"]
    returncode, stdout, stderr = run_vracer(files, summary=True)
    
    assert "Analyzing: examples" in stdout, "Should analyze each file"
    assert stdout.count("Analyzing:") == 3, "Should analyze all 3 files"
    assert "Total races:" in stdout, "Should report total races"
    assert returncode == 0, "Should exit successfully"
    print("[PASS] Multiple file analysis works")


def test_verbose_output():
    """Test verbose flag shows detailed information."""
    print("\n" + "="*70)
    print("TEST: Verbose Output")
    print("="*70)
    
    returncode, stdout, stderr = run_vracer(["examples/example_1.v"], verbose=True)
    
    assert "Design Statistics" in stdout, "Should show statistics in verbose mode"
    assert "Signals:" in stdout, "Should show signal count"
    assert "Processes:" in stdout, "Should show process count"
    assert returncode == 0, "Should exit successfully"
    print("[PASS] Verbose output works")


def test_summary_flag():
    """Test summary flag shows only counts."""
    print("\n" + "="*70)
    print("TEST: Summary Flag")
    print("="*70)
    
    returncode, stdout, stderr = run_vracer(["examples/example_1.v"], summary=True)
    
    assert "Races found:" in stdout, "Should show race count"
    assert "WW:" in stdout, "Should show WW count"
    assert "RW:" in stdout, "Should show RW count"
    assert "TR:" in stdout, "Should show TR count"
    assert "Design Statistics" not in stdout, "Should not show detailed stats"
    assert returncode == 0, "Should exit successfully"
    print("[PASS] Summary flag works")


def test_type_filtering():
    """Test race kind filtering flags."""
    print("\n" + "="*70)
    print("TEST: Race Kind Filtering")
    print("="*70)
    
    # No filters
    rc1, out1, _ = run_vracer(["examples/example_1.v"], summary=True)
    
    # Disable write-write
    rc2, out2, _ = run_vracer(["examples/example_1.v"], summary=True, skip_types=["ww"])
    
    assert rc1 == 0 and rc2 == 0, "Both should succeed"
    assert "Races found:" in out1, "Should report races without filter"
    assert "Races found:" in out2, "Should report races with filter"
    print("[PASS] Kind filtering works")


def test_nonexistent_file():
    """Test handling of nonexistent file."""
    print("\n" + "="*70)
    print("TEST: Nonexistent File Handling")
    print("="*70)
    
    returncode, stdout, stderr = run_vracer(["nonexistent.v"], summary=True)
    
    assert "Error" in stderr or "not found" in stderr, "Should report error"
    # Still continues and reports total
    assert "Total races:" in stdout, "Should still report total"
    print("[PASS] Nonexistent file handling works")


def test_all_examples():
    """Test analyzing all example files."""
    print("\n" + "="*70)
    print("TEST: All Examples")
    print("="*70)
    
    examples = [f"examples/example_{i}.v" for i in range(1, 10)]
    returncode, stdout, stderr = run_vracer(examples, summary=True)
    
    assert stdout.count("Analyzing:") == 9, "Should analyze all 9 examples"
    assert "Total races:" in stdout, "Should report total"
    assert returncode == 0, "Should complete successfully"
    print("[PASS] All examples analyzed successfully")


def test_race_kind_selection():
    """Test selecting specific race kinds."""
    print("\n" + "="*70)
    print("TEST: Race Kind Selection")
    print("="*70)
    
    # All kinds
    rc_all, out_all, _ = run_vracer(["examples/example_1.v"], summary=True)
    
    # Only WW
    rc_ww, out_ww, _ = run_vracer(
        ["examples/example_1.v"], 
        summary=True,
        skip_types=["rw", "trigger"]
    )
    
    assert rc_all == 0 and rc_ww == 0, "Both should succeed"
    assert "Races found:" in out_all, "Should report all races"
    assert "Races found:" in out_ww, "Should report WW races"
    print("[PASS] Race kind selection works")


def test_help_message():
    """Test help message."""
    print("\n" + "="*70)
    print("TEST: Help Message")
    print("="*70)
    
    result = subprocess.run(
        [sys.executable, "vracer.py", "-h"],
        capture_output=True,
        text=True
    )
    
    assert "Detect race conditions" in result.stdout, "Should show help"
    assert "verbose" in result.stdout, "Should document verbose flag"
    assert "summary" in result.stdout, "Should document summary flag"
    print("[PASS] Help message works")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("VRACER TEST SUITE")
    print("="*70)
    
    tests = [
        test_single_file,
        test_multiple_files,
        test_verbose_output,
        test_summary_flag,
        test_type_filtering,
        test_nonexistent_file,
        test_all_examples,
        test_race_kind_selection,
        test_help_message,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

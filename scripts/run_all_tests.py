"""
Consolidated test runner: runs both patched stress test (500 cases) and normal glucose test (500 cases),
then outputs structured results suitable for inclusion in research papers.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def extract_test_metrics(output: str, test_name: str) -> dict:
    """Parse test output to extract summary metrics."""
    lines = output.split('\n')
    metrics = {
        'test_name': test_name,
        'total_tested': 0,
        'passed': 0,
        'failed': 0,
        'pass_rate_pct': 0.0,
    }
    
    for line in lines:
        if 'Total tested:' in line:
            try:
                metrics['total_tested'] = int(line.split(':')[1].strip())
            except (ValueError, IndexError):
                pass
        elif line.strip().startswith('Passed:'):
            try:
                metrics['passed'] = int(line.split(':')[1].strip())
            except (ValueError, IndexError):
                pass
        elif line.strip().startswith('Failed:'):
            try:
                metrics['failed'] = int(line.split(':')[1].strip())
            except (ValueError, IndexError):
                pass
        elif 'Pass rate:' in line:
            try:
                metrics['pass_rate_pct'] = float(line.split(':')[1].strip().rstrip('%'))
            except (ValueError, IndexError):
                pass
    
    return metrics

def run_test(script_path, test_name, timeout=180):
    """Run a test script and return metrics."""
    print(f"\n{'='*80}")
    print(f"Running: {test_name}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout + result.stderr
        print(output)
        
        metrics = extract_test_metrics(output, test_name)
        return metrics, output
        
    except subprocess.TimeoutExpired:
        print(f"ERROR: Test timed out after {timeout} seconds")
        return {'test_name': test_name, 'error': 'Timeout'}, ""
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {'test_name': test_name, 'error': str(e)}, ""

def main():
    print("STARTING CONSOLIDATED TEST SUITE")
    print(f"Working directory: {ROOT_DIR}")
    
    results = {}
    
    # Run patched stress test
    stress_script = ROOT_DIR / "scripts" / "stress_test_predict_dose_api.py"
    stress_metrics, stress_output = run_test(stress_script, "Patched Stress Test (500 cases)", timeout=180)
    results['stress_test_patched'] = stress_metrics
    
    # Run normal glucose test
    normal_script = ROOT_DIR / "scripts" / "test_normal_glucose_range.py"
    normal_metrics, normal_output = run_test(normal_script, "Normal Glucose Range Test (500 cases)", timeout=180)
    results['normal_glucose_test'] = normal_metrics
    
    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY RESULTS")
    print(f"{'='*80}")
    print(json.dumps(results, indent=2))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

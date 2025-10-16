import sys
import io
from tests.parser_test_corpus import run_tests

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Run tests
passed, failed = run_tests()
total = passed + failed

print(f"\n{'='*60}")
print(f"TEST SUMMARY")
print(f"{'='*60}")
print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
print(f"Failed: {failed}/{total} ({failed/total*100:.1f}%)")
print(f"{'='*60}")

# Exit with success if >=95% passed
target = 0.95
if passed/total >= target:
    print(f"✅ TARGET REACHED: {passed/total*100:.1f}% >= {target*100:.0f}%")
    sys.exit(0)
else:
    print(f"⏳ PROGRESS: {passed/total*100:.1f}% (target: {target*100:.0f}%)")
    sys.exit(1)

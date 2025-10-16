import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from tests.parser_test_corpus import run_tests

passed, failed = run_tests()
print(f"\n\nRESULT: {passed}/{passed+failed} passed ({100*passed/(passed+failed):.1f}%)")

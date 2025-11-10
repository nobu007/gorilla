"""
Comprehensive test runner for Web Search API.

This script runs all test suites and provides detailed reporting.
"""

import unittest
import sys
import time
import os
from io import StringIO

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestSuiteResult:
    """Container for test results."""

    def __init__(self):
        self.total_tests = 0
        self.total_failures = 0
        self.total_errors = 0
        self.total_skipped = 0
        self.suites_run = 0
        self.suite_results = {}
        self.start_time = None
        self.end_time = None


class ColoredCustomTextTestResult(unittest.TextTestResult):
    """Custom test result with colored output."""

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.terminal_colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'reset': '\033[0m'
        }

    def _color(self, text, color):
        """Apply color to text."""
        return f"{self.terminal_colors[color]}{text}{self.terminal_colors['reset']}"

    def addSuccess(self, test):
        super().addSuccess(test)
        if self.verbosity > 1:
            self.stream.write(self._color("✓", "green") + " ")
            self.stream.write(str(test))
            self.stream.write("\n")
            self.stream.flush()

    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write(self._color("✗", "red") + " ")
            self.stream.write(str(test))
            self.stream.write(f" {self._color('(ERROR)', 'magenta')}")
            self.stream.write("\n")
            self.stream.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write(self._color("✗", "red") + " ")
            self.stream.write(str(test))
            self.stream.write(f" {self._color('(FAIL)', 'yellow')}")
            self.stream.write("\n")
            self.stream.flush()

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write(self._color("- ", "cyan") + " ")
            self.stream.write(str(test))
            self.stream.write(f" {self._color('(SKIP)', 'cyan')}")
            self.stream.write(f" - {reason}")
            self.stream.write("\n")
            self.stream.flush()


def discover_test_suites():
    """Discover all test suites."""
    loader = unittest.TestLoader()

    test_suites = {}

    # Define test modules
    test_modules = [
        ('test_backends', 'Backend Tests'),
        ('test_config', 'Configuration Tests'),
        ('test_api', 'API Integration Tests'),
        ('test_error_handling', 'Error Handling Tests'),
        ('test_performance', 'Performance Tests'),
    ]

    for module_name, suite_name in test_modules:
        try:
            suite = loader.loadTestsFromName(module_name)
            if suite.countTestCases() > 0:
                test_suites[suite_name] = suite
        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")
        except Exception as e:
            print(f"Error loading {module_name}: {e}")

    return test_suites


def run_suite(suite_name, test_suite, result):
    """Run a single test suite and collect results."""
    print(f"\n{'='*60}")
    print(f"Running {suite_name}")
    print(f"{'='*60}")

    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        resultclass=ColoredCustomTextTestResult,
        descriptions=True,
        failfast=False
    )

    start_time = time.time()
    suite_result = runner.run(test_suite)
    end_time = time.time()

    # Store results
    suite_result_data = {
        'tests_run': suite_result.testsRun,
        'failures': len(suite_result.failures),
        'errors': len(suite_result.errors),
        'skipped': len(suite_result.skipped),
        'success_rate': (suite_result.testsRun - len(suite_result.failures) - len(suite_result.errors)) / max(suite_result.testsRun, 1) * 100,
        'duration': end_time - start_time,
        'output': stream.getvalue(),
        'passed': suite_result.testsRun - len(suite_result.failures) - len(suite_result.errors)
    }

    result.suite_results[suite_name] = suite_result_data
    result.total_tests += suite_result_data['tests_run']
    result.total_failures += suite_result_data['failures']
    result.total_errors += suite_result_data['errors']
    result.total_skipped += suite_result_data['skipped']
    result.suites_run += 1

    return suite_result.wasSuccessful()


def print_summary(result):
    """Print comprehensive test summary."""
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")

    # Overall results
    total_passed = result.total_tests - result.total_failures - result.total_errors
    success_rate = (total_passed / max(result.total_tests, 1)) * 100

    print(f"Total Tests: {result.total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {result.total_failures}")
    print(f"Errors: {result.total_errors}")
    print(f"Skipped: {result.total_skipped}")
    print(f"Success Rate: {success_rate:.1f}%")

    # Time
    if result.end_time and result.start_time:
        total_duration = result.end_time - result.start_time
        print(f"Total Duration: {total_duration:.2f}s")

    print("\nSuite Breakdown:")
    print("-" * 60)

    for suite_name, suite_data in result.suite_results.items():
        status = "✓ PASS" if suite_data['failures'] == 0 and suite_data['errors'] == 0 else "✗ FAIL"
        color = "green" if status == "✓ PASS" else "red"

        print(f"{suite_name:30} | {status:8} | {suite_data['tests_run']:4d} tests | "
              f"{suite_data['duration']:.2f}s | {suite_data['success_rate']:5.1f}%")

    print("-" * 60)

    # Failed test details
    if result.total_failures > 0 or result.total_errors > 0:
        print("\nFAILED TEST DETAILS:")
        print("-" * 60)

        for suite_name, suite_data in result.suite_results.items():
            if suite_data['failures'] > 0 or suite_data['errors'] > 0:
                print(f"\n{suite_name}:")

                # Print output if available
                if suite_data.get('output'):
                    output_lines = suite_data['output'].split('\n')
                    for line in output_lines:
                        if '✗' in line or 'ERROR' in line or 'FAIL' in line:
                            print(f"  {line.strip()}")

    # Overall status
    print(f"\n{'='*80}")
    if result.total_failures == 0 and result.total_errors == 0:
        print("🎉 ALL TESTS PASSED! 🎉")
    else:
        print("❌ SOME TESTS FAILED ❌")
    print(f"{'='*80}")


def main():
    """Main test runner."""
    print("Web Search API - Comprehensive Test Suite")
    print("=" * 80)

    result = TestSuiteResult()

    # Discover test suites
    test_suites = discover_test_suites()

    if not test_suites:
        print("No test suites found!")
        return 1

    print(f"Found {len(test_suites)} test suites:")
    for suite_name in test_suites.keys():
        print(f"  - {suite_name}")
    print()

    result.start_time = time.time()

    # Run all test suites
    all_passed = True
    for suite_name, test_suite in test_suites.items():
        suite_passed = run_suite(suite_name, test_suite, result)
        if not suite_passed:
            all_passed = False

    result.end_time = time.time()

    # Print summary
    print_summary(result)

    # Return appropriate exit code
    return 0 if all_passed else 1


def run_specific_suite(suite_name):
    """Run a specific test suite."""
    loader = unittest.TestLoader()

    try:
        test_suite = loader.loadTestsFromName(suite_name)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return 0 if result.wasSuccessful() else 1

    except ImportError:
        print(f"Test suite '{suite_name}' not found")
        return 1


def run_quick_tests():
    """Run a quick subset of tests."""
    print("Running quick tests...")

    loader = unittest.TestLoader()

    # Load specific test classes for quick testing
    quick_tests = []

    # Add basic backend tests
    try:
        from tests.test_backends import TestDuckDuckGoBackend, TestSerpApiBackend
        quick_tests.extend([
            loader.loadTestsFromTestCase(TestDuckDuckGoBackend),
            loader.loadTestsFromTestCase(TestSerpApiBackend)
        ])
    except ImportError:
        pass

    # Add config tests
    try:
        from tests.test_config import TestSearchConfig
        quick_tests.append(loader.loadTestsFromTestCase(TestSearchConfig))
    except ImportError:
        pass

    if not quick_tests:
        print("No quick tests available")
        return 1

    # Combine tests
    combined_suite = unittest.TestSuite(quick_tests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(combined_suite)

    print(f"\nQuick tests: {result.testsRun} run, {len(result.failures)} failed, {len(result.errors)} errors")

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    # Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--quick":
            sys.exit(run_quick_tests())
        elif arg == "--backends":
            sys.exit(run_specific_suite("test_backends"))
        elif arg == "--config":
            sys.exit(run_specific_suite("test_config"))
        elif arg == "--api":
            sys.exit(run_specific_suite("test_api"))
        elif arg == "--performance":
            sys.exit(run_specific_suite("test_performance"))
        else:
            print(f"Unknown argument: {arg}")
            print("Available options: --quick, --backends, --config, --api, --performance")
            sys.exit(1)
    else:
        sys.exit(main())
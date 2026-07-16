import logging
import sys
import unittest


def run_tests() -> bool:
    logging.disable(logging.CRITICAL)

    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover("tests", "*_test.py")

    test_runner = unittest.TextTestRunner()
    result = test_runner.run(test_suite)

    return not result.wasSuccessful()


if __name__ == "__main__":
    sys.exit(run_tests())

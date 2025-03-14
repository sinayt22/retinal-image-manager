#!/bin/bash

# Run tests with coverage
python -m pytest --cov=app tests/ -v

# Generate HTML coverage report
python -m pytest --cov=app --cov-report=html tests/

echo "Tests completed. Coverage report available in htmlcov/ directory."
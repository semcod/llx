#!/usr/bin/env bash

# This script removes all Python scripts from the examples/ directory
# and cleans up OLD bash scripts that are replaced by run.sh

set -e

echo "Cleaning up Python scripts..."
find . -type f -name "*.py" -delete
echo "Python scripts deleted."

echo "Cleaning up old bash scripts..."
rm -f cli-tools/quick_cli.sh
rm -f cloud-local/integration.sh
rm -f filtering/demo.sh
rm -f fullstack/generate.sh
rm -f hybrid/hybrid_dev.sh
rm -f planfile/planfile_dev.sh
rm -f planfile/test-cases/test_with_free_models.sh

echo "Cleanup completed."

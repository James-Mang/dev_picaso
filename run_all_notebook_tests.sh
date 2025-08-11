#!/bin/bash

# This script runs the notebook tests for all subdirectories of docs/notebooks.
# It accepts optional arguments to specify paths for data dependencies.
# Example:
# ./run_all_notebook_tests.sh --picaso-refdata-path /path/to/refdata --sonora-path /path/to/sonora --virga-path /path/to/virga
# Use the --dry-run flag to see the generated config file without running the tests.

CONFIG_FILE="test_config.json"

# Default paths are empty
picaso_refdata_path=""
sonora_path=""
virga_path=""
dry_run=false

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --picaso-refdata-path) picaso_refdata_path="$2"; shift ;;
        --sonora-path) sonora_path="$2"; shift ;;
        --virga-path) virga_path="$2"; shift ;;
        --dry-run) dry_run=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Create the JSON config file
json_content="{"
first_entry=true

if [ -n "$picaso_refdata_path" ]; then
    json_content="$json_content\"picaso_refdata_path\": \"$picaso_refdata_path\""
    first_entry=false
fi

if [ -n "$sonora_path" ]; then
    if [ "$first_entry" = false ]; then json_content="$json_content,"; fi
    json_content="$json_content\"sonora_path\": \"$sonora_path\""
    first_entry=false
fi

if [ -n "$virga_path" ]; then
    if [ "$first_entry" = false ]; then json_content="$json_content,"; fi
    json_content="$json_content\"virga_path\": \"$virga_path\""
fi

json_content="$json_content}"

echo "$json_content" > "$CONFIG_FILE"


echo "Generated config file:"
cat "$CONFIG_FILE"
echo ""

if [ "$dry_run" = true ]; then
    echo "Dry run complete. The config file has been created. Exiting."
    exit 0
fi


NOTEBOOK_ROOT="docs/notebooks"
EXCLUDED_DIR="workshops"
FAILED_DIRS=()

# Find all immediate subdirectories of the notebook root
for dir in "$NOTEBOOK_ROOT"/*/; do
    # Remove trailing slash
    dir=${dir%/}
    # Get the base directory name
    base_dir=$(basename "$dir")

    # Skip the excluded directory
    if [ "$base_dir" == "$EXCLUDED_DIR" ]; then
        echo "Skipping directory: $dir"
        continue
    fi

    echo "--------------------------------------------------"
    echo "Testing notebooks in: $dir"
    echo "--------------------------------------------------"

    # Run the python test script on the directory
    python test_notebooks.py "$dir"
    exit_code=$?

    if [ $exit_code -ne 0 ]; then
        echo "Tests failed in directory: $dir"
        FAILED_DIRS+=("$dir")
    else
        echo "Tests passed in directory: $dir"
    fi
done

echo "--------------------------------------------------"
echo "Summary"
echo "--------------------------------------------------"

if [ ${#FAILED_DIRS[@]} -eq 0 ]; then
    echo "All notebook tests passed!"
else
    echo "The following directories have failing notebook tests:"
    for failed_dir in "${FAILED_DIRS[@]}"; do
        echo "  - $failed_dir"
    done
    exit 1
fi

# Clean up the config file
rm -f "$CONFIG_FILE"

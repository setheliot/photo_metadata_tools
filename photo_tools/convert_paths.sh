#!/bin/bash

# Check if the input file is provided
if [ -z "$1" ]; then
  echo "Usage: $0 input_file"
  exit 1
fi

# Read the input file line by line
while IFS= read -r line; do
  # Replace the paths and change backslashes to forward slashes
  updated_line=$(echo "$line" \
    | sed 's|C:\\Users\\sethe\\OneDrive\\M_Pictures\\|/mnt/c/Users/sethe/OneDrive/M_Pictures/|' \
    | sed 's|C:\\Users\\sethe\\OneDrive\\O Pictures\\|/mnt/c/Users/sethe/OneDrive/O Pictures/|' \
    | tr '\\' '/')
  # Print the updated line
  echo "$updated_line"
done < "$1"

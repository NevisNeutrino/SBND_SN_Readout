#!/bin/bash

# List of servers to check
# Read servers from external file (one per line, optionally prefixed with a number and dot)
servers=()
if [[ ! -f servers.txt ]]; then
    echo "Error: servers.txt file not found!"
    exit 1
fi

while IFS= read -r line; do
    # Remove leading number and dot if present
    server=$(echo "$line" | sed 's/^[0-9]\+\.\s*//')
    # Skip empty lines
    [ -n "$server" ] && servers+=("$server")
done < servers.txt

for server in "${servers[@]}"; do
    if ping -c 1 -W 2 "$server" > /dev/null 2>&1; then
        echo "$server is reachable"
    else
        echo "$server is NOT reachable"
    fi
done
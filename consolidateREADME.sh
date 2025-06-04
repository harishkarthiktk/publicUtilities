#!/bin/bash

echo "Generating consolidated README.md..."

rm -f README.md
echo -e "# Consolidated Information\n\nRandom utilities that I have written for various functions\n" > README.md
find . -type f -name "README*" ! -path "./README.md" -exec cat {} \; >> README.md

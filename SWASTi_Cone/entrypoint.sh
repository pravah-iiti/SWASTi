#!/bin/bash

cd /app/swasti_run || exit 1

if [ -d "SWASTi_Results" ]; then
    echo "SWASTi_Results exists."
    echo "Exiting."

    exit 0
else
    exec bash /app/swasti_run/swasti.sh
fi

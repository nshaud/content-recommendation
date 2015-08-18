#!/bin/bash

# Add caffe shared library to ld
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/distribute/lib

# Run the Python script
rand=$(( $RANDOM % 3 ))

for i in 0 1 2; do
    opt=""
    if [[ $rand -eq i ]]; then
        opt="--no-recommend"
    fi
    python2.7 content_recommendation.py $opt
done

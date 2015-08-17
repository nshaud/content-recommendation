#!/bin/bash

# Add caffe shared library to ld
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/distribute/lib

# Run the Python script
rand=$(( $RANDOM % 2 ))

if [[ $rand -eq 1 ]]; then
    python2.7 content_recommendation.py
    python2.7 content_recommendation.py --no-recommend
else
    python2.7 content_recommendation.py --no-recommend
    python2.7 content_recommendation.py
fi

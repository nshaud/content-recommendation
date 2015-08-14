#!/bin/sh

# Add caffe shared library to ld
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/distribute/lib

# Run the Python script
python2.7 content_recommendation.py

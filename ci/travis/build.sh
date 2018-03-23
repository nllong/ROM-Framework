#!/usr/bin/env bash

BUILD_SCOPE=$1

if [ "${BUILD_SCOPE}" == "all" ]; then
    echo "Post Processing Results"
    cd results
    ruby post_process.rb --post-process
    cd ..

    echo "Building Regression Models"
    cd python
    python build_models.py -a 5564b7d5-4def-498b-ad5b-d4f12a463275
    cd ..
fi

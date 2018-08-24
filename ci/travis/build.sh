#!/usr/bin/env bash

BUILD_SCOPE=$1

if [ "${BUILD_SCOPE}" == "all" ]; then
    echo "Post Processing Results"
    cd results && bundle exec ruby post_process.rb --post-process && cd ..

    echo "Building Regression Models"

    # Uncomment the below to build all the models
#    analyses=(results/*/)
#    for dir in "${analyses[@]}"
#    do
#        analysis_id=$(basename ${dir})
#        echo "Calling build_models.py from build.sh for ${analysis_id}"
#
#        cd python && python build_models.py -a ${analysis_id} && cd ..
#    done

    # One off builds using ID number - small office with delta T, 10 samples
    cd python && python build_models.py -a smoff_test && cd ..

fi

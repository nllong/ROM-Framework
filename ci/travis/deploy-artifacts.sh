#!/usr/bin/env bash

if [ "${TRAVIS_PULL_REQUEST}" == "false" ]; then
    if [ "${TRAVIS_BRANCH}" == "master" ]; then
        aws s3 cp --recursive ./python/output s3://openstudio-metamodels/small_office/latest/
    else
        aws s3 cp --recursive ./python/output s3://openstudio-metamodels/small_office/$TRAVIS_BUILD_NUMBER/
        #    artifacts upload --bucket openstudio-dashboard --target-paths $TRAVIS_REPO_SLUG/$TRAVIS_BUILD_NUMBER ./python/output

        # Post the result back to github
    fi
fi


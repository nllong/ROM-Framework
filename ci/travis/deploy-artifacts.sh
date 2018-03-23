#!/usr/bin/env bash

if [ "${TRAVIS_PULL_REQUEST}" == "false" ]; then
    if [ "${TRAVIS_BRANCH}" == "master" ]; then
        aws s3 cp --recursive ./python/output s3://openstudio-metamodels/small_office/latest/
    else
        aws s3 cp --recursive ./python/output s3://openstudio-metamodels/small_office/$TRAVIS_BUILD_NUMBER/
    fi
else
    # must be a pull request, post back to github
    aws s3 cp --recursive ./python/output s3://openstudio-metamodels/small_office/${TRAVIS_BUILD_NUMBER}/


    github_body="The builds of the models are here:\nhttps://s3.amazonaws.com/openstudio-metamodels/small_office/${TRAVIS_BUILD_NUMBER}/5564b7d5-4def-498b-ad5b-d4f12a463275/models/models.zip"

    curl -H "Authorization: token ${GITHUB_TOKEN}" -X POST \
         -d "{\"body\": \"${github_body}\"}" \
         "https://api.github.com/repos/${TRAVIS_REPO_SLUG}/issues/${TRAVIS_PULL_REQUEST}/comments"
fi


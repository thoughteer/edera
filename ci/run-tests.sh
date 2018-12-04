#/bin/bash

set -ev

if [ "$GROUP" == 'integration' ];
then
    docker run -d -p 27017:27017 --name edera-mongo mongo
    docker run -d -p 2181:2181 --name edera-zookeeper zookeeper
fi

if [ "$GROUP" == 'performance' ];
then
    if [ "$TRAVIS_PULL_REQUEST" != 'false' ];
    then
        BASE="$TRAVIS_BRANCH";
    elif [[ "$TRAVIS_BRANCH" =~ ^(bugfix|feature)/.* ]];
    then
        BASE='development';
    elif [[ "$TRAVIS_BRANCH" =~ ^(development$|(hotfix|release)/.*) ]];
    then
        BASE='master';
    else
        exit 0
    fi
    git config --replace-all remote.origin.fetch +refs/heads/*:refs/remotes/origin/*
    git fetch origin "$BASE"
    git checkout "$BASE"
    tox "tests/$GROUP"
    git checkout -qf "$TRAVIS_COMMIT"
    export EDERA_PERFORMANCE_CONTROL_FLAGS='--benchmark-compare --benchmark-compare-fail=median:50%'
fi

tox "tests/$GROUP"

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
        exit 1
    fi
    git config --replace-all remote.origin.fetch +refs/heads/*:refs/remotes/origin/*
    git fetch origin "$BASE"
    git checkout "$BASE"
    tox "tests/$GROUP"
    git checkout -qf "$TRAVIS_COMMIT"
fi

tox "tests/$GROUP"

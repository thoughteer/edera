#!/bin/sh

set -e

# make sure we're in the master branch
if [ "$(git rev-parse --abbrev-ref HEAD)" != 'master' ]
then
    echo 'Please, switch to the master branch' >&2
    exit 1
fi

# read command line arguments
VERSION="$1"
if [ -z "$VERSION" ]
then
    echo 'Usage: ./package VERSION [REPACK]' >&2
    exit 1
fi
REPACK="$2"
if [ -z "$REPACK" ]
then
    REPACK=1
fi

# update debian/changelog
dch -v "$VERSION-$REPACK" -D unstable -u low

# download and unpack the upstream tarball
UPSTREAM_TARBALL="${VERSION}.tar.gz"
UPSTREAM_SOURCE="edera-$VERSION"
rm -f "$UPSTREAM_TARBALL"
uscan --force-download --no-symlink --download-version "$VERSION" --destdir .
rm -rf "$UPSTREAM_SOURCE"
tar xfz "$UPSTREAM_TARBALL"

# build a source distribution
SOURCE_DISTRIBUTION="edera_${VERSION}.orig.tar.gz"
cd "$UPSTREAM_SOURCE"
python setup.py sdist
mv "dist/edera-${VERSION}.tar.gz" "../$SOURCE_DISTRIBUTION"
cd ..

# patch the source distribution and build a package out of it
rm -rf "$UPSTREAM_SOURCE"
tar xfz "$SOURCE_DISTRIBUTION"
cd "$UPSTREAM_SOURCE"
cp -r ../debian .
debuild 2>&1 | tee ../build.log
cd ..

# commit changes
git add debian/changelog
git commit -m "Create a debian package version $VERSION-$REPACK"

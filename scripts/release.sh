#!/usr/bin/env bash

set -e

if [[ "$#" -ne 1 ]]; then
  echo "Please pass version to release (e.g. scripts/release.sh 0.1.1)"
  exit 1
fi

VERSION=$1

sed -i.bak "s/version =.*/version = '$VERSION'/g" ./marathon/version.py
echo "Updated version on ./marathon/version.py to $VERSION"

echo "Making commit and tag for new release..."

BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$BRANCH" != "master" ]]; then
  echo "Not on master branch, aborting."
  exit 1
fi

echo "Pulling first..."
git pull

echo "Committing..."
git add ./marathon/version.py
git commit -m "Version increment $VERSION"

echo "Tagging..."
git tag "v$VERSION" master

echo "Pushing..."
git push origin master && git push origin "v$VERSION"

echo "Making release to PyPi..."
# Install deps
pip3 install --user --upgrade setuptools wheel twine
# Package run-marathon
rm -rf dist/ build/ marathon.egg-info/
python3 setup.py sdist bdist_wheel
# Upload run-marathon to PyPi
twine upload dist/*

echo "Done"

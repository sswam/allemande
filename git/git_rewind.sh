#!/bin/bash -eu

# Temporarily rewinds Git to a specified commit

commit_hash=$1

git branch temp-branch
git reset --hard "$commit_hash"

echo "Git has been rewound to commit $commit_hash"
echo "To return to the original state, run:"
echo "    git checkout temp-branch"
echo "Then delete the temporary branch with:"
echo "    git branch -d temp-branch"

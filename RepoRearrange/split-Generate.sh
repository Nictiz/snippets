#!/bin/bash

git clone git@github.com:Nictiz/Nictiz-STU3-testscripts.git Nictiz-tooling-testscripts
cd Nictiz-tooling-testscripts
git checkout Generate
git_filter_repo.py --force \
	--path Generate/general \
    --path Generate/lib \
    --path Generate/src \
    --path Generate/_ant \
    --path Utils
git_filter_repo.py --force --path-rename Generate:generate
git_filter_repo.py --force --path-rename Utils:utils

#git checkout stable-1.x
#for branch in $(git branch | cut -c 3-); do
#	if [[ $branch != 'stable-1.x' && $branch != 'MP-develop' ]]; then
#		git branch -D $branch
#	fi
#done
#git branch --move stable-1.x release-9.0.7
#git branch --move MP-develop release-9.1.x-beta

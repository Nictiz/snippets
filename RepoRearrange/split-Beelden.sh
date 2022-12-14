#!/bin/bash

git clone git@github.com:Nictiz/Nictiz-STU3-Zib2017.git Nictiz-STU3-Images
cd Nictiz-STU3-Images
git_filter_repo.py \
	--path README.md \
	--path 'Profiles - ZIB 2017/Images' \
	--path-glob 'Capabilitystatements/*images.xml' \
	--path-glob 'Examples/images-*'
git_filter_repo.py --path-rename 'Profiles - ZIB 2017/Images:Profiles'

git checkout stable-1.x
for branch in $(git branch | cut -c 3-); do
	if [[ $branch != 'stable-1.x' && $branch != 'master' && $branch != 'MM-1034' ]]; then
		git branch -D $branch
	fi
done

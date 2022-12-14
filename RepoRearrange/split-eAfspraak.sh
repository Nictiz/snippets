#!/bin/bash

git clone git@github.com:Nictiz/Nictiz-STU3-Zib2017.git Nictiz-STU3-eAfspraak
cd Nictiz-STU3-eAfspraak
git_filter_repo.py \
	--path README.md \
	--path 'Profiles - ZIB 2017/eAfspraak' \
	--path-glob 'Examples/eAfspraak-*'
git_filter_repo.py --path-rename 'Profiles - ZIB 2017/eAfspraak:Profiles'

git checkout stable-1.x
for branch in $(git branch | cut -c 3-); do
	if [[ $branch != 'stable-1.x' && $branch != 'master' && $branch != 'MM-433' ]]; then
		git branch -D $branch
	fi
done

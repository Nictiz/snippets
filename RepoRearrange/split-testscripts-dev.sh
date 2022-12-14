#!/bin/bash

git clone git@github.com:Nictiz/Nictiz-STU3-testscripts.git Nictiz-STU3-testscripts
cd Nictiz-STU3-testscripts
#git_filter_repo.py \
	--path 'Configuration' \
    --path-glob 'FHIR3-0-*-MM20*' \
    --path 'FHIR3-0-1-Geboortezorg' \
    --path 'FHIR3-0-1-eOverdracht' \
    --path 'README.md'
git checkout -b "repo-rearrange"
rm -rf Generate
git add . && git commit -m "Split out NTS materials to its own repo"
rm -rf FHIR3-0-1-MedMij-Dev
rm -rf FHIR3-0-1-Sandbox
git add . && git commit -m "Remove obsolete sandbox folders"
rm -rf FHIR3-0-2-MM201901-Dev
rm -rf FHIR3-0-2-MM202001-Dev
rm -rf FHIR3-0-2-MM202002-Dev
git add . && git commit -m "Remove obsolete -Dev folders"

cd ..
git clone git@github.com:Nictiz/Nictiz-STU3-testscripts.git Nictiz-STU3-testscripts-src
cd Nictiz-STU3-testscripts-src
git_filter_repo.py \
	--path 'Generate'
git_filter_repo.py --filename-callback 'return filename.replace(b"Generate/", b"")'
git subtree add -P dev ../Nictiz-STU3-testscripts repo-rearrange

git checkout master
for branch in $(git branch | cut -c 3-); do
	if [[ $branch != 'master' ]]; then
		git branch -D $branch
	fi
done

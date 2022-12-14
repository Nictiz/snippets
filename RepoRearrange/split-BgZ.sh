#!/bin/bash

#git clone git@github.com:Nictiz/Nictiz-STU3-Zib2017.git Nictiz-STU3-BgZ
#cd Nictiz-STU3-BgZ
#git_filter_repo.py \
	--path 'CapabilityStatements/capabilitystatement-client-bgz2017.xml' \
	--path 'CapabilityStatements/capabilitystatement-server-bgz2017.xml'

git checkout stable-1.x
for branch in $(git branch | cut -c 3-); do
	if [[ $branch != 'stable-1.x' && $branch != 'master' ]]; then
		git branch -D $branch
	fi
done

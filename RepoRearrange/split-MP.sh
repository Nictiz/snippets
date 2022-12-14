#!/bin/bash

git clone Nictiz-STU3-Zib2017 Nictiz-STU3-MedicationProcess
cd Nictiz-STU3-MedicationProcess
git_filter_repo.py --force \
	--path README.md \
    --path 'Profiles - ZIB 2017/zib-Medication' \
	--path 'Capabilitystatements/capabilitystatement-client-medication.xml' \
	--path 'Capabilitystatements/capabilitystatement-server-medication.xml'
git_filter_repo.py --force --path-rename 'Profiles - ZIB 2017/zib-Medication/OperationDefinitions:OperationDefinitions'
git_filter_repo.py --force --path-rename 'Profiles - ZIB 2017/zib-Medication/SearchParameters:SearchParameters'
git_filter_repo.py --force --path-rename 'Profiles - ZIB 2017/zib-Medication:Profiles'
git_filter_repo.py --force --path-rename 'Profiles - ZIB 2017/Valuesets:Profiles/Valuesets'

git checkout stable-1.x
for branch in $(git branch | cut -c 3-); do
	if [[ $branch != 'stable-1.x' && $branch != 'MP-develop' ]]; then
		git branch -D $branch
	fi
done
git branch --move stable-1.x release-9.0.7
git branch --move MP-develop release-9.1.x-beta

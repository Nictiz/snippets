#!/bin/bash

git clone Nictiz-STU3-Zib2017 Nictiz-STU3-MedicationProcess
cd Nictiz-STU3-MedicationProcess
git_filter_repo.py --force \
	--path README.md \
     --path 'Profiles - ZIB 2017/zib-Medication/Bundle-MedicationOverview.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/MedicationOverview-SourceOrganization.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/MedicationOverview-Verification.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-AdministrationAgreement-AuthoredOn.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-AdministrationAgreement-ReasonForDispense.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-Dispense-DistributionForm.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-Dispense-Location.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-Dispense-RequestDate.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-DispenseRequest-RelatedMedicationAgreement.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-Medication-AdditionalInformation.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-Medication-CopyIndicator.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-Medication-MedicationTreatment.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-Medication-PeriodOfUse.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-Medication-RepeatPeriodCyclicalSchedule.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-Medication-StopType.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-MedicationAdministration-AgreedDateTime.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-MedicationAdministration-DeviatingAdministration.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-MedicationAdministration-DoubleCheckPerformed.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-MedicationAgreement-BasedOnAgreementOrUse.StructureDefinition.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-MedicationUse-AsAgreedIndicator.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-MedicationUse-Author.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-MedicationUse-Duration.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-MedicationUse-Prescriber.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-MedicationUse-ReasonForChangeOrDiscontinuationOfUse.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/Extensions/zib-Product-Description.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/MedicationOverview.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/OperationDefinitions/OperationDefinition-medication-overview.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/SearchParameters/SearchParameter-MedicationDispense-requestdate.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/SearchParameters/SearchParameter-MedicationDispense-whendispensed.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/SearchParameters/SearchParameter-Medications-category.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/SearchParameters/SearchParameter-Medications-medicationtreatment.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/SearchParameters/SearchParameter-Medications-periodofuse.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/conceptmap-DagdeelCodelijst-to-EventTiming.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/conceptmap-MedicationUseStopTypeCodeList-to-MedicationStatementStatus.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/conceptmap-WeekdagCodelijst-to-days-of-week.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/mp612-AllergyIntoleranceToFHIRConversion.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/mp612-DispenseToFHIRConversion-AdministrationAgreement.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/mp612-DispenseToFHIRConversion-Dispense.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/mp612-DispenseToFHIRConversion-Organization.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/mp612-DispenseToFHIRConversion-Patient.xml'
     --path 'Profiles - ZIB 2017/zib-Medication/mp612-DispenseToFHIRConversion-Product.xml'

	--path 'Capabilitystatements/capabilitystatement-client-medication.xml' \
	--path 'Capabilitystatements/capabilitystatement-server-medication.xml' \
    --path 'Profiles - ZIB 2017/Valuesets/Stoptype-2.16.840.1.113883.2.4.3.11.60.20.77.11.19--20160617101300.xml' \ // Extensie
    --path 'Profiles - ZIB 2017/Valuesets/RedenWijzigenOfStoppenGebruikCodelijst-2.16.840.1.113883.2.4.3.11.60.40.2.9.11.2--20171231000000.xml' // Ongebruikt?
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

"""
Batch convert a curated list of openEHR archetypes to Excel and mix in a template.

Purpose
-------
Use short CKM search texts such as "pulse" or "blood_pressure", let the
existing ArchetypeToSpreadsheet converter resolve the matching archetype, and
then apply TemplateMixer to each generated workbook.

How to use
----------
1. Put this file in the same folder as ArchetypeToSpreadsheet.py
2. Adjust ARCHETYPES, OUTPUT_FOLDER and TEMPLATE_PATH below if needed
3. Run: python ArchetypeBatchConvertWithTemplate.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import List, Tuple

import templatemixer

# Edit this list to the archetypes you want to convert.
# Short CKM search texts are allowed, for example: "pulse".
ARCHETYPES: List[str] = [
    "openEHR-EHR-CLUSTER.device.v1",
    "openEHR-EHR-COMPOSITION.request.v1",
    "openEHR-EHR-OBSERVATION.story.v1",
    "openEHR-EHR-COMPOSITION.encounter.v1",
    "openEHR-EHR-ACTION.medication.v1",
    "openEHR-EHR-EVALUATION.goal.v1",
    "openEHR-EHR-OBSERVATION.glasgow_coma_scale.v1",
    "openEHR-EHR-OBSERVATION.urinalysis.v1",
    "openEHR-EHR-EVALUATION.problem_diagnosis.v1",
    "openEHR-EHR-EVALUATION.health_risk.v1",
    "openEHR-EHR-ACTION.procedure.v1",
    "openEHR-EHR-OBSERVATION.exam.v1",
    "openEHR-EHR-CLUSTER.address.v1",
    "openEHR-EHR-OBSERVATION.ecg_result.v1",
    "openEHR-EHR-COMPOSITION.medication_list.v1",
    "openEHR-EHR-EVALUATION.reason_for_encounter.v1",
    "openEHR-EHR-CLUSTER.specimen.v1",
    "openEHR-EHR-EVALUATION.substance_use_summary.v1",
    "openEHR-EHR-CLUSTER.specimen_processing.v1",
    "openEHR-EHR-CLUSTER.organisation.v1",
    "openEHR-EHR-CLUSTER.inspired_oxygen.v1",
    "openEHR-EHR-EVALUATION.clinical_synopsis.v1",
    "openEHR-EHR-CLUSTER.anatomical_location.v1",
    "openEHR-EHR-INSTRUCTION.service_request.v1",
    "openEHR-EHR-SECTION.adhoc.v1",
    "openEHR-EHR-COMPOSITION.report.v1",
    "openEHR-EHR-OBSERVATION.braden_scale.v1",
    "openEHR-EHR-EVALUATION.obstetric_summary.v1",
    "openEHR-EHR-OBSERVATION.timed_25_foot_walk.v1",
    "openEHR-EHR-OBSERVATION.nine_hole_peg_test.v1",
    "openEHR-EHR-OBSERVATION.paced_auditory_serial_addition_test.v1",
    "openEHR-EHR-OBSERVATION.body_surface_area.v1",
    "openEHR-EHR-COMPOSITION.report-procedure.v1",
    "openEHR-EHR-COMPOSITION.report-result.v1",
    "openEHR-EHR-OBSERVATION.asa_status.v1",
    "openEHR-EHR-OBSERVATION.demo.v1",
    "openEHR-EHR-EVALUATION.contraindication.v1",
    "openEHR-EHR-ACTION.health_education.v1",
    "openEHR-EHR-COMPOSITION.adverse_reaction_list.v1",
    "openEHR-EHR-OBSERVATION.nyha_heart_failure.v1",
    "openEHR-EHR-OBSERVATION.imaging_exam_result.v1",
    "openEHR-EHR-EVALUATION.alcohol_consumption_summary.v1",
    "openEHR-EHR-OBSERVATION.progress_note.v1",
    "openEHR-EHR-EVALUATION.menstruation_summary.v1",
    "openEHR-EHR-EVALUATION.differential_diagnoses.v1",
    "openEHR-EHR-OBSERVATION.fluid_input.v1",
    "openEHR-EHR-OBSERVATION.fluid_balance.v1",
    "openEHR-EHR-OBSERVATION.fluid_output.v1",
    "openEHR-EHR-CLUSTER.media_file.v1",
    "openEHR-EHR-CLUSTER.exclusion_exam.v1",
    "openEHR-EHR-OBSERVATION.menstruation.v1",
    "openEHR-EHR-COMPOSITION.health_summary.v1",
    "openEHR-EHR-COMPOSITION.transfer_summary.v1",
    "openEHR-EHR-CLUSTER.clinical_evidence.v1",
    "openEHR-EHR-CLUSTER.interpreter_request.v1",
    "openEHR-EHR-CLUSTER.family_prevalence.v1",
    "openEHR-EHR-CLUSTER.anatomical_location_circle.v1",
    "openEHR-EHR-OBSERVATION.laboratory_test_result.v1",
    "openEHR-EHR-CLUSTER.specimen_container.v1",
    "openEHR-EHR-CLUSTER.timing_daily.v1",
    "openEHR-EHR-CLUSTER.timing_nondaily.v1",
    "openEHR-EHR-OBSERVATION.stratify_no.v1",
    "openEHR-EHR-OBSERVATION.ipss.v1",
    "openEHR-EHR-ACTION.service.v1",
    "openEHR-EHR-EVALUATION.social_summary.v1",
    "openEHR-EHR-CLUSTER.occupation_record.v1",
    "openEHR-EHR-CLUSTER.tnm.v1",
    "openEHR-EHR-OBSERVATION.cgas.v1",
    "openEHR-EHR-OBSERVATION.news_uk_rcp.v1",
    "openEHR-EHR-EVALUATION.tobacco_smoking_summary.v1",
    "openEHR-EHR-EVALUATION.family_history.v2",
    "openEHR-EHR-OBSERVATION.head_circumference.v1",
    "openEHR-EHR-EVALUATION.precaution.v1",
    "openEHR-EHR-CLUSTER.religion.v1",
    "openEHR-EHR-EVALUATION.exclusion_global.v1",
    "openEHR-EHR-EVALUATION.exclusion_specific.v1",
    "openEHR-EHR-CLUSTER.therapeutic_direction.v1",
    "openEHR-EHR-OBSERVATION.body_temperature.v2",
    "openEHR-EHR-OBSERVATION.tanner.v1",
    "openEHR-EHR-OBSERVATION.waist_circumference.v1",
    "openEHR-EHR-OBSERVATION.hip_circumference.v1",
    "openEHR-EHR-OBSERVATION.malnutrition_screening_tool.v1",
    "openEHR-EHR-EVALUATION.smokeless_tobacco_summary.v1",
    "openEHR-EHR-EVALUATION.medication_summary.v1",
    "openEHR-EHR-OBSERVATION.nutritional_risk_screening.v1",
    "openEHR-EHR-OBSERVATION.testicular_volume.v1",
    "openEHR-EHR-CLUSTER.laboratory_test_analyte.v1",
    "openEHR-EHR-CLUSTER.language.v1",
    "openEHR-EHR-OBSERVATION.body_mass_index.v2",
    "openEHR-EHR-OBSERVATION.body_weight.v2",
    "openEHR-EHR-EVALUATION.occupation_summary.v1",
    "openEHR-EHR-EVALUATION.financial_summary.v1",
    "openEHR-EHR-OBSERVATION.mallampati_classification.v1",
    "openEHR-EHR-OBSERVATION.cormack_lehane.v1",
    "openEHR-EHR-OBSERVATION.pulse_oximetry.v1",
    "openEHR-EHR-EVALUATION.communication_capability.v1",
    "openEHR-EHR-CLUSTER.service_direction.v1",
    "openEHR-EHR-EVALUATION.education_summary.v1",
    "openEHR-EHR-OBSERVATION.height.v2",
    "openEHR-EHR-EVALUATION.contraceptive_summary.v1",
    "openEHR-EHR-CLUSTER.housing_record.v1",
    "openEHR-EHR-EVALUATION.housing_summary.v1",
    "openEHR-EHR-EVALUATION.social_network.v1",
    "openEHR-EHR-OBSERVATION.acvpu.v1",
    "openEHR-EHR-OBSERVATION.news2.v1",
    "openEHR-EHR-OBSERVATION.age_assertion.v1",
    "openEHR-EHR-ADMIN_ENTRY.translation_requirements.v1",
    "openEHR-EHR-OBSERVATION.blood_pressure.v2",
    "openEHR-EHR-OBSERVATION.body_segment_length.v1",
    "openEHR-EHR-OBSERVATION.body_segment_area.v1",
    "openEHR-EHR-EVALUATION.gender.v1",
    "openEHR-EHR-CLUSTER.education_record.v1",
    "openEHR-EHR-CLUSTER.knowledge_base_reference.v1",
    "openEHR-EHR-CLUSTER.genomic_conversion_variant.v1",
    "openEHR-EHR-CLUSTER.genomic_copy_number_variant.v1",
    "openEHR-EHR-CLUSTER.genomic_deletion_variant.v1",
    "openEHR-EHR-CLUSTER.genomic_duplication_variant.v1",
    "openEHR-EHR-CLUSTER.genomic_deletion_insertion_variant.v1",
    "openEHR-EHR-CLUSTER.genomic_insertion_variant.v1",
    "openEHR-EHR-CLUSTER.genomic_repeated_sequence_variant.v1",
    "openEHR-EHR-CLUSTER.genomic_substitution_variant.v1",
    "openEHR-EHR-CLUSTER.genomic_variant_result.v1",
    "openEHR-EHR-CLUSTER.reference_sequence.v1",
    "openEHR-EHR-OBSERVATION.body_segment_circumference.v1",
    "openEHR-EHR-OBSERVATION.qsofa_score.v1",
    "openEHR-EHR-OBSERVATION.esas_r.v1",
    "openEHR-EHR-CLUSTER.item_transport.v1",
    "openEHR-EHR-CLUSTER.tnm-pathological.v1",
    "openEHR-EHR-EVALUATION.absence.v2",
    "openEHR-EHR-OBSERVATION.respiration.v2",
    "openEHR-EHR-OBSERVATION.pulse.v2",
    "openEHR-EHR-OBSERVATION.four_a_test.v1",
    "openEHR-EHR-OBSERVATION.travel_screening.v1",
    "openEHR-EHR-OBSERVATION.symptom_sign_screening.v1",
    "openEHR-EHR-OBSERVATION.exposure_screening.v1",
    "openEHR-EHR-OBSERVATION.procedure_screening.v1",
    "openEHR-EHR-OBSERVATION.problem_screening.v1",
    "openEHR-EHR-CLUSTER.information_resource.v1",
    "openEHR-EHR-OBSERVATION.pf_ratio.v1",
    "openEHR-EHR-OBSERVATION.social_context_screening.v1",
    "openEHR-EHR-OBSERVATION.modified_rankin_scale.v1",
    "openEHR-EHR-OBSERVATION.medication_screening.v1",
    "openEHR-EHR-OBSERVATION.capillary_refill.v1",
    "openEHR-EHR-OBSERVATION.clinical_frailty_scale.v1",
    "openEHR-EHR-OBSERVATION.crb_65.v1",
    "openEHR-EHR-OBSERVATION.curb_65.v1",
    "openEHR-EHR-COMPOSITION.problem_list.v2",
    "openEHR-EHR-CLUSTER.anatomical_location_relative.v2",
    "openEHR-EHR-OBSERVATION.apgar.v2",
    "openEHR-EHR-CLUSTER.genomic_inversion_variant.v1",
    "openEHR-EHR-EVALUATION.advance_intervention_decisions.v1",
    "openEHR-EHR-OBSERVATION.substance_use_screening.v1",
    "openEHR-EHR-OBSERVATION.ygtss_revised.v1",
    "openEHR-EHR-CLUSTER.boston_bowel_preparation_scale.v1",
    "openEHR-EHR-OBSERVATION.mayo_score.v1",
    "openEHR-EHR-OBSERVATION.karnofsky_performance_status_scale.v1",
    "openEHR-EHR-OBSERVATION.bvc.v1",
    "openEHR-EHR-CLUSTER.ctcae.v1",
    "openEHR-EHR-OBSERVATION.family_history_screening_questionnaire.v1",
    "openEHR-EHR-EVALUATION.ethnicity.v1",
    "openEHR-EHR-CLUSTER.electronic_communication.v1",
    "openEHR-EHR-CLUSTER.person.v1",
    "openEHR-EHR-CLUSTER.structured_name.v1",
    "openEHR-EHR-OBSERVATION.pasi_score.v1",
    "openEHR-EHR-EVALUATION.death_summary.v1",
    "openEHR-EHR-EVALUATION.cause_of_death.v1",
    "openEHR-EHR-EVALUATION.last_menstrual_period.v1",
    "openEHR-EHR-OBSERVATION.menstrual_diary.v1",
    "openEHR-EHR-OBSERVATION.adverse_reaction_monitoring.v1",
    "openEHR-EHR-EVALUATION.recommendation.v2",
    "openEHR-EHR-CLUSTER.adverse_reaction_event.v1",
    "openEHR-EHR-COMPOSITION.health_certificate.v1",
    "openEHR-EHR-OBSERVATION.hirsutism_scales.v1",
    "openEHR-EHR-CLUSTER.exam_blastocyst.v1",
    "openEHR-EHR-CLUSTER.exam_embryo.v1",
    "openEHR-EHR-CLUSTER.exam_oocyte.v1",
    "openEHR-EHR-CLUSTER.exam_zygote.v1",
    "openEHR-EHR-OBSERVATION.embryo_assessment.v1",
    "openEHR-EHR-CLUSTER.imaging_exam-ovary.v1",
    "openEHR-EHR-CLUSTER.imaging_exam.v1",
    "openEHR-EHR-OBSERVATION.fetal_biometry.v1",
    "openEHR-EHR-CLUSTER.imaging_exam-foetus.v1",
    "openEHR-EHR-CLUSTER.imaging_exam-cervix.v1",
    "openEHR-EHR-CLUSTER.imaging_exam-gestational_sac.v1",
    "openEHR-EHR-CLUSTER.imaging_exam-rectouterine_pouch.v1",
    "openEHR-EHR-INSTRUCTION.medication_order.v3",
    "openEHR-EHR-CLUSTER.medication.v2",
    "openEHR-EHR-CLUSTER.dosage.v2",
    "openEHR-EHR-EVALUATION.art_cycle_summary.v1",
    "openEHR-EHR-CLUSTER.imaging_exam-fallopian_tube.v1",
    "openEHR-EHR-EVALUATION.specimen_summary.v1",
    "openEHR-EHR-CLUSTER.oocyte_specimen.v1",
    "openEHR-EHR-OBSERVATION.clinical_frailty_scale2.v1",
    "openEHR-EHR-CLUSTER.embryo_specimen.v1",
    "openEHR-EHR-CLUSTER.exam.v2",
    "openEHR-EHR-COMPOSITION.self_reported_data.v1",
    "openEHR-EHR-EVALUATION.advance_care_directive.v2",
    "openEHR-EHR-OBSERVATION.simplified_tanner_whitehouse_3.v1",
    "openEHR-EHR-OBSERVATION.lenke_classification.v1",
    "openEHR-EHR-OBSERVATION.body_segment_discrepancy.v1",
    "openEHR-EHR-OBSERVATION.investigation_screening.v1",
    "openEHR-EHR-EVALUATION.intervention_summary.v1",
    "openEHR-EHR-CLUSTER.problem_qualifier.v2",
    "openEHR-EHR-OBSERVATION.spirometry_result.v2",
    "openEHR-EHR-OBSERVATION.glasgow_outcome_scale_extended.v1",
    "openEHR-EHR-CLUSTER.imaging_exam-hip_joint.v1",
    "openEHR-EHR-CLUSTER.symptom_sign.v2",
    "openEHR-EHR-OBSERVATION.cpax.v1",
    "openEHR-EHR-INSTRUCTION.therapeutic_item_order.v1",
    "openEHR-EHR-OBSERVATION.adverse_reaction_screening.v1",
    "openEHR-EHR-EVALUATION.adverse_reaction_risk.v2",
    "openEHR-EHR-CLUSTER.fnclcc.v1",
    "openEHR-EHR-CLUSTER.range_of_motion.v1",
    "openEHR-EHR-CLUSTER.pharmacogenetic_test_result.v1",
    "openEHR-EHR-OBSERVATION.revised_cardiac_risk_index.v1",
    "openEHR-EHR-OBSERVATION.charlson_comorbidity_index.v2",
    "openEHR-EHR-CLUSTER.pi_rads_2_1.v1",
    "openEHR-EHR-CLUSTER.who_grade_bone_sarcoma.v1",
    "openEHR-EHR-CLUSTER.gist_modified_nih.v1",
    "openEHR-EHR-OBSERVATION.expanded_prostate_cancer_index_composite.v1",
    "openEHR-EHR-OBSERVATION.categorical_loudness_scaling.v1",
    "openEHR-EHR-CLUSTER.figo_staging_cancer.v1",
    "openEHR-EHR-OBSERVATION.map_hand.v1",
    "openEHR-EHR-OBSERVATION.management_screening.v2",
    "openEHR-EHR-OBSERVATION.guss.v1",
    "openEHR-EHR-OBSERVATION.guss_icu.v1",
    "openEHR-EHR-CLUSTER.physical_dimensions.v1",
    "openEHR-EHR-OBSERVATION.msfc_score.v2",
    "openEHR-EHR-OBSERVATION.mini_bestest.v1",
    "openEHR-EHR-CLUSTER.who_grade_urothelial_neoplasms_2004.v1",
    "openEHR-EHR-CLUSTER.who_grade_urothelial_neoplasms_1973.v1",
    "openEHR-EHR-CLUSTER.eau_nmibc_2021.v1",
    "openEHR-EHR-OBSERVATION.ecog.v2",
]

# Folder where the generated workbooks will be written.
OUTPUT_FOLDER = Path("output")

# Template workbook that TemplateMixer should apply to every generated output.
TEMPLATE_PATH = Path("template.xlsx")

# CKM fetch mode: auto, published or development.
FETCH_MODE = "auto"

# Name of the existing converter script in the same folder.
CONVERTER_SCRIPT = "ArchetypeToSpreadsheet.py"


def _load_converter_module(script_path: Path):
    spec = importlib.util.spec_from_file_location("archetype_converter", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load converter module from: {script_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    converter_path = base_dir / CONVERTER_SCRIPT

    if not converter_path.exists():
        raise FileNotFoundError(
            f"Converter script not found: {converter_path}. "
            f"Put this batch file next to {CONVERTER_SCRIPT}."
        )

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            f"Template workbook not found: {TEMPLATE_PATH}. "
            "Adjust TEMPLATE_PATH or place the template next to this script."
        )

    converter_module = _load_converter_module(converter_path)
    converter = converter_module.ArchetypeToSpreadsheet(output_folder=str(OUTPUT_FOLDER))
    mixer = templatemixer.TemplateMixer(str(TEMPLATE_PATH))

    failures: List[Tuple[str, str]] = []

    for archetype in ARCHETYPES:
        print(f"=== Converting {archetype}")
        try:
            out_path = converter.convert(archetype, fetch_mode=FETCH_MODE)
            print(f"Created: {out_path}")

            mixer.mix(out_path)
            print(f"Mixed template into: {out_path}")
        except Exception as exc:
            failures.append((archetype, str(exc)))
            print(f"FAILED {archetype}: {exc}")

    if failures:
        print("\nFailures:")
        for archetype, error in failures:
            print(f"- {archetype}: {error}")
        return 1

    print("\nAll archetypes converted successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

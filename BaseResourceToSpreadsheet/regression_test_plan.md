# Archetype regression test plan

Purpose: protect behavior while refactoring the script for readability.

## Recommended strategy

Use three layers of checks:

1. **Smoke test**
   - script runs successfully for selected archetypes
   - Excel file is created

2. **Semantic regression checks**
   - assert the specific behaviors we discussed during testing
   - these are the most important and least brittle tests

3. **Optional snapshot test**
   - export a normalized CSV or JSON view of the Excel rows
   - compare against a committed golden file after manual review

## Suggested archetypes for the regression suite

- `openEHR-EHR-OBSERVATION.blood_pressure.v2`
- `openEHR-EHR-OBSERVATION.pulse.v2`
- `openEHR-EHR-OBSERVATION.ecg_result.v1`
- `openEHR-EHR-EVALUATION.problem_diagnosis.v1`
- `openEHR-EHR-EVALUATION.differential_diagnoses.v1`

## Behaviors to lock down

### 1. Observation event handling
- event rows such as `24 hour average (events)` and `Maximum (events)` are emitted as events
- event children are indented below the event row
- interval event math function is resolved from openEHR terminology
- width stays visible for interval events

### 2. Slot vs internal cluster
- internal repeating clusters such as `Per differential` and `Per lead` are `CLUSTER`
- actual slots stay `SLOT (CLUSTER)`
- slot rows are shown, but slot internals are not expanded

### 3. DV_CODED_TEXT options
- local coded text options are shown in the definition field
- openEHR-coded options such as math function are resolved through the terminology XML
- if terminology resolution fails, the script continues and emits an unresolved marker plus a debug warning

### 4. General display behavior
- hierarchy order is parent first, then children
- indentation reflects hierarchy
- RM hide-list still suppresses language / encoding / guideline_id / workflow_id

## Refactor advice

When the code is cleaned up later, keep these tests passing before changing anything else.
Prefer semantic assertions over exact whole-sheet equality because formatting or row order may be intentionally improved later.

## JSON vs runner responsibilities

- The **runner** knows *how* to check things.
- The **JSON** tells it *what* to check for each archetype.

For your requested additions:
- **Slots with includes** -> should be represented in JSON as row expectations on the slot row, usually checking:
  - `type = "SLOT (CLUSTER)"`
  - `definition_contains_all = ["Includes:", "<archetype_name>"]`
- **Event structure** -> should be represented in JSON as:
  - event row existence in `contains`
  - child indentation in `indented_under`
- **RM attributes** -> should be represented in JSON as `absent` checks for hidden rows such as:
  - Language
  - Encoding
  - Guideline id
  - Workflow id

So yes: these *do* belong in the JSON, but the runner must support those check types first.
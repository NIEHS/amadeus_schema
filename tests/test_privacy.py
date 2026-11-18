"""Privacy metadata validation; synthetic fixtures never certify actual releases."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft201909Validator, FormatChecker, ValidationError
from linkml.generators.jsonschemagen import JsonSchemaGenerator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "src/amadeus_schema/schema/amadeus_schema.yaml"
spec = importlib.util.spec_from_file_location("privacy_checks", ROOT / "scripts/validate_privacy.py")
privacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(privacy)


@pytest.fixture(scope="module")
def validator():
    return Draft201909Validator(json.loads(JsonSchemaGenerator(str(SCHEMA)).serialize()),
                                format_checker=FormatChecker())


@pytest.fixture
def pending():
    return yaml.safe_load((ROOT / "examples/privacy/restricted_pending.yaml").read_text())


@pytest.fixture
def profile():
    return {"id": "example:profile", "name": "test", "privacy_profile_version": "1",
            "source_phi_assessment_status": "not_assessed",
            "location_identifiability": "not_assessed",
            "linkage_risk_assessment_status": "not_assessed",
            "location_linked_review_required": True}


def check(validator, doc):
    validator.validate(doc)
    privacy.check_privacy_relationships(doc)


def assessed_example(pending):
    """Invented evidence references for negative controls, not an actual approval."""
    doc = copy.deepcopy(pending)
    doc["privacy_declarations"][0].update(
        input_phi_assessment_status="assessed", input_phi_status="phi_present",
        assessment_evidence_reference="urn:example:synthetic-input-evidence")
    doc["privacy_release_assessments"][0].update(
        release_assessment_status="assessed", release_decision="approved",
        release_access_level="public", output_phi_status="aggregated_no_phi",
        output_artifact_sha256="a" * 64, assessed_by="synthetic-test-assessor",
        assessed_at="2020-01-03T00:00:00Z",
        assessment_evidence_reference="urn:example:synthetic-output-evidence",
        release_assessment_method="synthetic-test-v1",
        release_assessment_scope="Synthetic test only: joint variables, dates, audience and auxiliary information.",
        privacy_transformation_deviation_note="Synthetic test intentionally records no performed transformation.")
    return doc


def test_pending_example_and_all_references_validate(pending):
    privacy.validate_document(pending)


def test_complete_public_example_is_self_contained():
    doc = yaml.safe_load((ROOT / "examples/privacy/public_catalog.yaml").read_text())
    privacy.validate_document(doc)
    privacy.check_public_catalog(doc)


def test_existing_instance_without_privacy_metadata_remains_valid(validator):
    doc = yaml.safe_load((ROOT / "tests/data/valid/AmadeusDatabase-durham_heat_aq_slice.yaml").read_text())
    check(validator, doc)


def test_profile_optional_and_unassessed_has_no_phi_default(validator, profile):
    check(validator, {"schema_version": "0.1.0"})
    doc = {"schema_version": "0.1.0", "privacy_profiles": [profile]}
    check(validator, doc)
    assert "source_phi_status" not in profile


@pytest.mark.parametrize("field,value", [
    ("source_phi_status", "unknown"), ("source_phi_assessment_status", "complete"),
    ("location_identifiability", "safe"), ("location_linked_review_required", "true"),
    ("privacy_profile_version", ["1"]),
])
def test_profile_types_and_enumerations_are_enforced(validator, profile, field, value):
    profile[field] = value
    with pytest.raises(ValidationError):
        validator.validate({"schema_version": "0.1.0", "privacy_profiles": [profile]})


@pytest.mark.parametrize("field", ["name", "privacy_profile_version", "source_phi_assessment_status",
                                   "location_identifiability", "linkage_risk_assessment_status",
                                   "location_linked_review_required"])
def test_profile_required_fields_are_enforced(validator, profile, field):
    del profile[field]
    with pytest.raises(ValidationError):
        validator.validate({"schema_version": "0.1.0", "privacy_profiles": [profile]})


def test_source_classification_requires_assessment_and_evidence(validator, profile):
    doc = {"schema_version": "0.1.0", "privacy_profiles": [profile]}
    profile["source_phi_status"] = "no_phi"
    with pytest.raises(ValueError, match="assessed source"):
        check(validator, doc)
    profile["source_phi_assessment_status"] = "assessed"
    with pytest.raises(ValidationError):
        check(validator, doc)
    profile["assessment_evidence_reference"] = "urn:example:source-evidence"
    check(validator, doc)
    profile["source_phi_status_missing_reason"] = "under_investigation"
    with pytest.raises(ValueError, match="missing reason"):
        check(validator, doc)


def test_identifiability_is_separate_from_phi_classification(validator, profile):
    profile.update(source_phi_assessment_status="assessed", source_phi_status="no_phi",
                   assessment_evidence_reference="urn:example:context-evidence",
                   linkage_risk_assessment_status="assessed",
                   linkage_risk_note="Synthetic assessed context only.",
                   location_identifiability="potentially_identifiable")
    check(validator, {"schema_version": "0.1.0", "privacy_profiles": [profile]})


def test_dangling_profile_and_declaration_references_are_rejected(pending):
    with pytest.raises(ValueError, match="privacy_profile"):
        privacy.check_privacy_relationships({"products": [{"id": "example:p", "privacy_profile": "missing"}]})
    pending["extraction_requests"][0]["privacy_declaration"] = "missing"
    with pytest.raises(ValueError, match="Unresolved"):
        privacy.validate_document(pending)


def test_request_cannot_use_another_location_sets_declaration(validator, pending):
    pending["extraction_requests"][0]["location_set"] = "example:other"
    with pytest.raises(ValueError, match="different LocationSet"):
        check(validator, pending)


def test_pending_or_requested_masking_does_not_authorize_release(validator, pending):
    pending["privacy_release_assessments"][0]["release_decision"] = "approved"
    with pytest.raises(ValidationError):
        check(validator, pending)


@pytest.mark.parametrize("field", ["assessed_by", "assessed_at", "output_phi_status",
                                   "output_artifact_sha256", "assessment_evidence_reference",
                                   "release_assessment_scope", "release_assessment_method"])
def test_assessed_release_requires_artifact_bound_evidence(validator, pending, field):
    doc = assessed_example(pending)
    del doc["privacy_release_assessments"][0][field]
    with pytest.raises(ValidationError):
        check(validator, doc)


def test_public_phi_present_release_is_rejected_but_restricted_authorization_is_distinct(validator, pending):
    doc = assessed_example(pending)
    release = doc["privacy_release_assessments"][0]
    release["output_phi_status"] = "phi_present"
    with pytest.raises(ValueError, match="Public release"):
        check(validator, doc)
    release["release_access_level"] = "restricted"
    check(validator, doc)


def test_performed_actions_need_successful_run_and_requests_remain_independent(validator, pending):
    doc = assessed_example(pending)
    release = doc["privacy_release_assessments"][0]
    release["performed_privacy_transformations"] = [doc["privacy_transformations"][0]["id"]]
    with pytest.raises(ValueError, match="performed transformation run"):
        check(validator, doc)
    action = doc["privacy_transformations"][0]
    action["processing_run"] = "example:run"
    doc["tool_runs"] = [{"id": "example:run", "run_role": "export", "tool_name": "synthetic-test",
                         "tool_version": "1", "run_timestamp_utc": "2020-01-02T00:00:00Z", "status": "failed",
                         "log_excerpt": "Synthetic failure"}]
    with pytest.raises(ValueError, match="successful ToolRun"):
        check(validator, doc)
    doc["tool_runs"][0]["status"] = "succeeded"
    check(validator, doc)
    privacy.validate_document(doc)


def test_release_requires_input_assessment_explicit_history_and_deviation_rationale(validator, pending):
    doc = assessed_example(pending)
    check(validator, doc)
    release = doc["privacy_release_assessments"][0]
    del release["privacy_transformation_deviation_note"]
    with pytest.raises(ValueError, match="rationale"):
        check(validator, doc)
    release["privacy_transformation_deviation_note"] = "Synthetic justification"
    del release["performed_privacy_transformations"]
    with pytest.raises(ValueError, match="explicitly record"):
        check(validator, doc)


def test_input_assessment_and_legacy_label_cannot_be_bypassed(validator, pending):
    doc = assessed_example(pending)
    doc["location_sets"][0]["phi_status"] = "no_phi"
    with pytest.raises(ValueError, match="conflicts"):
        check(validator, doc)
    doc = assessed_example(pending)
    declaration = doc["privacy_declarations"][0]
    declaration["input_phi_assessment_status"] = "not_assessed"
    del declaration["input_phi_status"]
    with pytest.raises(ValueError, match="assessed input"):
        check(validator, doc)


def test_invalid_transformation_enum_and_negative_precision_are_rejected(validator, pending):
    pending["privacy_transformations"][0]["privacy_transformation"] = "guaranteed_anonymous"
    with pytest.raises(ValidationError):
        validator.validate(pending)
    pending["privacy_transformations"][0]["privacy_transformation"] = "suppression"
    pending["locations"][0]["location_precision_m"] = -1
    with pytest.raises(ValidationError):
        validator.validate(pending)


@pytest.mark.parametrize("collection", privacy.RESTRICTED_COLLECTIONS)
def test_restricted_collections_cannot_be_published_even_if_empty(collection):
    with pytest.raises(ValueError, match="Restricted"):
        privacy.check_public_catalog({"schema_version": "0.1.0", collection: []})


def test_new_declarations_never_use_legacy_no_phi_default():
    from linkml_runtime import SchemaView
    view = SchemaView(str(SCHEMA))
    for cls, name in [("PrivacyDeclaration", "input_phi_status"),
                      ("PrivacyProfile", "source_phi_status"),
                      ("PrivacyReleaseAssessment", "output_phi_status")]:
        slot = next(s for s in view.class_induced_slots(cls) if s.name == name)
        assert slot.range == "PhiStatusEnum"
        assert not slot.ifabsent

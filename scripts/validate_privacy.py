"""Validate privacy relationships that span objects, after schema validation.

The CLI validates a restricted AmadeusDatabase instance, including ordinary
references. Public catalog builds call check_public_catalog instead. These
checks validate declarations, never the sufficiency of scientific evidence,
de-identification, authorization authenticity, or runtime access controls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RESTRICTED_COLLECTIONS = (
    "location_sets", "locations", "extraction_requests", "ambient_values_at_location",
    "privacy_declarations", "privacy_transformations", "privacy_release_assessments",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_privacy_relationships(document):
    """Check declared relationships without inferring safety from absent metadata."""
    def records(collection):
        return document.get(collection) or []

    def index(collection):
        rows = records(collection)
        result = {r["id"]: r for r in rows}
        require(len(result) == len(rows), f"Duplicate ID in {collection}")
        return result

    profiles = index("privacy_profiles")
    declarations = index("privacy_declarations")
    transformations = index("privacy_transformations")
    releases = index("privacy_release_assessments")
    requests = index("extraction_requests")
    location_sets = index("location_sets")
    runs = index("tool_runs")

    def ref(mapping, identity, context):
        require(identity in mapping, f"Unresolved {context}: {identity}")
        return mapping[identity]

    for product in records("products"):
        if product.get("privacy_profile") is not None:
            ref(profiles, product["privacy_profile"], "Product.privacy_profile")
    for profile in profiles.values():
        status = profile["source_phi_assessment_status"]
        finding = profile.get("source_phi_status")
        if finding is not None:
            require(status == "assessed", "Source PHI finding requires an assessed source classification")
            require(not profile.get("source_phi_status_missing_reason"),
                    "Source PHI finding conflicts with its missing reason")
        if status == "assessed":
            require(finding is not None and profile.get("assessment_evidence_reference"),
                    "Assessed source classification needs a finding and evidence")
        if profile["location_identifiability"] != "not_assessed":
            require(profile["linkage_risk_assessment_status"] == "assessed",
                    "Location identifiability finding requires an assessed linkage context")
        if profile["linkage_risk_assessment_status"] == "assessed":
            require(profile.get("assessment_evidence_reference") and profile.get("linkage_risk_note"),
                    "Assessed linkage context needs evidence and a scope note")

    for declaration in declarations.values():
        locset = ref(location_sets, declaration["location_set"], "PrivacyDeclaration.location_set")
        finding = declaration.get("input_phi_status")
        assessed = declaration["input_phi_assessment_status"] == "assessed"
        if finding is not None:
            require(assessed, "Input PHI finding requires an assessed declaration")
        if assessed:
            require(finding is not None and declaration.get("assessment_evidence_reference"),
                    "Assessed input declaration needs classification and evidence")
            if locset.get("phi_status") is not None:
                require(locset["phi_status"] == finding,
                        "Input declaration conflicts with LocationSet.phi_status")
        if declaration["location_identifiability"] != "not_assessed":
            require(assessed, "Input location identifiability needs an assessed declaration")

    for request in requests.values():
        if request.get("privacy_declaration") is not None:
            declaration = ref(declarations, request["privacy_declaration"], "ExtractionRequest.privacy_declaration")
            require(declaration["location_set"] == request["location_set"],
                    "Request privacy declaration names a different LocationSet")
        for identity in request.get("requested_privacy_transformations") or []:
            ref(transformations, identity, "requested privacy transformation")
    for transformation in transformations.values():
        if transformation.get("processing_run") is not None:
            ref(runs, transformation["processing_run"], "PrivacyTransformation.processing_run")

    for release in releases.values():
        request = ref(requests, release["extraction_request"], "PrivacyReleaseAssessment.extraction_request")
        declaration = ref(declarations, release["privacy_declaration"], "PrivacyReleaseAssessment.privacy_declaration")
        require(request.get("privacy_declaration") == declaration["id"],
                "Release declaration differs from its request's declaration")
        actual = release.get("performed_privacy_transformations") or []
        for identity in actual:
            action = ref(transformations, identity, "performed privacy transformation")
            run = ref(runs, action.get("processing_run"), "performed transformation run")
            require(run["status"] == "succeeded", "Performed transformation needs a successful ToolRun")
        assessed = release["release_assessment_status"] == "assessed"
        if release.get("output_phi_status") is not None:
            require(assessed, "Output PHI finding requires an assessed release")
        if assessed:
            fields = ("output_phi_status", "output_artifact_sha256", "assessed_by", "assessed_at",
                      "assessment_evidence_reference", "release_assessment_method", "release_assessment_scope")
            require(all(release.get(f) for f in fields), "Assessed release needs artifact-bound evidence and findings")
        if release["release_decision"] == "approved":
            require(assessed and declaration["input_phi_assessment_status"] == "assessed",
                    "Release approval needs assessed input and output")
            require("performed_privacy_transformations" in release and
                    release["performed_privacy_transformations"] is not None,
                    "Approved release must explicitly record performed transformations (possibly [])")
            if release["release_access_level"] == "public":
                require(release["output_phi_status"] != "phi_present",
                        "Public release cannot be approved for phi_present output")
            def signature(identity):
                action = transformations[identity]
                return tuple(action[k] for k in ("privacy_transformation", "privacy_transformation_stage",
                                                 "privacy_transformation_specification"))
            requested = request.get("requested_privacy_transformations") or []
            if [signature(i) for i in requested] != [signature(i) for i in actual]:
                require(release.get("privacy_transformation_deviation_note"),
                        "Approved release needs a rationale for requested/performed transformation differences")


def check_public_catalog(document):
    """Reject restricted collections, even empty ones, at the publication boundary."""
    require(not set(document).intersection(RESTRICTED_COLLECTIONS),
            "Restricted location/request/privacy collections cannot enter a public catalog")
    allowed = {"schema_version", "data_sources", "products", "grid_definitions",
               "canonical_variables", "product_variables", "assets", "privacy_profiles"}
    require(not set(document) - allowed, "Public catalog contains non-catalog collections")
    check_privacy_relationships(document)


def validate_document(document, schema_path=None):
    """Validate structure plus all schema-derived references and privacy joins."""
    from jsonschema import Draft201909Validator, FormatChecker
    from linkml.generators.jsonschemagen import JsonSchemaGenerator
    from linkml_runtime import SchemaView

    schema_path = schema_path or Path(__file__).resolve().parents[1] / "src/amadeus_schema/schema/amadeus_schema.yaml"
    schema = json.loads(JsonSchemaGenerator(str(schema_path)).serialize())
    Draft201909Validator(schema, format_checker=FormatChecker()).validate(document)
    view = SchemaView(str(schema_path))
    collections = {s.name: s.range for s in view.class_induced_slots("AmadeusDatabase") if s.multivalued}
    byclass = {cls: {r["id"]: r for r in document.get(coll) or []}
               for coll, cls in collections.items()}
    ids = [r["id"] for coll in collections for r in document.get(coll) or []]
    require(len(ids) == len(set(ids)), "Duplicate IDs across instance collections")
    for coll, cls in collections.items():
        slots = {s.name: s for s in view.class_induced_slots(cls)}
        for record in document.get(coll) or []:
            for name, value in record.items():
                slot = slots[name]
                if value is None or slot.inlined or slot.range not in byclass:
                    continue
                for target in value if slot.multivalued else [value]:
                    require(target in byclass[slot.range], f"Unresolved {cls}.{name}: {target}")
    check_privacy_relationships(document)


def main():
    import yaml

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance", type=Path)
    args = parser.parse_args()
    validate_document(yaml.safe_load(args.instance.read_text()))
    print("PASS: schema, references and privacy relationships; no scientific privacy certification")


if __name__ == "__main__":
    main()

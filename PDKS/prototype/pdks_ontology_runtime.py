#!/usr/bin/env python3
"""Ontology-first PDKS runtime: validate canonical records and project them to RDF.

The JSON record is the source of truth. RDF is a versioned, rebuildable semantic
projection. This module deliberately does not infer consent or execute agent actions.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, SKOS, OWL, XSD, PROV

PDKS = Namespace("urn:pdks:ontology#")
PDKSV = Namespace("urn:pdks:vocabulary:0.2#")
PDTAX = Namespace("urn:pdks:taxonomy:event:0.1#")
TIME = Namespace("http://www.w3.org/2006/time#")
SH = Namespace("http://www.w3.org/ns/shacl#")
RDF_JSON = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON")

OBJECT_CLASS_MAP = {
    "entity": PDKS.DomainEntity,
    "source_asset": PDKS.SourceAsset,
    "evidence_segment": PDKS.EvidenceSegment,
    "event": PDKS.Event,
    "assertion": PDKS.Assertion,
    "knowledge_asset": PDKS.KnowledgeAsset,
    "personal_context": PDKS.PersonalContextStatement,
    "action": PDKS.ActionSpecification,
    "relationship": PDKS.QualifiedRelationship,
}
ENTITY_SUBTYPE_MAP = {
    "person": PDKS.Person, "organization": PDKS.Organization,
    "project": PDKS.Project, "place": PDKS.Place,
    "topic": PDKS.Topic, "tool": PDKS.Tool, "goal": PDKS.Goal,
}
ACTION_SUBTYPE_MAP = {
    "task": PDKS.Task, "plan": PDKS.Plan, "commitment": PDKS.Commitment,
    "reminder": PDKS.Reminder, "intent": PDKS.Intent,
}
RELATION_PREDICATE_MAP = {
    "derived_from": PDKS.derivedFrom,
    "supports": PDKS.supports,
    "contradicts": PDKS.contradicts,
    "related_to": PDKS.relatedTo,
    "part_of": PDKS.partOf,
    "depends_on": PDKS.dependsOn,
    "participated_in": PDKS.participatedIn,
}
VOCABULARY_VALUES = {
    "domain": {"work","learning","thinking","life","relationship","growth","finance","health","other"},
    "epistemic": {"reported","inferred","hypothesized","corroborated","disputed","retracted","unknown"},
    "assertion": {"observation","opinion","hypothesis","intention","commitment","decision","question","estimate","preference"},
    "context": {"role","goal","capability","responsibility","working_style","current_focus","constraint","relationship_context","preference_context"},
    "sensitivity": {"personal_private","personal_work","organization_internal","restricted","public"},
    "access": {"owner_only","explicitly_shared","organization_authorized","public"},
    "lifecycle": {"active","archived","superseded","retracted","deleted_tombstone","unresolved"},
    "relationship": set(RELATION_PREDICATE_MAP),
}

class OntologyValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))

class OntologyRuntime:
    def __init__(self, assets_dir: str | Path | None = None):
        if assets_dir is None:
            here = Path(__file__).resolve().parents[1]
            assets_dir = (here / "assets") if (here / "assets").exists() else (here / "skills" / "pdks-personal-knowledge" / "assets")
        self.assets_dir = Path(assets_dir)
        self.ontology_dir = self.assets_dir / "ontology" / "0.2.1"
        self.schema_path = self.assets_dir / "pdks-0.1-record.schema.json"
        self.taxonomy_path = self.assets_dir / "pdks-event-taxonomy-0.1.ttl"
        self.ontology_graph = Graph()
        self.vocabulary_graph = Graph()
        self.taxonomy_graph = Graph()
        self.shapes_graph = Graph()
        for name in ("pdks-core-ontology-0.2.ttl","pdks-governance-ontology-0.2.ttl","pdks-agent-runtime-ontology-0.2.ttl"):
            self.ontology_graph.parse(self.ontology_dir / name, format="turtle")
        self.vocabulary_graph.parse(self.ontology_dir / "pdks-core-vocabularies-0.2.ttl", format="turtle")
        self.taxonomy_graph.parse(self.taxonomy_path, format="turtle")
        self.shapes_graph.parse(self.ontology_dir / "pdks-core-shapes-0.2.ttl", format="turtle")
        self.schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        self.event_codes = self._notation_map(self.taxonomy_graph)
        self.vocab_codes = self._notation_map(self.vocabulary_graph)
        self.ontology_version = "0.2.1"
        self.ontology_iri = "urn:pdks:ontology:0.2.1"

    @staticmethod
    def _notation_map(graph: Graph) -> dict[str, URIRef]:
        result = {}
        for node, notation in graph.subject_objects(SKOS.notation):
            result[str(notation)] = node
        return result

    @staticmethod
    def _absolute_iri(value: Any) -> bool:
        if not isinstance(value, str) or not value.strip():
            return False
        return bool(urlsplit(value).scheme)

    def validate_records(self, records: Iterable[dict[str, Any]], *, strict_refs: bool = False,
                         trusted_consent_refs: set[str] | None = None) -> dict[str, Any]:
        records = list(records)
        trusted_consent_refs = set(trusted_consent_refs or ())
        errors: list[str] = []
        warnings: list[str] = []
        try:
            from jsonschema import Draft202012Validator, FormatChecker
            validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
            for i, record in enumerate(records):
                for err in validator.iter_errors(record):
                    path = ".".join(str(x) for x in err.absolute_path) or "$"
                    errors.append(f"record[{i}] {path}: {err.message}")
        except ImportError:
            warnings.append("jsonschema not installed; JSON Schema validation skipped")

        ids: set[str] = set()
        owner_refs: set[str] = set()
        for i, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append(f"record[{i}] must be an object")
                continue
            oid = record.get("object_id")
            typ = record.get("object_type")
            if not self._absolute_iri(oid):
                errors.append(f"record[{i}] object_id must be an absolute IRI")
            elif oid in ids:
                errors.append(f"duplicate object_id: {oid}")
            else:
                ids.add(oid)
            owner = record.get("owner_ref")
            if not self._absolute_iri(owner):
                errors.append(f"record[{i}] owner_ref must be an absolute IRI")
            else:
                owner_refs.add(owner)
            if typ not in OBJECT_CLASS_MAP:
                errors.append(f"record[{i}] unsupported object_type: {typ}")
            payload = record.get("payload", {}) if isinstance(record.get("payload", {}), dict) else {}
            gov = record.get("governance", {}) if isinstance(record.get("governance", {}), dict) else {}
            if typ == "source_asset" and payload.get("capture_method") in {"device_capture","connector_sync"}:
                consent_ref = gov.get("consent_ref")
                if not consent_ref:
                    errors.append(f"record[{i}] {payload.get('capture_method')} requires governance.consent_ref")
                elif consent_ref not in trusted_consent_refs:
                    errors.append(f"record[{i}] consent_ref is not in trusted active authorization set: {consent_ref}")
            for field, category in (("sensitivity","sensitivity"),("access_scope","access")):
                value = gov.get(field)
                if value not in VOCABULARY_VALUES[category]:
                    errors.append(f"record[{i}] governance.{field} is not in controlled vocabulary: {value}")
            for domain in record.get("domains", []) or []:
                if domain not in VOCABULARY_VALUES["domain"]:
                    errors.append(f"record[{i}] unknown domain: {domain}")
            if typ == "event":
                code = payload.get("event_type")
                if code not in self.event_codes:
                    errors.append(f"record[{i}] event_type not found in event taxonomy: {code}")
                start, end = payload.get("start_at"), payload.get("end_at")
                if start and end:
                    try:
                        if datetime.fromisoformat(end) < datetime.fromisoformat(start):
                            errors.append(f"record[{i}] event end_at precedes start_at")
                    except ValueError:
                        errors.append(f"record[{i}] invalid event time interval")
                if not payload.get("description"):
                    errors.append(f"record[{i}] event description is required by ontology profile")
            elif typ == "assertion":
                if payload.get("epistemic_status") not in VOCABULARY_VALUES["epistemic"]:
                    errors.append(f"record[{i}] invalid assertion epistemic_status")
                if payload.get("assertion_type") not in VOCABULARY_VALUES["assertion"]:
                    errors.append(f"record[{i}] invalid assertion_type")
                if not payload.get("asserted_by_ref"):
                    errors.append(f"record[{i}] assertion must retain asserted_by_ref")
            elif typ == "personal_context":
                if payload.get("context_type") not in VOCABULARY_VALUES["context"]:
                    errors.append(f"record[{i}] invalid personal_context context_type")
                if not payload.get("subject_ref"):
                    errors.append(f"record[{i}] personal_context must identify subject_ref")
                if not payload.get("verification_status"):
                    errors.append(f"record[{i}] personal_context must retain verification_status")
            elif typ == "evidence_segment" and not payload.get("source_ref"):
                errors.append(f"record[{i}] evidence_segment must link to source_ref")
            elif typ == "relationship":
                if not payload.get("subject_ref") or not payload.get("object_ref") or not payload.get("predicate"):
                    errors.append(f"record[{i}] relationship requires subject_ref, predicate and object_ref")
                elif payload.get("predicate") not in VOCABULARY_VALUES["relationship"]:
                    errors.append(f"record[{i}] relationship predicate is not in controlled vocabulary: {payload.get('predicate')}")
            elif typ == "action" and not payload.get("title"):
                errors.append(f"record[{i}] action title is required")

        if len(owner_refs) > 1:
            errors.append("one import batch must contain exactly one owner_ref")
        if strict_refs:
            known = ids
            for i, record in enumerate(records):
                refs = list(self._iter_record_refs(record.get("payload", {})))
                refs.extend(record.get("provenance", {}).get("source_refs", []) or [])
                for ref in refs:
                    if (isinstance(ref, str) and ref.startswith("urn:pdks:")
                            and not ref.startswith(("urn:pdks:agent:","urn:pdks:external:"))
                            and ref not in known):
                        errors.append(f"record[{i}] unresolved internal reference: {ref}")
        return {
            "status": "valid" if not errors else "invalid",
            "records": len(records), "unique_ids": len(ids),
            "owners": sorted(owner_refs), "errors": errors, "warnings": warnings,
            "ontology_version": self.ontology_version,
            "shacl_runtime": "not_run",
            "authorization_gate": "passed" if not errors else "blocked",
            "trusted_consent_refs_supplied": len(trusted_consent_refs)
        }

    @staticmethod
    def _pyshacl_available() -> bool:
        try:
            import pyshacl  # noqa: F401
            return True
        except ImportError:
            return False

    def validate_shacl(self, data_graph: Graph, *, advanced: bool = True) -> dict[str, Any]:
        """Execute the versioned SHACL shapes against one owner's RDF projection.

        Controlled vocabularies and the event taxonomy are included as read-only
        reference data so sh:class and SPARQL scheme-membership constraints can
        be evaluated without dereferencing remote ontology imports.
        """
        try:
            from pyshacl import validate as shacl_validate
        except ImportError:
            return {
                "status": "unavailable",
                "conforms": None,
                "results_count": 0,
                "message": "pySHACL is not installed; install requirements-ontology.txt to execute SHACL validation.",
                "report_text": None,
                "results": [],
            }

        validation_graph = Graph()
        for triple in data_graph:
            validation_graph.add(triple)
        for reference_graph in (self.vocabulary_graph, self.taxonomy_graph):
            for triple in reference_graph:
                validation_graph.add(triple)

        conforms, report_graph, report_text = shacl_validate(
            data_graph=validation_graph,
            shacl_graph=self.shapes_graph,
            ont_graph=self.ontology_graph,
            inference="rdfs",
            abort_on_first=False,
            allow_infos=False,
            allow_warnings=False,
            meta_shacl=True,
            advanced=advanced,
            inplace=False,
        )
        results = []
        for result in report_graph.subjects(RDF.type, SH.ValidationResult):
            results.append({
                "focus_node": str(report_graph.value(result, SH.focusNode) or ""),
                "result_path": str(report_graph.value(result, SH.resultPath) or ""),
                "severity": str(report_graph.value(result, SH.resultSeverity) or ""),
                "message": str(report_graph.value(result, SH.resultMessage) or ""),
                "source_shape": str(report_graph.value(result, SH.sourceShape) or ""),
                "constraint_component": str(report_graph.value(result, SH.sourceConstraintComponent) or ""),
            })
        return {
            "status": "conforms" if conforms else "non_conformant",
            "conforms": bool(conforms),
            "results_count": len(results),
            "message": "SHACL validation completed.",
            "report_text": str(report_text),
            "results": results,
        }

    @staticmethod
    def _iter_record_refs(value: Any):
        if isinstance(value, dict):
            for key, child in value.items():
                if key.endswith("_ref") and isinstance(child, str):
                    yield child
                elif key.endswith("_refs") and isinstance(child, list):
                    for item in child:
                        if isinstance(item, str):
                            yield item
                else:
                    yield from OntologyRuntime._iter_record_refs(child)
        elif isinstance(value, list):
            for item in value:
                yield from OntologyRuntime._iter_record_refs(item)

    def project_records(self, records: Iterable[dict[str, Any]]) -> Graph:
        graph = Graph()
        self._bind(graph)
        for record in records:
            self.project_record(record, graph)
        return graph

    @staticmethod
    def _bind(graph: Graph) -> None:
        graph.bind("pdks", PDKS)
        graph.bind("pdksv", PDKSV)
        graph.bind("pdtax", PDTAX)
        graph.bind("prov", PROV)
        graph.bind("skos", SKOS)
        graph.bind("time", TIME)
        graph.bind("dcterms", DCTERMS)

    def _concept(self, code: str | None) -> URIRef | None:
        if code is None:
            return None
        return self.vocab_codes.get(code)

    @staticmethod
    def _uri(value: Any) -> URIRef | None:
        if isinstance(value, str) and value.strip() and urlsplit(value).scheme:
            return URIRef(value)
        return None

    @staticmethod
    def _add_literal(g: Graph, subject, predicate, value, datatype=None):
        if value is None:
            return
        if isinstance(value, (str, int, float, bool)):
            if isinstance(value, bool):
                dt = XSD.boolean
            elif isinstance(value, int):
                dt = XSD.integer
            elif isinstance(value, float):
                dt = XSD.decimal
            else:
                dt = datatype
            g.add((subject, predicate, Literal(value, datatype=dt) if dt else Literal(value)))

    @staticmethod
    def _add_ref(g: Graph, subject, predicate, value):
        uri = OntologyRuntime._uri(value)
        if uri:
            g.add((subject, predicate, uri))

    def _add_time_instant(self, g: Graph, parent, predicate, value, suffix: str):
        if not value:
            return
        node = URIRef(f"{str(parent)}#{suffix}")
        g.add((parent, predicate, node))
        g.add((node, RDF.type, TIME.Instant))
        g.add((node, TIME.inXSDDateTimeStamp, Literal(value, datatype=XSD.dateTimeStamp)))

    def _add_time_interval(self, g: Graph, parent, predicate, start, end, suffix: str):
        if not start and not end:
            return
        interval = URIRef(f"{str(parent)}#{suffix}")
        g.add((parent, predicate, interval))
        g.add((interval, RDF.type, TIME.Interval))
        if start:
            self._add_time_instant(g, interval, TIME.hasBeginning, start, "begin")
        if end:
            self._add_time_instant(g, interval, TIME.hasEnd, end, "end")

    def project_record(self, record: dict[str, Any], graph: Graph | None = None) -> Graph:
        g = graph if graph is not None else Graph()
        self._bind(g)
        subject = self._uri(record.get("object_id"))
        if subject is None:
            raise ValueError("object_id must be an absolute IRI")
        typ = record.get("object_type")
        payload = record.get("payload", {}) or {}
        g.add((subject, RDF.type, PDKS.PersonalDataRecord))
        g.add((subject, RDF.type, OBJECT_CLASS_MAP[typ]))
        self._add_literal(g, subject, PDKS.objectTypeCode, typ)
        self._add_literal(g, subject, PDKS.recordSchemaVersion, record.get("pdks_version"))
        self._add_literal(g, subject, DCTERMS.created, record.get("created_at"), XSD.dateTime)
        self._add_literal(g, subject, DCTERMS.modified, record.get("updated_at"), XSD.dateTime)
        self._add_literal(g, subject, PDKS.recordedAt, record.get("created_at"), XSD.dateTimeStamp)
        self._add_ref(g, subject, PDKS.ownedBy, record.get("owner_ref"))
        for domain in record.get("domains", []) or []:
            concept = self._concept(domain)
            if concept:
                g.add((subject, PDKS.hasDomain, concept))
        provenance = record.get("provenance", {}) or {}
        self._add_ref(g, subject, PROV.wasAttributedTo, provenance.get("created_by"))
        self._add_ref(g, subject, PDKS.generatedBy, provenance.get("processing_activity_ref"))
        for ref in provenance.get("source_refs", []) or []:
            self._add_ref(g, subject, PDKS.hasSourceReference, ref)
        governance = record.get("governance", {}) or {}
        sensitivity = self._concept(governance.get("sensitivity"))
        access_scope = self._concept(governance.get("access_scope"))
        if sensitivity: g.add((subject, PDKS.hasSensitivity, sensitivity))
        if access_scope: g.add((subject, PDKS.hasAccessScope, access_scope))
        self._add_ref(g, subject, PDKS.hasConsent, governance.get("consent_ref"))
        lifecycle = record.get("lifecycle", {}) or {}
        self._add_literal(g, subject, PDKS.lifecycleStatus, lifecycle.get("status"))
        self._add_literal(g, subject, PDKS.recordVersion, lifecycle.get("version"))
        self._add_ref(g, subject, PDKS.supersedes, lifecycle.get("supersedes_ref"))
        self._add_time_interval(g, subject, PDKS.validDuring, lifecycle.get("valid_from"), lifecycle.get("valid_until"), "valid-during")

        if typ == "entity":
            subtype = ENTITY_SUBTYPE_MAP.get(payload.get("entity_type"))
            if subtype: g.add((subject, RDF.type, subtype))
            self._add_literal(g, subject, PDKS.entityTypeCode, payload.get("entity_type"))
            self._add_literal(g, subject, PDKS.canonicalName, payload.get("canonical_name"))
            self._add_literal(g, subject, PDKS.description, payload.get("description"))
            for alias in payload.get("aliases", []) or []:
                self._add_literal(g, subject, PDKS.alternateName, alias)
        elif typ == "source_asset":
            for key, prop in [
                ("source_type",PDKS.sourceType),("origin_system",PDKS.originSystem),
                ("source_locator",PDKS.sourceLocator),("media_type",PDKS.mediaType),
                ("capture_method",PDKS.captureMethod)
            ]:
                self._add_literal(g, subject, prop, payload.get(key))
            self._add_literal(g, subject, PDKS.capturedAt, payload.get("captured_at"), XSD.dateTimeStamp)
            ch = payload.get("content_hash")
            if isinstance(ch, dict):
                self._add_literal(g, subject, PDKS.contentHash, f"{ch.get('algorithm','sha256')}:{ch.get('value','')}")
            self._add_ref(g, subject, PDKS.hasConsent, governance.get("consent_ref"))
        elif typ == "evidence_segment":
            self._add_ref(g, subject, PDKS.extractedFrom, payload.get("source_ref"))
            self._add_literal(g, subject, PDKS.excerpt, payload.get("excerpt"))
            locator = payload.get("locator")
            if locator is not None:
                self._add_literal(g, subject, PDKS.locatorJson, json.dumps(locator,ensure_ascii=False,sort_keys=True), RDF_JSON)
            for key, prop in (("modality",PDKS.modality),("transcript_status",PDKS.transcriptStatus),("recognition_quality",PDKS.recognitionQuality)):
                self._add_literal(g, subject, prop, payload.get(key))
        elif typ == "event":
            code = payload.get("event_type")
            if code in self.event_codes:
                g.add((subject, PDKS.hasEventType, self.event_codes[code]))
            self._add_literal(g, subject, PDKS.title, payload.get("title"))
            self._add_literal(g, subject, PDKS.description, payload.get("description"))
            self._add_literal(g, subject, PDKS.timePrecision, payload.get("time_precision"))
            self._add_literal(g, subject, PDKS.eventMode, payload.get("event_mode"))
            self._add_literal(g, subject, PDKS.eventTaxonomyVersion, payload.get("event_taxonomy_version"))
            self._add_time_interval(g, subject, PDKS.occurredDuring, payload.get("start_at"), payload.get("end_at"), "occurred-during")
            for ref in payload.get("context_refs", []) or []:
                self._add_ref(g, subject, PDKS.hasContextEntity, ref)
            for ref in payload.get("evidence_refs", []) or []:
                self._add_ref(g, subject, PDKS.hasEvidence, ref)
            for i, participant in enumerate(payload.get("participants", []) or []):
                if not isinstance(participant, dict): continue
                actor = self._uri(participant.get("entity_ref"))
                if actor:
                    g.add((subject, PDKS.hasParticipant, actor))
                    assignment = URIRef(f"{str(subject)}#participant-{i+1}")
                    g.add((subject, PDKS.hasParticipantAssignment, assignment))
                    g.add((assignment, RDF.type, PDKS.ParticipantRoleAssignment))
                    g.add((assignment, PDKS.participantAgent, actor))
                    self._add_literal(g, assignment, PDKS.participantRole, participant.get("role"))
                    self._add_literal(g, assignment, PDKS.identityStatus, participant.get("identity_status"))
        elif typ == "assertion":
            self._add_literal(g, subject, PDKS.content, payload.get("content"))
            # A qualified relationship is an InformationObject, not an Assertion.
            self._add_ref(g, subject, PDKS.attributedTo, payload.get("asserted_by_ref"))
            self._add_literal(g, subject, PDKS.assertionAt, payload.get("assertion_at"), XSD.dateTimeStamp)
            for field, prop in (("assertion_type",PDKS.hasAssertionType),("epistemic_status",PDKS.hasEpistemicStatus)):
                concept = self._concept(payload.get(field))
                if concept: g.add((subject, prop, concept))
            for ref in payload.get("about_refs", []) or []:
                self._add_ref(g, subject, PDKS.about, ref)
            for ref in payload.get("evidence_refs", []) or []:
                self._add_ref(g, subject, PDKS.hasEvidence, ref)
        elif typ == "knowledge_asset":
            for field, prop in (("title",PDKS.title),("summary",PDKS.summary),("content",PDKS.content),("knowledge_type",PDKS.knowledgeType),("verification_status",PDKS.verificationStatus)):
                self._add_literal(g, subject, prop, payload.get(field))
            for ref in payload.get("derived_from_refs", []) or []:
                self._add_ref(g, subject, PDKS.derivedFrom, ref)
            for item in payload.get("applicability", []) or []:
                self._add_literal(g, subject, PDKS.applicability, item)
            for item in payload.get("limitations", []) or []:
                self._add_literal(g, subject, PDKS.limitation, item)
        elif typ == "personal_context":
            self._add_ref(g, subject, PDKS.hasSubject, payload.get("subject_ref"))
            self._add_literal(g, subject, PDKS.content, payload.get("value"))
            self._add_literal(g, subject, PDKS.verificationStatus, payload.get("verification_status"))
            self._add_literal(g, subject, PDKS.confidenceLevel, payload.get("confidence_level"))
            self._add_literal(g, subject, PDKS.reviewPolicy, payload.get("review_policy"))
            concept = self._concept(payload.get("context_type"))
            if concept: g.add((subject, PDKS.hasContextType, concept))
            for ref in payload.get("evidence_refs", []) or []:
                self._add_ref(g, subject, PDKS.hasEvidence, ref)
        elif typ == "action":
            subtype = ACTION_SUBTYPE_MAP.get(payload.get("action_type"))
            if subtype: g.add((subject, RDF.type, subtype))
            for field, prop in (("title",PDKS.title),("description",PDKS.description),("status",PDKS.actionStatus),("priority",PDKS.priority)):
                self._add_literal(g, subject, prop, payload.get(field))
            self._add_ref(g, subject, PDKS.assignedTo, payload.get("assignee_ref"))
            self._add_time_instant(g, subject, PDKS.hasDueTime, payload.get("due_at"), "due-at")
            for ref in payload.get("created_from_refs", []) or []:
                self._add_ref(g, subject, PDKS.derivedFrom, ref)
        elif typ == "relationship":
            subj = self._uri(payload.get("subject_ref"))
            obj = self._uri(payload.get("object_ref"))
            predicate_code = payload.get("predicate")
            self._add_ref(g, subject, PDKS.relationshipSubject, payload.get("subject_ref"))
            self._add_ref(g, subject, PDKS.relationshipObject, payload.get("object_ref"))
            self._add_literal(g, subject, PDKS.relationshipPredicateCode, predicate_code)
            self._add_literal(g, subject, PDKS.relationshipStatus, payload.get("status"))
            self._add_literal(g, subject, PDKS.confidenceLevel, payload.get("confidence_level"))
            self._add_ref(g, subject, PDKS.assertedBy, payload.get("asserted_by_ref"))
            for ref in payload.get("evidence_refs", []) or []:
                self._add_ref(g, subject, PDKS.hasEvidence, ref)
            concept = self._concept(predicate_code)
            if concept: g.add((subject, PDKS.relationshipPredicate, concept))
            direct = RELATION_PREDICATE_MAP.get(predicate_code)
            if subj and obj and direct:
                g.add((subj, direct, obj))
        return g

#!/usr/bin/env python3
"""Ontology CI checks: term coverage, migration bridges and semantic compatibility."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS

try:
    from .pdks_ontology_runtime import VOCABULARY_VALUES
except ImportError:
    from pdks_ontology_runtime import VOCABULARY_VALUES

TERM_TYPES = (OWL.Class, RDFS.Class, OWL.ObjectProperty, OWL.DatatypeProperty, RDF.Property)


def _local(uri: Any) -> str:
    return str(uri).rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def declared_terms(graph: Graph) -> dict[URIRef, URIRef]:
    result: dict[URIRef, URIRef] = {}
    for term_type in TERM_TYPES:
        for term in graph.subjects(RDF.type, term_type):
            result[term] = term_type
    return result


def _map_legacy_uri(uri: URIRef) -> URIRef:
    value = str(uri)
    if value.startswith("urn:pdks:ontology:0.1#"):
        return URIRef(value.replace("urn:pdks:ontology:0.1#", "urn:pdks:ontology#", 1))
    return uri


def check_runtime_term_coverage(runtime, runtime_source: str | Path | None = None) -> dict[str, Any]:
    """Check code symbols, controlled codes, event codes and JSON-LD aliases."""
    if runtime_source is None:
        runtime_source = Path(__file__).with_name("pdks_ontology_runtime.py")
    source = Path(runtime_source).read_text(encoding="utf-8")
    used_pdks = sorted(set(re.findall(r"\bPDKS\.([A-Za-z_][A-Za-z0-9_]*)", source)))
    declared_pdks = {
        _local(term) for term in declared_terms(runtime.ontology_graph)
        if str(term).startswith("urn:pdks:ontology#")
    }
    missing_pdks = sorted(set(used_pdks) - declared_pdks)

    vocab_values = sorted({value for values in VOCABULARY_VALUES.values() for value in values})
    missing_vocab = sorted(set(vocab_values) - set(runtime.vocab_codes))

    event_codes = sorted(runtime.event_codes)
    if not event_codes:
        missing_event_taxonomy = ["<empty event taxonomy>"]
    else:
        missing_event_taxonomy = []

    context_path = runtime.ontology_dir / "pdks-jsonld-context-0.2.json"
    context = json.loads(context_path.read_text(encoding="utf-8"))["@context"]
    context_errors: list[str] = []
    for alias, definition in context.items():
        if alias.startswith("@") or not isinstance(definition, dict):
            continue
        target = definition.get("@id")
        if not isinstance(target, str) or target.startswith("@"):
            continue
        if target.startswith("pdks:"):
            local = target.split(":", 1)[1]
            if local not in declared_pdks:
                context_errors.append(f"{alias} -> {target} is not a declared PDKS term")

    return {
        "status": "valid" if not (missing_pdks or missing_vocab or missing_event_taxonomy or context_errors) else "invalid",
        "runtime_terms_referenced": len(used_pdks),
        "runtime_terms_declared": len(set(used_pdks) & declared_pdks),
        "missing_runtime_terms": missing_pdks,
        "controlled_vocabulary_codes": len(runtime.vocab_codes),
        "required_controlled_vocabulary_codes": len(vocab_values),
        "missing_controlled_vocabulary_codes": missing_vocab,
        "event_taxonomy_codes": len(event_codes),
        "missing_event_taxonomy": missing_event_taxonomy,
        "jsonld_context_errors": context_errors,
    }


def _is_subclass_of(graph: Graph, child, parent) -> bool:
    """Return whether child is parent or a transitive rdfs:subClassOf of parent."""
    if child == parent:
        return True
    seen = set()
    pending = [child]
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        for superclass in graph.objects(current, RDFS.subClassOf):
            if superclass == parent:
                return True
            if superclass not in seen:
                pending.append(superclass)
    return False


def compare_ontology_versions(baseline: Graph, candidate: Graph) -> dict[str, Any]:
    """Compare declared terms and property constraints with an explicit bridge requirement.

    Removing a legacy term without an equivalence bridge is breaking. Adding a
    narrower domain/range constraint is breaking. Replacing a class constraint
    with one of its superclasses broadens the constraint and is recorded for
    review rather than incorrectly classified as a breaking change.
    """
    old_terms = declared_terms(baseline)
    new_terms = declared_terms(candidate)
    breaking: list[dict[str, Any]] = []
    relaxed: list[dict[str, Any]] = []
    bridged: list[dict[str, Any]] = []

    for old_uri, old_type in sorted(old_terms.items(), key=lambda item: str(item[0])):
        eq_pred = OWL.equivalentClass if old_type in (OWL.Class, RDFS.Class) else OWL.equivalentProperty
        targets = list(candidate.objects(old_uri, eq_pred))
        target = targets[0] if targets else None
        if target is None or target not in new_terms:
            issue = {"kind": "removed_term_without_bridge", "term": str(old_uri), "term_type": str(old_type)}
            breaking.append(issue)
            continue
        if old_uri != target:
            bridged.append({"from": str(old_uri), "to": str(target), "term_type": str(old_type)})

        if old_type in (OWL.ObjectProperty, OWL.DatatypeProperty, RDF.Property):
            for predicate, label in ((RDFS.domain, "domain"), (RDFS.range, "range")):
                old_values = {_map_legacy_uri(x) for x in baseline.objects(old_uri, predicate)}
                new_values = set(candidate.objects(target, predicate))
                added = new_values - old_values
                removed = old_values - new_values
                broadened = {
                    new_value for new_value in added
                    if any(_is_subclass_of(candidate, old_value, new_value) for old_value in removed)
                }
                tightened = added - broadened
                if tightened:
                    breaking.append({
                        "kind": f"{label}_constraint_tightened", "term": str(old_uri),
                        "target": str(target), "added": sorted(map(str, tightened)),
                    })
                if broadened:
                    relaxed.append({
                        "kind": f"{label}_constraint_broadened", "term": str(old_uri),
                        "target": str(target), "added": sorted(map(str, broadened)),
                        "replaces": sorted(map(str, removed)),
                    })
                if removed:
                    relaxed.append({
                        "kind": f"{label}_constraint_relaxed", "term": str(old_uri),
                        "target": str(target), "removed": sorted(map(str, removed)),
                    })

    old_targets = {_map_legacy_uri(term) for term in old_terms}
    additions = sorted(str(term) for term in new_terms if term not in old_targets and not str(term).startswith("urn:pdks:ontology:0.1#"))
    status = "breaking" if breaking else ("compatible_with_review" if relaxed else "compatible")
    return {
        "status": status,
        "baseline_declared_terms": len(old_terms),
        "candidate_declared_terms": len(new_terms),
        "bridged_legacy_terms": len(bridged),
        "added_terms": len(additions),
        "breaking_changes": breaking,
        "relaxed_constraints_requiring_review": relaxed,
        "bridges": bridged,
        "additions": additions,
    }


def load_candidate_ontology(ontology_dir: str | Path) -> Graph:
    directory = Path(ontology_dir)
    graph = Graph()
    for name in (
        "pdks-core-ontology-0.2.ttl",
        "pdks-governance-ontology-0.2.ttl",
        "pdks-agent-runtime-ontology-0.2.ttl",
    ):
        graph.parse(directory / name, format="turtle")
    return graph


def check_vocabulary_migration(old_vocab_path: str | Path, candidate_vocab: Graph) -> dict[str, Any]:
    old_graph = Graph().parse(old_vocab_path, format="turtle")
    new_by_code = {str(code): node for node, code in candidate_vocab.subject_objects(SKOS.notation)}
    missing = []
    mapped = []
    for old_node, code in old_graph.subject_objects(SKOS.notation):
        value = str(code)
        if value.endswith(".0") and value.split(".")[0].isdigit():
            continue  # version labels describe the scheme, not a domain concept
        new_node = new_by_code.get(value)
        if new_node is None or (old_node, SKOS.exactMatch, new_node) not in candidate_vocab:
            missing.append({"code": value, "old": str(old_node), "new": str(new_node or "")})
        else:
            mapped.append({"code": value, "old": str(old_node), "new": str(new_node)})
    return {
        "status": "valid" if not missing else "invalid",
        "legacy_concepts": len(mapped) + len(missing),
        "bridged_concepts": len(mapped),
        "missing_bridges": missing,
    }


def verify_ontology_manifest(ontology_dir: str | Path) -> dict[str, Any]:
    import hashlib
    directory = Path(ontology_dir)
    manifest_path = directory / "ontology-manifest.json"
    if not manifest_path.exists():
        return {"status": "missing", "manifest": str(manifest_path), "errors": ["ontology-manifest.json not found"]}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []
    for item in manifest.get("files", []):
        path = directory / item["path"]
        if not path.exists():
            errors.append(f"missing file: {item['path']}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item.get("sha256"):
            errors.append(f"sha256 mismatch: {item['path']}")
    return {
        "status": "valid" if not errors else "invalid",
        "ontology_version": manifest.get("ontology_version"),
        "files_verified": len(manifest.get("files", [])) - len(errors),
        "files_declared": len(manifest.get("files", [])),
        "errors": errors,
    }


def build_governance_report(runtime, baseline_path: str | Path | None = None) -> dict[str, Any]:
    baseline_path = Path(baseline_path) if baseline_path else runtime.assets_dir / "pdks-core-ontology-0.1.ttl"
    baseline = Graph().parse(baseline_path, format="turtle")
    coverage = check_runtime_term_coverage(runtime)
    compatibility = compare_ontology_versions(baseline, runtime.ontology_graph)
    old_vocab_path = runtime.assets_dir / "pdks-core-vocabularies-0.1.ttl"
    vocabulary_migration = check_vocabulary_migration(old_vocab_path, runtime.vocabulary_graph)
    manifest = verify_ontology_manifest(runtime.ontology_dir)
    valid = (coverage["status"] == "valid" and compatibility["status"] != "breaking"
             and vocabulary_migration["status"] == "valid" and manifest["status"] == "valid")
    return {
        "status": "valid" if valid else "invalid",
        "ontology_version": runtime.ontology_version,
        "term_coverage": coverage,
        "compatibility": compatibility,
        "vocabulary_migration": vocabulary_migration,
        "manifest": manifest,
    }

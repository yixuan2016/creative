from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"prototype"))
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, SKOS, OWL, RDFS
from pdks_ontology_runtime import OntologyRuntime, PDKS, PDTAX, TIME, OntologyValidationError
from pdks_ontology_sqlite import OntologySQLiteStore, ConcurrentWriteError, ObjectConflictError
from pdks_ontology_governance import (build_governance_report, compare_ontology_versions,
    check_runtime_term_coverage, check_vocabulary_migration, verify_ontology_manifest)

SKILL=ROOT/"skills"/"pdks-personal-knowledge"
SCENARIOS=SKILL/"examples"/"scenarios"

def load_scenario(name):
    folder=SCENARIOS/name
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(folder.glob("*.json"))]

def trusted_consents(records):
    return {r.get("governance",{}).get("consent_ref") for r in records
            if r.get("object_type")=="source_asset" and r.get("governance",{}).get("consent_ref")}

class OntologyFirstRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime=OntologyRuntime()

    def test_ontology_modules_parse(self):
        self.assertGreater(len(self.runtime.ontology_graph),400)
        self.assertGreater(len(self.runtime.vocabulary_graph),300)
        self.assertGreater(len(self.runtime.taxonomy_graph),300)
        self.assertGreater(len(self.runtime.shapes_graph),50)
        self.assertEqual(self.runtime.ontology_version,"0.2.1")

    def test_all_three_scenarios_validate(self):
        total=0
        for name in ("daily-work","research","voice-meeting"):
            records=load_scenario(name)
            result=self.runtime.validate_records(records,strict_refs=True,trusted_consent_refs=trusted_consents(records))
            self.assertEqual(result["status"],"valid",result["errors"])
            total+=len(records)
        self.assertEqual(total,29)


    def test_device_capture_requires_trusted_consent_reference(self):
        records=load_scenario("voice-meeting")
        blocked=self.runtime.validate_records(records,strict_refs=True,trusted_consent_refs=set())
        self.assertEqual(blocked["status"],"invalid")
        self.assertTrue(any("trusted active authorization set" in x for x in blocked["errors"]))
        allowed=self.runtime.validate_records(records,strict_refs=True,trusted_consent_refs=trusted_consents(records))
        self.assertEqual(allowed["status"],"valid")

    def test_event_projects_to_ontology_and_taxonomy_concept(self):
        records=load_scenario("voice-meeting")
        event=next(x for x in records if x["object_type"]=="event")
        graph=self.runtime.project_record(event)
        subject=URIRef(event["object_id"])
        self.assertIn((subject,RDF.type,PDKS.Event),graph)
        event_type=list(graph.objects(subject,PDKS.hasEventType))
        self.assertEqual(len(event_type),1)
        self.assertIn((event_type[0],SKOS.notation,None),self.runtime.taxonomy_graph)
        interval=list(graph.objects(subject,PDKS.occurredDuring))[0]
        self.assertIn((interval,RDF.type,TIME.Interval),graph)
        self.assertTrue(list(graph.objects(interval,TIME.hasBeginning)))
        self.assertTrue(list(graph.objects(interval,TIME.hasEnd)))

    def test_assertion_and_creator_are_distinct_roles(self):
        records=load_scenario("voice-meeting")
        assertion=next(x for x in records if x["object_type"]=="assertion")
        graph=self.runtime.project_record(assertion)
        subject=URIRef(assertion["object_id"])
        creator=URIRef(assertion["provenance"]["created_by"])
        speaker=URIRef(assertion["payload"]["asserted_by_ref"])
        self.assertIn((subject,URIRef("http://www.w3.org/ns/prov#wasAttributedTo"),creator),graph)
        self.assertIn((subject,PDKS.assertedBy,speaker),graph)

    def test_action_does_not_become_agent_action_proposal(self):
        records=load_scenario("voice-meeting")
        action=next(x for x in records if x["object_type"]=="action")
        graph=self.runtime.project_record(action)
        subject=URIRef(action["object_id"])
        self.assertIn((subject,RDF.type,PDKS.ActionSpecification),graph)
        self.assertNotIn((subject,RDF.type,PDKS.AgentActionProposal),graph)

    def test_strict_refs_reject_missing_internal_payload_reference(self):
        records=load_scenario("voice-meeting")
        event=next(x for x in records if x["object_type"]=="event")
        event["payload"]["context_refs"].append("urn:pdks:example:missing:entity:1")
        result=self.runtime.validate_records(records,strict_refs=True,trusted_consent_refs=trusted_consents(records))
        self.assertEqual(result["status"],"invalid")
        self.assertTrue(any("unresolved internal reference" in x for x in result["errors"]))

    def test_sqlite_import_restart_idempotency_and_rdf_export(self):
        records=load_scenario("voice-meeting")
        owner=records[0]["owner_ref"]
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"personal.sqlite3"
            store=OntologySQLiteStore(db,self.runtime)
            result=store.import_records(owner,records,expected_revision=0,strict_refs=True,trusted_consent_refs=trusted_consents(records))
            self.assertEqual(result["inserted"],11)
            self.assertEqual(store.revision(owner),1)
            first_graph=store.export_graph(owner)
            self.assertGreater(len(first_graph),200)
            restarted=OntologySQLiteStore(db,self.runtime)
            self.assertEqual(len(restarted.list_objects(owner)),11)
            self.assertEqual(len(restarted.export_graph(owner)),len(first_graph))
            same=restarted.import_records(owner,records,expected_revision=1,strict_refs=True,trusted_consent_refs=trusted_consents(records))
            self.assertEqual(same["status"],"no_change")
            self.assertEqual(restarted.revision(owner),1)
            turtle=restarted.export_turtle(owner)
            parsed=Graph().parse(data=turtle,format="turtle")
            self.assertEqual(len(parsed),len(first_graph))
            self.assertEqual(restarted.integrity_check(),"ok")

    def test_owner_partition_and_optimistic_concurrency(self):
        a=load_scenario("voice-meeting")
        b=load_scenario("daily-work")
        owner_a=a[0]["owner_ref"]; owner_b=b[0]["owner_ref"]
        with tempfile.TemporaryDirectory() as td:
            store=OntologySQLiteStore(Path(td)/"p.sqlite3",self.runtime)
            store.import_records(owner_a,a,expected_revision=0,strict_refs=True,trusted_consent_refs=trusted_consents(a))
            store.import_records(owner_b,b,expected_revision=0,strict_refs=True,trusted_consent_refs=trusted_consents(b))
            self.assertEqual(len(store.list_objects(owner_a)),11)
            self.assertEqual(len(store.list_objects(owner_b)),8)
            self.assertNotEqual(len(store.export_graph(owner_a)),len(store.export_graph(owner_b)))
            with self.assertRaises(ConcurrentWriteError):
                store.import_records(owner_a,a,expected_revision=0,strict_refs=True,trusted_consent_refs=trusted_consents(a))

    def test_update_requires_explicit_allow_and_creates_version(self):
        records=load_scenario("daily-work")
        owner=records[0]["owner_ref"]
        with tempfile.TemporaryDirectory() as td:
            store=OntologySQLiteStore(Path(td)/"p.sqlite3",self.runtime)
            store.import_records(owner,records,expected_revision=0,strict_refs=True,trusted_consent_refs=trusted_consents(records))
            changed=[dict(x) for x in records]
            changed[0]=json.loads(json.dumps(records[0]))
            changed[0]["payload"]["description"]="经本人修订后的描述"
            with self.assertRaises(ObjectConflictError):
                store.import_records(owner,changed,expected_revision=1,strict_refs=True,trusted_consent_refs=trusted_consents(records))
            result=store.import_records(owner,changed,expected_revision=1,allow_updates=True,strict_refs=True,trusted_consent_refs=trusted_consents(records))
            self.assertEqual(result["updated"],1)
            self.assertEqual(store.revision(owner),2)


    def test_owner_scoped_sparql_query(self):
        records=load_scenario("voice-meeting")
        owner=records[0]["owner_ref"]
        with tempfile.TemporaryDirectory() as td:
            store=OntologySQLiteStore(Path(td)/"p.sqlite3",self.runtime)
            store.import_records(owner,records,strict_refs=True,trusted_consent_refs=trusted_consents(records))
            rows=store.query_sparql(owner,"SELECT ?s WHERE { ?s a <urn:pdks:ontology#Event> . }")
            self.assertEqual(len(rows),1)
            self.assertIn(":event:",rows[0]["s"])


    def test_legacy_namespace_bridge_and_term_coverage(self):
        from rdflib.namespace import OWL
        self.assertIn((URIRef("urn:pdks:ontology:0.1#Event"),OWL.equivalentClass,PDKS.Event),self.runtime.ontology_graph)
        import re
        source=(ROOT/"prototype"/"pdks_ontology_runtime.py").read_text(encoding="utf-8")
        used=set(re.findall(r"PDKS\.([A-Za-z_][A-Za-z0-9_]*)",source))
        defined={str(x).split("#")[-1] for x in self.runtime.ontology_graph.subjects()}
        self.assertFalse(sorted(used-defined))

    def test_jsonld_roundtrip_preserves_graph_size(self):
        records=load_scenario("voice-meeting")
        graph=self.runtime.project_records(records)
        from rdflib.compare import isomorphic
        context=json.loads((self.runtime.ontology_dir/"pdks-jsonld-context-0.2.1.json").read_text(encoding="utf-8"))["@context"]
        encoded=graph.serialize(format="json-ld",context=context,auto_compact=True)
        decoded=Graph().parse(data=encoded,format="json-ld")
        self.assertTrue(isomorphic(decoded,graph))

    def test_ontology_extension_can_share_existing_ads_sqlite_file(self):
        from personal_memory_sqlite import SQLitePersonalMemoryStore
        records=load_scenario("daily-work")
        owner=records[0]["owner_ref"]
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"combined.sqlite3"
            ads_store=SQLitePersonalMemoryStore(db)
            pdks_store=OntologySQLiteStore(db,self.runtime)
            self.assertEqual(pdks_store.integrity_check(),"ok")
            self.assertEqual(pdks_store.revision(owner),0)
            pdks_store.import_records(owner,records,strict_refs=True,trusted_consent_refs=trusted_consents(records))
            self.assertEqual(len(pdks_store.list_objects(owner)),8)


    def test_ontology_governance_report_has_complete_legacy_bridge(self):
        report=build_governance_report(self.runtime)
        self.assertEqual(report["status"],"valid",report)
        self.assertEqual(report["term_coverage"]["runtime_terms_referenced"],98)
        self.assertEqual(report["term_coverage"]["runtime_terms_declared"],98)
        self.assertEqual(report["compatibility"]["bridged_legacy_terms"],71)
        self.assertEqual(report["compatibility"]["breaking_changes"],[])
        self.assertEqual(report["vocabulary_migration"]["missing_bridges"],[])
        self.assertEqual(report["manifest"]["status"],"valid")

    def test_vocabulary_legacy_concepts_have_exact_match_bridges(self):
        report=check_vocabulary_migration(self.runtime.assets_dir/"pdks-core-vocabularies-0.1.ttl",self.runtime.vocabulary_graph)
        self.assertEqual(report["status"],"valid")
        self.assertEqual(report["legacy_concepts"],34)
        self.assertEqual(report["bridged_concepts"],34)

    def test_semantic_diff_detects_missing_legacy_bridge(self):
        baseline=Graph().parse(self.runtime.assets_dir/"pdks-core-ontology-0.1.ttl",format="turtle")
        candidate=Graph()
        for triple in self.runtime.ontology_graph:
            candidate.add(triple)
        candidate.remove((URIRef("urn:pdks:ontology:0.1#Event"),OWL.equivalentClass,PDKS.Event))
        report=compare_ontology_versions(baseline,candidate)
        self.assertEqual(report["status"],"breaking")
        self.assertTrue(any(x["term"]=="urn:pdks:ontology:0.1#Event" for x in report["breaking_changes"]))

    def test_semantic_diff_detects_newly_restrictive_property_domain(self):
        baseline=Graph().parse(self.runtime.assets_dir/"pdks-core-ontology-0.1.ttl",format="turtle")
        candidate=Graph()
        for triple in self.runtime.ontology_graph:
            candidate.add(triple)
        candidate.add((PDKS.ownedBy,RDFS.domain,PDKS.Person))
        report=compare_ontology_versions(baseline,candidate)
        self.assertEqual(report["status"],"breaking")
        self.assertTrue(any(x["kind"]=="domain_constraint_tightened" and x["term"].endswith("#ownedBy") for x in report["breaking_changes"]))

    def test_relationship_attribution_does_not_infer_assertion(self):
        records=load_scenario("voice-meeting")
        relationship=next(x for x in records if x["object_type"]=="relationship")
        graph=self.runtime.project_record(relationship)
        subject=URIRef(relationship["object_id"])
        actor=URIRef(relationship["payload"]["asserted_by_ref"])
        self.assertIn((subject,PDKS.attributedTo,actor),graph)
        self.assertNotIn((subject,PDKS.assertedBy,actor),graph)

    def test_shacl_runtime_status_and_conformance(self):
        records=load_scenario("voice-meeting")
        result=self.runtime.validate_shacl(self.runtime.project_records(records))
        if self.runtime._pyshacl_available():
            self.assertEqual(result["status"],"conforms",result)
            self.assertEqual(result["results_count"],0,result)
        else:
            self.assertEqual(result["status"],"unavailable")

    def test_shacl_rejects_event_without_taxonomy_type_when_available(self):
        if not self.runtime._pyshacl_available():
            self.skipTest("pySHACL is installed in CI; not available in this local environment")
        records=load_scenario("voice-meeting")
        graph=self.runtime.project_records(records)
        event=next(x for x in records if x["object_type"]=="event")
        graph.remove((URIRef(event["object_id"]),PDKS.hasEventType,None))
        result=self.runtime.validate_shacl(graph)
        self.assertEqual(result["status"],"non_conformant",result)
        self.assertGreater(result["results_count"],0)

    def test_ontology_manifest_integrity(self):
        report=verify_ontology_manifest(self.runtime.ontology_dir)
        self.assertEqual(report["status"],"valid",report)
        self.assertEqual(report["files_verified"],8)

    def test_projection_can_be_rebuilt_from_canonical_records(self):
        records=load_scenario("research")
        owner=records[0]["owner_ref"]
        with tempfile.TemporaryDirectory() as td:
            store=OntologySQLiteStore(Path(td)/"p.sqlite3",self.runtime)
            store.import_records(owner,records,expected_revision=0,strict_refs=True,trusted_consent_refs=trusted_consents(records))
            before=len(store.export_graph(owner))
            report=store.rebuild_projection(owner)
            after=len(store.export_graph(owner))
            self.assertEqual(report["status"],"rebuilt")
            self.assertEqual(before,after)
            self.assertEqual(report["records"],10)

if __name__=="__main__":
    unittest.main()

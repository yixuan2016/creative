import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "pdks-setup" / "scripts" / "pdks_setup.py"
spec = importlib.util.spec_from_file_location("pdks_setup_engine", SCRIPT)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class PDKSSetupEngineTests(unittest.TestCase):
    def test_plan_contains_visible_file_vault_and_current_track(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            plan = setup.build_plan(ROOT, base / "install", base / "vault")
            self.assertEqual(plan["pdks_track"], "0.5.2.2")
            self.assertEqual(plan["vault_root"], str((base / "vault").resolve()))
            self.assertIn("Markdown, JSONL, ontology assets", " ".join(plan["actions"]))
            self.assertEqual(len(plan["plan_sha256"]), 64)

    def test_plan_hash_is_deterministic_for_same_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            a = setup.build_plan(ROOT, base / "install", base / "vault")
            b = setup.build_plan(ROOT, base / "install", base / "vault")
            self.assertEqual(a["plan_sha256"], b["plan_sha256"])

    def test_non_empty_unmanaged_vault_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            vault = base / "vault"
            vault.mkdir()
            (vault / "my-notes.md").write_text("user data", encoding="utf-8")
            plan = setup.build_plan(ROOT, base / "install", vault)
            self.assertEqual(plan["vault_root_state"], "non_empty_unmanaged_directory")
            result = setup.doctor(ROOT, base / "install", vault)
            self.assertEqual(result["status"], "blocked")
            self.assertFalse(next(x for x in result["checks"] if x["name"] == "vault_path_available")["ok"])

    def test_existing_pdks_vault_is_reusable(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            vault = base / "vault"
            vault.mkdir()
            (vault / "PDKS-MANIFEST.json").write_text("{}", encoding="utf-8")
            plan = setup.build_plan(ROOT, base / "install", vault)
            self.assertEqual(plan["vault_root_state"], "existing_pdks_vault")
            result = setup.doctor(ROOT, base / "install", vault)
            self.assertTrue(next(x for x in result["checks"] if x["name"] == "vault_path_available")["ok"])


    def test_file_vault_initialization_seeds_ontology_and_safe_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "PDKS-Vault"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT / "runtime")
            result = setup.initialize_file_vault(Path(sys.executable), ROOT, vault, env)
            self.assertTrue((vault / "PDKS-MANIFEST.json").is_file())
            self.assertTrue((vault / ".pdks" / "ontology" / "0.2.1" / "ontology-manifest.json").is_file())
            config = json.loads((vault / ".pdks" / "config" / "runtime.json").read_text(encoding="utf-8"))
            self.assertEqual(config["ontology_version"], "0.2.1")
            self.assertFalse(config["default_capture_enabled"])
            self.assertGreaterEqual(result["ontology_files_added"], 1)

    def test_file_vault_initialization_preserves_existing_user_config_and_ontology(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "PDKS-Vault"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT / "runtime")
            setup.initialize_file_vault(Path(sys.executable), ROOT, vault, env)
            config_path = vault / ".pdks" / "config" / "runtime.json"
            ontology_path = vault / ".pdks" / "ontology" / "0.2.1" / "ontology-manifest.json"
            config_path.write_text('{"user_customized":true}\n', encoding="utf-8")
            ontology_path.write_text('user-edited ontology manifest\n', encoding="utf-8")
            setup.initialize_file_vault(Path(sys.executable), ROOT, vault, env)
            self.assertEqual(json.loads(config_path.read_text(encoding="utf-8")), {"user_customized": True})
            self.assertEqual(ontology_path.read_text(encoding="utf-8"), "user-edited ontology manifest\n")

    def test_install_refuses_wrong_plan_hash_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            with self.assertRaises(PermissionError):
                setup.install(ROOT, base / "install", "wrong", True, base / "vault")
            self.assertFalse((base / "install").exists())

    def test_install_refuses_missing_unencrypted_storage_acknowledgement(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            plan = setup.build_plan(ROOT, base / "install", base / "vault")
            with self.assertRaises(PermissionError):
                setup.install(ROOT, base / "install", plan["plan_sha256"], False, base / "vault")
            self.assertFalse((base / "install").exists())


if __name__ == "__main__":
    unittest.main()

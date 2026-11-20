import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "sync-release.py"
SPEC = importlib.util.spec_from_file_location("sync_release", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class SafePathTests(unittest.TestCase):
    def test_accepts_project_file(self):
        self.assertTrue(MODULE.safe_relative_path("PDKS/docs/guide.md"))
    def test_rejects_parent_traversal(self):
        self.assertFalse(MODULE.safe_relative_path("PDKS/../../outside.txt"))
    def test_rejects_windows_separator(self):
        self.assertFalse(MODULE.safe_relative_path(r"PDKS\\..\\outside.txt"))
    def test_rejects_drive_prefix(self):
        self.assertFalse(MODULE.safe_relative_path("C:/PDKS/file.txt"))
    def test_rejects_non_project_root(self):
        self.assertFalse(MODULE.safe_relative_path("other/file.txt"))
    def test_rejects_credentials(self):
        self.assertFalse(MODULE.safe_relative_path("PDKS/config/.env"))
    def test_rejects_personal_runtime_data(self):
        self.assertFalse(MODULE.safe_relative_path("PDKS/runtime/data/private.json"))
    def test_rejects_build_cache(self):
        self.assertFalse(MODULE.safe_relative_path("PDKS/agent-native/node_modules/pkg/index.js"))

if __name__ == "__main__":
    unittest.main()

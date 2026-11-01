import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class BuildInterfaceAcceptanceTests(unittest.TestCase):
    def run_make(self, target: str) -> str:
        result = subprocess.run(
            ["make", "--no-print-directory", target],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_help_exposes_developer_and_ci_commands(self) -> None:
        output = self.run_make("help")
        for command in ("bootstrap", "validate", "test-unit", "test-integration", "test-acceptance", "ci"):
            self.assertIn(f"make {command}", output)

    def test_component_listing_is_human_readable(self) -> None:
        output = self.run_make("components")
        self.assertIn("apps/world", output)
        self.assertIn("services/agent", output)
        self.assertIn("packages/contracts", output)
        self.assertIn("tools/evaluation", output)

    def test_browser_prototype_is_archived(self) -> None:
        archived = ROOT / "archive" / "apps" / "browser-prototype"
        self.assertTrue(archived.is_dir(), "browser prototype must be archived under archive/apps/")
        self.assertTrue((archived / "README.md").is_file(), "archived prototype must have a README")

    def test_browser_prototype_not_in_active_apps(self) -> None:
        active = ROOT / "apps" / "browser-prototype"
        self.assertFalse(active.exists(), "browser prototype must not remain under apps/")

    def test_browser_prototype_not_in_build_contract(self) -> None:
        components = (ROOT / "build" / "components.mk").read_text(encoding="utf-8")
        self.assertNotIn("browser-prototype", components)

    def test_contributing_describes_godot_as_only_active_runtime(self) -> None:
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertIn("Godot 4 with Jolt is the supported world runtime", contributing)
        # No active run instructions for the prototype
        self.assertNotIn("cd apps/browser-prototype", contributing)
        self.assertNotIn("npm install", contributing)
        self.assertNotIn("npm run dev", contributing)
        self.assertNotIn("npm run build", contributing)


if __name__ == "__main__":
    unittest.main()

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


if __name__ == "__main__":
    unittest.main()

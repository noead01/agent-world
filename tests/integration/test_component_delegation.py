import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ComponentDelegationTests(unittest.TestCase):
    def test_root_validation_delegates_to_every_component(self) -> None:
        result = subprocess.run(
            ["make", "--no-print-directory", "validate"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for component in ("apps/world", "services/agent", "packages/contracts", "tools/evaluation"):
            self.assertIn(f"==> {component}: validate", result.stdout)


if __name__ == "__main__":
    unittest.main()

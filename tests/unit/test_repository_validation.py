import tempfile
import unittest
from pathlib import Path

from tools.repository.validate import (
    ROOT,
    metadata,
    registered_components,
    validate_component,
    validate_repository,
)


class RepositoryValidationTests(unittest.TestCase):
    def test_registry_contains_expected_component_boundaries(self) -> None:
        paths = {str(path.relative_to(ROOT)) for path in registered_components()}
        self.assertEqual(
            paths,
            {"apps/world", "services/agent", "packages/contracts", "tools/evaluation"},
        )

    def test_component_metadata_parser(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            component = Path(directory)
            (component / "component.mk").write_text(
                "COMPONENT_NAME := example\nCOMPONENT_KIND := service\n",
                encoding="utf-8",
            )
            self.assertEqual(
                metadata(component),
                {"COMPONENT_NAME": "example", "COMPONENT_KIND": "service"},
            )

    def test_repository_contract_is_valid(self) -> None:
        self.assertEqual(validate_repository(), [])

    def test_invalid_component_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="invalid-component-", dir=ROOT) as directory:
            component = Path(directory)
            (component / "README.md").write_text("# Invalid\n", encoding="utf-8")
            (component / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
            (component / "component.mk").write_text(
                "COMPONENT_NAME := wrong-name\nCOMPONENT_KIND := mystery\n",
                encoding="utf-8",
            )
            errors = validate_component(component)
        self.assertTrue(any("missing COMPONENT_RUNTIME" in error for error in errors))
        self.assertTrue(any("invalid COMPONENT_KIND" in error for error in errors))
        self.assertTrue(any("shared component contract" in error for error in errors))
        self.assertTrue(any("missing tests/unit/README.md" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

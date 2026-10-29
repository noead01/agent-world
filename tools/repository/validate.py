#!/usr/bin/env python3
"""Validate Agent World's monorepo structure without third-party dependencies."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "build" / "components.mk"
REQUIRED_METADATA = ("COMPONENT_NAME", "COMPONENT_KIND", "COMPONENT_RUNTIME")
ALLOWED_KINDS = {"application", "service", "package", "tool"}
TEST_LAYERS = ("unit", "integration", "acceptance")


def registered_components(registry: Path = REGISTRY) -> list[Path]:
    text = registry.read_text(encoding="utf-8")
    paths = re.findall(r"^\s*(apps|services|packages|tools)/([a-z0-9][a-z0-9-]*)\s*\\?\s*$", text, re.MULTILINE)
    return [ROOT / parent / name for parent, name in paths]


def metadata(component: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in (component / "component.mk").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([A-Z_]+)\s*:=\s*(\S+)", line)
        if match:
            result[match.group(1)] = match.group(2)
    return result


def validate_component(component: Path) -> list[str]:
    errors: list[str] = []
    relative = component.relative_to(ROOT)
    for filename in ("Makefile", "README.md", "component.mk"):
        if not (component / filename).is_file():
            errors.append(f"{relative}: missing {filename}")
    if errors:
        return errors

    values = metadata(component)
    for key in REQUIRED_METADATA:
        if not values.get(key):
            errors.append(f"{relative}/component.mk: missing {key}")
    if values.get("COMPONENT_KIND") not in ALLOWED_KINDS:
        errors.append(f"{relative}/component.mk: invalid COMPONENT_KIND")
    if values.get("COMPONENT_NAME") != component.name:
        errors.append(f"{relative}/component.mk: COMPONENT_NAME must match directory name")

    makefile = (component / "Makefile").read_text(encoding="utf-8")
    if "build/component.mk" not in makefile:
        errors.append(f"{relative}/Makefile: must include the shared component contract")
    for layer in TEST_LAYERS:
        if not (component / "tests" / layer / "README.md").is_file():
            errors.append(f"{relative}: missing tests/{layer}/README.md")
    return errors


def validate_repository() -> list[str]:
    components = registered_components()
    errors: list[str] = []
    relative = [str(path.relative_to(ROOT)) for path in components]
    if not components:
        errors.append("build/components.mk: no components registered")
    if len(relative) != len(set(relative)):
        errors.append("build/components.mk: duplicate component registration")
    for component in components:
        if not component.is_dir():
            errors.append(f"{component.relative_to(ROOT)}: registered directory does not exist")
        else:
            errors.extend(validate_component(component))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--component", type=Path, help="validate one registered component")
    args = parser.parse_args()
    if args.component:
        component = args.component.resolve()
        errors = validate_component(component)
        label = component.relative_to(ROOT)
    else:
        errors = validate_repository()
        label = "repository"
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"validated {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""The declared dependency floor must support the APIs the service imports."""
import re
import tomllib
from pathlib import Path

COMPONENT_DIR = Path(__file__).resolve().parents[2]
PYPROJECT = COMPONENT_DIR / "pyproject.toml"
AGENT_SERVICE = COMPONENT_DIR / "src" / "agent_service.py"


def _dependency_floor(name: str) -> int:
    with open(PYPROJECT, "rb") as f:
        project = tomllib.load(f)
    for requirement in project["project"]["dependencies"]:
        package, _, specifier = requirement.partition(">=")
        if package.strip().lower() != name:
            continue
        match = re.match(r"\s*(\d+)", specifier)
        assert match, f"{name} requirement has no lower bound: {requirement}"
        return int(match.group(1))
    raise AssertionError(f"{name} is not declared in pyproject.toml")


def test_websockets_floor_supports_the_imported_asyncio_api():
    """`websockets.asyncio.server` and ServerConnection arrived in websockets 13.

    A lower bound below 13 permits an installation where the service cannot even
    import, so the declared floor must reflect the imported namespace.
    """
    source = AGENT_SERVICE.read_text()
    assert "from websockets.asyncio.server import" in source
    assert "ServerConnection" in source

    floor = _dependency_floor("websockets")

    assert floor >= 13, (
        "agent_service.py imports websockets.asyncio.server, which requires "
        f"websockets 13+, but pyproject.toml allows websockets {floor}.x"
    )

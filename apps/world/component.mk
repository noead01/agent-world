COMPONENT_NAME := world
COMPONENT_KIND := application
COMPONENT_RUNTIME := godot-4
COMPONENT_TEST_UNIT := uv run --with pytest python -m pytest tests/unit
# Acceptance tests import the contracts package from the source tree, which
# needs jsonschema in the isolated uv environment.
COMPONENT_TEST_ACCEPTANCE := uv run --with pytest --with websockets --with jsonschema python -m pytest tests/acceptance

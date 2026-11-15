COMPONENT_NAME := contracts
COMPONENT_KIND := package
COMPONENT_RUNTIME := schema
COMPONENT_BOOTSTRAP := python3 -m pip install --break-system-packages -e .
COMPONENT_TEST_UNIT := uv run --with pytest python -m pytest tests/unit

COMPONENT_NAME := agent
COMPONENT_KIND := service
COMPONENT_RUNTIME := python
COMPONENT_BOOTSTRAP := python3 -m pip install --break-system-packages -e .
COMPONENT_TEST_UNIT := uv run --with pytest python -m pytest tests/unit

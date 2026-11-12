ifndef COMPONENT_NAME
$(error COMPONENT_NAME must be set before including build/component.mk)
endif

COMPONENT_ROOT := $(abspath $(CURDIR))
REPOSITORY_ROOT := $(abspath $(COMPONENT_ROOT)/../..)

.PHONY: bootstrap build format format-check lint validate \
	test-unit test-integration test-acceptance clean

bootstrap:
ifdef COMPONENT_BOOTSTRAP
	@$(COMPONENT_BOOTSTRAP)
else
	@printf '%s: %s has no implementation yet\n' '$(COMPONENT_NAME)' '$@'
endif

build format format-check lint clean:
	@printf '%s: %s has no implementation yet\n' '$(COMPONENT_NAME)' '$@'

validate:
	@python3 '$(REPOSITORY_ROOT)/tools/repository/validate.py' --component '$(COMPONENT_ROOT)'

test-unit:
ifdef COMPONENT_TEST_UNIT
	@$(COMPONENT_TEST_UNIT)
else
	@printf '%s: %s has no testable implementation yet\n' '$(COMPONENT_NAME)' '$@'
endif

test-integration test-acceptance:
	@printf '%s: %s has no testable implementation yet\n' '$(COMPONENT_NAME)' '$@'

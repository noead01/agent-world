SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

include build/components.mk

.PHONY: help components bootstrap build format format-check lint validate \
	test-unit test-integration test-acceptance test ci clean run-agent-service

help: ## Show the supported repository commands.
	@printf '%s\n' \
		'Agent World repository commands' \
		'' \
		'  make components       List registered monorepo components' \
		'  make bootstrap        Install component development dependencies' \
		'  make build            Build every implemented component' \
		'  make format           Apply component formatters' \
		'  make format-check     Check formatting without modifying files' \
		'  make lint             Run static analysis' \
		'  make validate         Validate repository and component contracts' \
		'  make test-unit        Run isolated unit tests' \
		'  make test-integration Run cross-component integration tests' \
		'  make test-acceptance  Run black-box acceptance tests' \
		'  make test             Run all test layers' \
		'  make run-agent-service Start the external agent service' \
		'  make ci               Run every non-mutating CI check' \
		'  make clean            Remove generated component output'

components: ## List registered components.
	@for component in $(COMPONENTS); do \
		kind="$$(sed -n 's/^COMPONENT_KIND[[:space:]]*:=[[:space:]]*//p' "$$component/component.mk")"; \
		printf '%-24s %s\n' "$$component" "$$kind"; \
	done

run-agent-service: ## Start the external agent service.
	@$(MAKE) --no-print-directory -C services/agent run-agent-service

bootstrap build format format-check lint clean:
	@set -e; for component in $(COMPONENTS); do \
		printf '\n==> %s: $@\n' "$$component"; \
		$(MAKE) --no-print-directory -C "$$component" $@; \
	done

validate:
	@python3 tools/repository/validate.py
	@set -e; for component in $(COMPONENTS); do \
		printf '\n==> %s: validate\n' "$$component"; \
		$(MAKE) --no-print-directory -C "$$component" validate; \
	done

test-unit:
	@python3 -m unittest discover -s tests/unit -p 'test_*.py' -v
	@set -e; for component in $(COMPONENTS); do \
		printf '\n==> %s: test-unit\n' "$$component"; \
		$(MAKE) --no-print-directory -C "$$component" test-unit; \
	done

test-integration:
	@python3 -m unittest discover -s tests/integration -p 'test_*.py' -v
	@set -e; for component in $(COMPONENTS); do \
		printf '\n==> %s: test-integration\n' "$$component"; \
		$(MAKE) --no-print-directory -C "$$component" test-integration; \
	done

test-acceptance:
	@python3 -m unittest discover -s tests/acceptance -p 'test_*.py' -v
	@set -e; for component in $(COMPONENTS); do \
		printf '\n==> %s: test-acceptance\n' "$$component"; \
		$(MAKE) --no-print-directory -C "$$component" test-acceptance; \
	done

test: test-unit test-integration test-acceptance

ci: format-check lint validate test build

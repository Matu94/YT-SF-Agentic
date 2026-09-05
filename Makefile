# Snowflake Deploy — Local development
# Run from repo root: make dry-run | make deploy
#
# Prerequisites: pip install snowflake-connector-python, source .env

ifeq ($(OS),Windows_NT)
    PYTHON = python
else
    PYTHON = python3
endif
DEPLOY = $(PYTHON) .deployment/deploy.py

.PHONY: help detect-changes detect-all dry-run deploy deploy-log seed

help:
	@echo "Snowflake Deploy (local)"
	@echo ""
	@echo "  make detect-changes  List changed SQL files (diff vs dev or last deploy)"
	@echo "  make detect-all      List ALL .sql files (for log-based deploy)"
	@echo "  make dry-run         Preview what would deploy (no execution)"
	@echo "  make deploy          Deploy changed files (diff-based, SSO)"
	@echo "  make deploy-log      Deploy using log table (all files not in log)"
	@echo "  make seed            Register existing files to Deployment History without executing"
	@echo ""
	@echo "For dry-run/deploy, ensure .env is loaded. Local uses SSO (browser)."

detect-changes:
	@$(DEPLOY) detect-changes --mode diff

detect-all:
	@$(DEPLOY) detect-changes --mode log

dry-run: detect-changes
	@set -a; [ -f .env ] && . ./.env; set +a; \
	$(DEPLOY) deploy --dry-run

seed: detect-all
	@set -a; [ -f .env ] && . ./.env; set +a; \
	$(DEPLOY) seed

deploy: detect-changes
	@set -a; [ -f .env ] && . ./.env; set +a; \
	$(DEPLOY) deploy

deploy-log: detect-all
	@set -a; [ -f .env ] && . ./.env; set +a; \
	$(DEPLOY) deploy

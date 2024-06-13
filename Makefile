.PHONY: fmt local-run
.ONESHELL: local-run
default: local-run
CONFIG_PATH ?= ../config.yaml
fmt:
	@black src/
local-run:
	@cd src && CONFIG_PATH=${CONFIG_PATH} poetry run uvicorn --reload main:app

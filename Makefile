.PHONY: all help submodules build build-all build-context7 build-fetch build-lean build-ponytail build-graphify build-anytype build-codegraph config check clean

SHELL := /usr/bin/env bash

all: help

help:
	@echo "agents-arwaky - Developer Commands"
	@echo ""
	@echo "Submodules:"
	@echo "  make submodules        - Initialize and update submodules"
	@echo ""
	@echo "Building Tools:"
	@echo "  make build-all         - Build all MCP tools"
	@echo "  make build-context7    - Build Context7 MCP"
	@echo "  make build-fetch       - Build Fetch-MCP"
	@echo "  make build-lean        - Build Lean-Ctx"
	@echo "  make build-ponytail    - Build Ponytail MCP"
	@echo "  make build-graphify    - Build/verify Graphify"
	@echo "  make build-anytype     - Build Anytype-MCP"
	@echo "  make build-codegraph   - Build CodeGraph MCP"
	@echo ""
	@echo "Configuration & Quality:"
	@echo "  make config            - Generate unified mcp_servers.generated.json"
	@echo "  make check             - Run verification, shellcheck and JSON validation"
	@echo "  make clean             - Clean build outputs and dist directories"
	@echo ""

submodules:
	git submodule update --init

build-all: submodules
	./tools/build-all.sh

build-context7:
	git submodule update --init vendor/context7
	./tools/context7/install.sh

build-fetch:
	git submodule update --init vendor/fetch-mcp
	./tools/fetch-mcp/install.sh

build-lean:
	git submodule update --init vendor/lean-ctx
	./tools/lean-ctx/install.sh

build-ponytail:
	git submodule update --init vendor/ponytail
	./tools/ponytail/install.sh

build-graphify:
	git submodule update --init vendor/graphify
	./tools/graphify/build.sh

build-anytype:
	git submodule update --init vendor/anytype-mcp
	./tools/anytype-mcp/install.sh

build-codegraph:
	git submodule update --init vendor/codegraph
	./tools/codegraph/install.sh

config:
	./tools/generate-mcp-config.sh

check:
	./tools/verify.sh

clean:
	rm -rf tools/*/dist tools/ponytail/hooks tools/ponytail/skills tools/ponytail/package.json tools/context7/package.json mcp_servers.generated.json

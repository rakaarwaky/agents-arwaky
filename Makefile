.PHONY: all help submodules build-all build-context7 build-fetch build-lean build-ponytail build-graphify build-anytype build-codegraph config check clean

SHELL := /usr/bin/env bash

all: help

help:
	@echo "agents-arwaky - Developer Commands"
	@echo ""
	@echo "Submodules:"
	@echo "  make submodules        - Initialize and update vendor submodules"
	@echo ""
	@echo "Install Tools to Linux XDG (~/.local/share/<tool> and ~/.local/bin/<tool>):"
	@echo "  make build-all         - Install all vendor MCP tools to XDG paths"
	@echo "  make build-context7    - Install Context7 (context7-mcp)"
	@echo "  make build-fetch       - Install Fetch-MCP (fetch-mcp)"
	@echo "  make build-lean        - Install Lean-Ctx (lean-ctx)"
	@echo "  make build-ponytail    - Install Ponytail (ponytail-mcp)"
	@echo "  make build-graphify    - Install Graphify (graphify-mcp)"
	@echo "  make build-anytype     - Install Anytype-MCP (anytype-mcp)"
	@echo "  make build-codegraph   - Install CodeGraph (codegraph-mcp)"
	@echo ""
	@echo "Configuration & Quality:"
	@echo "  make config            - Generate unified XDG MCP client configuration"
	@echo "  make check             - Run verification, shellcheck, and JSON validation"
	@echo "  make clean             - Clean local build artifacts"
	@echo ""

submodules:
	git submodule update --init vendor/

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
	rm -rf tools/*/dist mcp_servers.generated.json

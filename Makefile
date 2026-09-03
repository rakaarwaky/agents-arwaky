.PHONY: all help submodules build-all build-context7 build-fetch build-lean build-ponytail build-graphify build-anytype build-codegraph config check clean distrobox-check distrobox-create distrobox-enter distrobox-build distrobox-export distrobox-destroy

SHELL := /usr/bin/env bash

all: help

help:
	@echo "agents-arwaky - Developer Commands"
	@echo ""
	@echo "Distrobox + Podman (Sandbox Environment):"
	@echo "  make distrobox-check   - Check if podman and distrobox are installed on host"
	@echo "  make distrobox-create  - Create/assemble agents-env container"
	@echo "  make distrobox-enter   - Enter the interactive sandbox container"
	@echo "  make distrobox-build   - Build all tools inside the Distrobox container"
	@echo "  make distrobox-export  - Export all tool binaries to host ~/.local/bin"
	@echo "  make distrobox-destroy - Destroy sandbox container (keeps all persistent data)"
	@echo ""
	@echo "Submodules:"
	@echo "  make submodules        - Initialize and update vendor submodules"
	@echo ""
	@echo "Install Tools to Linux XDG (~/.local/share/<vendor> and ~/.local/bin/<tool>):"
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

# Distrobox commands
distrobox-check:
	@./tools/distrobox/setup-host.sh

distrobox-create:
	@distrobox assemble create --file distrobox.ini

distrobox-enter:
	@distrobox enter agents-env

distrobox-build:
	@distrobox enter agents-env -- bash -c "cd $(CURDIR) && make build-all"

distrobox-export:
	@distrobox enter agents-env -- bash -c "distrobox-export --bin /home/raka/.local/bin/context7-mcp --export-path /home/raka/.local/bin && distrobox-export --bin /home/raka/.local/bin/fetch-mcp --export-path /home/raka/.local/bin && distrobox-export --bin /home/raka/.local/bin/lean-ctx --export-path /home/raka/.local/bin && distrobox-export --bin /home/raka/.local/bin/ponytail-mcp --export-path /home/raka/.local/bin && distrobox-export --bin /home/raka/.local/bin/graphify --export-path /home/raka/.local/bin && distrobox-export --bin /home/raka/.local/bin/anytype-mcp --export-path /home/raka/.local/bin && distrobox-export --bin /home/raka/.local/bin/codegraph-mcp --export-path /home/raka/.local/bin"

distrobox-destroy:
	@distrobox rm -f agents-env

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

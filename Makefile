.PHONY: default all help install build setup enter shell config check clean clean-host distclean destroy submodules \
        distrobox-check distrobox-create distrobox-build distrobox-export distrobox-enter distrobox-destroy \
        host-build host-build-all host-build-context7 host-build-fetch host-build-lean host-build-lean-ctx host-build-ponytail host-build-anytype host-build-codegraph host-build-9router \
        host-build-lint host-build-qwen-web host-build-vision host-build-blender

SHELL := /usr/bin/env bash

# Distrobox First-Class: default target installs via sandbox container
default: install

all: install

help:
	@echo "agents-arwaky - Developer Commands (Distrobox First-Class)"
	@echo ""
	@echo "Primary Workflow (Distrobox Container - Default):"
	@echo "  make setup             - Install host prerequisites (podman & distrobox)"
	@echo "  make install           - Complete setup: submodules -> container -> build -> export -> config"
	@echo "  make build             - Rebuild all tools inside Distrobox and re-export binaries"
	@echo "  make enter / shell     - Open interactive shell inside agents-env sandbox container"
	@echo "  make config            - Generate unified XDG MCP client configuration"
	@echo "  make check             - Run repository verification and validation"
	@echo "  make clean             - Clean local build artifacts"
	@echo "  make destroy           - Destroy the sandbox container (preserves persistent data)"
	@echo ""
	@echo "Secondary / Fallback Workflow (Bare-Metal Host):"
	@echo "  make host-build        - Install all vendor tools directly on host OS without container"
	@echo "  make host-build-<tool> - Build a specific tool directly on host (e.g. host-build-context7)"
	@echo ""

# Distrobox First-Class Pipeline
setup:
	@./tools/distrobox/setup-host.sh --install

distrobox-check:
	@./tools/distrobox/setup-host.sh

distrobox-create:
	@if ! distrobox list 2>/dev/null | grep -q "agents-env"; then \
		echo ">>> Creating Distrobox container 'agents-env'..."; \
		distrobox assemble create --file distrobox.ini; \
	else \
		echo ">>> Container 'agents-env' already exists."; \
	fi
	@echo ">>> Ensuring container environment is initialized..."
	@distrobox enter agents-env -- bash $(CURDIR)/tools/distrobox/init-container.sh

distrobox-enter enter shell:
	@distrobox enter agents-env

distrobox-build: submodules
	@echo ">>> Building tools inside Distrobox container 'agents-env'..."
	@distrobox enter agents-env -- bash -c "cd $(CURDIR) && XDG_BIN_HOME=\$$HOME/.local/share/agents-arwaky/internal-bin ./tools/build/build-all.sh"

distrobox-export:
	@./tools/distrobox/export-bins.sh

distrobox-destroy destroy:
	@distrobox rm -f agents-env

build: distrobox-build distrobox-export

install: submodules distrobox-check distrobox-create distrobox-build distrobox-export config
	@echo ""
	@echo "============================================================"
	@echo " agents-arwaky Distrobox First-Class installation complete! "
	@echo " Binaries exported to $(HOME)/.local/bin"
	@echo " MCP configuration generated at mcp_servers.generated.json"
	@echo "============================================================"

submodules:
	git submodule update --init vendor/

config:
	./tools/mcp/generate-config.sh

check:
	./tools/ci/verify.sh

clean:
	rm -rf tools/*/dist mcp_servers.generated.json

clean-host:
	@echo ">>> Cleaning host ~/.local/bin and ~/.local/share tool installations..."
	rm -f $(HOME)/.local/bin/{context7-mcp,fetch-mcp,lean-ctx,ponytail-mcp,anytype-mcp,codegraph-mcp,9router,agents-arwaky,aa,arwaky,lint-arwaky-cli,lac}
	rm -rf $(HOME)/.local/share/{context7,fetch-mcp,lean-ctx,ponytail,anytype-mcp,codegraph,9router,agents-arwaky}
	@echo ">>> Host tool binaries and data directories cleaned."

distclean: clean clean-host
	git submodule foreach --recursive 'git clean -fd && git checkout .'

# Host / Bare-Metal Fallback Targets
host-build host-build-all: submodules
	./tools/build/build-all.sh

host-build-context7:
	git submodule update --init vendor/context7
	./tools/context7/install.sh

host-build-fetch:
	git submodule update --init vendor/fetch-mcp
	./tools/fetch-mcp/install.sh

host-build-lean host-build-lean-ctx:
	git submodule update --init vendor/lean-ctx
	./tools/lean-ctx/install.sh

host-build-ponytail:
	git submodule update --init vendor/ponytail
	./tools/ponytail/install.sh

host-build-anytype:
	git submodule update --init vendor/anytype-mcp
	./tools/anytype-mcp/install.sh

host-build-codegraph:
	git submodule update --init vendor/codegraph
	./tools/codegraph/install.sh

host-build-9router:
	git submodule update --init vendor/9router
	./tools/9router/install.sh

# Internal In-House Agent Targets
host-build-lint:
	git submodule update --init internal/lint-arwaky
	./tools/lint/install.sh

host-build-qwen-web:
	git submodule update --init internal/qwen-web-arwaky
	./internal/qwen-web-arwaky/scripts/install.sh

host-build-vision:
	git submodule update --init internal/vision-arwaky
	./internal/vision-arwaky/scripts/install.local.sh

host-build-blender:
	git submodule update --init internal/blender-arwaky
	./internal/blender-arwaky/scripts/install/install.sh



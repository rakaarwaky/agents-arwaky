.PHONY: default all help install build setup enter shell config check clean clean-host distclean destroy submodules \
        distrobox-check distrobox-create distrobox-build distrobox-export distrobox-enter distrobox-destroy \
        host-build host-build-all

SHELL := /usr/bin/env bash

# Distrobox First-Class: default target installs via sandbox container
default: install

all: install

help:
	@echo "agents-arwaky - Developer Commands (Two Installation Paradigms Only)"
	@echo ""
	@echo "1. Distrobox Mode (Sandboxed / Default - Zero Host Contamination):"
	@echo "  make install             - Install full ecosystem via Distrobox sandbox container"
	@echo "  make install-<tool>      - Install a specific tool via Distrobox sandbox container"
	@echo "  make build               - Rebuild all tools inside Distrobox and re-export binaries"
	@echo "  make enter / shell       - Open interactive shell inside agents-env container"
	@echo ""
	@echo "2. Host Mode (Bare-Metal Fallback):"
	@echo "  make host-build          - Install all tools directly on host OS without container"
	@echo "  make host-build-<tool>   - Install a specific tool directly on host (e.g. make host-build-fetch)"
	@echo ""
	@echo "Lifecycle & Diagnostics:"
	@echo "  make setup               - Check / install host prerequisites (podman & distrobox)"
	@echo "  make check               - Run repository verification and quality gates"
	@echo "  make clean               - Clean local build artifacts"
	@echo "  make clean-host          - Clean host binaries and share directories"
	@echo "  make destroy             - Destroy the sandbox container (preserves persistent data)"
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

# ==============================================================================
# 1. Distrobox First-Class Mode (Default & Recommended)
# ==============================================================================
install: submodules distrobox-check distrobox-create distrobox-build distrobox-export config
	@echo ""
	@echo "============================================================"
	@echo " agents-arwaky Distrobox First-Class installation complete! "
	@echo " Binaries exported to $(HOME)/.local/bin"
	@echo " MCP configuration generated at mcp_servers.generated.json"
	@echo "============================================================"

# Single-tool installation via Distrobox (e.g. make install-fetch or make distrobox-build-fetch)
install-% distrobox-build-%: distrobox-check distrobox-create
	@echo ">>> Building $* inside Distrobox container 'agents-env'..."
	@distrobox enter agents-env -- bash -c "cd $(CURDIR) && XDG_BIN_HOME=\$$HOME/.local/share/agents-arwaky/internal-bin $(CURDIR)/tools/build/build-tool.sh $*"
	@$(CURDIR)/tools/distrobox/export-bins.sh $*

submodules:
	git submodule update --init vendor/ internal/

config:
	./tools/mcp/generate-config.sh

check:
	./tools/ci/verify.sh

clean:
	rm -rf tools/*/dist mcp_servers.generated.json

clean-host:
	@echo ">>> Cleaning host ~/.local/bin and ~/.local/share tool installations..."
	rm -f $(HOME)/.local/bin/{context7-mcp,fetch-mcp,lean-ctx,ponytail-mcp,anytype-mcp,codegraph-mcp,9router,agents-arwaky,aa,arwaky,lint-arwaky,la,lint-arwaky-cli,lac,vision-arwaky,va,vision-arwaky-mcp,qwen-web-arwaky,qwa,qwc,qwen-web-mcp,blender-arwaky,ba,blender-mcp}
	rm -rf $(HOME)/.local/share/{context7,fetch-mcp,lean-ctx,ponytail,anytype-mcp,codegraph,9router,agents-arwaky,vision-arwaky,qwen-web,blender-arwaky}
	@echo ">>> Host tool binaries and data directories cleaned."

distclean: clean clean-host
	git submodule foreach --recursive 'git clean -fd && git checkout .'

# ==============================================================================
# 2. Host Bare-Metal Mode (Fallback)
# ==============================================================================
host-build host-build-all: submodules
	./tools/build/build-all.sh

# Single-tool installation directly on Host (e.g. make host-build-fetch)
host-build-%:
	@$(CURDIR)/tools/build/build-tool.sh $*




"""Tests for the command catalog taxonomy module."""
import pytest
from taxonomy.blender_command_vo import COMMAND_CATALOG, list_actions


class TestCommandCatalog:
    """Tests for COMMAND_CATALOG data integrity."""

    REQUIRED_FIELDS = {"description", "capability", "parameters", "domain", "returns"}

    def test_catalog_is_not_empty(self):
        """COMMAND_CATALOG must contain at least one entry."""
        assert len(COMMAND_CATALOG) > 0

    def test_all_actions_have_required_fields(self):
        """Every catalog entry must have all required fields."""
        for name, spec in COMMAND_CATALOG.items():
            missing = self.REQUIRED_FIELDS - set(spec.keys())
            assert not missing, f"Action '{name}' missing fields: {missing}"

    def test_all_actions_have_valid_domain(self):
        """Every catalog entry must have a known domain."""
        valid_domains = {"scene", "asset", "generation", "viewport", "infrastructure", "object", "render", "io"}
        for name, spec in COMMAND_CATALOG.items():
            domain = spec.get("domain", "")
            assert domain in valid_domains, (
                f"Action '{name}' has unknown domain '{domain}'. "
                f"Valid: {valid_domains}"
            )

    def test_all_actions_have_valid_capability_format(self):
        """capability field must follow 'Protocol.method' format."""
        for name, spec in COMMAND_CATALOG.items():
            capability = spec.get("capability", "")
            assert "." in capability, (
                f"Action '{name}' capability '{capability}' missing '.' separator"
            )
            parts = capability.split(".")
            assert len(parts) == 2, (
                f"Action '{name}' capability '{capability}' must have exactly one '.'"
            )
            assert parts[0], f"Action '{name}' has empty protocol name"
            assert parts[1], f"Action '{name}' has empty method name"

    def test_no_duplicate_action_names(self):
        """Action names must be unique."""
        assert len(COMMAND_CATALOG) == len(set(COMMAND_CATALOG.keys()))

    def test_parameters_is_dict(self):
        """parameters field must be a dict."""
        for name, spec in COMMAND_CATALOG.items():
            params = spec.get("parameters", {})
            assert isinstance(params, dict), (
                f"Action '{name}' parameters must be a dict, got {type(params)}"
            )

    def test_list_actions_returns_all(self):
        """list_actions() must return all action names."""
        actions = list_actions()
        assert len(actions) == len(COMMAND_CATALOG)
        assert set(actions) == set(COMMAND_CATALOG.keys())


class TestCommandCatalogDomains:
    """Tests that each known domain has at least one action."""

    def test_every_domain_has_at_least_one_action(self):
        """Each domain found in the catalog must have at least one action."""
        from taxonomy.blender_command_vo import COMMAND_CATALOG
        actual_domains = {}
        for name, spec in COMMAND_CATALOG.items():
            d = spec.get("domain", "unknown")
            actual_domains.setdefault(d, []).append(name)
        for domain, actions in actual_domains.items():
            assert len(actions) >= 1, (
                f"Domain '{domain}' has 0 actions"
            )

    def test_knows_actual_domains(self):
        """Document the actual domains present in the catalog."""
        from taxonomy.blender_command_vo import COMMAND_CATALOG
        actual_domains = {spec.get("domain", "") for spec in COMMAND_CATALOG.values()}
        expected_domains = {"scene", "asset", "generation", "viewport", "infrastructure", "object", "render", "io"}
        assert actual_domains == expected_domains, (
            f"Domains mismatch. Got {actual_domains}, expected {expected_domains}"
        )


class TestCommandCatalogDescriptions:
    """Tests for description quality."""

    def test_all_descriptions_are_strings(self):
        for name, spec in COMMAND_CATALOG.items():
            desc = spec.get("description", "")
            assert isinstance(desc, str), (
                f"Action '{name}' description must be a string"
            )
            assert len(desc) >= 5, (
                f"Action '{name}' description too short: '{desc}'"
            )

    def test_all_returns_are_strings(self):
        for name, spec in COMMAND_CATALOG.items():
            returns = spec.get("returns", "")
            assert isinstance(returns, str), (
                f"Action '{name}' returns must be a string"
            )

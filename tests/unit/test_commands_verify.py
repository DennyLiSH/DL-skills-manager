"""Tests for verify command - TBD."""

from __future__ import annotations

import pytest


class TestVerifyCommand:
    """Tests for verify command - skipped since command is TBD."""

    @pytest.mark.skip(reason="verify command is TBD")
    def test_verify_promotes_dev_to_stable(self) -> None:
        """Test promoting a dev version to stable."""
        pass

    @pytest.mark.skip(reason="verify command is TBD")
    def test_verify_nonexistent_skill(self) -> None:
        """Test verifying a skill that doesn't exist."""
        pass

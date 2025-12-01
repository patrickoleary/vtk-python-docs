"""Unit tests for roles module."""

from vtk_python_docs.extract.roles import (
    ROLE_DESCRIPTIONS,
    ROLE_LABELS,
    VISIBILITY_DESCRIPTIONS,
    VISIBILITY_LABELS,
)


class TestRoleLabels:
    """Tests for role labels and descriptions."""

    def test_role_labels_not_empty(self):
        """Test that role labels list is not empty."""
        assert len(ROLE_LABELS) > 0

    def test_role_labels_are_strings(self):
        """Test that all role labels are strings."""
        for label in ROLE_LABELS:
            assert isinstance(label, str)

    def test_role_labels_are_snake_case(self):
        """Test that role labels use snake_case."""
        for label in ROLE_LABELS:
            assert label == label.lower()
            assert " " not in label

    def test_role_descriptions_match_labels(self):
        """Test that every label has a description."""
        assert set(ROLE_LABELS) == set(ROLE_DESCRIPTIONS.keys())

    def test_role_descriptions_are_strings(self):
        """Test that all descriptions are non-empty strings."""
        for label, desc in ROLE_DESCRIPTIONS.items():
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestVisibilityLabels:
    """Tests for visibility labels and descriptions."""

    def test_visibility_labels_not_empty(self):
        """Test that visibility labels list is not empty."""
        assert len(VISIBILITY_LABELS) > 0

    def test_visibility_labels_count(self):
        """Test that there are exactly 5 visibility levels."""
        assert len(VISIBILITY_LABELS) == 5

    def test_visibility_labels_are_strings(self):
        """Test that all visibility labels are strings."""
        for label in VISIBILITY_LABELS:
            assert isinstance(label, str)

    def test_visibility_descriptions_match_labels(self):
        """Test that every label has a description."""
        assert set(VISIBILITY_LABELS) == set(VISIBILITY_DESCRIPTIONS.keys())

    def test_visibility_descriptions_are_strings(self):
        """Test that all descriptions are non-empty strings."""
        for label, desc in VISIBILITY_DESCRIPTIONS.items():
            assert isinstance(desc, str)
            assert len(desc) > 0

    def test_expected_visibility_labels(self):
        """Test that expected visibility labels exist."""
        expected = ["very_likely", "likely", "maybe", "unlikely", "internal_only"]
        assert VISIBILITY_LABELS == expected

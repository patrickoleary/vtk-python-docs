"""Unit tests for extractor module.

Tests the public API extract_all() and internal helpers via their renamed _prefixed names.
"""

from vtk_python_docs.extract.extractor import (
    _clean_docstring,
    _extract_methods_from_section,
    _get_vtk_classes,
    _parse_help_structure,
)


class TestCleanDocstring:
    """Tests for _clean_docstring function."""

    def test_empty_string(self):
        """Test empty string returns empty."""
        assert _clean_docstring("") == ""

    def test_none_returns_empty(self):
        """Test None returns empty."""
        assert _clean_docstring(None) == ""

    def test_removes_c_signature(self):
        """Test that C++ signatures are removed."""
        docstring = "C++: vtkObject::Method() -> void\nThis is the description."
        result = _clean_docstring(docstring)
        assert "C++" not in result
        assert "This is the description" in result

    def test_removes_virtual(self):
        """Test that 'virtual' keyword is removed."""
        docstring = "virtual void Method()\nDescription here."
        result = _clean_docstring(docstring)
        assert "virtual" not in result

    def test_preserves_description(self):
        """Test that description is preserved."""
        docstring = "This is a simple description."
        result = _clean_docstring(docstring)
        assert result == docstring


class TestExtractMethodsFromSection:
    """Tests for _extract_methods_from_section function."""

    def test_empty_content(self):
        """Test empty content returns empty dict."""
        assert _extract_methods_from_section("") == {}

    def test_extracts_method(self):
        """Test that methods are extracted."""
        content = """ |  GetClassName(self) -> str
 |      Return the class name."""
        result = _extract_methods_from_section(content)
        assert "GetClassName" in result


class TestParseHelpStructure:
    """Tests for _parse_help_structure function."""

    def test_empty_help(self):
        """Test empty help text."""
        result = _parse_help_structure("", "vtkTest")
        assert "class_doc" in result
        assert "sections" in result

    def test_extracts_class_doc(self):
        """Test that class documentation is extracted."""
        help_text = """Help on class vtkTest:

class vtkTest(vtkObject)
 |  vtkTest - A test class for testing.
 |
 |  This is the description.
"""
        result = _parse_help_structure(help_text, "vtkTest")
        assert "class_doc" in result


class TestGetVTKClasses:
    """Tests for _get_vtk_classes function."""

    def test_returns_dict(self):
        """Test that function returns a dict."""
        result = _get_vtk_classes()
        assert isinstance(result, dict)

    def test_contains_tuples(self):
        """Test that values contain tuples."""
        result = _get_vtk_classes()
        for module_name, classes in result.items():
            assert isinstance(classes, list)
            if classes:
                assert all(isinstance(item, tuple) for item in classes)
                assert all(len(item) == 2 for item in classes)

    def test_finds_vtk_classes(self):
        """Test that VTK classes are found."""
        result = _get_vtk_classes()
        total = sum(len(classes) for classes in result.values())
        assert total > 0

    def test_class_names_start_with_vtk(self):
        """Test that class names start with vtk."""
        result = _get_vtk_classes()
        for module_name, classes in list(result.items())[:3]:
            for full_module, class_name in classes[:5]:
                assert class_name.startswith("vtk")

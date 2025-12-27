"""Unit tests for introspection module.

Tests the public API introspect_class() which returns role, datatypes, and semantic methods.
"""

from vtk_python_docs.extract.introspection import BOILERPLATE_METHODS, introspect_class


class TestIntrospectClassRole:
    """Tests for role classification via introspect_class()."""

    def test_unknown_class_returns_utility(self):
        """Test that unknown class returns utility."""
        result = introspect_class("vtkNonExistentClass")
        assert result["role"] == "utility"

    def test_named_colors_returns_color(self):
        """Test that vtkNamedColors returns color."""
        result = introspect_class("vtkNamedColors")
        assert result["role"] == "color"

    def test_color_series_returns_color(self):
        """Test that vtkColorSeries returns color."""
        result = introspect_class("vtkColorSeries")
        assert result["role"] == "color"

    def test_sphere_source_returns_input(self):
        """Test that vtkSphereSource (0 inputs, 1+ outputs) returns input."""
        result = introspect_class("vtkSphereSource")
        assert result["role"] == "input"

    def test_stl_reader_returns_input(self):
        """Test that vtkSTLReader returns input."""
        result = introspect_class("vtkSTLReader")
        assert result["role"] == "input"

    def test_contour_filter_returns_filter(self):
        """Test that vtkContourFilter returns filter."""
        result = introspect_class("vtkContourFilter")
        assert result["role"] == "filter"

    def test_polydata_mapper_returns_properties(self):
        """Test that vtkPolyDataMapper returns properties."""
        result = introspect_class("vtkPolyDataMapper")
        assert result["role"] == "properties"

    def test_stl_writer_returns_output(self):
        """Test that vtkSTLWriter returns output."""
        result = introspect_class("vtkSTLWriter")
        assert result["role"] == "output"

    def test_renderer_returns_renderer(self):
        """Test that vtkRenderer returns renderer."""
        result = introspect_class("vtkRenderer")
        assert result["role"] == "renderer"

    def test_render_window_returns_infrastructure(self):
        """Test that vtkRenderWindow returns infrastructure."""
        result = introspect_class("vtkRenderWindow")
        assert result["role"] == "infrastructure"

    def test_camera_returns_scene(self):
        """Test that vtkCamera returns scene."""
        result = introspect_class("vtkCamera")
        assert result["role"] == "scene"

    def test_actor_returns_properties(self):
        """Test that vtkActor (a prop) returns properties."""
        result = introspect_class("vtkActor")
        assert result["role"] == "properties"

    def test_property_returns_properties(self):
        """Test that vtkProperty returns properties."""
        result = introspect_class("vtkProperty")
        assert result["role"] == "properties"

    def test_lookup_table_returns_properties(self):
        """Test that vtkLookupTable returns properties."""
        result = introspect_class("vtkLookupTable")
        assert result["role"] == "properties"


class TestIntrospectClassDatatypes:
    """Tests for datatype extraction via introspect_class()."""

    def test_unknown_class_returns_empty(self):
        """Test that unknown class returns empty strings."""
        result = introspect_class("vtkNonExistentClass")
        assert result["input_datatype"] == ""
        assert result["output_datatype"] == ""

    def test_sphere_source_has_output_type(self):
        """Test that vtkSphereSource has output datatype."""
        result = introspect_class("vtkSphereSource")
        assert result["input_datatype"] == ""  # No input ports
        assert result["output_datatype"] != ""  # Has output type (vtkPolyData)

    def test_contour_filter_has_both_types(self):
        """Test that vtkContourFilter has input and output datatypes."""
        result = introspect_class("vtkContourFilter")
        assert result["input_datatype"] != ""  # Has input type
        assert result["output_datatype"] != ""  # Has output type


class TestIntrospectClassSemanticMethods:
    """Tests for semantic methods extraction via introspect_class()."""

    def test_unknown_class_returns_empty(self):
        """Test that unknown class returns empty list."""
        result = introspect_class("vtkNonExistentClass")
        assert result["semantic_methods"] == []

    def test_returns_sorted_list(self):
        """Test that result is a sorted list."""
        result = introspect_class("vtkSphereSource")
        methods = result["semantic_methods"]
        assert isinstance(methods, list)
        assert methods == sorted(methods)

    def test_excludes_boilerplate(self):
        """Test that boilerplate methods are excluded."""
        result = introspect_class("vtkSphereSource")
        methods = result["semantic_methods"]
        for method in BOILERPLATE_METHODS:
            assert method not in methods

    def test_includes_semantic_methods(self):
        """Test that semantic methods are included."""
        result = introspect_class("vtkSphereSource")
        methods = result["semantic_methods"]
        # vtkSphereSource should have SetRadius, GetRadius, etc.
        assert "SetRadius" in methods or "GetRadius" in methods


class TestIntrospectClassStructure:
    """Tests for introspect_class() return structure."""

    def test_returns_dict_with_required_keys(self):
        """Test that result has all required keys."""
        result = introspect_class("vtkSphereSource")
        assert "role" in result
        assert "input_datatype" in result
        assert "output_datatype" in result
        assert "semantic_methods" in result

    def test_role_is_string(self):
        """Test that role is a string."""
        result = introspect_class("vtkSphereSource")
        assert isinstance(result["role"], str)

    def test_datatypes_are_strings(self):
        """Test that datatypes are strings."""
        result = introspect_class("vtkSphereSource")
        assert isinstance(result["input_datatype"], str)
        assert isinstance(result["output_datatype"], str)

    def test_semantic_methods_is_list(self):
        """Test that semantic_methods is a list."""
        result = introspect_class("vtkSphereSource")
        assert isinstance(result["semantic_methods"], list)

    def test_unknown_class_returns_defaults(self):
        """Test that unknown class returns default values."""
        result = introspect_class("vtkNonExistentClass")
        assert result["role"] == "utility"
        assert result["input_datatype"] == ""
        assert result["output_datatype"] == ""
        assert result["semantic_methods"] == []

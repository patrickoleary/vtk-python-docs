"""Unit tests for introspection module."""


from vtk_python_docs.extract.introspection import (
    BOILERPLATE_METHODS,
    classify_vtk_class,
    get_algorithm_datatypes,
    get_semantic_methods,
    introspect_class,
    is_boilerplate_method,
)


class TestClassifyVtkClass:
    """Tests for classify_vtk_class function."""

    def test_unknown_class_returns_utility(self):
        """Test that unknown class returns utility."""
        result = classify_vtk_class("vtkNonExistentClass")
        assert result == "utility"

    def test_named_colors_returns_color(self):
        """Test that vtkNamedColors returns color."""
        result = classify_vtk_class("vtkNamedColors")
        assert result == "color"

    def test_color_series_returns_color(self):
        """Test that vtkColorSeries returns color."""
        result = classify_vtk_class("vtkColorSeries")
        assert result == "color"

    def test_sphere_source_returns_input(self):
        """Test that vtkSphereSource (0 inputs, 1+ outputs) returns input."""
        result = classify_vtk_class("vtkSphereSource")
        assert result == "input"

    def test_stl_reader_returns_input(self):
        """Test that vtkSTLReader returns input."""
        result = classify_vtk_class("vtkSTLReader")
        assert result == "input"

    def test_contour_filter_returns_filter(self):
        """Test that vtkContourFilter returns filter."""
        result = classify_vtk_class("vtkContourFilter")
        assert result == "filter"

    def test_polydata_mapper_returns_properties(self):
        """Test that vtkPolyDataMapper returns properties."""
        result = classify_vtk_class("vtkPolyDataMapper")
        assert result == "properties"

    def test_stl_writer_returns_output(self):
        """Test that vtkSTLWriter returns output."""
        result = classify_vtk_class("vtkSTLWriter")
        assert result == "output"

    def test_renderer_returns_renderer(self):
        """Test that vtkRenderer returns renderer."""
        result = classify_vtk_class("vtkRenderer")
        assert result == "renderer"

    def test_render_window_returns_infrastructure(self):
        """Test that vtkRenderWindow returns infrastructure."""
        result = classify_vtk_class("vtkRenderWindow")
        assert result == "infrastructure"

    def test_camera_returns_scene(self):
        """Test that vtkCamera returns scene."""
        result = classify_vtk_class("vtkCamera")
        assert result == "scene"

    def test_actor_returns_properties(self):
        """Test that vtkActor (a prop) returns properties."""
        result = classify_vtk_class("vtkActor")
        assert result == "properties"

    def test_property_returns_properties(self):
        """Test that vtkProperty returns properties."""
        result = classify_vtk_class("vtkProperty")
        assert result == "properties"

    def test_lookup_table_returns_properties(self):
        """Test that vtkLookupTable returns properties."""
        result = classify_vtk_class("vtkLookupTable")
        assert result == "properties"


class TestGetAlgorithmDatatypes:
    """Tests for get_algorithm_datatypes function."""

    def test_unknown_class_returns_empty(self):
        """Test that unknown class returns empty strings."""
        input_dt, output_dt = get_algorithm_datatypes("vtkNonExistentClass")
        assert input_dt == ""
        assert output_dt == ""

    def test_sphere_source_has_output_type(self):
        """Test that vtkSphereSource has output datatype."""
        input_dt, output_dt = get_algorithm_datatypes("vtkSphereSource")
        assert input_dt == ""  # No input ports
        assert output_dt != ""  # Has output type (vtkPolyData)

    def test_contour_filter_has_both_types(self):
        """Test that vtkContourFilter has input and output datatypes."""
        input_dt, output_dt = get_algorithm_datatypes("vtkContourFilter")
        assert input_dt != ""  # Has input type
        assert output_dt != ""  # Has output type


class TestIsBoilerplateMethod:
    """Tests for is_boilerplate_method function."""

    def test_dunder_methods_are_boilerplate(self):
        """Test that dunder methods are boilerplate."""
        assert is_boilerplate_method("__init__")
        assert is_boilerplate_method("__str__")
        assert is_boilerplate_method("__repr__")

    def test_private_methods_are_boilerplate(self):
        """Test that private methods are boilerplate."""
        assert is_boilerplate_method("_internal")
        assert is_boilerplate_method("_helper")

    def test_vtk_boilerplate_methods(self):
        """Test that VTK boilerplate methods are detected."""
        assert is_boilerplate_method("GetClassName")
        assert is_boilerplate_method("IsA")
        assert is_boilerplate_method("SafeDownCast")
        assert is_boilerplate_method("Modified")

    def test_semantic_methods_not_boilerplate(self):
        """Test that semantic methods are not boilerplate."""
        assert not is_boilerplate_method("SetRadius")
        assert not is_boilerplate_method("GetOutput")
        assert not is_boilerplate_method("Update")


class TestGetSemanticMethods:
    """Tests for get_semantic_methods function."""

    def test_unknown_class_returns_empty(self):
        """Test that unknown class returns empty list."""
        result = get_semantic_methods("vtkNonExistentClass")
        assert result == []

    def test_returns_sorted_list(self):
        """Test that result is a sorted list."""
        result = get_semantic_methods("vtkSphereSource")
        assert isinstance(result, list)
        assert result == sorted(result)

    def test_excludes_boilerplate(self):
        """Test that boilerplate methods are excluded."""
        result = get_semantic_methods("vtkSphereSource")
        for method in BOILERPLATE_METHODS:
            assert method not in result

    def test_includes_semantic_methods(self):
        """Test that semantic methods are included."""
        result = get_semantic_methods("vtkSphereSource")
        # vtkSphereSource should have SetRadius, GetRadius, etc.
        assert "SetRadius" in result or "GetRadius" in result


class TestIntrospectClass:
    """Tests for introspect_class function."""

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

    def test_unknown_class_returns_utility(self):
        """Test that unknown class returns utility role."""
        result = introspect_class("vtkNonExistentClass")
        assert result["role"] == "utility"
        assert result["input_datatype"] == ""
        assert result["output_datatype"] == ""
        assert result["semantic_methods"] == []

"""VTK class introspection for role, datatypes, and semantic methods.

Computes these fields at extraction time to include in JSONL records:
- role: Pipeline classification (input, filter, output, properties, renderer, scene, infrastructure, utility, color)
- input_datatype: Input data type for vtkAlgorithm subclasses
- output_datatype: Output data type for vtkAlgorithm subclasses
- semantic_methods: Non-boilerplate callable methods

Code map:
    introspect_class()             Main entry point, returns all introspection data
        _classify_vtk_class()      Classify VTK class into pipeline role
        _get_algorithm_datatypes() Get input/output datatypes for algorithms
        _get_semantic_methods()    Get non-boilerplate methods
            _is_boilerplate_method()   Check if method is boilerplate
"""

from __future__ import annotations

from collections.abc import Iterable

import vtk

# VTK-wide infrastructure / pipeline boilerplate methods to exclude
BOILERPLATE_METHODS = {
    # vtkObject / vtkObjectBase
    "GetClassName", "IsA", "IsTypeOf", "NewInstance", "SafeDownCast",
    "PrintSelf", "Register", "UnRegister", "FastDelete",
    "GetReferenceCount", "SetReferenceCount",
    "Modified", "GetMTime",
    "AddObserver", "RemoveObserver", "RemoveObservers",
    "HasObserver", "InvokeEvent", "GetCommand",
    "GetNumberOfGenerationsFromBase", "GetNumberOfGenerationsFromBaseType",
    "GetAddressAsString", "GetIsInMemkind", "GetUsingMemkind",
    "InitializeObjectBase", "SetMemkindDirectory", "UsesGarbageCollector",
    "GetObjectName", "SetObjectName", "GetObjectDescription",
    # Python binding infrastructure
    "override",
    # Debug/warning infrastructure
    "DebugOn", "DebugOff", "GetDebug", "SetDebug",
    "GlobalWarningDisplayOn", "GlobalWarningDisplayOff",
    "GetGlobalWarningDisplay", "SetGlobalWarningDisplay",
    "BreakOnError",
}


def _classify_vtk_class(class_name: str) -> str:
    """Classify a VTK class into pipeline role using VTK introspection.

    Returns one of: input, filter, properties, renderer, scene, infrastructure, output, utility, color
    """
    # Color utilities (by class name)
    if class_name in ("vtkNamedColors", "vtkColorSeries"):
        return "color"

    vtk_class = getattr(vtk, class_name, None)
    if vtk_class is None:
        return "utility"

    try:
        instance = vtk_class()
    except Exception:
        # Non-instantiable algorithm base classes are filters (like vtkAlgorithm itself)
        if class_name in (
            "vtkHyperTreeGridAlgorithm",
            "vtkImageAlgorithm",
            "vtkPartitionedDataSetAlgorithm",
            "vtkPartitionedDataSetCollectionAlgorithm",
            "vtkReaderAlgorithm",
            "vtkStatisticsAlgorithm",
            "vtkThreadedImageAlgorithm",
        ):
            return "filter"
        return "utility"

    # Check if instance has IsA method (some VTK classes don't inherit from vtkObjectBase)
    if not hasattr(instance, "IsA"):
        return "utility"

    # ---- 1. vtkAlgorithm ----
    if instance.IsA("vtkAlgorithm"):
        # Special cases: algorithm base classes that need explicit classification
        if class_name in ("vtkResliceCursorPolyDataAlgorithm", "vtkMultiTimeStepAlgorithm"):
            return "filter"
        if instance.IsA("vtkAbstractMapper") or instance.IsA("vtkTexture"):
            return "properties"
        elif instance.IsA("vtkWriter") or instance.IsA("vtkExporter") or instance.IsA("vtkImageWriter"):
            return "output"
        elif instance.IsA("vtkReader"):
            return "input"
        else:
            nin = instance.GetNumberOfInputPorts()
            nout = instance.GetNumberOfOutputPorts()
            if nin == 0 and nout > 0:
                return "input"
            elif nin > 0 and nout > 0:
                return "filter"
            elif nin > 0 and nout == 0:
                return "output"
            else:
                return "filter"

    # ---- classify non-algorithms in safe order ----

    # Importers (scene file loaders)
    if instance.IsA("vtkImporter"):
        return "input"

    # Renderer first
    if instance.IsA("vtkRenderer"):
        return "renderer"

    # Infrastructure next
    if instance.IsA("vtkRenderWindow") or instance.IsA("vtkRenderWindowInteractor"):
        return "infrastructure"

    if instance.IsA("vtkInteractorStyle") or instance.IsA("vtkAbstractPicker"):
        return "infrastructure"

    if class_name in ("vtkImageViewer", "vtkImageViewer2", "vtkViewTheme"):
        return "infrastructure"

    # Charts
    if instance.IsA("vtkContextActor") or instance.IsA("vtkContextView") or instance.IsA("vtkContextMapper2D") or instance.IsA("vtkContextItem"):
        return "infrastructure"

    # View classes
    if instance.IsA("vtkView"):
        return "infrastructure"

    # Render backend helpers
    if instance.IsA("vtkRenderPass"):
        return "renderer"

    # Exporters (non-algorithm, like vtkOpenGLGL2PSExporter)
    if instance.IsA("vtkExporter"):
        return "output"

    # Scene objects (camera/light/widget) - before vtkProp check
    if instance.IsA("vtkCamera") or instance.IsA("vtkCameraActor"):
        return "scene"

    if instance.IsA("vtkLight") or instance.IsA("vtkLightKit") or instance.IsA("vtkLightActor"):
        return "scene"

    if instance.IsA("vtkAbstractWidget") or instance.IsA("vtk3DWidget"):
        return "scene"

    # Properties objects (styling) - before vtkOpenGL check
    if instance.IsA("vtkProp"):
        return "properties"

    if instance.IsA("vtkProperty") or instance.IsA("vtkVolumeProperty"):
        return "properties"

    if instance.IsA("vtkTexture"):
        return "properties"

    if "LookupTable" in class_name or "ColorTransfer" in class_name:
        return "properties"

    if class_name.startswith("vtkOpenGL"):
        return "renderer"

    # Data / utility
    if instance.IsA("vtkDataObject"):
        return "utility"

    if instance.IsA("vtkImplicitFunction") or instance.IsA("vtkAbstractTransform") \
    or instance.IsA("vtkMatrix4x4") or instance.IsA("vtkMatrix3x3"):
        return "utility"

    return "utility"


def _get_algorithm_datatypes(class_name: str) -> tuple[str, str]:
    """Get input and output datatypes for a vtkAlgorithm subclass.

    Returns:
        Tuple of (input_datatype, output_datatype). Empty strings if not applicable.
    """
    vtk_class = getattr(vtk, class_name, None)
    if vtk_class is None:
        return "", ""

    try:
        instance = vtk_class()
    except Exception:
        return "", ""

    # Check if instance has IsA method
    if not hasattr(instance, "IsA"):
        return "", ""

    if not instance.IsA("vtkAlgorithm"):
        return "", ""

    def _normalize_type_value(v):
        if v is None:
            return ""
        if isinstance(v, str):
            return v
        if isinstance(v, Iterable):
            items = [str(x) for x in v if x]
            return ",".join(items) if items else str(v)
        return str(v)

    input_datatype = ""
    output_datatype = ""

    if instance.GetNumberOfInputPorts() > 0:
        info = instance.GetInputPortInformation(0)
        req_key = vtk.vtkAlgorithm.INPUT_REQUIRED_DATA_TYPE()
        if info and info.Has(req_key):
            input_datatype = _normalize_type_value(info.Get(req_key))

    if instance.GetNumberOfOutputPorts() > 0:
        info = instance.GetOutputPortInformation(0)
        out_key = vtk.vtkDataObject.DATA_TYPE_NAME()
        if info and info.Has(out_key):
            output_datatype = _normalize_type_value(info.Get(out_key))

    return input_datatype, output_datatype


def _is_boilerplate_method(name: str) -> bool:
    """Check if a method name is VTK boilerplate."""
    # All Python dunder methods
    if name.startswith("__") and name.endswith("__"):
        return True

    # Private methods
    if name.startswith("_"):
        return True

    # VTK-wide infrastructure / pipeline boilerplate
    return name in BOILERPLATE_METHODS


def _get_semantic_methods(class_name: str) -> list[str]:
    """Get non-boilerplate callable methods for a VTK class.

    Returns:
        Sorted list of semantic method names.
    """
    vtk_class = getattr(vtk, class_name, None)
    if vtk_class is None:
        return []

    return sorted(
        name for name in dir(vtk_class)
        if not _is_boilerplate_method(name) and callable(getattr(vtk_class, name, None))
    )


def introspect_class(class_name: str) -> dict[str, str | list[str]]:
    """Full introspection of a VTK class.

    Returns dict with:
        - role: Pipeline classification
        - input_datatype: Input data type (for algorithms)
        - output_datatype: Output data type (for algorithms)
        - semantic_methods: List of non-boilerplate methods
    """
    role = _classify_vtk_class(class_name)
    input_datatype, output_datatype = _get_algorithm_datatypes(class_name)
    semantic_methods = _get_semantic_methods(class_name)

    return {
        "role": role,
        "input_datatype": input_datatype,
        "output_datatype": output_datatype,
        "semantic_methods": semantic_methods,
    }

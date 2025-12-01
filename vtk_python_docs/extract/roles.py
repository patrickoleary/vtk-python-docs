"""Role labels and descriptions for VTK class classification."""

# Role labels for classifying VTK classes
ROLE_LABELS = [
    # Data objects - what holds the data
    "data_polydata",
    "data_unstructured",
    "data_structured",
    "data_image",
    "data_rectilinear",
    "data_multiblock",
    "data_table",
    "data_graph",
    "data_tree",
    "data_selection",
    "data_array",
    "data_field",
    # Sources - procedural data generation
    "source_geometric",
    "source_image",
    "source_table",
    "source_graph",
    # I/O - readers and writers
    "io_reader",
    "io_writer",
    "io_exporter",
    "io_importer",
    # Filters - data transformation
    "filter_polydata",
    "filter_image",
    "filter_volume",
    "filter_table",
    "filter_graph",
    "filter_composite",
    "filter_sampling",
    "filter_topology",
    "filter_geometry",
    "filter_extraction",
    "filter_texture",
    # Mappers - data to graphics
    "mapper_polydata",
    "mapper_dataset",
    "mapper_image",
    "mapper_volume",
    "mapper_label",
    "mapper_glyph",
    # Props - renderable scene objects
    "prop_actor3d",
    "prop_actor2d",
    "prop_volume",
    "prop_image",
    "prop_assembly",
    # Rendering infrastructure
    "render_renderer",
    "render_window",
    "render_camera",
    "render_light",
    "render_context",
    # Appearance - visual properties
    "appearance_property",
    "appearance_volume_property",
    "appearance_image_property",
    "appearance_texture",
    "appearance_lut",
    "appearance_transfer_function",
    "appearance_shader",
    # Interaction - user input handling
    "interaction_interactor",
    "interaction_style",
    "interaction_picker",
    "interaction_selector",
    # Widgets - interactive 3D/2D controls
    "widget_3d",
    "widget_2d",
    "widget_representation",
    "widget_handle",
    # Charts and plotting
    "chart_view",
    "chart_plot",
    "chart_axis",
    "chart_legend",
    # Annotations and text
    "annotation_text",
    "annotation_scalar_bar",
    "annotation_axes",
    "annotation_caption",
    # Pipeline infrastructure
    "pipeline_algorithm",
    "pipeline_executive",
    "pipeline_information",
    # Collections and iterators
    "collection",
    "iterator",
    # Math and transforms
    "math_matrix",
    "math_transform",
    "math_function",
    "math_interpolator",
    # Spatial structures
    "spatial_locator",
    "spatial_cell_locator",
    "spatial_point_locator",
    "spatial_bounding_box",
    # Parallel and distributed
    "parallel_controller",
    "parallel_communicator",
    # Render passes and GPU backend
    "render_pass",
    "render_backend",
    # Domain-specific
    "domain_molecular",
    # Parallel synchronization
    "parallel_sync",
    # Web and remote
    "web_service",
    # Utility and infrastructure
    "utility_object",
    "utility_callback",
    "utility_observer",
    "utility_timer",
    "utility_logger",
    "utility_helper",
]

# Natural language descriptions for each role (for LLM classification)
ROLE_DESCRIPTIONS = {
    # Data objects
    "data_polydata": "Class that holds polygonal meshes (points, vertices, lines, polygons, triangle strips).",
    "data_unstructured": "Class that holds unstructured grids with arbitrary cell types.",
    "data_structured": "Class for structured grids with regular topology but variable geometry.",
    "data_image": "Class for image or volume data on uniform rectilinear grids.",
    "data_rectilinear": "Class for rectilinear grids with axis-aligned but non-uniform spacing.",
    "data_multiblock": "Class that groups multiple datasets into a composite or hierarchical structure.",
    "data_table": "Class representing tabular data with rows and columns.",
    "data_graph": "Class representing graph structures with nodes and edges.",
    "data_tree": "Class representing hierarchical tree structures.",
    "data_selection": "Class representing selected subsets of data elements.",
    "data_array": "Class for storing arrays of numeric or string data.",
    "data_field": "Class for field data associated with points, cells, or datasets.",
    # Sources
    "source_geometric": "Source that procedurally generates geometric primitives (spheres, cones, cubes, etc.).",
    "source_image": "Source that procedurally generates image or volume data.",
    "source_table": "Source that procedurally generates tabular data.",
    "source_graph": "Source that procedurally generates graph structures.",
    # I/O
    "io_reader": "Reader that loads data from files or streams into datasets.",
    "io_writer": "Writer that saves datasets to files or streams.",
    "io_exporter": "Exporter that writes scene or rendering data to external formats.",
    "io_importer": "Importer that loads scene data from external formats.",
    # Filters
    "filter_polydata": "Filter that transforms or processes polygonal mesh data.",
    "filter_image": "Filter that processes 2D images or 3D volumes.",
    "filter_volume": "Filter specifically for volumetric dataset processing.",
    "filter_table": "Filter that processes tabular data.",
    "filter_graph": "Filter that processes graph or network data.",
    "filter_composite": "Filter that processes composite or multiblock datasets.",
    "filter_sampling": "Filter that samples, probes, or resamples data at different locations.",
    "filter_topology": "Filter that modifies connectivity, topology, or mesh structure.",
    "filter_geometry": "Filter that extracts or modifies geometry (contours, surfaces, edges).",
    "filter_extraction": "Filter that extracts subsets of data based on criteria.",
    "filter_texture": "Filter that generates or processes texture coordinates.",
    # Mappers
    "mapper_polydata": "Mapper that converts polygonal data to graphics primitives for rendering.",
    "mapper_dataset": "Mapper for general dataset types to graphics primitives.",
    "mapper_image": "Mapper that displays 2D images or slices.",
    "mapper_volume": "Mapper that performs volume rendering of 3D data.",
    "mapper_label": "Mapper that renders text labels or glyphs.",
    "mapper_glyph": "Mapper that renders glyphs (arrows, spheres) at data points.",
    # Props
    "prop_actor3d": "Renderable 3D object in a scene (actor, follower, LOD actor).",
    "prop_actor2d": "Renderable 2D overlay element (text, scalar bar, legend).",
    "prop_volume": "Renderable volume entity for volume rendering.",
    "prop_image": "Renderable image slice or 2D image plane.",
    "prop_assembly": "Collection of props grouped together for transformation.",
    # Rendering
    "render_renderer": "Renderer that manages a viewport and renders a scene.",
    "render_window": "Window that owns the rendering surface and OpenGL context.",
    "render_camera": "Camera that controls view position, orientation, and projection.",
    "render_light": "Light source that illuminates the scene.",
    "render_context": "Rendering context for 2D drawing operations.",
    # Appearance
    "appearance_property": "Property controlling surface appearance (color, opacity, lighting).",
    "appearance_volume_property": "Property controlling volume rendering appearance.",
    "appearance_image_property": "Property controlling image display appearance.",
    "appearance_texture": "Texture for image-based surface mapping.",
    "appearance_lut": "Lookup table or color transfer function for scalar mapping.",
    "appearance_transfer_function": "Transfer function for opacity or color mapping.",
    "appearance_shader": "Shader property for programmable GPU rendering.",
    # Interaction
    "interaction_interactor": "Interactor that handles user input events (mouse, keyboard).",
    "interaction_style": "Interactor style that defines camera and interaction behavior.",
    "interaction_picker": "Picker that identifies scene objects from screen coordinates.",
    "interaction_selector": "Selector for hardware-accelerated picking and selection.",
    # Widgets
    "widget_3d": "Interactive 3D widget for scene manipulation (planes, boxes, handles).",
    "widget_2d": "Interactive 2D widget for overlay controls.",
    "widget_representation": "Visual representation of a widget's state.",
    "widget_handle": "Handle for widget interaction (points, lines, spheres).",
    # Charts
    "chart_view": "View or viewport for chart and plot rendering.",
    "chart_plot": "Plot type (line, bar, scatter, pie, etc.).",
    "chart_axis": "Axis for charts with labels, ticks, and ranges.",
    "chart_legend": "Legend showing plot series labels and colors.",
    # Annotations
    "annotation_text": "Text annotation or label in 2D or 3D.",
    "annotation_scalar_bar": "Scalar bar (color legend) showing data range.",
    "annotation_axes": "Axes actor showing coordinate system orientation.",
    "annotation_caption": "Caption or callout annotation.",
    # Pipeline
    "pipeline_algorithm": "Base class for pipeline algorithms (filters, sources, mappers).",
    "pipeline_executive": "Executive that controls pipeline execution and updates.",
    "pipeline_information": "Information object or key for pipeline metadata.",
    # Collections
    "collection": "Collection that holds multiple objects of the same type.",
    "iterator": "Iterator for traversing data structures or collections.",
    # Math
    "math_matrix": "Matrix class for linear algebra operations.",
    "math_transform": "Transform for coordinate system transformations.",
    "math_function": "Mathematical function or implicit function.",
    "math_interpolator": "Interpolator for data interpolation and splines.",
    # Spatial
    "spatial_locator": "Spatial search structure for efficient queries.",
    "spatial_cell_locator": "Locator optimized for finding cells containing points.",
    "spatial_point_locator": "Locator optimized for finding nearest points.",
    "spatial_bounding_box": "Bounding box or bounds computation.",
    # Parallel
    "parallel_controller": "Controller for parallel and distributed processing.",
    "parallel_communicator": "Communicator for inter-process communication.",
    "parallel_sync": "Synchronization class for distributed rendering or data exchange.",
    # Render passes and GPU backend
    "render_pass": "Render pass for multi-pass rendering pipelines (shadow, composite, blur).",
    "render_backend": "GPU/OpenGL backend implementation (framebuffers, texture units, shaders).",
    # Domain-specific
    "domain_molecular": "Molecular visualization and chemistry-specific class.",
    # Web and remote
    "web_service": "Web application, remote interaction, or data encoding service.",
    # Utility
    "utility_object": "Base object class or general utility object.",
    "utility_callback": "Callback for event handling and notifications.",
    "utility_observer": "Observer for monitoring object state changes.",
    "utility_timer": "Timer for performance measurement or scheduling.",
    "utility_logger": "Logger for output and debugging messages.",
    "utility_helper": "Helper class for specific functionality.",
}

# Verify all labels have descriptions
assert set(ROLE_LABELS) == set(ROLE_DESCRIPTIONS.keys()), "Mismatch between labels and descriptions"


# Visibility labels: likelihood of appearing in user prompts
VISIBILITY_LABELS = [
    "very_likely",
    "likely",
    "maybe",
    "unlikely",
    "internal_only",
]

VISIBILITY_DESCRIPTIONS = {
    "very_likely": (
        "Classes users actively ask about or search for. These solve specific problems: "
        "loading data (vtkSTLReader, vtkPLYReader), creating geometry (vtkSphereSource, "
        "vtkArrowSource), processing meshes (vtkContourFilter, vtkClipPolyData, vtkGlyph3D), "
        "or coloring data (vtkLookupTable, vtkColorTransferFunction)."
    ),
    "likely": (
        "Classes users ask about for specific tasks. Appearance and shading (vtkProperty, "
        "vtkTexture), widgets (vtkBoxWidget), interactor styles, volume rendering, "
        "and specialized filters (vtkStreamTracer, vtkCutter)."
    ),
    "maybe": (
        "Classes users occasionally mention but often just copy from examples. "
        "Standard pipeline components that work without much configuration "
        "(e.g., vtkRenderer, vtkRenderWindow, vtkActor, vtkPolyDataMapper, vtkCamera)."
    ),
    "unlikely": (
        "Rarely named by users. Internal data structures, iterators, collections, "
        "or components typically accessed through convenience methods "
        "(e.g., vtkCellArray, vtkPoints, vtkFieldData, iterators)."
    ),
    "internal_only": (
        "Infrastructure and base classes that users almost never type directly. "
        "These are superclasses, pipeline internals, or backend implementations "
        "(e.g., vtkAlgorithm, vtkExecutive, vtkInformation*, vtkOpenGL* internals)."
    ),
}

# Verify visibility labels have descriptions
assert set(VISIBILITY_LABELS) == set(VISIBILITY_DESCRIPTIONS.keys()), "Mismatch between visibility labels and descriptions"

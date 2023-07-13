import adsk.core as core
import adsk.fusion as fusion
from math import pi


def create_empty_component(parent, name, T):
    design = fusion.Design.cast(core.Application.get().activeProduct)
    root_comp = design.rootComponent

    if parent:
        new_comp = parent.component.occurrences.addNewComponent(T)
        new_comp = new_comp.createForAssemblyContext(parent)
    else:
        new_comp = root_comp.occurrences.addNewComponent(T)
        new_comp.isGrounded = True

    new_comp.component.name = name
    new_comp.component.isOriginFolderLightBulbOn = True  # make origin frame visible on default
    new_comp.component.xYConstructionPlane.isLightBulbOn = False  # hide XY plane on default
    new_comp.component.xZConstructionPlane.isLightBulbOn = False  # hide XZ plane on default
    new_comp.component.yZConstructionPlane.isLightBulbOn = False  # hide YZ plane on default

    return new_comp

def dh_to_SE3(dh):
    # Compute transformation based on DH parameters
    a = dh['a']
    alpha = dh['alpha']
    d = dh['d']
    theta = dh['theta']

    # Create transformation matrices
    # spatialmath notation:  T = SE3.Rz(theta) * SE3.Tz(d) * SE3.Tx(a) * SE3.Rx(alpha)
    # Fusion notation:
    Rz = core.Matrix3D.create()
    Rz.setToRotation(theta, core.Vector3D.create(0, 0, 1), core.Point3D.create(0, 0, 0))
    Tz = core.Matrix3D.create()
    Tz.translation = core.Vector3D.create(0, 0, d)
    Tx = core.Matrix3D.create()
    Tx.translation = core.Vector3D.create(a, 0, 0)
    Rx = core.Matrix3D.create()
    Rx.setToRotation(alpha, core.Vector3D.create(1, 0, 0), core.Point3D.create(0, 0, 0))

    # Perform the transformations
    T = core.Matrix3D.create() # identity transformation as starting point
    T.transformBy(Rx)
    T.transformBy(Tx)
    T.transformBy(Tz)
    T.transformBy(Rz)

    return T

def add_joint(parent, component):
        joint_geometry = fusion.JointGeometry.createByPoint(parent.component.originConstructionPoint)
        asBuiltJointInput = parent.component.asBuiltJoints.createInput(component, parent, joint_geometry)
        asBuiltJointInput.setAsRevoluteJointMotion(fusion.JointDirections.ZAxisJointDirection)
        parent.component.asBuiltJoints.add(asBuiltJointInput)

def generate_robot_assembly(dh_parameters):
    base_comp = create_empty_component(None, "Base", core.Matrix3D.create())
    prev_comp = base_comp

    for dh in dh_parameters:
        # Create name for component
        comp_name = f"Link_{dh['index']}"

        # Converts length units, Fusion always uses cm internally
        dh['a'] = dh['a'] * 100 # convert from meters to centimeters
        dh['d'] = dh['d'] * 100 # convert from meters to centimeters

        # Compute transformation based on DH parameters
        T_fusion = dh_to_SE3(dh)

        # Create new component and add to assembly with computed transformation
        comp = create_empty_component(prev_comp, comp_name, T_fusion)

        # Create asBuiltJoint between previous component and new component
        add_joint(prev_comp, comp)

        prev_comp = comp

    return base_comp

def run(context):
    # Example DH parameters of a robot arm
    # a and d in meters, alpha and theta in radians
    dh_parameters = [
        {"index": 1, "a": 0, "alpha": pi/2, "d": 0.2, "theta": 0},
        {"index": 2, "a": 0.2, "alpha": 0, "d": 0, "theta": 0},
        {"index": 3, "a": 0.2, "alpha": 0, "d": 0, "theta": 0},
        {"index": 4, "a": 0, "alpha": pi/2, "d": 0, "theta": 0},
        {"index": 5, "a": 0, "alpha": 0, "d": 0.15, "theta": 0},
        # Add more DH parameters for additional links
    ]

    app = core.Application.get()
    product = app.activeProduct

    base_comp = generate_robot_assembly(dh_parameters)
    fusion.Design.cast(product).activeProduct = base_comp.component.parentDesign

    # fit the view to the model
    app = core.Application.get()
    viewPort = app.activeViewport  # get the viewport
    cam = viewPort.camera  # get the camera
    cam.isFitView = True  # set the camera to automatically fit the view
    viewPort.camera = cam  # set the camera
    viewPort.refresh()  # refresh the viewport

    print("Assembly generation complete.")

import adsk.core as core
import adsk.fusion as fusion
from adsk import autoTerminate, terminate
import traceback

_app = None
_ui = None
_rowNumber = 0
_handlers = []


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
    a = dh['a']
    alpha = dh['alpha']
    d = dh['d']
    theta = dh['theta']

    Rz = core.Matrix3D.create()
    Rz.setToRotation(theta, core.Vector3D.create(0, 0, 1), core.Point3D.create(0, 0, 0))
    Tz = core.Matrix3D.create()
    Tz.translation = core.Vector3D.create(0, 0, d)
    Tx = core.Matrix3D.create()
    Tx.translation = core.Vector3D.create(a, 0, 0)
    Rx = core.Matrix3D.create()
    Rx.setToRotation(alpha, core.Vector3D.create(1, 0, 0), core.Point3D.create(0, 0, 0))

    T = core.Matrix3D.create()  # identity transformation as starting point
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

def generate_robot_assembly(inputs):
    base_comp = create_empty_component(None, "Base", core.Matrix3D.create())
    prev_comp = base_comp

    table = inputs.itemById('table')
    dh_parameters = []
    for row in range(table.rowCount):
        dh = {
            'index': row + 1,
            'a': table.getInputAtPosition(row, 1).value,
            'alpha': table.getInputAtPosition(row, 2).value,
            'd': table.getInputAtPosition(row, 3).value,
            'theta': table.getInputAtPosition(row, 4).value
        }
        dh_parameters.append(dh)

    for dh in dh_parameters:
        comp_name = f"Link_{dh['index']}"
        T_fusion = dh_to_SE3(dh)
        comp = create_empty_component(prev_comp, comp_name, T_fusion)
        add_joint(prev_comp, comp)
        prev_comp = comp

    return base_comp

class MyCommandInputChangedHandler(core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            event_args = core.InputChangedEventArgs.cast(args)
            inputs = event_args.inputs
            cmd_input = event_args.input

            if cmd_input.id == 'tableAdd':
                table_input = inputs.itemById('table')
                add_row_to_table(table_input)
            elif cmd_input.id == 'tableDelete':
                table_input = inputs.itemById('table')
                if table_input.selectedRow == -1:
                    _ui.messageBox('Select one row to delete.')
                else:
                    table_input.deleteRow(table_input.selectedRow)

        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class MyCommandExecuteHandler(core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            command = args.firingEvent.sender
            inputs = command.commandInputs

            # generate the robot assembly
            generate_robot_assembly(inputs)
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class MyCommandDestroyHandler(core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            terminate()

            # fit the view to the model
            app = core.Application.get()
            viewPort = app.activeViewport  # get the viewport
            cam = viewPort.camera  # get the camera
            cam.isFitView = True  # set the camera to automatically fit the view
            viewPort.camera = cam  # set the camera
            viewPort.refresh()  # refresh the viewport
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class MyCommandCreatedHandler(core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = core.Command.cast(args.command)
            onDestroy = MyCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)

            onInputChanged = MyCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)

            onExecute = MyCommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)

            inputs = cmd.commandInputs

            inputs.addTextBoxCommandInput('commandDescription', '', 'Add the DH Parameters of your Robot below to generate its kinematic structure.', 2, True)

            add_table_headings(inputs)

            table_input = inputs.addTableCommandInput('table', 'DH Parameters', 5, '1:2:2:2:2')
            table_input.maximumVisibleRows = 7
            table_input.minimumVisibleRows = 5
            add_row_to_table(table_input)  # add first row
            
            add_button_input = inputs.addBoolValueInput('tableAdd', 'Add link', False, '', True)
            table_input.addToolbarCommandInput(add_button_input)

            delete_button_input = inputs.addBoolValueInput('tableDelete', 'Delete link', False, '', True)
            table_input.addToolbarCommandInput(delete_button_input)

        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def add_row_to_table(table_input):
    global _rowNumber
    cmd_inputs = core.CommandInputs.cast(table_input.commandInputs)
    link_name_input = cmd_inputs.addTextBoxCommandInput('TableInput_linkName{}'.format(_rowNumber), '', 'Link {}'.format(_rowNumber + 1), 1, True)
    a_input = cmd_inputs.addValueInput('TableInput_a{}'.format(_rowNumber), 'a', 'm', core.ValueInput.createByReal(0))
    alpha_input = cmd_inputs.addValueInput('TableInput_alpha{}'.format(_rowNumber), 'alpha', 'rad', core.ValueInput.createByReal(0))
    d_input = cmd_inputs.addValueInput('TableInput_d{}'.format(_rowNumber), 'd', 'm', core.ValueInput.createByReal(0))
    theta_input = cmd_inputs.addValueInput('TableInput_theta{}'.format(_rowNumber), 'theta', 'rad', core.ValueInput.createByReal(0))
    row = table_input.rowCount
    table_input.addCommandInput(link_name_input, row, 0)
    table_input.addCommandInput(a_input, row, 1)
    table_input.addCommandInput(alpha_input, row, 2)
    table_input.addCommandInput(d_input, row, 3)
    table_input.addCommandInput(theta_input, row, 4)
    _rowNumber += 1

def add_table_headings(inputs):
    table_headings_input = inputs.addTableCommandInput('tableHeadings', 'Table Headings', 5, '1:2:2:2:2')
    table_headings_input.minimumVisibleRows = 1
    table_headings_input.tablePresentationStyle = 2  # transparent background table
    link_name_heading_input = inputs.addTextBoxCommandInput('TableHeadingsInput_linkName', '', '<div align="center"><b> Link </b></div>', 1, True)
    a_heading_input = inputs.addTextBoxCommandInput('TableHeadingsInput_a', '', '<div align="center"><b>a</b></div>', 1, True)
    alpha_heading_input = inputs.addTextBoxCommandInput('TableHeadingsInput_alpha', '', '<div align="center"><b> alpha </b></div>', 1, True)
    d_heading_input = inputs.addTextBoxCommandInput('TableHeadingsInput_d', '', '<div align="center"><b> d </b></div>', 1, True)
    theta_heading_input = inputs.addTextBoxCommandInput('TableHeadingsInput_theta', '', '<div align="center"><b> theta </b></div>', 1, True)
    table_headings_input.addCommandInput(link_name_heading_input, 0, 0)
    table_headings_input.addCommandInput(a_heading_input, 0, 1)
    table_headings_input.addCommandInput(alpha_heading_input, 0, 2)
    table_headings_input.addCommandInput(d_heading_input, 0, 3)
    table_headings_input.addCommandInput(theta_heading_input, 0, 4)

def run(context):
    try:
        global _app, _ui
        _app = core.Application.get()
        _ui = _app.userInterface

        cmd_def = _ui.commandDefinitions.itemById('cmdInputs')
        if not cmd_def:
            cmd_def = _ui.commandDefinitions.addButtonDefinition('cmdInputs', 'Generate Robot from DH Parameters',
                                                                  'Generate the kinematic structure of a robot from DH parameters.')

        on_command_created = MyCommandCreatedHandler()
        cmd_def.commandCreated.add(on_command_created)
        _handlers.append(on_command_created)

        cmd_def.execute()

        autoTerminate(False)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

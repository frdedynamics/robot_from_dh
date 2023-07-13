# robot_from_dh
 Fusion360 scripts to generate the kinematic structure of a robot from DH parameters.  
__robot_from_dh__ generates a robot from DH parameters defined inside the script.  
__robot_from_dh_gui__ generates a robot from DH parameters specified in the GUI in Fusion360.

 ## Setup
 1. To add the scripts to Fusion 360, clone the repository into the Fusion 360 scripts folder.

    __On Windows__, scripts are located at
    ```%appdata%\Autodesk\Autodesk Fusion 360\API\Scripts```

    __On macOS__, scripts are located at
    ```~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts```

2. In Fusion 360, go to UTILITIES > Scripts and Add-ins.
3. In the Scripts and Add-ins dialog box, click on the green plus sign next to "My Scripts" to add a new script.
4. Select the subfolder of one of the scripts. Repeat for the other script.

## Usage
In the Scripts and Add-ins dialog box, select the script you want to run and click on the Run button.

## Development
In the Scripts and Add-ins dialog box, select the script you want to edit and click on the Edit button.

This will open the script in VSCode and create a ```.env``` file in the script folder, pointing to the Python installation used by Fusion 360.

Once the ```.env``` file is created, you can open the scripts directly in VSCode.
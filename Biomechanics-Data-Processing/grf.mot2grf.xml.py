import pandas as pd
import numpy as np
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom  # For pretty printing XML

# --- Configuration ---
# 1. Path to your generated GRF .mot file
MOT_FILE_PATH = r"D:\uni\post stroke\0core\SUBJ75(healthy female)\grf\SUBJ75_grf.mot"  # <--- CHANGE THIS

# 2. Path to save the output ExternalLoads.xml file
OUTPUT_XML_PATH = r"D:\uni\post stroke\0core\SUBJ75(healthy female)\grf\SUBJ75_ExternalLoads.xml"  # <--- CHANGE THIS

# 3. Force Plate to OpenSim Body Mapping (CRITICAL)
# This dictionary maps the force plate identifier (e.g., 'fp1', 'fp2' from your .mot column names)
# to the corresponding body in your OpenSim model (e.g., 'calcn_r', 'calcn_l').
# The 'prefix' in your .mot file is 'ground_fpX_' (e.g., ground_fp1_).
# You need to specify which 'fpX' maps to which body.
# Example: If ground_fp1_ is your Right foot, and ground_fp2_ is your Left foot.
FORCE_PLATE_MAPPING = {
    'fp1': 'calcn_r',  # Force Plate 1 in .mot maps to Right Calcaneus in OpenSim model
    'fp2': 'calcn_l',  # Force Plate 2 in .mot maps to Left Calcaneus in OpenSim model
    'fp4': 'calcn_r',  # Example: If fp4 is another right force plate, adjust body as needed
    # Add more entries if you have more force plates (e.g., 'fp3': 'some_other_body')
}


# If you only have one force plate, you might have:
# FORCE_PLATE_MAPPING = {'fp1': 'calcn_r'} # Or 'calcn_l' depending on which foot it is

# --- XML Generation Logic ---
def create_external_loads_xml(mot_file_path, output_xml_path, fp_mapping):
    """
    Creates an OpenSim ExternalLoads.xml file from a GRF .mot file.

    Args:
        mot_file_path (str): Path to the input GRF .mot file.
        output_xml_path (str): Path to save the output ExternalLoads.xml.
        fp_mapping (dict): Dictionary mapping force plate identifiers (e.g., 'fp1')
                           to OpenSim model body names (e.g., 'calcn_r').
    """
    print(f"Generating ExternalLoads.xml for: {mot_file_path}")

    # 1. Read .mot file to get time range and column headers
    try:
        # Pandas can read .mot files if they are tab-delimited and have standard headers
        # We need to find the 'endheader' line to know where data starts
        with open(mot_file_path, 'r') as f:
            header_lines = []
            data_start_line = 0
            for i, line in enumerate(f):
                header_lines.append(line)
                if 'endheader' in line:
                    data_start_line = i + 1
                    break

        # Read the data, skipping lines up to the actual column headers
        # The column headers are on the line *after* 'endheader'
        df_mot = pd.read_csv(mot_file_path, sep='\t', skiprows=data_start_line, header=0)

        # The first column is usually 'time', remove it for data processing
        time_column = df_mot['time']
        df_data = df_mot.drop(columns=['time'])

        start_time = time_column.iloc[0]
        end_time = time_column.iloc[-1]

        print(f"MOT file loaded. Time range: {start_time:.3f} to {end_time:.3f} seconds.")
        print(f"MOT column headers found: {list(df_data.columns)}")  # Added for debugging

    except FileNotFoundError:
        print(f"Error: MOT file not found at {mot_file_path}")
        return
    except Exception as e:
        print(f"Error reading MOT file: {e}")
        print("Please ensure your .mot file is correctly formatted and tab-delimited.")
        return

    # 2. Prepare XML structure
    root = ET.Element("OpenSimDocument")
    root.set("Version", "40000")  # Or your OpenSim version

    external_loads = ET.SubElement(root, "ExternalLoads")
    external_loads.set("name", "ExternalLoads")

    # Add data file name
    data_file = ET.SubElement(external_loads, "datafile")
    data_file.text = os.path.basename(mot_file_path)  # Only the filename, OpenSim expects it in the same folder

    # Add time range
    ET.SubElement(external_loads, "external_loads_model_scaler_file")
    ET.SubElement(external_loads, "external_loads_model_marker_file")
    ET.SubElement(external_loads, "lowpass_cutoff_frequency").text = "-1.0"  # -1.0 means no filtering

    # Loop through each force plate defined in the mapping
    for fp_id, applied_to_body in fp_mapping.items():
        # Construct the prefix based on your .mot file naming (e.g., 'ground_fp1_')
        # This assumes your .mot file has columns like ground_fp1_force_vx, ground_fp1_force_px etc.
        force_prefix_in_mot = f'ground_{fp_id}_'

        # Verify that the expected columns exist in the DataFrame
        expected_force_cols = [f'{force_prefix_in_mot}force_vx', f'{force_prefix_in_mot}force_vy',
                               f'{force_prefix_in_mot}force_vz']
        expected_point_cols = [f'{force_prefix_in_mot}force_px', f'{force_prefix_in_mot}force_py',
                               f'{force_prefix_in_mot}force_pz']

        print(
            f"Checking for force plate '{fp_id}' with expected columns: {expected_force_cols[0]}...")  # Added for debugging
        if not all(col in df_data.columns for col in expected_force_cols + expected_point_cols):
            print(
                f"Warning: Columns for force plate '{fp_id}' (e.g., '{expected_force_cols[0]}') NOT found in MOT file. Skipping this force plate.")  # Improved warning
            print(f"  Expected: {expected_force_cols + expected_point_cols}")
            print(f"  Found in MOT: {list(df_data.columns)}")
            continue

        # Create an ExternalForce block for each force plate
        ext_force = ET.SubElement(external_loads, "ExternalForce", name=f"{fp_id}_GRF")

        # Force components
        ET.SubElement(ext_force, "force_expression").text = \
            f"{force_prefix_in_mot}force_vx {force_prefix_in_mot}force_vy {force_prefix_in_mot}force_vz"

        # Point of application (CoP) components
        ET.SubElement(ext_force, "point_expression").text = \
            f"{force_prefix_in_mot}force_px {force_prefix_in_mot}force_py {force_prefix_in_mot}force_pz"

        ET.SubElement(ext_force, "force_is_global").text = "true"
        ET.SubElement(ext_force, "point_is_global").text = "true"
        ET.SubElement(ext_force, "applied_to_body").text = applied_to_body
        ET.SubElement(ext_force, "force_applied_to_body_is_global").text = "true"  # Often true for GRF

    # Add start and end times for the analysis
    ET.SubElement(external_loads, "start_time").text = str(start_time)
    ET.SubElement(external_loads, "end_time").text = str(end_time)

    # 3. Write XML to file (pretty printed)
    rough_string = ET.tostring(root, 'utf-8')
    reparsed_xml = minidom.parseString(rough_string)
    pretty_xml_str = reparsed_xml.toprettyxml(indent="  ")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_xml_path), exist_ok=True)

    with open(output_xml_path, "w") as f:
        f.write(pretty_xml_str)

    print(f"✅ ExternalLoads.xml saved to: {output_xml_path}")


# --- Execute the XML generation ---
if __name__ == "__main__":
    create_external_loads_xml(MOT_FILE_PATH, OUTPUT_XML_PATH, FORCE_PLATE_MAPPING)

    print("\nNext steps:")
    print("1. **CRITICAL:** Review the generated `BWA3_ExternalLoads.xml` file in a text editor.")
    print(
        "   - Ensure the `datafile` path is correct (it should just be the filename if in the same folder as the setup file).")
    print("   - Verify the `force_expression` and `point_expression` column names match your `.mot` file exactly.")
    print("   - Confirm the `applied_to_body` names (e.g., 'calcn_r', 'calcn_l') are correct for your OpenSim model.")
    print(
        "2. Use this `BWA3_ExternalLoads.xml` file as the 'External Loads File' in your OpenSim Inverse Dynamics Tool settings.")
    print("3. Run Inverse Dynamics in OpenSim.")

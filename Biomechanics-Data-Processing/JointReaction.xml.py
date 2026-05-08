import os
import xml.etree.ElementTree as ET
from xml.dom import minidom # For pretty printing XML

# --- Configuration ---
# 1. Path to your scaled OpenSim model file
MODEL_FILE_PATH = r"D:\uni\post stroke\0core\molderate\model_scaled.osim" # <--- CHANGE THIS

# 2. Path to your Inverse Kinematics (IK) results file (.mot or .sto)
INPUT_MOTION_FILE_PATH = r"D:\uni\post stroke\0core\molderate\results\IK32.mot" # <--- CHANGE THIS

# 3. Path to your Inverse Dynamics (ID) or Static Optimization (SO) results file (.sto)
# Use the SO results if you ran Static Optimization, otherwise use ID results.
INPUT_FORCES_FILE_PATH = r"D:\uni\post stroke\0core\molderate\results\model_scaled_StaticOptimization_force.sto" # <--- CHANGE THIS

# 4. Path to save the output JointReaction.xml file
OUTPUT_XML_PATH = r"D:\uni\post stroke\0core\molderate\results\JRF\32JointReaction.xml" # <--- CHANGE THIS

# 5. List of Joints to Analyze (CRITICAL)
# Provide the exact names of the joints from your OpenSim model.
# For each joint, specify the frame in which to express the reaction forces/moments.
# Options for 'express_in_frame': 'ground', 'parent', 'child'
# You will get 6 outputs for each joint: Fx, Fy, Fz, Mx, My, Mz
JOINTS_TO_ANALYZE = [
    {'name': 'hip_r', 'express_in_frame': 'ground'},
    {'name': 'knee_r', 'express_in_frame': 'ground'},
    {'name': 'ankle_r', 'express_in_frame': 'ground'},
    {'name': 'hip_l', 'express_in_frame': 'ground'},
    {'name': 'knee_l', 'express_in_frame': 'ground'},
    {'name': 'ankle_l', 'express_in_frame': 'ground'},
    # Add more joints as needed
]

# --- XML Generation Logic ---
def create_joint_reaction_xml(model_path, motion_path, forces_path, output_xml_path, joints_to_analyze):
    """
    Creates an OpenSim JointReaction.xml setup file.

    Args:
        model_path (str): Path to the OpenSim model file.
        motion_path (str): Path to the input motion file (IK results).
        forces_path (str): Path to the input generalized forces file (ID/SO results).
        output_xml_path (str): Path to save the output XML.
        joints_to_analyze (list): List of dictionaries, each specifying a joint name
                                  and the frame to express results in.
    """
    print(f"Generating JointReaction.xml for model: {model_path}")

    # Root element
    root = ET.Element("OpenSimDocument")
    root.set("Version", "40000") # Standard for OpenSim 4.x XML files

    # Analyze Tool
    analyze_tool = ET.SubElement(root, "AnalyzeTool")
    analyze_tool.set("name", "JointReactionAnalysis")

    # Common AnalyzeTool properties
    ET.SubElement(analyze_tool, "model_file").text = os.path.basename(model_path) # Only filename if in same folder
    ET.SubElement(analyze_tool, "replace_force_set").text = "false" # Usually false for JRA
    ET.SubElement(analyze_tool, "results_directory").text = "./" # Current directory, or specify a path
    ET.SubElement(analyze_tool, "output_precision").text = "20"
    ET.SubElement(analyze_tool, "initial_time").text = "0.0" # Will be overridden by input motion if specified
    ET.SubElement(analyze_tool, "final_time").text = "1.0"   # Will be overridden by input motion if specified
    ET.SubElement(analyze_tool, "solve_for_equilibrium_for_torque_driven_models").text = "false"
    ET.SubElement(analyze_tool, "start_time").text = "0.0" # These will be set by the input motion file
    ET.SubElement(analyze_tool, "end_time").text = "1.0"   # These will be set by the input motion file

    # Input files
    ET.SubElement(analyze_tool, "coordinates_file").text = os.path.basename(motion_path)
    ET.SubElement(analyze_tool, "forces_file").text = os.path.basename(forces_path)
    ET.SubElement(analyze_tool, "load_external_loads").text = "false" # External loads are already in forces_file (ID/SO)
    ET.SubElement(analyze_tool, "external_loads_file") # Empty, as not loading external loads directly

    # Analyses set
    analyses_set = ET.SubElement(analyze_tool, "AnalysisSet")
    objects = ET.SubElement(analyses_set, "objects")

    # JointReaction analysis
    jra = ET.SubElement(objects, "JointReaction")
    jra.set("name", "JointReaction")

    ET.SubElement(jra, "on").text = "true"
    ET.SubElement(jra, "start_time").text = "-1" # -1 means use tool's start/end time
    ET.SubElement(jra, "end_time").text = "-1"   # -1 means use tool's start/end time
    ET.SubElement(jra, "step_interval").text = "1" # Output every step
    ET.SubElement(jra, "in_degrees").text = "false" # Output is forces/moments, not degrees
    ET.SubElement(jra, "output_precision").text = "20"
    ET.SubElement(jra, "apply_to_simulation").text = "true" # Apply forces/moments to the simulation

    # Joint list for JRA
    joint_list = ET.SubElement(jra, "joint_list")
    for joint_info in joints_to_analyze:
        joint = ET.SubElement(joint_list, "Joint")
        joint.set("name", joint_info['name'])
        ET.SubElement(joint, "express_in_frame").text = joint_info['express_in_frame']

    # 3. Write XML to file (pretty printed)
    rough_string = ET.tostring(root, 'utf-8')
    reparsed_xml = minidom.parseString(rough_string)
    pretty_xml_str = reparsed_xml.toprettyxml(indent="  ")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_xml_path), exist_ok=True)

    with open(output_xml_path, "w") as f:
        f.write(pretty_xml_str)

    print(f"✅ JointReaction.xml saved to: {output_xml_path}")

# --- Execute the XML generation ---
if __name__ == "__main__":
    create_joint_reaction_xml(MODEL_FILE_PATH, INPUT_MOTION_FILE_PATH, INPUT_FORCES_FILE_PATH, OUTPUT_XML_PATH, JOINTS_TO_ANALYZE)

    print("\nNext steps:")
    print("1. **CRITICAL:** Verify the generated `JointReaction.xml` file in a text editor.")
    print("   - Ensure `model_file`, `coordinates_file`, and `forces_file` paths are correct (only filenames if in the same folder as the setup file).")
    print("   - Confirm the `joint_list` names and `express_in_frame` settings are accurate for your model and analysis.")
    print("2. OpenSim GUI: Go to 'Tools' -> 'Analyze'.")
    print("3. Load the generated `JointReaction.xml` as the 'Setup File'.")
    print("4. Set the 'Model File', 'Coordinates File', and 'Forces File' paths in the Analyze Tool settings (they should auto-populate from the XML).")
    print("5. Run the Analyze Tool.")
    print("6. Results will be in the 'results_directory' (default is your current working directory), typically in a folder like 'JointReaction_JointReaction'.")

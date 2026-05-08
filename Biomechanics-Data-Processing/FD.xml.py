import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


# --- XML Generation Logic ---
def create_forward_dynamics_xml(model_path, controls_path, initial_states_path, output_xml_path, initial_time,
                                final_time):
    """
    Generates an OpenSim ForwardDynamics.xml setup file.

    Args:
        model_path (str): Path to the OpenSim model file.
        controls_path (str): Path to the input controls file (SO activations).
        initial_states_path (str): Path to the initial states file (IK results).
        output_xml_path (str): Path to save the output XML.
        initial_time (float): Start time of simulation.
        final_time (float): End time of simulation.
    """
    print(f"Generating ForwardDynamics.xml for model: {model_path}")
    print(f"  Controls from: {controls_path}")
    print(f"  Initial states from: {initial_states_path}")
    print(f"  Time range: {initial_time} to {final_time}")

    root = ET.Element("OpenSimDocument")
    root.set("Version", "40000")

    fd_tool = ET.SubElement(root, "ForwardTool")
    fd_tool.set("name", "ForwardDynamicsSimulation")

    # IMPORTANT: OpenSim expects only the filename if the file is in the same directory
    # as the XML, or a relative path. If files are in different directories,
    # you might need to adjust these to be just the filename, and ensure OpenSim
    # can find them (e.g., by placing them in the same folder as the XML or setting paths in OpenSim GUI).
    # For simplicity, we'll use full paths here, but be aware OpenSim might prefer relative.
    ET.SubElement(fd_tool, "model_file").text = model_path  # Using full path
    ET.SubElement(fd_tool, "replace_force_set").text = "false"
    ET.SubElement(fd_tool, "results_directory").text = os.path.dirname(
        output_xml_path)  # Save results in same dir as XML
    ET.SubElement(fd_tool, "output_precision").text = "20"
    ET.SubElement(fd_tool, "initial_time").text = str(initial_time)
    ET.SubElement(fd_tool, "final_time").text = str(final_time)

    # Input files for Forward Dynamics
    ET.SubElement(fd_tool, "states_file").text = initial_states_path  # Provides initial states
    ET.SubElement(fd_tool, "controls_file").text = controls_path  # Provides muscle excitations

    # External loads (if any, typically not for FD unless explicitly adding GRF)
    ET.SubElement(fd_tool, "load_external_loads").text = "false"
    ET.SubElement(fd_tool, "external_loads_file")

    # Integrator settings (common defaults)
    ET.SubElement(fd_tool, "integrator_accuracy").text = "1e-5"
    ET.SubElement(fd_tool, "maximum_integrator_step_size").text = "1.0"
    ET.SubElement(fd_tool, "minimum_integrator_step_size").text = "1e-8"
    ET.SubElement(fd_tool, "internal_steps_limit").text = "10000"

    # Write XML to file
    rough_string = ET.tostring(root, 'utf-8')
    reparsed_xml = minidom.parseString(rough_string)
    pretty_xml_str = reparsed_xml.toprettyxml(indent="  ")

    os.makedirs(os.path.dirname(output_xml_path), exist_ok=True)
    with open(output_xml_path, "w") as f:
        f.write(pretty_xml_str)

    print(f"✅ ForwardDynamics.xml saved to: {output_xml_path}")


# --- Execute the XML generation ---
if __name__ == "__main__":
    # --- Configuration for Strengthened Severe Case ---
    # Uncomment this block to generate XML for the strengthened severe case
    # Comment it out before running for the healthy case.

    # --- Configuration ---
    # 1. Path to your MODIFIED (strengthened) OpenSim model file for the severe case
    model_path = r"D:\uni\post stroke\0core\severe\model_scaled_strengthened_severe.osim"  # <--- Use the new strengthened model

    # 2. Path to your Static Optimization (SO) results file for the severe case
    controls_path = r"D:\uni\post stroke\0core\severe\results\model_scaled_StaticOptimization_force.sto"  # <--- Use severe case SO results (ensure this is the correct filename for SO output)

    # 3. Path to your Inverse Kinematics (IK) results file for the severe case (for initial states)
    initial_states_path = r"D:\uni\post stroke\0core\severe\results\5IK.mot"  # <--- Use severe case IK results

    # 4. Path to save the output ForwardDynamics.xml file for the severe case
    output_xml_path = r"D:\uni\post stroke\0core\severe\setup\ForwardDynamics_Strengthened_Severe.xml"  # <--- New name

    # 5. Time range for the simulation (Left Gait Cycle 1 for severe case)
    initial_time = 25.08
    final_time = 27.31

    create_forward_dynamics_xml(model_path,
                                controls_path,
                                initial_states_path,
                                output_xml_path,
                                initial_time,
                                final_time)

    print("\nInstructions:")
    print("1. **UNCOMMENT ONE BLOCK AT A TIME** above (either 'Strengthened Severe Case' or 'Healthy Case').")
    print("2. **ADJUST ALL PATHS** within the uncommented block to your exact file locations.")
    print("3. **Save** the script.")
    print("4. **Run** the script in PyCharm to generate the XML file for that case.")
    print("5. **Repeat** for the other case by commenting/uncommenting and adjusting paths.")
    print("\nAfter generating both XMLs, proceed to Phase 3 (Run Forward Dynamics in OpenSim GUI).")

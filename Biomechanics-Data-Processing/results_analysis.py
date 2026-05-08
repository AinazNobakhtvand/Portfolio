import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
# Path to your Joint Reaction Analysis results file (.sto)
# This file is typically found in a subfolder like 'JointReaction_JointReaction'
# within your OpenSim results directory.
JRA_RESULTS_FILE = r"D:\uni\post stroke\0core\severe\results\JRF\model_scaled_JointReaction_ReactionLoads.sto" # <--- CHANGE THIS

# List of specific columns you want to plot (e.g., forces in N, moments in Nm)
# These names come directly from the column headers in your JRA_RESULTS_FILE.
# I've updated these based on the "Available columns in .sto file" output you provided.
COLUMNS_TO_PLOT = [
    'hip_r_on_femur_r_in_ground_fx', 'hip_r_on_femur_r_in_ground_fy', 'hip_r_on_femur_r_in_ground_fz',
    'knee_r_on_tibia_r_in_ground_fx', 'knee_r_on_tibia_r_in_ground_fy', 'knee_r_on_tibia_r_in_ground_fz',
    'ankle_r_on_talus_r_in_ground_fx', 'ankle_r_on_talus_r_in_ground_fy', 'ankle_r_on_talus_r_in_ground_fz',
    'hip_l_on_femur_l_in_ground_fx', 'hip_l_on_femur_l_in_ground_fy', 'hip_l_on_femur_l_in_ground_fz',
    'knee_l_on_tibia_l_in_ground_fx', 'knee_l_on_tibia_l_in_ground_fy', 'knee_l_on_tibia_l_in_ground_fz',
    'ankle_l_on_talus_l_in_ground_fx', 'ankle_l_on_talus_l_in_ground_fy', 'ankle_l_on_talus_l_in_ground_fz',
    # You can add more columns here if you want to plot moments (e.g., '_mx', '_my', '_mz')
    # or other joints like 'subtalar_r_on_calcn_r_in_ground_fx', etc.
]

# --- NEW: Scaling Factor for Plotting ---
# If your JRA results are still too large (e.g., in Nmm instead of N),
# you can apply a scaling factor for plotting purposes only.
# If your forces are showing 80000 N instead of 800 N, set this to 1000.0.
# If the data itself is correct, set this to 1.0.
PLOT_SCALE_FACTOR = 10.0  # <--- ADJUST THIS if your JRA results are still too large


# --- Plotting Logic ---
def plot_jra_data(file_path, columns_to_plot, scale_factor=1.0):
    """
    Reads an OpenSim .sto file and plots specified columns, with optional scaling.

    Args:
        file_path (str): Path to the .sto file.
        columns_to_plot (list): List of column names to plot.
        scale_factor (float): Factor to divide the data by for plotting (e.g., 1000.0 if data is in mN or Nmm).
    """
    print(f"Attempting to plot data from: {file_path}")

    # 1. Read the .sto file
    try:
        # OpenSim .sto files have a header before the actual data.
        # We need to find the 'endheader' line to know where data starts.
        with open(file_path, 'r') as f:
            data_start_line = 0
            for i, line in enumerate(f):
                if 'endheader' in line:
                    data_start_line = i + 1
                    break

        # Read the data using pandas, skipping header lines
        df = pd.read_csv(file_path, sep='\t', skiprows=data_start_line, header=0)

        # The first column is always 'time'
        time = df['time']

        print(f"Successfully loaded .sto file. Data shape: {df.shape}")
        print(f"Available columns in .sto file: {list(df.columns)}")

    except FileNotFoundError:
        print(f"Error: .sto file not found at {file_path}")
        return
    except Exception as e:
        print(f"Error reading .sto file: {e}")
        print("Please ensure your .sto file is correctly formatted and tab-delimited.")
        return

    # 2. Prepare data for plotting
    plot_df = pd.DataFrame({'time': time})
    missing_columns = []

    for col in columns_to_plot:
        if col in df.columns:
            plot_df[col] = df[col] / scale_factor  # Apply scaling here
        else:
            missing_columns.append(col)
            print(f"Warning: Column '{col}' not found in the .sto file. Skipping.")

    if not missing_columns and len(columns_to_plot) == 0:
        print("No columns specified to plot or no valid columns found.")
        return

    if plot_df.shape[1] <= 1:  # Only 'time' column means no data to plot
        print("No valid data columns found to plot after filtering. Please check `COLUMNS_TO_PLOT`.")
        return

    # 3. Plotting
    sns.set_style("whitegrid")  # Optional: Use seaborn for nicer aesthetics
    plt.figure(figsize=(12, 8))  # Adjust figure size as needed

    for col in columns_to_plot:
        if col in plot_df.columns:  # Only plot columns that were successfully added
            plt.plot(plot_df['time'], plot_df[col], label=col)

    plt.xlabel("Time (s)", fontsize=12)

    # Adjust Y-label to reflect the scaling (e.g., "Joint Reaction Force (N)")
    if scale_factor == 1.0:
        plt.ylabel("Joint Reaction Force/Moment", fontsize=12)
    else:
        plt.ylabel(f"Joint Reaction Force/Moment", fontsize=12)  # Indicate scaling

    plt.title("Joint Reaction Analysis Results-severe case", fontsize=14)
    plt.legend(loc='best', bbox_to_anchor=(1.05, 1), borderaxespad=0.)  # Place legend outside plot
    plt.grid(True)
    plt.tight_layout()  # Adjust layout to prevent labels overlapping
    plt.show()

    print("Plotting complete.")


# --- Execute the plotting ---
if __name__ == "__main__":
    plot_jra_data(JRA_RESULTS_FILE, COLUMNS_TO_PLOT, scale_factor=PLOT_SCALE_FACTOR)

    print("\nNext steps:")
    print(
        "1. Review the generated plot. You might need to adjust `COLUMNS_TO_PLOT` to focus on specific joints or components (e.g., only FZ for vertical forces).")
    print(
        "2. **CRITICAL:** The `PLOT_SCALE_FACTOR` is a band-aid for visualization. The ideal solution is for your JRA `.sto` file to contain correct magnitudes already.")
    print(
        "   To achieve this, you MUST ensure that OpenSim's Inverse Dynamics (ID) is correctly processing your moment data.")
    print(
        "   - **Verify `BWA3_grf.mot`:** Open it in a text editor. Are the moment values (ground_fpX_moment_mX) in Nm (small values like 0.1, 10, 50) or still in Nmm (thousands)? If they are still Nmm, the `csv_to_grf_mot` script was not re-run or saved correctly.")
    print(
        "   - **Verify `BWA3_ExternalLoads.xml`:** Open it. Does it contain `<moment_expression>` tags for each force plate, referencing `ground_fpX_moment_mX`? It should look like this: `<moment_expression>ground_fp1_moment_mx ground_fp1_moment_my ground_fp1_moment_mz</moment_expression>`")
    print(
        "   - **Verify OpenSim ID Tool:** When you open the ID tool in OpenSim and load the `ExternalLoads.xml`, does it correctly show the moment columns being loaded? If you look at the ID output `.sto` file, are the joint moments (e.g., `hip_flexion_moment`) in realistic Nm values (tens/hundreds) or still very large? If they are large, the issue is with ID's input or setup.")
    print("3. Customize plot labels, colors, and styles using Matplotlib/Seaborn functions for presentation.")
    print("4. You can save the plot using `plt.savefig('my_jra_plot.png')` before `plt.show()`.")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
# Path to your Joint Reaction Analysis results file (.sto)
# This file is typically found in a subfolder like 'JointReaction_JointReaction'
# within your OpenSim results directory.
JRA_RESULTS_FILE = r"D:\uni\post stroke\0core\SUBJ75(healthy female)\results\JRF\model_scaled_JointReaction_ReactionLoads.sto"  # <--- CHANGE THIS

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


# --- Helper Function to read .sto files ---
def read_sto_file(file_path):
    """
    Reads an OpenSim .sto file.
    """
    try:
        with open(file_path, 'r') as f:
            data_start_line = 0
            for i, line in enumerate(f):
                if 'endheader' in line:
                    data_start_line = i + 1
                    break
        df = pd.read_csv(file_path, sep='\t', skiprows=data_start_line, header=0)
        return df
    except FileNotFoundError:
        print(f"Error: .sto file not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading .sto file: {e}")
        print("Please ensure your .sto file is correctly formatted and tab-delimited.")
        return


# --- Original Plotting Function (single plot) ---
def plot_jra_data(file_path, columns_to_plot, scale_factor=1.0):
    """
    Reads an OpenSim .sto file and plots specified columns, with optional scaling.

    Args:
        file_path (str): Path to the .sto file.
        columns_to_plot (list): List of column names to plot.
        scale_factor (float): Factor to divide the data by for plotting (e.g., 1000.0 if data is in mN or Nmm).
    """
    print(f"Attempting to plot data from: {file_path}")

    df = read_sto_file(file_path)
    if df is None:
        return

    time = df['time']
    print(f"Successfully loaded .sto file. Data shape: {df.shape}")
    print(f"Available columns in .sto file: {list(df.columns)}")

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

    sns.set_style("whitegrid")
    plt.figure(figsize=(12, 8))

    for col in columns_to_plot:
        if col in plot_df.columns:
            plt.plot(plot_df['time'], plot_df[col], label=col)

    plt.xlabel("Time (s)", fontsize=12)
    plt.ylabel(f"Joint Reaction Force/Moment", fontsize=12)  # Indicate scaling
    plt.title("Joint Reaction Analysis Results-mild", fontsize=14)
    plt.legend(loc='best', bbox_to_anchor=(1.05, 1), borderaxespad=0.)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    print("Plotting complete.")


# --- NEW Plotting Function (subplots) ---
def plot_jra_subsets(file_path, jra_groups_to_plot, scale_factor=1.0):
    """
    Reads an OpenSim .sto file and plots specified JRA component subsets in subplots.
    Ideal for comparing contralateral joints or specific force/moment components.

    Args:
        file_path (str): Path to the .sto file.
        jra_groups_to_plot (list of lists): Each inner list contains column names
                                            to be plotted on a single subplot.
                                            e.g., [['hip_r_on_femur_r_in_ground_fz', 'hip_l_on_femur_l_in_ground_fz']]
        scale_factor (float): Factor to divide the data by for plotting.
    """
    print(f"Attempting to plot JRA subsets from: {file_path}")

    df = read_sto_file(file_path)
    if df is None:
        return

    time = df['time']
    print(f"Successfully loaded .sto file. Data shape: {df.shape}")
    print(f"Available columns in .sto file: {list(df.columns)}")

    num_subplots = len(jra_groups_to_plot)
    if num_subplots == 0:
        print("No JRA groups specified for subplots. Exiting.")
        return

    fig, axes = plt.subplots(num_subplots, 1, figsize=(12, 3.5 * num_subplots), sharex=True)
    if num_subplots == 1:
        axes = [axes]  # Ensure axes is iterable even for a single subplot

    sns.set_style("whitegrid")

    for i, group_cols in enumerate(jra_groups_to_plot):
        ax = axes[i]
        valid_cols_in_group = []
        for col in group_cols:
            if col in df.columns:
                ax.plot(time, df[col] / scale_factor, label=col)  # Apply scaling here
                valid_cols_in_group.append(col)
            else:
                print(f"Warning: Column '{col}' not found for subplot {i + 1}. Skipping.")

        if valid_cols_in_group:
            ax.set_ylabel(f"Force/Moment", fontsize=9)  # Y-label for subplots
            ax.set_title(f"JRA: {', '.join(valid_cols_in_group)}", fontsize=10)
            ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0., fontsize=8)
            ax.axhline(0, color='black', linewidth=0.5)
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.tick_params(axis='both', which='major', labelsize=8)
        else:
            ax.set_visible(False)  # Hide empty subplot

    axes[-1].set_xlabel("Time (s)", fontsize=12)
    fig.suptitle("Joint Reaction Analysis Results (Subplots)", fontsize=14)
    plt.tight_layout(rect=[0, 0.03, 0.9, 0.95])  # Adjust rect to make space for suptitle and legend
    plt.show()
    print("Subplot plotting complete.")


# --- Execute the plotting ---
if __name__ == "__main__":
    # You can choose to run the single plot or the subplot function
    # Uncomment the function you want to run.

    # --- Option 1: Plot all selected JRA components on one graph (as before) ---
    # plot_jra_data(JRA_RESULTS_FILE, COLUMNS_TO_PLOT, scale_factor=PLOT_SCALE_FACTOR)

    # --- Option 2: Plot specific JRA components in subplots ---
    # Define groups for subplots. Each inner list is a separate subplot.
    # This is excellent for comparing contralateral components (e.g., right vs. left Fz)
    # or all components of a single joint.
    JRA_GROUPS_FOR_SUBPLOTS = [
        # Vertical Forces (FZ) - Contralateral Comparison
        ['hip_r_on_femur_r_in_ground_fz', 'hip_l_on_femur_l_in_ground_fz'],
        ['knee_r_on_tibia_r_in_ground_fz', 'knee_l_on_tibia_l_in_ground_fz'],
        ['ankle_r_on_talus_r_in_ground_fz', 'ankle_l_on_talus_l_in_ground_fz'],

        # Anterior-Posterior Forces (FX) - Contralateral Comparison
        ['hip_r_on_femur_r_in_ground_fx', 'hip_l_on_femur_l_in_ground_fx'],
        ['knee_r_on_tibia_r_in_ground_fx', 'knee_l_on_tibia_l_in_ground_fx'],
        ['ankle_r_on_talus_r_in_ground_fx', 'ankle_l_on_talus_l_in_ground_fx'],

        # Medial-Lateral Forces (FY) - Contralateral Comparison
        ['hip_r_on_femur_r_in_ground_fy', 'hip_l_on_femur_l_in_ground_fy'],
        ['knee_r_on_tibia_r_in_ground_fy', 'knee_l_on_tibia_l_in_ground_fy'],
        ['ankle_r_on_talus_r_in_ground_fy', 'ankle_l_on_talus_l_in_ground_fy'],

        # You can also group all XYZ for a single joint:
        # ['hip_r_on_femur_r_in_ground_fx', 'hip_r_on_femur_r_in_ground_fy', 'hip_r_on_femur_r_in_ground_fz'],
        # Add more groups as needed
    ]
    plot_jra_subsets(JRA_RESULTS_FILE, JRA_GROUPS_FOR_SUBPLOTS, scale_factor=PLOT_SCALE_FACTOR)

    print("\nNext steps:")
    print("1. Review the generated subplot. It should provide clearer comparisons.")
    print(
        "2. Customize `JRA_GROUPS_FOR_SUBPLOTS` to focus on the specific components and joints most relevant to your analysis.")
    print(
        "3. Remember to verify the `PLOT_SCALE_FACTOR` to ensure magnitudes are correct (1.0 if .sto is in N, 1000.0 if in mN).")
    print("4. Save the plot using `plt.savefig('my_jra_subplots.png')`.")

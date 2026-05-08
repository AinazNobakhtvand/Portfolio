import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
# Path to your Static Optimization results file (.sto)
# This file is typically named something like 'static_optimization_results.sto'
# or 'your_trial_StaticOptimization_activation.sto' / '_force.sto'
SO_RESULTS_FILE = r"D:\uni\post stroke\0core\molderate\results\model_scaled_StaticOptimization_force.sto"  # <--- CHANGE THIS

# List of specific muscle force columns you want to plot.
# You MUST get these exact names from your SO_RESULTS_FILE.
# Common naming conventions are 'muscle_name.force' or just 'muscle_name'.
# Examples: 'gasmed_r.force', 'vaslat_r.force', 'bifemlh_l.force'
# Or simply 'gasmed_r', 'vaslat_r', 'bifemlh_l' if the file contains forces directly.
MUSCLE_COLUMNS_TO_PLOT = [
    'glut_med1_r', 'glut_med2_r', 'glut_med3_r', 'glut_min1_r', 'glut_min2_r', 'glut_min3_r',
    'semimem_r', 'semiten_r', 'bifemlh_r', 'bifemsh_r', 'sar_r', 'add_long_r', 'add_brev_r',
    'add_mag1_r', 'add_mag2_r', 'add_mag3_r', 'tfl_r', 'pect_r', 'grac_r', 'glut_max1_r',
    'glut_max2_r', 'glut_max3_r', 'iliacus_r', 'psoas_r', 'quad_fem_r', 'gem_r', 'peri_r',
    'rect_fem_r', 'vas_med_r', 'vas_int_r', 'vas_lat_r', 'med_gas_r', 'lat_gas_r', 'soleus_r',
    'tib_post_r', 'flex_dig_r', 'flex_hal_r', 'tib_ant_r', 'per_brev_r', 'per_long_r',
    'per_tert_r', 'ext_dig_r', 'ext_hal_r',
    'glut_med1_l', 'glut_med2_l', 'glut_med3_l', 'glut_min1_l', 'glut_min2_l', 'glut_min3_l',
    'semimem_l', 'semiten_l', 'bifemlh_l', 'bifemsh_l', 'sar_l', 'add_long_l', 'add_brev_l',
    'add_mag1_l', 'add_mag2_l', 'add_mag3_l', 'tfl_l', 'pect_l', 'grac_l', 'glut_max1_l',
    'glut_max2_l', 'glut_max3_l', 'iliacus_l', 'psoas_l', 'quad_fem_l', 'gem_l', 'peri_l',
    'rect_fem_l', 'vas_med_l', 'vas_int_l', 'vas_lat_l', 'med_gas_l', 'lat_gas_l', 'soleus_l',
    'tib_post_l', 'flex_dig_l', 'flex_hal_l', 'tib_ant_l', 'per_brev_l', 'per_long_l',
    'per_tert_l', 'ext_dig_l', 'ext_hal_l',
    'ercspn_r', 'ercspn_l', 'intobl_r', 'intobl_l', 'extobl_r', 'extobl_l'
]

# --- Normalization Settings ---
# Choose normalization type: 'none', 'body_weight'
NORMALIZATION_TYPE = 'body_weight'  # <--- ADJUST THIS

# If NORMALIZATION_TYPE is 'body_weight', provide the subject's mass in kg.
SUBJECT_MASS_KG = 80.0  # <--- ADJUST THIS FOR YOUR SUBJECT


# --- Plotting Logic ---
def plot_muscle_force_data(file_path, columns_to_plot, normalization_type='none', subject_mass_kg=None):
    """
    Reads an OpenSim .sto file (Static Optimization results) and plots specified muscle force columns.

    Args:
        file_path (str): Path to the .sto file.
        columns_to_plot (list): List of column names (muscle forces) to plot.
        normalization_type (str): Type of normalization ('none', 'body_weight').
        subject_mass_kg (float): Subject's mass in kg, required for 'body_weight' normalization.
    """
    print(f"Attempting to plot muscle force data from: {file_path}")

    # 1. Read the .sto file
    try:
        with open(file_path, 'r') as f:
            data_start_line = 0
            for i, line in enumerate(f):
                if 'endheader' in line:
                    data_start_line = i + 1
                    break

        df = pd.read_csv(file_path, sep='\t', skiprows=data_start_line, header=0)
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

    # 2. Prepare data for plotting and apply normalization
    plot_df = pd.DataFrame({'time': time})
    missing_columns = []

    normalization_factor = 1.0
    y_label_suffix = " (N)"

    if normalization_type == 'body_weight':
        if subject_mass_kg is None or subject_mass_kg <= 0:
            print("Error: Subject mass (SUBJECT_MASS_KG) must be provided for body_weight normalization.")
            return
        normalization_factor = subject_mass_kg * 9.81  # Convert mass to body weight in Newtons
        y_label_suffix = " (%BW)"
        print(f"Normalizing by Body Weight ({subject_mass_kg} kg = {normalization_factor:.2f} N)")
    elif normalization_type == 'none':
        pass  # No normalization
    else:
        print(f"Warning: Unknown normalization type '{normalization_type}'. No normalization applied.")

    for col in columns_to_plot:
        if col in df.columns:
            plot_df[col] = df[col] / normalization_factor  # Apply normalization here
        else:
            missing_columns.append(col)
            print(f"Warning: Muscle force column '{col}' not found in the .sto file. Skipping.")

    if not missing_columns and len(columns_to_plot) == 0:
        print("No muscle force columns specified to plot or no valid columns found.")
        return

    if plot_df.shape[1] <= 1:  # Only 'time' column means no data to plot
        print("No valid muscle force columns found to plot after filtering. Please check `MUSCLE_COLUMNS_TO_PLOT`.")
        return

    # 3. Plotting
    sns.set_style("whitegrid")
    plt.figure(figsize=(14, 10))

    for col in columns_to_plot:
        if col in plot_df.columns:
            plt.plot(plot_df['time'], plot_df[col], label=col)

    plt.xlabel("Time (s)", fontsize=12)
    plt.ylabel(f"Muscle Force{y_label_suffix}", fontsize=12)
    plt.title("Muscle Forces from Static Optimization", fontsize=14)
    plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    print("Plotting complete.")


def plot_muscle_force_subsets(file_path, muscle_groups_to_plot, normalization_type='none', subject_mass_kg=None):
    """
    Reads an OpenSim .sto file and plots specified muscle force subsets in subplots.
    This is ideal for comparing contralateral muscles or specific muscle groups.

    Args:
        file_path (str): Path to the .sto file.
        muscle_groups_to_plot (list of lists): Each inner list contains column names
                                                to be plotted on a single subplot.
        normalization_type (str): Type of normalization ('none', 'body_weight').
        subject_mass_kg (float): Subject's mass in kg, required for 'body_weight' normalization.
    """
    print(f"Attempting to plot muscle force subsets from: {file_path}")

    # 1. Read the .sto file (same reading logic as before)
    try:
        with open(file_path, 'r') as f:
            data_start_line = 0
            for i, line in enumerate(f):
                if 'endheader' in line:
                    data_start_line = i + 1
                    break
        df = pd.read_csv(file_path, sep='\t', skiprows=data_start_line, header=0)
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

    # Determine normalization factor
    normalization_factor = 1.0
    y_label_suffix = " (N)"
    if normalization_type == 'body_weight':
        if subject_mass_kg is None or subject_mass_kg <= 0:
            print("Error: Subject mass (SUBJECT_MASS_KG) must be provided for body_weight normalization.")
            return
        normalization_factor = subject_mass_kg * 9.81
        y_label_suffix = " (%BW)"
        print(f"Normalizing by Body Weight ({subject_mass_kg} kg = {normalization_factor:.2f} N)")
    elif normalization_type == 'none':
        pass
    else:
        print(f"Warning: Unknown normalization type '{normalization_type}'. No normalization applied.")

    # Determine number of subplots
    num_subplots = len(muscle_groups_to_plot)
    if num_subplots == 0:
        print("No muscle groups specified for subplots. Exiting.")
        return

    # Create subplots
    fig, axes = plt.subplots(num_subplots, 1, figsize=(12, 4 * num_subplots), sharex=True)
    if num_subplots == 1:  # If only one subplot, axes is not an array
        axes = [axes]

    sns.set_style("whitegrid")

    for i, group_cols in enumerate(muscle_groups_to_plot):
        ax = axes[i]
        valid_cols_in_group = []
        for col in group_cols:
            if col in df.columns:
                ax.plot(time, df[col] / normalization_factor, label=col)  # Apply normalization here
                valid_cols_in_group.append(col)
            else:
                print(f"Warning: Column '{col}' not found for subplot {i + 1}. Skipping.")

        if valid_cols_in_group:
            ax.set_ylabel(f"Force{y_label_suffix}", fontsize=10)
            ax.set_title(f"Muscle Forces: {', '.join(valid_cols_in_group)}", fontsize=12)
            ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)
            ax.grid(True)
        else:
            ax.set_visible(False)  # Hide empty subplot

    # Set common labels
    axes[-1].set_xlabel("Time (s)", fontsize=12)
    fig.suptitle("Muscle Forces from Static Optimization (Subplots)", fontsize=14)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust rect to make space for suptitle

    plt.show()
    print("Subplot plotting complete.")


# --- Execute the plotting ---
if __name__ == "__main__":
    # You can choose to run the single plot or the subplot function
    # Uncomment the function you want to run.

    # --- Option 1: Plot all selected muscles on one graph (as before) ---
    # plot_muscle_force_data(SO_RESULTS_FILE, MUSCLE_COLUMNS_TO_PLOT,
    #                        normalization_type=NORMALIZATION_TYPE, subject_mass_kg=SUBJECT_MASS_KG)

    # --- Option 2: Plot specific muscle groups/pairs in subplots ---
    # Define groups for subplots. Each inner list is a separate subplot.
    # This is excellent for comparing contralateral muscles (e.g., right vs. left)
    # or specific functional groups.
    MUSCLE_GROUPS_FOR_SUBPLOTS = [
        # Hip Abductors (Contralateral Comparison)
        ['glut_med1_r', 'glut_med1_l'],
        ['glut_med2_r', 'glut_med2_l'],
        ['glut_med3_r', 'glut_med3_l'],
        # Knee Extensors (Contralateral Comparison)
        ['rect_fem_r', 'rect_fem_l'],
        ['vas_lat_r', 'vas_lat_l'],
        ['vas_med_r', 'vas_med_l'],
        # Ankle Plantarflexors (Contralateral Comparison)
        ['soleus_r', 'soleus_l'],
        ['med_gas_r', 'med_gas_l'],
        ['lat_gas_r', 'lat_gas_l'],
        # Ankle Dorsiflexors (Contralateral Comparison)
        ['tib_ant_r', 'tib_ant_l'],
        # Hamstrings (Contralateral Comparison)
        ['bifemlh_r', 'bifemlh_l'],
        ['semimem_r', 'semimem_l'],
        # Trunk Muscles (if relevant for comparison)
        ['ercspn_r', 'ercspn_l'],
        # Add more groups as needed, e.g., all hip flexors: ['iliacus_r', 'psoas_r', 'iliacus_l', 'psoas_l']
    ]
    plot_muscle_force_subsets(SO_RESULTS_FILE, MUSCLE_GROUPS_FOR_SUBPLOTS,
                              normalization_type=NORMALIZATION_TYPE, subject_mass_kg=SUBJECT_MASS_KG)

    print("\nFinal Next steps:")
    print("1. **Review the generated plots.** The subplot version should offer much clearer insights.")
    print(
        "2. **Customize `MUSCLE_GROUPS_FOR_SUBPLOTS`** to focus on the specific muscles most relevant to your research question or the subject's impairment.")
    print("3. For quantitative comparison, consider extracting peak forces and timing of activation from these plots.")
    print("4. You can save plots using `plt.savefig('my_muscle_forces_subplots.png')` before `plt.show()`.")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
# Path to your Static Optimization results file (.sto)
# This file is typically named something like 'static_optimization_results.sto'
# or 'your_trial_StaticOptimization_activation.sto' / '_force.sto'
SO_RESULTS_FILE = r"D:\uni\post stroke\0core\mild\TVC15\result1000\model_scaled_StaticOptimization_force.sto"  # <--- CHANGE THIS

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


# --- Plotting Logic ---
def plot_muscle_force_data(file_path, columns_to_plot):
    """
    Reads an OpenSim .sto file (Static Optimization results) and plots specified muscle force columns.

    Args:
        file_path (str): Path to the .sto file.
        columns_to_plot (list): List of column names (muscle forces) to plot.
    """
    print(f"Attempting to plot muscle force data from: {file_path}")

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
        print(f"Available columns in .sto file: {list(df.columns)}")  # Print all columns for user to see

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
            plot_df[col] = df[col]
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
    sns.set_style("whitegrid")  # Optional: Use seaborn for nicer aesthetics
    plt.figure(figsize=(18, 14))  # Adjust figure size as needed

    for col in columns_to_plot:
        if col in plot_df.columns:  # Only plot columns that were successfully added
            plt.plot(plot_df['time'], plot_df[col], label=col)

    plt.xlabel("Time (s)", fontsize=12)
    plt.ylabel("Muscle Force (N)", fontsize=12)  # Assuming forces are in Newtons
    plt.title("Muscle Forces from Static Optimization", fontsize=14)
    plt.legend(loc='best', bbox_to_anchor=(1.05, 1), borderaxespad=0.)  # Place legend outside plot
    plt.grid(True)
    plt.tight_layout()  # Adjust layout to prevent labels overlapping
    plt.show()

    print("Plotting complete.")


# --- Execute the plotting ---
if __name__ == "__main__":
    plot_muscle_force_data(SO_RESULTS_FILE, MUSCLE_COLUMNS_TO_PLOT)

    print("\nNext steps:")
    print(
        "1. **CRITICAL:** Open your Static Optimization results `.sto` file in a text editor (or check the 'Available columns' output above).")
    print("   - Identify the exact column names for the muscle forces you are interested in.")
    print("   - Update the `MUSCLE_COLUMNS_TO_PLOT` list in the script with these exact names.")
    print("2. Review the generated plot to analyze muscle activation patterns and magnitudes.")
    print("   - Look for peak forces, timing of activation, and differences between limbs (paretic vs. non-paretic).")
    print("3. Customize plot labels, colors, and styles using Matplotlib/Seaborn functions for presentation.")
    print("4. You can save the plot using `plt.savefig('my_muscle_forces_plot.png')` before `plt.show()`.")

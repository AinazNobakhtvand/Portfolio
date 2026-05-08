import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
# 1. Paths to your data files and their specific gait cycle times
#    For healthy group, provide a list of dictionaries. Each dict should have:
#    'file_path': Path to the .mot/.sto file
#    'initial_time': Start time of the gait cycle for this subject (manual override). Set to None to use gait_events_file.
#    'final_time': End time of the gait cycle for this subject (manual override). Set to None to use gait_events_file.
#    'gait_events_file': Path to this subject's specific gait events CSV (used if initial/final_time are None).
HEALTHY_GROUP_DATA_FILES = [
    {
        'file_path': r"D:\uni\post stroke\0core\healthy body\results\healthyIK.mot",
        'initial_time': 1.64,  # <--- Manual initial time for this healthy subject
        'final_time': 2.66,  # <--- Manual final time for this healthy subject
        'gait_events_file': r"D:\uni\post stroke\0core\healthy body\SUBJ33 (2).csv"
        # <--- Subject-specific events file
    },
    # Add more healthy subject IK files here if you have them for group average
    # {
    #     'file_path': r"path\to\healthy_subject2_ik.mot",
    #     'initial_time': None, # Set to None to use gait_events_file for this subject
    #     'final_time': None,
    #     'gait_events_file': r"path\to\healthy_subject2_events.csv"
    # },
]

# For individual subjects, provide a dictionary with labels and file paths/times.
# 'file_path': Path to the .mot/.sto file
# 'initial_time': Manual initial time for this subject's gait cycle. Set to None to use gait_events_file.
# 'final_time': Manual final time for this subject's gait cycle. Set to None to use gait_events_file.
# 'gait_events_file': Path to this subject's specific gait events CSV (used if initial/final_time are None).
INDIVIDUAL_SUBJECT_DATA_FILES = {
    'Mild Case': {
        'file_path': r"D:\uni\post stroke\0core\mild\TVC15\result1000\15IK1000.mot",
        'initial_time': 5.432,  # <--- Manual initial time for Mild Case
        'final_time': 6.68,  # <--- Manual final time for Mild Case
        'gait_events_file': r"D:\uni\post stroke\0core\mild\TVC15\preprocessing\grf.mot\BWA3all.csv"
        # <--- Mild Case events file
    },
    'Moderate Case': {
        'file_path': r"D:\uni\post stroke\0core\molderate\results\IK32.mot",
        'initial_time': 2.95,  # <--- Manual initial time for Moderate Case (from your FD XML)
        'final_time': 4.32,  # <--- Manual final time for Moderate Case (from your FD XML)
        'gait_events_file': r"D:\uni\post stroke\0core\molderate\grf\BWA 06.csv"
        # <--- Moderate Case events file (adjust path)
    },
    # Add more individual subjects if needed
}

# 2. Global fallback gait events file (only used if subject-specific gait_events_file is also None)
#    You can set this to None if you always provide subject-specific event files or manual times.
GLOBAL_FALLBACK_GAIT_EVENTS_FILE = None  # <--- No longer the primary source

# 3. Define the joint coordinates to plot in each subplot
#    Use the EXACT column names from your IK .mot/.sto files.
#    Provide a list of dictionaries, where each dict defines a subplot.
#    'coord_name_r': Right limb coordinate name
#    'coord_name_l': Left limb coordinate name
#    'title': Title for the subplot
#    'ylabel': Y-axis label (e.g., 'Angle (deg)' or 'Angle (rad)')
#    'unit_conversion_factor': 1.0 for degrees, np.rad2deg(1.0) for radians if you want degrees on plot
#    'affected_side_suffix': The suffix for the affected limb (e.g., '_l' if left is paretic)
#                            This helps in coloring individual subject lines.
JOINT_COORDINATES_TO_PLOT = [
    {
        'coord_name_r': 'hip_flexion_r',
        'coord_name_l': 'hip_flexion_l',
        'title': 'Hip Flexion/Extension',
        'ylabel': 'Angle (deg)',
        'unit_conversion_factor': 1.0,  # If your IK is already in degrees for plotting
        'affected_side_suffix': '_l'  # Assuming left is paretic
    },
    {
        'coord_name_r': 'hip_adduction_r',
        'coord_name_l': 'hip_adduction_l',
        'title': 'Hip Ab/Adduction',
        'ylabel': 'Angle (deg)',
        'unit_conversion_factor': 1.0,
        'affected_side_suffix': '_l'
    },
    {
        'coord_name_r': 'knee_angle_r',
        'coord_name_l': 'knee_angle_l',
        'title': 'Knee Flexion/Extension',
        'ylabel': 'Angle (deg)',
        'unit_conversion_factor': 1.0,
        'affected_side_suffix': '_l'
    },
    {
        'coord_name_r': 'ankle_angle_r',
        'coord_name_l': 'ankle_angle_l',
        'title': 'Ankle Dorsi/Plantar Flexion',
        'ylabel': 'Angle (deg)',
        'unit_conversion_factor': 1.0,
        'affected_side_suffix': '_l'
    },
    # Add more joints as needed (e.g., pelvis_tilt, pelvis_list, etc.)
]

# --- Plotting Settings ---
# Event names and their colors for vertical lines.
# You'll need to calculate their % gait cycle if you want to plot them.
GAIT_CYCLE_EVENTS_PERCENT = {
    'Initial Contact': 0,
    'Toe Off': 60,  # Example, you'd calculate this from your event data
    'Opposite Foot Strike': 50,  # Example
}


# --- Helper Functions ---
def read_sto_mot_file(file_path):
    """Reads OpenSim .sto or .mot files."""
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
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def normalize_gait_cycle(df, initial_time, final_time):
    """Normalizes time to 0-100% gait cycle."""
    df_norm = df.copy()
    # Ensure time column is within the specified cycle
    df_cycle = df_norm[(df_norm['time'] >= initial_time) & (df_norm['time'] <= final_time)]

    if df_cycle.empty:
        print(f"Warning: No data found within specified gait cycle [{initial_time}, {final_time}].")
        return pd.DataFrame()  # Return empty DataFrame

    df_cycle['time_norm'] = ((df_cycle['time'] - initial_time) / (final_time - initial_time)) * 100
    return df_cycle


def get_gait_cycle_times_from_file(events_file, foot_strike_event='Left_Foot Strike', cycle_index=0):
    """
    Extracts initial and final time for a specific gait cycle from an events CSV.
    Assumes events CSV has event names in first column and times in subsequent columns.
    """
    if events_file is None or not os.path.exists(events_file):
        print(
            f"Warning: Gait events file not provided or not found at '{events_file}'. Cannot extract gait cycle times from file.")
        return None, None
    try:
        df_events = pd.read_csv(events_file, header=None)
        # Find the row for the specified foot strike event
        strike_row = df_events[df_events.iloc[:, 0] == foot_strike_event]
        if strike_row.empty:
            print(f"Error: Event '{foot_strike_event}' not found in events file '{events_file}'.")
            return None, None

        # Get the times for this event
        strike_times = strike_row.iloc[0, 1:].dropna().astype(float).values

        if cycle_index + 1 >= len(strike_times):
            print(
                f"Error: Not enough '{foot_strike_event}' events for cycle_index {cycle_index} in file '{events_file}'.")
            return None, None

        initial_time = strike_times[cycle_index]
        final_time = strike_times[cycle_index + 1]
        return initial_time, final_time
    except Exception as e:
        print(f"Error reading gait events file '{events_file}': {e}")
        return None, None


# --- Main Plotting Function ---
def plot_gait_kinematics_comparison():
    sns.set_style("whitegrid")

    # Determine the number of rows and columns for subplots
    num_rows = len(JOINT_COORDINATES_TO_PLOT)
    num_cols = len(INDIVIDUAL_SUBJECT_DATA_FILES) + 1  # For healthy group + individual subjects

    fig, axes = plt.subplots(num_rows, num_cols, figsize=(4 * num_cols, 3 * num_rows), sharex=True, sharey='row')

    # Adjust axes if only one row or one column
    if num_rows == 1 and num_cols == 1:
        axes = np.array([[axes]])
    elif num_rows == 1:
        axes = np.array([axes])
    elif num_cols == 1:
        axes = np.array([[ax] for ax in axes])

    # --- Process Healthy Group Data ---
    healthy_dfs_norm = []
    for h_config in HEALTHY_GROUP_DATA_FILES:
        df_h = read_sto_mot_file(h_config['file_path'])
        if df_h is not None:
            # Use manual times if provided, else try from subject-specific events file, else global fallback
            h_initial_time = h_config.get('initial_time')
            h_final_time = h_config.get('final_time')

            if h_initial_time is None or h_final_time is None:
                subject_events_file = h_config.get('gait_events_file')
                h_initial_time, h_final_time = get_gait_cycle_times_from_file(subject_events_file, 'Left_Foot Strike',
                                                                              0)
                if h_initial_time is None:  # Fallback to global events file if subject-specific fails
                    h_initial_time, h_final_time = get_gait_cycle_times_from_file(GLOBAL_FALLBACK_GAIT_EVENTS_FILE,
                                                                                  'Left_Foot Strike', 0)
                    if h_initial_time is None:  # Final fallback: use full trial
                        h_initial_time, h_final_time = df_h['time'].iloc[0], df_h['time'].iloc[-1]
                        print(
                            f"Warning: Using full trial for healthy subject {h_config['file_path']} due to missing event data or manual times.")

            df_h_norm = normalize_gait_cycle(df_h, h_initial_time, h_final_time)
            if not df_h_norm.empty:
                healthy_dfs_norm.append(df_h_norm)

    if not healthy_dfs_norm:
        print("Error: No healthy group data loaded. Cannot plot normative range.")
        return

    # Calculate mean and std dev for healthy group
    time_points = np.linspace(0, 100, 101)  # Common 0-100% gait cycle base
    healthy_interpolated_data = {}

    for df_h_norm in healthy_dfs_norm:
        for col_info in JOINT_COORDINATES_TO_PLOT:
            for suffix in ['_r', '_l']:
                coord_name = col_info[f'coord_name{suffix}']
                if coord_name in df_h_norm.columns:
                    if coord_name not in healthy_interpolated_data:
                        healthy_interpolated_data[coord_name] = []

                    # Interpolate to common time points
                    interp_func = np.interp(time_points, df_h_norm['time_norm'],
                                            df_h_norm[coord_name] * col_info['unit_conversion_factor'])
                    healthy_interpolated_data[coord_name].append(interp_func)

    healthy_mean = {k: np.mean(v, axis=0) for k, v in healthy_interpolated_data.items()}
    healthy_std = {k: np.std(v, axis=0) for k, v in healthy_interpolated_data.items()}

    # --- Plotting ---
    for row_idx, joint_info in enumerate(JOINT_COORDINATES_TO_PLOT):
        coord_name_r = joint_info['coord_name_r']
        coord_name_l = joint_info['coord_name_l']
        title = joint_info['title']
        ylabel = joint_info['ylabel']
        unit_conv = joint_info['unit_conversion_factor']
        affected_side_suffix = joint_info['affected_side_suffix']

        # Plot Healthy Group (Column 0)
        ax_healthy = axes[row_idx, 0]
        ax_healthy.set_title(f'Healthy {title}', fontsize=10)
        ax_healthy.set_ylabel(ylabel, fontsize=9)

        if coord_name_r in healthy_mean and coord_name_r in healthy_std:
            ax_healthy.plot(time_points, healthy_mean[coord_name_r], color='gray', label='Healthy Mean')
            ax_healthy.fill_between(time_points, healthy_mean[coord_name_r] - healthy_std[coord_name_r],
                                    healthy_mean[coord_name_r] + healthy_std[coord_name_r],
                                    color='lightgray', alpha=0.5, label='Healthy Std Dev')
        if coord_name_l in healthy_mean and coord_name_l in healthy_std:
            ax_healthy.plot(time_points, healthy_mean[coord_name_l], color='darkgray', linestyle='--',
                            label='Healthy Mean L')  # Optional: distinguish left

        ax_healthy.axhline(0, color='black', linewidth=0.5)  # Zero line
        ax_healthy.grid(True, linestyle='--', alpha=0.6)
        ax_healthy.tick_params(axis='both', which='major', labelsize=8)

        # Add vertical lines for events for healthy group (e.g., foot strike/off)
        for event_name, event_percent in GAIT_CYCLE_EVENTS_PERCENT.items():
            ax_healthy.axvline(x=event_percent, color=GAIT_CYCLE_EVENTS.get(event_name, 'gray'), linestyle='-',
                               linewidth=1)

        # Plot Individual Subjects (Columns 1 onwards)
        col_idx = 1
        for sub_label, sub_config in INDIVIDUAL_SUBJECT_DATA_FILES.items():
            ax_sub = axes[row_idx, col_idx]
            ax_sub.set_title(f'{sub_label} {title}', fontsize=10)

            df_sub = read_sto_mot_file(sub_config['file_path'])
            if df_sub is not None:
                # Use manual times if provided, else try from subject-specific events file, else global fallback
                sub_initial_time = sub_config.get('initial_time')
                sub_final_time = sub_config.get('final_time')

                if sub_initial_time is None or sub_final_time is None:
                    subject_events_file = sub_config.get('gait_events_file')
                    sub_initial_time, sub_final_time = get_gait_cycle_times_from_file(subject_events_file,
                                                                                      'Left_Foot Strike', 0)
                    if sub_initial_time is None:  # Fallback to global events file if subject-specific fails
                        sub_initial_time, sub_final_time = get_gait_cycle_times_from_file(
                            GLOBAL_FALLBACK_GAIT_EVENTS_FILE, 'Left_Foot Strike', 0)
                        if sub_initial_time is None:  # Final fallback: use full trial
                            sub_initial_time, sub_final_time = df_sub['time'].iloc[0], df_sub['time'].iloc[-1]
                            print(
                                f"Warning: Using full trial for {sub_label} due to missing event data or manual times.")

                df_sub_norm = normalize_gait_cycle(df_sub, sub_initial_time, sub_final_time)

                # Plot healthy mean/std as background for individual subjects
                if coord_name_r in healthy_mean and coord_name_r in healthy_std:
                    ax_sub.fill_between(time_points, healthy_mean[coord_name_r] - healthy_std[coord_name_r],
                                        healthy_mean[coord_name_r] + healthy_std[coord_name_r],
                                        color='lightgray', alpha=0.5)

                # Plot individual subject data
                if coord_name_r in df_sub_norm.columns:
                    color_r = 'red' if affected_side_suffix == '_l' else 'green'  # Right is green if left is affected
                    ax_sub.plot(df_sub_norm['time_norm'], df_sub_norm[coord_name_r] * unit_conv, color=color_r,
                                label=f'{sub_label} R')
                if coord_name_l in df_sub_norm.columns:
                    color_l = 'green' if affected_side_suffix == '_l' else 'red'  # Left is red if left is affected
                    ax_sub.plot(df_sub_norm['time_norm'], df_sub_norm[coord_name_l] * unit_conv, color=color_l,
                                label=f'{sub_label} L')

                # Add vertical lines for events (e.g., foot strike/off)
                for event_name, event_percent in GAIT_CYCLE_EVENTS_PERCENT.items():
                    ax_sub.axvline(x=event_percent, color=GAIT_CYCLE_EVENTS.get(event_name, 'gray'), linestyle='-',
                                   linewidth=1)

            ax_sub.axhline(0, color='black', linewidth=0.5)
            ax_sub.grid(True, linestyle='--', alpha=0.6)
            ax_sub.tick_params(axis='both', which='major', labelsize=8)
            col_idx += 1

    # Set common X-axis label for the bottom row
    for col_idx in range(num_cols):
        axes[-1, col_idx].set_xlabel('% Gait cycle', fontsize=10)

    fig.suptitle("Gait Kinematics Comparison", fontsize=16)

    # Create a single legend for the entire figure
    handles, labels = [], []
    # Add healthy group legend items
    if HEALTHY_GROUP_DATA_FILES:
        handles.append(plt.Line2D([0], [0], color='gray', lw=2))
        labels.append('Healthy Mean R')
        handles.append(plt.Line2D([0], [0], color='darkgray', lw=2, linestyle='--'))
        labels.append('Healthy Mean L')
        handles.append(plt.FillBetween([], [], [], color='lightgray', alpha=0.5))
        labels.append('Healthy Std Dev')

    # Add individual subject legend items (assuming consistent colors)
    if INDIVIDUAL_SUBJECT_DATA_FILES:
        first_sub_label = list(INDIVIDUAL_SUBJECT_DATA_FILES.keys())[0]
        # Assuming affected_side_suffix is consistent across all plotted joints
        if JOINT_COORDINATES_TO_PLOT and JOINT_COORDINATES_TO_PLOT[0]['affected_side_suffix'] == '_l':
            handles.append(plt.Line2D([0], [0], color='red', lw=2))
            labels.append(f'{first_sub_label} R (Non-Paretic)')
            handles.append(plt.Line2D([0], [0], color='green', lw=2))
            labels.append(f'{first_sub_label} L (Paretic)')
        else:  # Assuming affected_side_suffix is _r or not explicitly set
            handles.append(plt.Line2D([0], [0], color='green', lw=2))
            labels.append(f'{first_sub_label} R (Paretic)')
            handles.append(plt.Line2D([0], [0], color='red', lw=2))
            labels.append(f'{first_sub_label} L (Non-Paretic)')

    # Add event legend items
    for event_name, color in GAIT_CYCLE_EVENTS.items():
        handles.append(plt.Line2D([0], [0], color=color, linestyle='-', lw=1))
        labels.append(event_name)

    fig.legend(handles, labels, loc='upper right', bbox_to_anchor=(1.0, 1.0), ncol=1, fontsize=8)

    plt.tight_layout(rect=[0, 0.03, 0.9, 0.95])  # Adjust rect to make space for suptitle and legend
    plt.show()


# --- Execute Plotting ---
if __name__ == "__main__":
    plot_gait_kinematics_comparison()

    print("\nNext steps:")
    print(
        "1. **CRITICAL:** Adjust `HEALTHY_GROUP_DATA_FILES`, `INDIVIDUAL_SUBJECT_DATA_FILES`, and `GLOBAL_FALLBACK_GAIT_EVENTS_FILE` paths.")
    print(
        "   - For each subject, provide `initial_time` and `final_time` for their specific gait cycle, OR set them to `None` to use their `gait_events_file`.")
    print(
        "2. **CRITICAL:** Verify and adjust `JOINT_COORDINATES_TO_PLOT` for exact coordinate names, units, and affected side suffix.")
    print(
        "   - Ensure `unit_conversion_factor` is correct (1.0 if IK is already in degrees for plotting, np.rad2deg(1.0) if IK is in radians but you want degrees).")
    print(
        "3. **CRITICAL:** Adjust `GAIT_CYCLE_EVENTS_PERCENT` with the correct percentage values for your gait events (e.g., from your event data).")
    print("4. Customize colors, line styles, and add legends as needed for clarity.")
    print("5. Save the plot using `plt.savefig('gait_kinematics_comparison.png')`.")

import pandas as pd
import numpy as np
import os

# --- Configuration for your CSV file structure ---
# IMPORTANT: You MUST adjust these based on your BWA3.csv file!
# Open your BWA3.csv in a plain text editor (like Notepad++, VS Code).

# The 0-indexed row number where your actual column headers (e.g., 'Time', 'Fx1', 'Fy1'...) are located.
# For example, if the headers are on the 13th line of the file (when viewed in a text editor, 1-indexed),
# then this value should be 12 (0-indexed).
# If your CSV has a line like "Time,Fx1,Fy1,..." at, say, line 10 (1-indexed), then set this to 9.
CSV_HEADER_ROW_INDEX = 9  # <--- ADJUSTED BASED ON YOUR INPUT!

# The number of initial rows (0-indexed up to, but not including, this number)
# that contain descriptive metadata/comments you want to include in the .mot header.
# This should typically be the same as CSV_HEADER_ROW_INDEX, as all lines before the header are comments.
CSV_METADATA_END_ROW_INDEX = 9  # <--- ADJUSTED BASED ON YOUR INPUT!

# --- Force Plate Configuration (CRITICAL for CoP Calculation) ---
# You MUST provide the global origin (x, y, z) for each force plate in meters.
# This information is typically found in your original .C3d file parameters or motion capture system setup.
# ADJUSTED FOR 4 FORCE PLATES. YOU MUST REPLACE THESE WITH YOUR ACTUAL VALUES.
# Assuming Z is the vertical axis.
FORCE_PLATE_ORIGINS_M = [
    [0.0, 0.0, 0.05],  # Origin for Force Plate 1
    [1.0, 0.0, 0.05],  # Origin for Force Plate 2
    [2.0, 0.0, 0.05],  # Origin for Force Plate 3
    [3.0, 0.0, 0.05],  # Origin for Force Plate 4
]
# Threshold for vertical force (Fz) below which CoP will be set to NaN (no contact)
FZ_THRESHOLD_N = 10.0  # Newtons

# --- NEW: Force Plate Column Mapping (CRITICAL for Generic Headers) ---
# This maps the generic column names from your CSV (e.g., 'N', 'N.1', 'Nmm')
# to the specific Fx, Fy, Fz, Mx, My, Mz for EACH force plate.
# You MUST adjust this based on the actual order and meaning of columns in your CSV.
# The order here must match the order in FORCE_PLATE_ORIGINS_M.
# ADJUSTED FOR 4 FORCE PLATES based on your provided column names.
FORCE_PLATE_COLUMN_MAP = [
    # Force Plate 1
    {'Fx': 'N', 'Fy': 'N.1', 'Fz': 'N.2', 'Mx': 'Nmm', 'My': 'Nmm.1', 'Mz': 'Nmm.2'},
    # Force Plate 2
    {'Fx': 'N.3', 'Fy': 'N.4', 'Fz': 'N.5', 'Mx': 'Nmm.3', 'My': 'Nmm.4', 'Mz': 'Nmm.5'},
    # Force Plate 3
    {'Fx': 'N.6', 'Fy': 'N.7', 'Fz': 'N.8', 'Mx': 'Nmm.6', 'My': 'Nmm.7', 'Mz': 'Nmm.8'},
    # Force Plate 4
    {'Fx': 'N.9', 'Fy': 'N.10', 'Fz': 'N.11', 'Mx': 'Nmm.9', 'My': 'Nmm.10', 'Mz': 'Nmm.11'},
]


# Note: The 'V' columns ('V', 'V.1', ..., 'V.17') found in your CSV output are likely
# raw analog voltages and are NOT included in this mapping, as they are not forces/moments.
# If your data source documentation indicates these 'V' columns *are* force/moment data,
# then your CSV's header is mislabeled, and you'd need to adjust this map accordingly.

def calculate_cop(F, M, fp_origin):
    """
    Calculates Center of Pressure (CoP) from forces (F) and moments (M)
    about the force plate origin.

    Args:
        F (np.array): Nx3 array of forces (Fx, Fy, Fz) in Newtons.
        M (np.array): Nx3 array of moments (Mx, My, Mz) in Newton-meters.
        fp_origin (list): [Ox, Oy, Oz] origin of the force plate in meters.

    Returns:
        np.array: Nx3 array of CoP (Px, Py, Pz) in meters.
    """
    Px = np.zeros(F.shape[0])
    Py = np.zeros(F.shape[0])
    Pz = np.full(F.shape[0], fp_origin[2])  # CoP Z is usually constant at plate height

    # Avoid division by zero: only calculate CoP where Fz is above threshold
    non_zero_fzs = np.abs(F[:, 2]) > FZ_THRESHOLD_N

    if np.any(non_zero_fzs):
        # Common CoP equations (assuming Z is vertical, moments about origin)
        # Px = (-My + Fz * Ox) / Fz
        # Py = (Mx + Fz * Oy) / Fz
        # Note: Sign conventions for moments (Mx, My) can vary.
        # If your CoP values look inverted, try changing the signs of M[:,0] or M[:,1]

        Px[non_zero_fzs] = (-M[non_zero_fzs, 1] + F[non_zero_fzs, 2] * fp_origin[0]) / F[non_zero_fzs, 2]
        Py[non_zero_fzs] = (M[non_zero_fzs, 0] + F[non_zero_fzs, 2] * fp_origin[1]) / F[non_zero_fzs, 2]

    # Set CoP to NaN where Fz is below threshold (no contact)
    Px[~non_zero_fzs] = np.nan
    Py[~non_zero_fzs] = np.nan
    Pz[~non_zero_fzs] = np.nan  # Or can keep at fp_origin[2] if preferred

    return np.column_stack((Px, Py, Pz))


def csv_to_grf_mot(csv_path, output_path, sampling_frequency):
    """
    Converts a CSV file containing raw force plate data (Fx,Fy,Fz,Mx,My,Mz)
    into an OpenSim-compatible GRF .mot file. Automatically detects columns
    and includes CSV header info.

    Args:
        csv_path (str): Path to the input CSV file.
        output_path (str): Path to save the output .mot file.
        sampling_frequency (float): The sampling frequency of the force plate data in Hz.
    """
    print(f"Starting conversion for: {csv_path}")

    # 1. Read initial metadata/comments from CSV
    mot_header_comments = []
    try:
        with open(csv_path, 'r') as f:
            for i, line in enumerate(f):
                if i < CSV_METADATA_END_ROW_INDEX:
                    mot_header_comments.append(line.strip())
                else:
                    break
    except Exception as e:
        print(f"Warning: Could not read CSV metadata. Error: {e}")

    # 2. Read the CSV file, dynamically setting the header row
    try:
        # header=CSV_HEADER_ROW_INDEX tells pandas which row (0-indexed) contains the column names.
        # skiprows is no longer needed for skipping rows *before* the header, as header handles it.
        df = pd.read_csv(csv_path, header=CSV_HEADER_ROW_INDEX)
        print(f"CSV columns found: {list(df.columns)}")  # Debugging: show all columns

        # --- NEW CRITICAL CHECK: Warn if headers look like numbers ---
        # This checks if the first few columns (or all) look like numbers,
        # which indicates the header index is wrong.
        if all(is_numeric_like(col) for col in df.columns[:min(5, len(df.columns))]) or \
                any(not col.strip() for col in df.columns):  # Also check for empty column names
            print("\n" + "=" * 80)
            print("CRITICAL ERROR: The detected CSV column headers appear to be numeric data values or are empty.")
            print("This strongly indicates `CSV_HEADER_ROW_INDEX` is set too low and is reading data as headers.")
            print(
                "Please open your CSV file in a plain text editor and adjust `CSV_HEADER_ROW_INDEX` to the correct row number for your column titles.")
            print("The script will now stop. Correct the index and run again.")
            print("=" * 80 + "\n")
            return  # Stop execution as data parsing will be incorrect
        # --- END NEW CRITICAL CHECK ---

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
        return
    except Exception as e:
        print(f"Error reading CSV file with header at row {CSV_HEADER_ROW_INDEX}: {e}")
        print("Please check your CSV_HEADER_ROW_INDEX and CSV_METADATA_END_ROW_INDEX settings.")
        return

    # Assume the first column is always time, and the rest are data columns
    # This is a common convention for motion capture data exports.
    time_vector = df.iloc[:, 0].values.astype(float)

    # --- NEW: Select only the force/moment columns based on FORCE_PLATE_COLUMN_MAP ---
    # Flatten the FORCE_PLATE_COLUMN_MAP to get a list of all relevant data column names
    data_column_names = []
    for fp_map in FORCE_PLATE_COLUMN_MAP:
        data_column_names.extend([fp_map['Fx'], fp_map['Fy'], fp_map['Fz'],
                                  fp_map['Mx'], fp_map['My'], fp_map['Mz']])

    # Select these specific columns from the DataFrame
    try:
        data_df = df[data_column_names]
        print(f"Selected data columns for processing: {list(data_df.columns)}")
    except KeyError as ke:
        print(f"Error: One or more columns specified in FORCE_PLATE_COLUMN_MAP not found in CSV. Missing: {ke}")
        print(f"Available CSV columns: {list(df.columns)}")
        print("Please verify `FORCE_PLATE_COLUMN_MAP` matches your CSV's actual column headers.")
        return

    # Optional: Check if the time column appears to be frame numbers and regenerate if so
    if np.all(np.diff(time_vector) == 1) and time_vector[0] == 0:
        print(
            "Warning: First column appears to be frame numbers (0, 1, 2...). Regenerating time vector based on sampling_frequency.")
        time_vector = np.arange(df.shape[0]) / sampling_frequency
    else:
        print("Using first column from CSV as time vector (assuming it's actual time in seconds).")

    # 3. Process force plate data and calculate CoP
    num_data_cols_per_fp = 6  # Fx, Fy, Fz, Mx, My, Mz

    # The number of force plates to process is now determined by the length of FORCE_PLATE_COLUMN_MAP
    num_force_plates_to_process = len(FORCE_PLATE_COLUMN_MAP)
    print(f"Processing {num_force_plates_to_process} force plate(s) based on FORCE_PLATE_COLUMN_MAP.")

    # Check if the total number of selected data columns matches the expected count
    if data_df.shape[1] != num_force_plates_to_process * num_data_cols_per_fp:
        print(f"Error: Total selected data columns ({data_df.shape[1]}) "
              f"does not match expected ({num_force_plates_to_process} * {num_data_cols_per_fp} = {num_force_plates_to_process * num_data_cols_per_fp}). "
              "Please verify `FORCE_PLATE_COLUMN_MAP` and your CSV column structure.")
        return

    all_fp_processed_data = []  # Will store Fx,Fy,Fz,Px,Py,Pz for all plates
    mot_column_headers_final = ['time']

    for i in range(num_force_plates_to_process):
        # Get the column names for the current force plate from the map
        fp_map = FORCE_PLATE_COLUMN_MAP[i]

        # Extract F, M data using the mapped column names
        F = data_df[[fp_map['Fx'], fp_map['Fy'], fp_map['Fz']]].values  # Forces are already in N
        M_nmm = data_df[[fp_map['Mx'], fp_map['My'], fp_map['Mz']]].values  # Moments are in Nmm

        # --- CRITICAL CORRECTION: Convert Moments from Nmm to Nm ---
        M = M_nmm / 1000.0  # Divide by 1000 to convert Nmm to Nm

        # Calculate CoP for the current force plate
        current_fp_origin = FORCE_PLATE_ORIGINS_M[i]
        COP = calculate_cop(F, M, current_fp_origin)

        # Combine F, M, CoP for the current plate (only F and CoP go into .mot)
        # --- NEW: Include Moments (M) in the output .mot file ---
        # OpenSim's ExternalLoads tool needs Fx,Fy,Fz,Mx,My,Mz,Px,Py,Pz
        all_fp_processed_data.append(np.column_stack((F, M, COP)))

        # Append column headers for current force plate (OpenSim convention)
        # Adjust these names if your ExternalLoads.xml expects 'left_ground_force_v' etc.
        # For now, we use ground_fpX_ naming.
        prefix = f'ground_fp{i + 1}_'
        mot_column_headers_final.extend([
            f'{prefix}force_vx', f'{prefix}force_vy', f'{prefix}force_vz',
            f'{prefix}moment_mx', f'{prefix}moment_my', f'{prefix}moment_mz',  # Added moment headers
            f'{prefix}force_px', f'{prefix}force_py', f'{prefix}force_pz'
        ])

    # Combine all data into a single array for .mot file
    all_data_for_mot = np.column_stack([time_vector] + all_fp_processed_data)

    # 4. Prepare .mot file header
    mot_lines = []
    mot_lines.append(f"name {os.path.basename(output_path)}")
    mot_lines.append(f"datacolumns {all_data_for_mot.shape[1]}")
    mot_lines.append(f"nRows\t{all_data_for_mot.shape[0]}")  # Corrected to nRows
    mot_lines.append(f"range {time_vector[0]:.5f} {time_vector[-1]:.5f}")
    mot_lines.append("inDegrees no")  # CRITICAL CORRECTION: Forces/moments/CoP are not angles
    mot_lines.append("endheader")

    # Add original CSV metadata as comments to the MOT header
    if mot_header_comments:
        mot_lines.insert(0, '; Original CSV Header Info:')
        # Insert comments just before 'endheader'
        insert_idx = mot_lines.index('endheader')
        for comment_line in reversed(mot_header_comments):  # Insert in reverse to maintain order
            mot_lines.insert(insert_idx, f'; {comment_line}')

            # 5. Write data to .mot file
    print(f"Writing GRF data to: {output_path}")
    with open(output_path, 'w') as f:
        for line in mot_lines:
            f.write(line + '\n')
        f.write('\t'.join(mot_column_headers_final) + '\n')  # Write the final headers
        np.savetxt(f, all_data_for_mot, fmt="%.8f", delimiter="\t")

    print(f"✅ MOT file saved to: {output_path}")


# Helper function to check if a string is numeric-like
def is_numeric_like(s):
    try:
        pd.to_numeric(s)
        return True
    except (ValueError, TypeError):
        return False


if __name__ == "__main__":
    # --- Main Configuration ---
    csv_input_path = r"D:\uni\post stroke\0core\SUBJ75(healthy female)\grf\SUBJ75 (1).csv"
    mot_output_path = r"D:\uni\post stroke\0core\SUBJ75(healthy female)\grf\SUBJ75_grf.mot"

    # IMPORTANT: Set your force plate's sampling frequency (e.g., 1000 Hz)
    # This must match the rate at which your CSV data was collected.
    DATA_SAMPLING_FREQUENCY_HZ = 1000

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(mot_output_path), exist_ok=True)

    # Run the conversion
    csv_to_grf_mot(csv_input_path, mot_output_path, sampling_frequency=DATA_SAMPLING_FREQUENCY_HZ)

    print("\nNext steps:")
    print("1. **CRITICAL:** Open your `BWA3all.csv` in a plain text editor and verify/adjust:")
    print(
        f"   - `CSV_HEADER_ROW_INDEX` (currently {CSV_HEADER_ROW_INDEX}): This is the 0-indexed row number where your column titles are.")
    print(
        f"   - `CSV_METADATA_END_ROW_INDEX` (currently {CSV_METADATA_END_ROW_INDEX}): This is the 0-indexed row number *before* which all lines are considered metadata/comments.")
    print(
        "   - `FORCE_PLATE_ORIGINS_M` (currently placeholders): Provide the actual [x, y, z] origins for EACH force plate in meters.")
    print(
        "   - `FZ_THRESHOLD_N` (currently 10.0): Adjust if a different force threshold is needed to detect ground contact.")
    print(
        "   - `FORCE_PLATE_COLUMN_MAP`: **CRITICAL!** This maps the generic column names (`N`, `N.1`, `Nmm`, etc.) from your CSV to the correct Fx, Fy, Fz, Mx, My, Mz for each force plate. You MUST adjust this based on your CSV's exact column order and meaning. The 'V' columns should typically be excluded.")
    print("2. Verify the generated `BWA3_grf.mot` file by opening it in a text editor like Notepad++.")
    print("   - Check the header comments, column names, and data alignment.")
    print("   - Pay close attention to the CoP (Px, Py, Pz) values; they should be NaN when Fz is low.")
    print(
        "3. **OpenSim ExternalLoads.xml:** The script generates column names like `ground_fp1_force_vx`. If your `ExternalLoads.xml` expects names like `left_ground_force_vx`, you'll need to either:")
    print("   a) Modify the `prefix` logic in the Python script (around line 160) to match your XML's naming.")
    print("   b) Modify your `ExternalLoads.xml` to match the generated names (e.g., `ground_fp1_force_vx`).")
    print("4. You can now use this .mot file for Inverse Dynamics in OpenSim.")

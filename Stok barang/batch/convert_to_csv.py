import pandas as pd
import os

# Configuration
input_file = 'RINCIAN STOK PEMAKAIAN UNDANGAN PABRIKAN.xlsx'
output_file = 'output_stok.csv'

def clean_col_name(name):
    if pd.isna(name): return ""
    return str(name).strip().lower()

def process_excel():
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    xl = pd.ExcelFile(input_file)
    all_data = []
    unknown_counter = 1
    global_row_no = 1

    for sheet_name in xl.sheet_names:
        print(f"Processing sheet: {sheet_name}")
        
        # Read the sheet without headers first to get row 1 (Nama Barang)
        df_raw = xl.parse(sheet_name, header=None)
        
        if df_raw.empty:
            continue
            
        # Nama Barang is from row 1 (index 0)
        # We search for the first non-NaN value in the first row
        row1_values = df_raw.iloc[0].dropna().tolist()
        nama_barang = row1_values[0] if row1_values else ""
        
        if not nama_barang or pd.isna(nama_barang):
            nama_barang = f"unknown ({unknown_counter})"
            unknown_counter += 1
        
        # Kategori Barang = Undangan
        kategori_barang = "Undangan"
        
        # Nama Barang = [Sheet Name] - [Nama Barang]
        nama_barang_full = f"{sheet_name} - {nama_barang}"
        
        # Now read with headers at row 2 (index 1)
        df = xl.parse(sheet_name, header=1)
        
        # Identify relevant columns
        # We need to handle cases where there are multiple blocks of (Nama Klien, Masuk, Keluar)
        # We will find all sets of indices
        
        cols = [clean_col_name(c) for c in df.columns]
        
        # Map columns to sets of (tanggal_idx, klien_idx, masuk_idx, keluar_idx)
        # We assume they appear in groups
        tanggal_indices = [i for i, c in enumerate(cols) if "tanggal" in c]
        klien_indices = [i for i, c in enumerate(cols) if "nama klien" in c or c == "nama"]
        masuk_indices = [i for i, c in enumerate(cols) if "masuk" in c]
        keluar_indices = [i for i, c in enumerate(cols) if "keluar" in c]
        
        # Determine how many blocks we have
        # Usually they are paired. We'll iterate through klien_indices and find closest tanggal/masuk/keluar
        blocks = []
        for kidx in klien_indices:
            # Find the closest tanggal_idx < kidx or closest to kidx
            tidx = next((i for i in reversed(tanggal_indices) if i < kidx), None)
            if tidx is None and tanggal_indices:
                tidx = tanggal_indices[0]

            # Find the closest masuk_idx > kidx
            midx = next((i for i in masuk_indices if i > kidx), None)
            # Find the closest keluar_idx > kidx
            oidx = next((i for i in keluar_indices if i > kidx), None)
            if midx is not None and oidx is not None:
                blocks.append((tidx, kidx, midx, oidx))

        if not blocks:
            # Fallback
            tidx = tanggal_indices[0] if tanggal_indices else None
            kidx = klien_indices[0] if klien_indices else None
            midx = masuk_indices[0] if masuk_indices else None
            oidx = keluar_indices[0] if keluar_indices else None
            if any(i is not None for i in [tidx, kidx, midx, oidx]):
                blocks.append((tidx, kidx, midx, oidx))

        # Process each block and append to all_data
        for tidx, kidx, midx, oidx in blocks:
            for _, row in df.iterrows():
                tanggal_raw = row.iloc[tidx] if tidx is not None else ""
                nama_klien = row.iloc[kidx] if kidx is not None else ""
                masuk = row.iloc[midx] if midx is not None else 0
                keluar = row.iloc[oidx] if oidx is not None else 0
                
                # Only include rows that have at least a client name or some movement
                if pd.isna(nama_klien) and pd.isna(masuk) and pd.isna(keluar):
                    continue
                
                # Fill NaNs with defaults
                nama_klien = str(nama_klien).strip() if not pd.isna(nama_klien) else ""
                masuk = masuk if not pd.isna(masuk) else 0
                keluar = keluar if not pd.isna(keluar) else 0
                
                # If everything is empty/zero after stripping, skip
                if not nama_klien and masuk == 0 and keluar == 0:
                    continue

                # Filter out rows that look like headers or totals
                if nama_klien.lower() in ["nama klien", "nama", "sisa", "tanggal"]:
                    continue

                # Format Tanggal
                tanggal_str = ""
                if not pd.isna(tanggal_raw):
                    try:
                        dt = pd.to_datetime(tanggal_raw)
                        # Format as D/M/YYYY (e.g. 1/4/2026)
                        tanggal_str = f"{dt.day}/{dt.month}/{dt.year}"
                    except:
                        tanggal_str = str(tanggal_raw).split(' ')[0] # Fallback to original if parse fails

                all_data.append({
                    "No": global_row_no,
                    "Tanggal": tanggal_str,
                    "Kategori Barang": kategori_barang,
                    "Nama Barang": nama_barang_full,
                    "Nama Klien": nama_klien,
                    "Barang Masuk": masuk,
                    "Barang Keluar": keluar
                })
                global_row_no += 1

    # Convert to DataFrame and save
    result_df = pd.DataFrame(all_data)
    result_df.to_csv(output_file, index=False) # Default is comma
    print(f"Success! Saved {len(all_data)} rows to {output_file}")

if __name__ == "__main__":
    process_excel()

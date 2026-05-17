import csv
import os
import re

def process_all_stock():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [base_dir, os.path.join(base_dir, 'batch')]
    
    # 1. KONFIGURASI
    target_files = [
        '1. LAPORAN STOCK TRIKARTA SOV .xlsx - Master Inv SOV.csv',
        '2. LAPORAN STOCK TRIKARTA UND .xlsx - Master Inv UND.csv',
        '3. LAPORAN STOCK TRIKARTA KEMASAN & PACKING.xlsx - Master Inv KEMASAN.csv',
        '4. LAPORAN STOCK TRIKARTA PITA & KAIN.xlsx - Master PITA & KAIN.csv',
        '5. LAPORAN STOCK TRIKARTA INVENTORY.xlsx - Master INV.csv'
    ]
    
    COLOR_KEYWORDS = [
        'PUTIH', 'HITAM', 'MERAH', 'BIRU', 'KUNING', 'HIJAU', 'COKLAT', 
        'ABU', 'ABU-ABU', 'ORANGE', 'ORANYE', 'UNGU', 'PINK', 'GOLD', 
        'SILVER', 'BENING', 'TRANSPARAN', 'NAVY', 'KREM', 'IVORY', 
        'ROSEGOLD', 'RAINBOW', 'MARBLE', 'DOFF', 'GLOSSY', 'RANDOM', 'MIX',
        'COKSU', 'CREAM', 'MARON', 'BURGUNDY', 'FUSIA', 'ARMY', 'MINT', 'EMERALD'
    ]

    # Master Data Stores
    master = {
        'KATEGORI': {}, 
        'SUB_KATEGORI': {}, 
        'MATERIAL': {}, 
        'WARNA': {} # Global
    }
    counters = {'cat': 0, 'color': 0}
    
    all_data_clean = {} # {filename: [cleaned_rows]}

    # 2. LOGIKA STANDARDIZASI (Cleaning)
    def clean_name(full_name, sub_cat):
        pattern = re.compile(re.escape(sub_cat), re.IGNORECASE)
        cleaned = pattern.sub('', full_name).strip()
        cleaned = re.sub(r'^-+', '', cleaned).strip()
        cleaned = re.sub(r'-+$', '', cleaned).strip()
        cleaned = re.sub(r'\s*-+\s*', ' ', cleaned)
        return " ".join(cleaned.split()).strip()

    def extract_color(name):
        words = name.split()
        mat_words, found_colors = [], []
        for word in words:
            clean_word = re.sub(r'[^a-zA-Z-]', '', word).upper()
            if clean_word in COLOR_KEYWORDS:
                color_name = 'Random' if clean_word in ['MIX', 'RANDOM'] else word
                found_colors.append(color_name)
            else:
                mat_words.append(word)
        material = " ".join(mat_words).strip()
        material = re.sub(r'^-+', '', material).strip()
        material = re.sub(r'-+$', '', material).strip()
        return material, " ".join(found_colors).strip()

    # 3. PROSES TAHAP 1: Standardisasi & Koleksi Master Mapping
    print("Membaca dan menstandarisasi data dari semua file...")
    for filename in target_files:
        file_path = None
        for path in possible_paths:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                file_path = full_path
                break
        
        if not file_path:
            print(f"Peringatan: File {filename} tidak ditemukan.")
            continue
            
        all_data_clean[filename] = []
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('Kategori') or row['Kategori'] in ['Kategori', 'SubKategori', 'Material', 'Warna']:
                    continue
                
                cat_name = row['Kategori']
                sub_cat_name = row['Sub Kategori']
                orig_name = row['Nama Barang']
                
                # Cleaning
                cleaned_base = clean_name(orig_name, sub_cat_name)
                mat_name, col_name = extract_color(cleaned_base)
                if not mat_name and not col_name: mat_name = cleaned_base if cleaned_base else orig_name
                
                # Update Master Mapping
                # Category
                if cat_name not in master['KATEGORI']:
                    counters['cat'] += 1
                    master['KATEGORI'][cat_name] = f"{counters['cat']:03}"
                cat_id = master['KATEGORI'][cat_name]
                
                # Sub-Category
                if cat_id not in master['SUB_KATEGORI']: master['SUB_KATEGORI'][cat_id] = {}
                if sub_cat_name not in master['SUB_KATEGORI'][cat_id]:
                    new_id = len(master['SUB_KATEGORI'][cat_id]) + 1
                    master['SUB_KATEGORI'][cat_id][sub_cat_name] = f"{new_id:03}"
                sub_id = master['SUB_KATEGORI'][cat_id][sub_cat_name]
                
                # Material (Reset per Sub-Cat)
                if cat_id not in master['MATERIAL']: master['MATERIAL'][cat_id] = {}
                if sub_id not in master['MATERIAL'][cat_id]: master['MATERIAL'][cat_id][sub_id] = {}
                if mat_name not in master['MATERIAL'][cat_id][sub_id]:
                    new_id = len(master['MATERIAL'][cat_id][sub_id]) + 1
                    master['MATERIAL'][cat_id][sub_id][mat_name] = f"{new_id:03}"
                
                # Color (Global)
                if col_name:
                    col_upper = col_name.upper()
                    if col_upper not in master['WARNA']:
                        counters['color'] += 1
                        master['WARNA'][col_upper] = (col_name, f"{counters['color']:03}")

                # Simpan data bersih untuk tahap SKU
                row['__mat_name'] = mat_name
                row['__col_name'] = col_name
                all_data_clean[filename].append(row)

    # 4. PROSES TAHAP 2: Generate SKU & Simpan Hasil
    def add_backtick(value):
        """Tambahkan backtick pada nilai yang dimulai dengan 0"""
        if isinstance(value, str) and value.startswith('0'):
            return f"`{value}"
        return value
    
    print("Menghasilkan SKU dan menyimpan file hasil...")
    for filename, rows in all_data_clean.items():
        if not rows: continue
        
        # Tentukan header
        header = [k for k in rows[0].keys() if not k.startswith('__')] + ['SKU']
        
        output_name = filename.replace('.csv', ' - with SKU.csv')
        # Cari lokasi asli untuk output
        output_path = None
        for path in possible_paths:
            if os.path.exists(os.path.join(path, filename)):
                output_path = os.path.join(path, output_name)
                break
        
        with open(output_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
            writer.writeheader()
            for row in rows:
                cat_id = master['KATEGORI'][row['Kategori']]
                sub_id = master['SUB_KATEGORI'][cat_id][row['Sub Kategori']]
                mat_id = master['MATERIAL'][cat_id][sub_id][row['__mat_name']]
                col_id = master['WARNA'][row['__col_name'].upper()][1] if row['__col_name'] else "000"
                
                row['SKU'] = f"TKR-{cat_id}{sub_id}-{mat_id}{col_id}"
                # Apply backtick to values starting with 0
                for field in header:
                    if field in row and isinstance(row[field], str) and row[field].startswith('0'):
                        row[field] = add_backtick(row[field])
                writer.writerow(row)
        print(f"Berhasil: {output_name}")

    # 5. SIMPAN MASTER RULES UNTUK DOKUMENTASI
    master_path = os.path.join(base_dir, 'MASTER_SKU_RULES.csv')
    with open(master_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Tipe', 'Induk 1 (Cat)', 'Induk 2 (Sub-Cat)', 'Nama Item', 'Kode Digit'])
        for name, code in master['KATEGORI'].items(): writer.writerow(['KATEGORI', '-', '-', name, add_backtick(code)])
        for cid, subs in master['SUB_KATEGORI'].items():
            cname = [k for k, v in master['KATEGORI'].items() if v == cid][0]
            for name, code in subs.items(): writer.writerow(['SUB_KATEGORI', cname, '-', name, add_backtick(code)])
        for upper, (orig, code) in master['WARNA'].items(): writer.writerow(['WARNA_GLOBAL', '-', '-', orig, add_backtick(code)])
        for cid, sub_data in master['MATERIAL'].items():
            cname = [k for k, v in master['KATEGORI'].items() if v == cid][0]
            for sid, materials in sub_data.items():
                sname = [k for k, v in master['SUB_KATEGORI'][cid].items() if v == sid][0]
                for name, code in materials.items(): writer.writerow(['MATERIAL', cname, sname, name, add_backtick(code)])
    
    print(f"Dokumentasi Aturan Master diperbarui: {master_path}")
    print("\nPROSES SELESAI!")

if __name__ == "__main__":
    process_all_stock()

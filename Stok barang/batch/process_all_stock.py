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
    
    # Expanded Color Keywords for better extraction
    COLOR_KEYWORDS = [
        'PUTIH', 'HITAM', 'MERAH', 'BIRU', 'KUNING', 'HIJAU', 'COKLAT', 
        'ABU', 'ABU-ABU', 'ORANGE', 'ORANYE', 'UNGU', 'PINK', 'GOLD', 
        'SILVER', 'BENING', 'TRANSPARAN', 'NAVY', 'KREM', 'IVORY', 
        'ROSEGOLD', 'ROSE', 'RAINBOW', 'MARBLE', 'DOFF', 'GLOSSY', 'RANDOM', 'MIX',
        'COKSU', 'CREAM', 'MARON', 'BURGUNDY', 'FUSIA', 'ARMY', 'MINT', 'EMERALD',
        'NATURAL', 'TULANG', 'TOSCA', 'LAVENDER', 'LILAC', 'MAGENTA', 'PEACH',
        'SOFT', 'BRONZE', 'COPPER', 'CHAMPAGNE', 'BEIGE', 'KHAKI', 'TAN',
        'MATTE', 'TERRAZZO', 'WOOD', 'KAYU', 'JERAMI', 'BINTIK', 'JATI',
        'COFFEE', 'COFFE'
    ]
    
    # Keywords that indicate a complex variation but should be part of "Color/Pattern"
    PATTERN_KEYWORDS = [
        'BUNGA', 'DAUN', 'FULL', 'MAWAR', 'DADU', 'GUCCI', 'SAKURA', 'MERRY', 
        'MARBLE', 'EMBOS', 'UKIR', 'LIST', 'POLOS', 'MOTIF', 'PRINTING', 
        'TEKSTUR', 'ANYAMAN', 'GLITER', 'KOTAK', 'GARIS', 'ANTIS', 'BINTIK'
    ]

    # Material Range Mapping
    MATERIAL_OFFSETS = {
        'KERAMIK': 100,
        'RESIN': 200,
        'KACA': 300,
        'STAINLESS': 400
    }
    RESIN_PATTERNS = [r'\bRESIN\b', r'\bR\b']

    # Sub-Category Ordered List
    ORDERED_SUB_CATS = [
        "AROMATHERAPHY", "BOTOL", "TERMOS", "TUMBLER", "TOPLES", 
        "PIRING", "GELAS", "MUG", "MANGKOK", "HANDSOAP", 
        "SENDOK", "GARPU", "SUMPIT", "SGS", "HANDUK", "TEA CUP", "PAYUNG"
    ]
    SUB_CAT_ID_MAP = {name: f"{(i+1):03}" for i, name in enumerate(ORDERED_SUB_CATS)}

    # Master Data Stores
    master = {
        'KATEGORI': {}, 
        'SUB_KATEGORI': SUB_CAT_ID_MAP.copy(), 
        'MATERIAL': {}, 
        'WARNA': {'DEFAULT': ('Default', '000')} # Global Unique Variations
    }
    counters = {'cat': 0, 'color': 0}
    
    all_data_clean = {}

    # 2. LOGIKA STANDARDIZASI (Cleaning)
    def clean_name(full_name, sub_cat):
        pattern = re.compile(re.escape(sub_cat), re.IGNORECASE)
        cleaned = pattern.sub('', full_name).strip()
        cleaned = re.sub(r'^-+', '', cleaned).strip()
        cleaned = re.sub(r'-+$', '', cleaned).strip()
        cleaned = re.sub(r'\s*-+\s*', ' ', cleaned)
        return " ".join(cleaned.split()).strip()

    def get_core_name(full_name, sub_cat_upper, mat_keyword):
        """
        Extracts the most unique part of the name for Material grouping.
        """
        # 1. Remove Sub-Category
        name = clean_name(full_name, sub_cat_upper)
        
        # 2. Remove Material
        if mat_keyword:
            if mat_keyword == 'RESIN':
                name = re.sub(r'\bRESIN\b|\bR\b', '', name, flags=re.IGNORECASE).strip()
            else:
                name = re.sub(re.escape(mat_keyword), '', name, flags=re.IGNORECASE).strip()
        
        # 3. Remove Color/Pattern Keywords to get the "Core"
        words = name.split()
        core_words = []
        for word in words:
            w_match = re.sub(r'[^a-zA-Z]', '', word).upper()
            if w_match not in COLOR_KEYWORDS and w_match not in PATTERN_KEYWORDS:
                core_words.append(word)
        
        core = " ".join(core_words).strip()
        return core if core else "Default"

    def get_material_info(name, sub_cat_upper):
        name_upper = name.upper()
        offset = 0
        mat_found = None

        is_resin = False
        for p in RESIN_PATTERNS:
            if re.search(p, name_upper):
                is_resin = True
                break
        
        if is_resin:
            offset = MATERIAL_OFFSETS['RESIN']
            mat_found = 'RESIN'
        elif 'KACA' in name_upper:
            offset = MATERIAL_OFFSETS['KACA']
            mat_found = 'KACA'
        elif 'KERAMIK' in name_upper:
            offset = MATERIAL_OFFSETS['KERAMIK']
            mat_found = 'KERAMIK'
        elif 'STAINLESS' in name_upper:
            offset = MATERIAL_OFFSETS['STAINLESS']
            mat_found = 'STAINLESS'
        
        # New Logic: Mangkok, Piring, Mug (non-glass) are Ceramic by default
        if sub_cat_upper in ['MANGKOK', 'PIRING', 'MUG']:
            if mat_found != 'KACA':
                offset = MATERIAL_OFFSETS['KERAMIK']
                mat_found = 'KERAMIK'
        
        if sub_cat_upper == 'TOPLES' and 'CRYSTAL' in name_upper:
            # For Toples, Crystal is offset 0 as per previous instruction
            offset = 0
            mat_found = None

        return mat_found, offset

    def extract_variation_unique(name, sub_cat_upper):
        """
        Extracts a unique variation (color + pattern) from the name.
        Example: "HANDSOAP R GUCCI PUTIH TULANG BUNGA PINK DAUN HIJAU"
        Result: ("GUCCI PUTIH TULANG BUNGA PINK DAUN HIJAU", "Handsoap name part")
        """
        words = name.split()
        var_words, remaining_words = [], []
        
        name_upper = name.upper()
        
        # Keywords that indicate the start of a variation
        # Often after "R", "KERAMIK", "KACA" or just part of the description
        
        for word in words:
            word_upper = re.sub(r'[^a-zA-Z]', '', word).upper()
            if word_upper in COLOR_KEYWORDS or word_upper in PATTERN_KEYWORDS or (len(word) == 1 and word.upper() == 'R'):
                var_words.append(word)
            else:
                # Check if it's a size or specific model part
                if re.search(r'\d', word) or word.upper() in ['CM', 'ML', 'INCH']:
                    remaining_words.append(word)
                else:
                    # If it's not a color/pattern keyword, it might be the core name
                    remaining_words.append(word)
        
        # Refined Logic: We want to capture the WHOLE suffix after the sub-category name
        # that describes the color/motif.
        
        # Let's try a simpler approach for "Unique Variation":
        # Any words that are NOT the sub-category name itself are part of the variation.
        # But we need to separate "Material Name" from "Color/Variation".
        
        # Actually, for "Unique Variation", the user wants the detailed color/motif 
        # to be the ColorID.
        
        return " ".join(var_words).strip(), " ".join(remaining_words).strip()

    # 3. PROSES TAHAP 1
    print("Membaca dan menstandarisasi data...")
    for filename in target_files:
        file_path = None
        for path in possible_paths:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                file_path = full_path
                break
        
        if not file_path: continue
            
        all_data_clean[filename] = []
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('Kategori') or row['Kategori'] in ['Kategori', 'SubKategori', 'Material', 'Warna']:
                    continue
                
                cat_name = row['Kategori']
                sub_cat_name = row['Sub Kategori'].upper().strip()
                orig_name = row['Nama Barang']
                
                # 1. Identify material type and offset
                mat_keyword, offset = get_material_info(orig_name, sub_cat_name)
                
                # 2. Extract components
                # Cleaned name after removing sub-category
                cleaned_name = clean_name(orig_name, sub_cat_name)
                
                # Variation part (COLOR + PATTERN only)
                var_words = []
                # Core part (Everything else)
                core_words = []
                
                # Temp name for word splitting (remove material keyword from core logic)
                temp_name = cleaned_name
                if mat_keyword:
                    if mat_keyword == 'RESIN':
                        temp_name = re.sub(r'\bRESIN\b|\bR\b', '', temp_name, flags=re.IGNORECASE).strip()
                    else:
                        temp_name = re.sub(re.escape(mat_keyword), '', temp_name, flags=re.IGNORECASE).strip()
                
                for word in temp_name.split():
                    w_match = re.sub(r'[^a-zA-Z]', '', word).upper()
                    if w_match in COLOR_KEYWORDS or w_match in PATTERN_KEYWORDS:
                        var_words.append(word)
                    else:
                        core_words.append(word)
                
                variation = " ".join(var_words).strip()
                if not variation: variation = "DEFAULT"
                
                mat_group_name = " ".join(core_words).strip()
                if not mat_group_name: mat_group_name = "Default"

                # 3. Update Master
                if cat_name not in master['KATEGORI']:
                    counters['cat'] += 1
                    master['KATEGORI'][cat_name] = f"{counters['cat']:03}"
                cat_id = master['KATEGORI'][cat_name]
                
                if sub_cat_name not in master['SUB_KATEGORI']:
                    new_id = len(master['SUB_KATEGORI']) + 1
                    master['SUB_KATEGORI'][sub_cat_name] = f"{new_id:03}"
                sub_id = master['SUB_KATEGORI'][sub_cat_name]
                
                if cat_id not in master['MATERIAL']: master['MATERIAL'][cat_id] = {}
                if sub_id not in master['MATERIAL'][cat_id]: master['MATERIAL'][cat_id][sub_id] = {}
                
                if mat_group_name not in master['MATERIAL'][cat_id][sub_id]:
                    current_materials = master['MATERIAL'][cat_id][sub_id]
                    range_materials = [int(v) for v in current_materials.values() if offset < int(v) <= (offset + 100)]
                    next_code_val = (max(range_materials) + 1) if range_materials else (offset + 1)
                    master['MATERIAL'][cat_id][sub_id][mat_group_name] = f"{next_code_val:03}"
                
                # Color (Unique Variation)
                col_key = variation.upper().strip()
                if col_key not in master['WARNA']:
                    counters['color'] += 1
                    master['WARNA'][col_key] = (variation if variation else "Default", f"{counters['color']:03}")

                row['__sub_cat_upper'] = sub_cat_name
                row['__sub_id'] = sub_id
                row['__mat_group_name'] = mat_group_name
                row['__mat_id'] = master['MATERIAL'][cat_id][sub_id][mat_group_name]
                row['__variation_key'] = col_key
                all_data_clean[filename].append(row)

    # 4. SAVE
    def add_backtick(value):
        if isinstance(value, str) and value.startswith('0'): return f"`{value}"
        return value
    
    print("Menyimpan hasil...")
    for filename, rows in all_data_clean.items():
        if not rows: continue
        rows.sort(key=lambda x: (x['__sub_id'], x['__mat_id'], x['__variation_key']))
        header = [k for k in rows[0].keys() if not k.startswith('__')] + ['SKU']
        output_name = filename.replace('.csv', ' - with SKU.csv')
        
        output_path = os.path.join(base_dir, output_name)
        try:
            with open(output_path, mode='w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
                writer.writeheader()
                for row in rows:
                    cat_id = master['KATEGORI'][row['Kategori']]
                    sub_id = row['__sub_id']
                    mat_id = row['__mat_id']
                    col_id = master['WARNA'][row['__variation_key']][1]
                    
                    row['SKU'] = f"TKR-{cat_id}{sub_id}-{mat_id}{col_id}"
                    for field in header:
                        if field in row and isinstance(row[field], str) and row[field].startswith('0'):
                            row[field] = add_backtick(row[field])
                    writer.writerow(row)
        except PermissionError:
            print(f"Warning: Tidak bisa menulis ke {output_name} (File mungkin sedang terbuka).")

    # 5. MASTER RULES
    master_path = os.path.join(base_dir, 'MASTER_SKU_RULES.csv')
    with open(master_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Tipe', 'Induk 1 (Cat)', 'Induk 2 (Sub-Cat)', 'Nama Item', 'Kode Digit'])
        for name, code in sorted(master['KATEGORI'].items(), key=lambda x: x[1]): 
            writer.writerow(['KATEGORI', '-', '-', name, add_backtick(code)])
        for name, code in sorted(master['SUB_KATEGORI'].items(), key=lambda x: x[1]): 
            writer.writerow(['SUB_KATEGORI', '-', '-', name, add_backtick(code)])
        for upper, (orig, code) in sorted(master['WARNA'].items(), key=lambda x: x[1][1]): 
            writer.writerow(['WARNA_GLOBAL', '-', '-', orig, add_backtick(code)])
        for cid, sub_data in master['MATERIAL'].items():
            cname = [k for k, v in master['KATEGORI'].items() if v == cid][0]
            for sid, materials in sub_data.items():
                sname = [k for k, v in master['SUB_KATEGORI'].items() if v == sid][0]
                for name, code in sorted(materials.items(), key=lambda x: x[1]): 
                    writer.writerow(['MATERIAL', cname, sname, name, add_backtick(code)])

if __name__ == "__main__":
    process_all_stock()

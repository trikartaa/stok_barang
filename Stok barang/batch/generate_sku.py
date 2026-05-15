import csv
import os
import re

def generate_sku_script():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [base_dir, os.path.join(base_dir, 'batch')]
    
    # Lokasi File
    souvenir_file = None
    undangan_file = None
    master_file = None
    
    for path in possible_paths:
        s_file = os.path.join(path, 'Stock - Souvenir.csv')
        u_file = os.path.join(path, 'Stock - Undangan.csv')
        m_file = os.path.join(path, 'MASTER_SKU_RULES.csv')
        if os.path.exists(s_file) and os.path.exists(u_file):
            souvenir_file = s_file
            undangan_file = u_file
        if os.path.exists(m_file):
            master_file = m_file
            
    if not souvenir_file or not master_file:
        print(f"Error: File CSV atau MASTER_SKU_RULES.csv tidak ditemukan.")
        return

    # 1. LOAD MASTER MAPPING
    master_mapping = {
        'KATEGORI': {}, 
        'SUB_KATEGORI': {}, 
        'MATERIAL': {}, 
        'WARNA': {} 
    }
    
    print("Memuat Master SKU Rules...")
    with open(master_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tipe = row['Tipe']
            name = row['Nama Item']
            code = row['Kode Digit']
            
            if tipe == 'KATEGORI':
                master_mapping['KATEGORI'][name] = code
            elif tipe == 'SUB_KATEGORI':
                cat = row['Induk 1 (Cat)']
                if cat not in master_mapping['SUB_KATEGORI']: master_mapping['SUB_KATEGORI'][cat] = {}
                master_mapping['SUB_KATEGORI'][cat][name] = code
            elif tipe == 'WARNA_GLOBAL':
                master_mapping['WARNA'][name.upper()] = code
            elif tipe == 'MATERIAL':
                cat = row['Induk 1 (Cat)']
                sub = row['Induk 2 (Sub-Cat)']
                if cat not in master_mapping['MATERIAL']: master_mapping['MATERIAL'][cat] = {}
                if sub not in master_mapping['MATERIAL'][cat]: master_mapping['MATERIAL'][cat][sub] = {}
                master_mapping['MATERIAL'][cat][sub][name] = code

    # 2. STANDARDIZATION LOGIC (Must match standardize_stock.py)
    COLOR_KEYWORDS = list(master_mapping['WARNA'].keys())
    if 'MIX' not in COLOR_KEYWORDS: COLOR_KEYWORDS.append('MIX')
    if 'RANDOM' not in COLOR_KEYWORDS: COLOR_KEYWORDS.append('RANDOM')

    def clean_name(full_name, sub_cat):
        pattern = re.compile(re.escape(sub_cat), re.IGNORECASE)
        cleaned = pattern.sub('', full_name).strip()
        cleaned = re.sub(r'^-+', '', cleaned)
        cleaned = re.sub(r'-+$', '', cleaned)
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

    # 3. SKU GENERATION LOGIC
    def get_code(type_, name, parent1=None, parent2=None):
        if type_ == 'KATEGORI':
            return master_mapping['KATEGORI'].get(name, "000")
        elif type_ == 'SUB_KATEGORI':
            return master_mapping['SUB_KATEGORI'].get(parent1, {}).get(name, "000")
        elif type_ == 'WARNA':
            if not name: return "000"
            return master_mapping['WARNA'].get(name.upper(), "000")
        elif type_ == 'MATERIAL':
            if not name: return "000"
            return master_mapping['MATERIAL'].get(parent1, {}).get(parent2, {}).get(name, "000")
        return "000"

    def process_file(file_path):
        results = []
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames + ['SKU']
            for row in reader:
                if row['Kategori'] in ['Kategori', 'SubKategori', 'Material', 'Warna']: continue
                
                cat_name = row['Kategori']
                sub_cat_name = row['Sub Kategori']
                original_name = row['Nama Barang']
                
                # Standarisasi Nama
                cleaned = clean_name(original_name, sub_cat_name)
                mat_name, color_name = extract_color(cleaned)
                if not mat_name and not color_name: mat_name = cleaned if cleaned else original_name
                
                # Ambil Kode dari Master
                c_id = get_code('KATEGORI', cat_name)
                s_id = get_code('SUB_KATEGORI', sub_cat_name, cat_name)
                m_id = get_code('MATERIAL', mat_name, cat_name, sub_cat_name)
                w_id = get_code('WARNA', color_name)
                
                row['SKU'] = f"TKR-{c_id}{s_id}-{m_id}{w_id}"
                results.append(row)
        return results, fieldnames

    print("Menghasilkan SKU berdasarkan Master Rules...")
    souvenir_results, souvenir_fields = process_file(souvenir_file)
    undangan_results, undangan_fields = process_file(undangan_file)

    def save(file_path, data, fields):
        out = file_path.replace('.csv', ' - with SKU.csv')
        with open(out, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
        print(f"Selesai: {out}")

    save(souvenir_file, souvenir_results, souvenir_fields)
    save(undangan_file, undangan_results, undangan_fields)

if __name__ == "__main__":
    generate_sku_script()

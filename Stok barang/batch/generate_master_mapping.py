import csv
import os

def generate_master_mapping():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [base_dir, os.path.join(base_dir, 'batch')]
    
    # Ambil data dari file yang SUDAH terstandarisasi
    souvenir_file = None
    undangan_file = None
    for path in possible_paths:
        s_file = os.path.join(path, 'Stock - Souvenir - Standardized.csv')
        u_file = os.path.join(path, 'Stock - Undangan - Standardized.csv')
        if os.path.exists(s_file) and os.path.exists(u_file):
            souvenir_file = s_file
            undangan_file = u_file
            break
            
    if not souvenir_file:
        print(f"Error: File Standardized CSV tidak ditemukan. Pastikan sudah menjalankan standardize_stock.py terlebih dahulu.")
        return

    # Data Stores
    master_mapping = {
        'KATEGORI': {}, 
        'SUB_KATEGORI': {}, 
        'MATERIAL': {}, 
        'WARNA': {} 
    }
    
    counters = {'cat': 0, 'color': 0}

    def process_standardized_file(file_path):
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cat_name = row['Kategori']
                sub_cat_name = row['Sub Kategori']
                mat_name = row['Material (Standard)']
                color_name = row['Warna (Standard)']
                
                # 1. Kategori
                if cat_name not in master_mapping['KATEGORI']:
                    counters['cat'] += 1
                    master_mapping['KATEGORI'][cat_name] = counters['cat']
                cat_id = master_mapping['KATEGORI'][cat_name]
                
                # 2. Sub Kategori
                if cat_id not in master_mapping['SUB_KATEGORI']: master_mapping['SUB_KATEGORI'][cat_id] = {}
                if sub_cat_name not in master_mapping['SUB_KATEGORI'][cat_id]:
                    new_id = len(master_mapping['SUB_KATEGORI'][cat_id]) + 1
                    master_mapping['SUB_KATEGORI'][cat_id][sub_cat_name] = new_id
                sub_cat_id = master_mapping['SUB_KATEGORI'][cat_id][sub_cat_name]
                
                # 3. Material
                if cat_id not in master_mapping['MATERIAL']: master_mapping['MATERIAL'][cat_id] = {}
                if sub_cat_id not in master_mapping['MATERIAL'][cat_id]: master_mapping['MATERIAL'][cat_id][sub_cat_id] = {}
                if mat_name not in master_mapping['MATERIAL'][cat_id][sub_cat_id]:
                    new_id = len(master_mapping['MATERIAL'][cat_id][sub_cat_id]) + 1
                    master_mapping['MATERIAL'][cat_id][sub_cat_id][mat_name] = new_id
                
                # 4. Warna (Global)
                if color_name:
                    color_upper = color_name.upper()
                    if color_upper not in master_mapping['WARNA']:
                        counters['color'] += 1
                        master_mapping['WARNA'][color_upper] = (color_name, counters['color'])

    process_standardized_file(souvenir_file)
    process_standardized_file(undangan_file)

    # Save Master Mapping
    output_path = os.path.join(base_dir, 'MASTER_SKU_RULES.csv')
    with open(output_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Tipe', 'Induk 1 (Cat)', 'Induk 2 (Sub-Cat)', 'Nama Item', 'Kode Digit'])
        
        # Categories
        for name, id_ in master_mapping['KATEGORI'].items():
            writer.writerow(['KATEGORI', '-', '-', name, f"{id_:03}"])
            
        # Sub-Categories
        for cat_id, subs in master_mapping['SUB_KATEGORI'].items():
            cat_name = [k for k, v in master_mapping['KATEGORI'].items() if v == cat_id][0]
            for name, id_ in subs.items():
                writer.writerow(['SUB_KATEGORI', cat_name, '-', name, f"{id_:03}"])
                
        # Colors (Global)
        for upper, (orig, id_) in master_mapping['WARNA'].items():
            writer.writerow(['WARNA_GLOBAL', '-', '-', orig, f"{id_:03}"])
            
        # Materials (Per Sub-Cat)
        for cat_id, sub_data in master_mapping['MATERIAL'].items():
            cat_name = [k for k, v in master_mapping['KATEGORI'].items() if v == cat_id][0]
            for sub_cat_id, materials in sub_data.items():
                sub_name = [k for k, v in master_mapping['SUB_KATEGORI'][cat_id].items() if v == sub_cat_id][0]
                for name, id_ in materials.items():
                    writer.writerow(['MATERIAL', cat_name, sub_name, name, f"{id_:03}"])

    print(f"Master Mapping berhasil dibuat berdasarkan file Standardized: {output_path}")

if __name__ == "__main__":
    generate_master_mapping()

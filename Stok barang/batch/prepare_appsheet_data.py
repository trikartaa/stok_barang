import csv
import os
import re

def prepare_appsheet():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    master_file = os.path.join(base_dir, 'MASTER_SKU_RULES.csv')
    
    if not os.path.exists(master_file):
        print("Error: MASTER_SKU_RULES.csv tidak ditemukan.")
        return

    # Data Containers
    categories = []
    sub_categories = []
    materials = []
    colors = []
    products = []

    # Mapping for IDs
    cat_to_id = {}
    sub_to_id = {}
    mat_to_id = {}
    col_to_id = {}

    print("Membaca Master Rules (Memastikan format teks untuk Code)...")
    with open(master_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tipe = row['Tipe']
            name = row['Nama Item']
            # Pastikan code adalah string 3 digit
            code = str(row['Kode Digit']).zfill(3)
            
            if tipe == 'KATEGORI':
                cid = f"CAT{code}"
                cat_to_id[name] = cid
                categories.append({'CategoryID': cid, 'CategoryName': name, 'CategoryCode': code})
                
            elif tipe == 'SUB_KATEGORI':
                cat_name = row['Induk 1 (Cat)']
                cid = cat_to_id[cat_name]
                scid = f"SC{cid[3:]}{code}" 
                sub_to_id[(cat_name, name)] = scid
                sub_categories.append({
                    'SubCategoryID': scid, 
                    'CategoryID': cid, 
                    'SubCategoryName': name, 
                    'SubCategoryCode': code
                })
                
            elif tipe == 'WARNA_GLOBAL':
                coid = f"COL{code}"
                col_to_id[name.upper()] = coid
                colors.append({'ColorID': coid, 'ColorName': name, 'ColorCode': code})
                
            elif tipe == 'MATERIAL':
                cat_name = row['Induk 1 (Cat)']
                sub_name = row['Induk 2 (Sub-Cat)']
                scid = sub_to_id[(cat_name, sub_name)]
                mid = f"MAT{scid[2:]}{code}" 
                mat_to_id[(cat_name, sub_name, name)] = mid
                materials.append({
                    'MaterialID': mid, 
                    'SubCategoryID': scid, 
                    'MaterialName': name, 
                    'MaterialCode': code
                })

    # PROSES PRODUCTS
    print("Membaca file produk...")
    target_files = [
        'Stock - Souvenir - with SKU.csv',
        'Stock - Undangan - with SKU.csv',
        '4. LAPORAN STOCK TRIKARTA PITA & KAIN.xlsx - Master PITA & KAIN - with SKU.csv',
        '5. LAPORAN STOCK TRIKARTA INVENTORY.xlsx - Master INV - with SKU.csv'
    ]

    def clean_name(full_name, sub_cat):
        pattern = re.compile(re.escape(sub_cat), re.IGNORECASE)
        cleaned = pattern.sub('', full_name).strip()
        cleaned = re.sub(r'^-+', '', cleaned).strip()
        cleaned = re.sub(r'-+$', '', cleaned).strip()
        cleaned = re.sub(r'\s*-+\s*', ' ', cleaned)
        return " ".join(cleaned.split()).strip()

    def extract_color(name, color_list):
        words = name.split()
        mat_words, found_colors = [], []
        for word in words:
            clean_word = re.sub(r'[^a-zA-Z-]', '', word).upper()
            if clean_word in color_list:
                color_name = 'Random' if clean_word in ['MIX', 'RANDOM'] else word
                found_colors.append(color_name)
            else:
                mat_words.append(word)
        mat = " ".join(mat_words).strip()
        mat = re.sub(r'^-+', '', mat).strip()
        mat = re.sub(r'-+$', '', mat).strip()
        return mat, " ".join(found_colors).strip()

    color_names_upper = list(col_to_id.keys())

    for filename in target_files:
        file_path = os.path.join(base_dir, filename)
        if not os.path.exists(file_path): continue
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cat, sub, orig = row['Kategori'], row['Sub Kategori'], row['Nama Barang']
                sku = row['SKU']
                cleaned = clean_name(orig, sub)
                mat, col = extract_color(cleaned, color_names_upper)
                if not mat and not col: mat = cleaned if cleaned else orig
                
                products.append({
                    'SKU': sku,
                    'OriginalName': orig,
                    'CategoryID': cat_to_id.get(cat),
                    'SubCategoryID': sub_to_id.get((cat, sub)),
                    'MaterialID': mat_to_id.get((cat, sub, mat)),
                    'ColorID': col_to_id.get(col.upper()) if col else None,
                    'StockQty': 0
                })

    # SAVE ALL FILES
    def save_csv(filename, data, fields):
        path = os.path.join(base_dir, filename)
        with open(path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            writer.writerows(data)
        print(f"Berhasil dibuat: {filename}")

    save_csv('AppSheet_Categories.csv', categories, ['CategoryID', 'CategoryName', 'CategoryCode'])
    save_csv('AppSheet_SubCategories.csv', sub_categories, ['SubCategoryID', 'CategoryID', 'SubCategoryName', 'SubCategoryCode'])
    save_csv('AppSheet_Materials.csv', materials, ['MaterialID', 'SubCategoryID', 'MaterialName', 'MaterialCode'])
    save_csv('AppSheet_Colors.csv', colors, ['ColorID', 'ColorName', 'ColorCode'])
    save_csv('AppSheet_Products.csv', products, ['SKU', 'OriginalName', 'CategoryID', 'SubCategoryID', 'MaterialID', 'ColorID', 'StockQty'])

if __name__ == "__main__":
    prepare_appsheet()

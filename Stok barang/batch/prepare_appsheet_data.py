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

    def add_backtick(value):
        """Tambahkan backtick pada nilai yang dimulai dengan 0"""
        if isinstance(value, str) and value.startswith('0'):
            return f"`{value}"
        return str(value)

    print("Membaca Master Rules...")
    with open(master_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tipe = row['Tipe']
            name = row['Nama Item']
            code_raw = row['Kode Digit'].replace('`', '')
            code = code_raw.zfill(3)
            
            if tipe == 'KATEGORI':
                cid = f"CAT{code}"
                cat_to_id[name] = cid
                categories.append({'CategoryID': cid, 'CategoryName': name, 'CategoryCode': add_backtick(code)})
                
            elif tipe == 'SUB_KATEGORI':
                # Sub-Category now is global/not strictly tied to one category in the ID
                scid = f"SC{code}" 
                sub_to_id[name.upper()] = scid
                sub_categories.append({
                    'SubCategoryID': scid, 
                    'SubCategoryName': name, 
                    'SubCategoryCode': add_backtick(code)
                })
                
            elif tipe == 'WARNA_GLOBAL':
                coid = f"COL{code}"
                col_to_id[name.upper()] = coid
                colors.append({'ColorID': coid, 'ColorName': name, 'ColorCode': add_backtick(code)})
                
            elif tipe == 'MATERIAL':
                cat_name = row['Induk 1 (Cat)']
                sub_name = row['Induk 2 (Sub-Cat)'].upper()
                cid = cat_to_id.get(cat_name, "CAT000")
                scid = sub_to_id.get(sub_name, "SC000")
                
                mid = f"MAT{cid[3:]}{scid[2:]}{code}" 
                mat_to_id[(cat_name, sub_name, name)] = mid
                materials.append({
                    'MaterialID': mid, 
                    'SubCategoryID': scid, 
                    'CategoryID': cid,
                    'MaterialName': name, 
                    'MaterialCode': add_backtick(code)
                })

    # PROSES PRODUCTS
    print("Membaca file produk...")
    target_files = [
        '1. LAPORAN STOCK TRIKARTA SOV .xlsx - Master Inv SOV - with SKU.csv',
        '2. LAPORAN STOCK TRIKARTA UND .xlsx - Master Inv UND - with SKU.csv',
        '3. LAPORAN STOCK TRIKARTA KEMASAN & PACKING.xlsx - Master Inv KEMASAN - with SKU.csv',
        '4. LAPORAN STOCK TRIKARTA PITA & KAIN.xlsx - Master PITA & KAIN - with SKU.csv',
        '5. LAPORAN STOCK TRIKARTA INVENTORY.xlsx - Master INV - with SKU.csv'
    ]

    for filename in target_files:
        file_path = os.path.join(base_dir, filename)
        if not os.path.exists(file_path): continue
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Re-read to get raw names for matching
            for row in reader:
                cat = row['Kategori']
                sub = row['Sub Kategori'].upper().strip()
                orig = row['Nama Barang']
                sku = row['SKU'].replace('`', '')
                
                # Logic to find which material name was used
                # In the new script, we saved metadata in SKU or can derive it
                # But easiest is to use the MaterialID from SKU parts
                sku_parts = sku.split('-')
                if len(sku_parts) >= 3:
                    mat_code = sku_parts[2][:3]
                    col_code = sku_parts[2][3:]
                else:
                    mat_code = "000"
                    col_code = "000"

                # Find Material Name from code
                mat_name = "Default"
                for (c, s, m), mid in mat_to_id.items():
                    if c == cat and s == sub and mid.endswith(mat_code):
                        mat_name = m
                        break
                
                products.append({
                    'SKU': add_backtick(sku) if sku.startswith('0') else sku,
                    'OriginalName': orig,
                    'CategoryID': cat_to_id.get(cat),
                    'SubCategoryID': sub_to_id.get(sub),
                    'MaterialID': mat_to_id.get((cat, sub, mat_name)),
                    'ColorID': f"COL{col_code}" if col_code != "000" else None,
                    'StockQty': 0
                })

    # SAVE ALL FILES
    def save_csv(filename, data, fields):
        path = os.path.join(base_dir, filename)
        with open(path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_NONNUMERIC, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)
        print(f"Berhasil dibuat: {filename}")

    save_csv('AppSheet_Categories.csv', categories, ['CategoryID', 'CategoryName', 'CategoryCode'])
    save_csv('AppSheet_SubCategories.csv', sub_categories, ['SubCategoryID', 'SubCategoryName', 'SubCategoryCode'])
    save_csv('AppSheet_Materials.csv', materials, ['MaterialID', 'SubCategoryID', 'CategoryID', 'MaterialName', 'MaterialCode'])
    save_csv('AppSheet_Colors.csv', colors, ['ColorID', 'ColorName', 'ColorCode'])
    save_csv('AppSheet_Products.csv', products, ['SKU', 'OriginalName', 'CategoryID', 'SubCategoryID', 'MaterialID', 'ColorID'])

if __name__ == "__main__":
    prepare_appsheet()

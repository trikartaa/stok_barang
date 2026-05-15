import csv
import os
import re

def standardize_stock():
    # Cek file di folder saat ini atau di folder 'batch'
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [base_dir, os.path.join(base_dir, 'batch')]
    
    souvenir_file = None
    undangan_file = None
    for path in possible_paths:
        s_file = os.path.join(path, 'Stock - Souvenir.csv')
        u_file = os.path.join(path, 'Stock - Undangan.csv')
        if os.path.exists(s_file) and os.path.exists(u_file):
            souvenir_file = s_file
            undangan_file = u_file
            break
            
    if not souvenir_file:
        print(f"Error: File CSV tidak ditemukan.")
        return

    # Daftar Warna Standar
    COLOR_KEYWORDS = [
        'PUTIH', 'HITAM', 'MERAH', 'BIRU', 'KUNING', 'HIJAU', 'COKLAT', 
        'ABU', 'ABU-ABU', 'ORANGE', 'ORANYE', 'UNGU', 'PINK', 'GOLD', 
        'SILVER', 'BENING', 'TRANSPARAN', 'NAVY', 'KREM', 'IVORY', 
        'ROSEGOLD', 'RAINBOW', 'MARBLE', 'DOFF', 'GLOSSY', 'RANDOM', 'MIX'
    ]

    def clean_name(full_name, sub_cat):
        # 1. Hilangkan kata Sub Kategori dari Nama Barang
        pattern = re.compile(re.escape(sub_cat), re.IGNORECASE)
        cleaned = pattern.sub('', full_name).strip()
        
        # 2. BERSIHKAN TANDA HUBUNG (-) YANG TERSISA
        # Hapus strip di awal, akhir, atau strip ganda
        cleaned = re.sub(r'^-+', '', cleaned) # Hapus strip di awal
        cleaned = re.sub(r'-+$', '', cleaned) # Hapus strip di akhir
        cleaned = re.sub(r'\s*-+\s*', ' ', cleaned) # Ganti strip di tengah dengan spasi jika dikelilingi spasi
        
        cleaned = " ".join(cleaned.split()).strip()
        return cleaned

    def extract_color_v2(name):
        if not name:
            return "", ""
            
        words = name.split()
        mat_words = []
        found_colors = []
        
        for word in words:
            # Bersihkan karakter non-alfabet untuk pengecekan (seperti koma)
            clean_word = re.sub(r'[^a-zA-Z-]', '', word).upper()
            
            if clean_word in COLOR_KEYWORDS:
                if clean_word == 'MIX':
                    found_colors.append('Random')
                elif clean_word == 'RANDOM':
                    found_colors.append('Random')
                else:
                    found_colors.append(word)
            else:
                mat_words.append(word)
                
        material = " ".join(mat_words).strip()
        
        # BERSIHKAN MATERIAL SEKALI LAGI (Jika setelah warna diambil masih ada strip)
        material = re.sub(r'^-+', '', material).strip()
        material = re.sub(r'-+$', '', material).strip()
        
        color = " ".join(found_colors).strip()
        return material, color

    def process_file(file_path):
        results = []
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Kategori'] in ['Kategori', 'SubKategori', 'Material', 'Warna']:
                    continue
                
                cat_name = row['Kategori']
                sub_cat_name = row['Sub Kategori']
                original_name = row['Nama Barang']
                
                # Standarisasi
                cleaned = clean_name(original_name, sub_cat_name)
                material, color = extract_color_v2(cleaned)
                
                if not material and not color:
                    material = cleaned if cleaned else original_name

                results.append({
                    'Kategori': cat_name,
                    'Sub Kategori': sub_cat_name,
                    'Nama Barang Original': original_name,
                    'Material (Standard)': material,
                    'Warna (Standard)': color
                })
        return results

    print("Sedang memproses standarisasi data (Pembersihan Tanda Hubung & Sub-Kategori)...")
    souvenir_results = process_file(souvenir_file)
    undangan_results = process_file(undangan_file)

    fieldnames = ['Kategori', 'Sub Kategori', 'Nama Barang Original', 'Material (Standard)', 'Warna (Standard)']

    def save_standard(file_path, data):
        out = file_path.replace('.csv', ' - Standardized.csv')
        with open(out, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"File standar berhasil diperbarui: {out}")

    save_standard(souvenir_file, souvenir_results)
    save_standard(undangan_file, undangan_results)

if __name__ == "__main__":
    standardize_stock()

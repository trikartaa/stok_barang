# Panduan Sistem & Aturan SKU Trikarta

Dokumen ini mendeskripsikan struktur, aturan, dan daftar kode yang digunakan dalam sistem penomoran SKU Trikarta secara otomatis melalui skrip Python.

## 1. Struktur SKU
Setiap SKU terdiri dari 4 blok kode utama dengan format:
**`TKR-{Kategori}{SubKategori}-{Material}{Warna}`**

| Blok | Deskripsi | Format | Contoh |
| :--- | :--- | :--- | :--- |
| **Prefix** | Identitas Perusahaan | Teks Tetap | `TKR` |
| **Kategori** | ID Kategori Utama | 3 Digit | `001` (SOV) |
| **Sub-Kategori** | ID Jenis Barang | 3 Digit | `005` (TOPLES) |
| **Material** | Range Kode Material | 3 Digit | `101` (KERAMIK) |
| **Warna** | ID Variasi Unik | 3 Digit | `010` (MOTIF DETAIL) |

---

## 2. Aturan & Daftar Kode Kategori
Kategori ditentukan berdasarkan file sumber data.
- **001**: SOV (Souvenir)
- **002**: UND (Undangan)
- **003**: KEMASAN
- **004**: PITA & KAIN
- **005**: INVENTORY

---

## 3. Aturan & Daftar Kode Sub-Kategori
Sub-kategori diurutkan secara manual sesuai daftar prioritas berikut. Jika ada sub-kategori baru di luar daftar ini, sistem akan memberikan nomor urut otomatis mulai dari `018`.

| Kode | Nama Sub-Kategori | Keterangan |
| :--- | :--- | :--- |
| **001** | AROMATHERAPHY | Termasuk Botol, Stik, Oil |
| **002** | BOTOL | |
| **003** | TERMOS | |
| **004** | TUMBLER | |
| **005** | TOPLES | Termasuk Toples Crystal |
| **006** | PIRING | Default: Keramik |
| **007** | GELAS | |
| **008** | MUG | Default: Keramik |
| **009** | MANGKOK | Default: Keramik |
| **010** | HANDSOAP | Termasuk Keramik, Resin, Kaca |
| **011** | SENDOK | |
| **012** | GARPU | |
| **013** | SUMPIT | |
| **014** | SGS | |
| **015** | HANDUK | |
| **016** | TEA CUP | |
| **017** | PAYUNG | |

---

## 4. Aturan & Daftar Range Kode Material
Material ditentukan menggunakan sistem **Range 100**. Angka digit pertama menentukan kelompok materialnya.

| Range Kode | Material | Aturan Identifikasi |
| :--- | :--- | :--- |
| **001 - 100** | **Default** | Barang tanpa material khusus atau **Crystal** (khusus Toples) |
| **101 - 200** | **Keramik** | Nama mengandung `KERAMIK` atau kategori **Mangkok/Piring/Mug** |
| **201 - 300** | **Resin** | Nama mengandung `RESIN` atau inisial `R` (pada Handsoap) |
| **301 - 400** | **Kaca** | Nama mengandung `KACA` |
| **401 - 500** | **Stainless** | Nama mengandung `STAINLESS` |

*Catatan: Jika Mangkok/Piring/Mug tertulis `KACA`, maka ia akan masuk ke range 301, bukan 101.*

---

## 5. Aturan Kode Warna (Variasi Unik)
Sistem menggunakan pendekatan **Varian Unik**. Setiap kombinasi detail motif/warna dianggap sebagai satu identitas unik untuk akurasi stok.

- **Logika:** Sistem akan mengambil teks dari Nama Barang, menghapus nama Sub-Kategori dan kata kunci Material, kemudian **menyaring** kata-kata yang tersisa agar hanya menyertakan kata kunci warna atau motif yang terdaftar (misalnya: PUTIH, GOLD, GUCCI, BUNGA).
- **Pembersihan:** Kata-kata yang tidak terkait warna/motif (seperti ukuran '30ml', tipe 'tutup', atau deskripsi teknis lainnya) akan dibuang dari Nama Variasi untuk menjaga kebersihan data di AppSheet.
- **Daftar Kode:** Kode warna dibuat otomatis secara berurutan (`001`, `002`, dst) berdasarkan kombinasi warna/motif unik yang telah disaring. Jika tidak ditemukan kata kunci warna, akan menggunakan `DEFAULT`.

### Contoh Kasus:
1. `HANDSOAP R GUCCI NATURAL`
   - Sub-Kat: `HANDSOAP` (010)
   - Material: `RESIN` (Range 201)
   - Warna: `GUCCI NATURAL` (001)
   - **SKU: TKR-001010-201001**

2. `MANGKOK SENDOK MOTIF PINK SOFT`
   - Sub-Kat: `MANGKOK` (009)
   - Material: `KERAMIK` (Default Mangkok - Range 101)
   - Warna: `SENDOK MOTIF PINK SOFT` (001)
   - **SKU: TKR-001009-101001**

---

## 6. Pemeliharaan Sistem
Untuk memperbarui data, jalankan perintah berikut secara berurutan:
1. `python process_all_stock.py` (Menghasilkan SKU & Aturan Master)
2. `python prepare_appsheet_data.py` (Menyiapkan data untuk upload AppSheet)

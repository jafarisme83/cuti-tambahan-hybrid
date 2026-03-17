# FORM CUTI GENERATOR - STREAMLIT (HYBRID: INPUT SAJA, PDF OLEH APPS SCRIPT)
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Form Cuti Generator",
    page_icon="📄",
    layout="wide"
)

# Opsional: sembunyikan sidebar sepenuhnya
st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] {display: none;}
    [data-testid="stSidebar"][aria-expanded="false"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================
# CONFIGURATION
# ============================================
COUNTER_FILE = "nomor_surat_counter.txt"  # Jika ingin nomor surat dari Python (opsional)

# ============================================
# FUNCTIONS
# ============================================
@st.cache_resource
def setup_gsheets_from_secrets():
    """Setup Google Sheets connection menggunakan st.secrets"""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_dict = dict(st.secrets["gcp_service_account"])
    spreadsheet_id = st.secrets["app"]["spreadsheet_id"]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict, scope
    )
    client = gspread.authorize(creds)
    ss = client.open_by_key(spreadsheet_id)

    sheet_pegawai = ss.worksheet("DataPegawai")
    sheet_form = ss.worksheet("FormCuti")  # pastikan sheet ini sudah dibuat

    return sheet_pegawai, sheet_form


def get_pegawai_data(sheet_pegawai):
    """Ambil data pegawai dari sheet DataPegawai"""
    data = sheet_pegawai.get_all_records()

    pegawai_dict = {}
    for row in data:
        pegawai_dict[row["Nama"]] = {
            "nip": str(row["NIP"]),
            "jabatan": row["Jabatan"],
            "atasan": row["Atasan Langsung"],
            "nip_atasan": str(row["NIP Atasan"]),
        }

    return pegawai_dict


def get_next_nomor_surat_local():
    """
    Opsional: auto-increment nomor surat di sisi Python.
    Jika nomor surat akan dikelola di Apps Script, fungsi ini boleh tidak dipakai.
    """
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            current = int(f.read().strip() or "0")
    else:
        current = 0

    next_number = current + 1

    with open(COUNTER_FILE, "w") as f:
        f.write(str(next_number))

    return f"{next_number:04d}"

# ============================================
# STREAMLIT APP
# ============================================
def main():
    st.title("📄 Form Cuti Generator")
    st.markdown(
        "**Hybrid Mode:** Input via Streamlit → Data ke Google Sheets → PDF dibuat otomatis oleh Apps Script."
    )

    # Koneksi ke Google Sheets
    try:
        with st.spinner("Menghubungkan ke Google Sheets..."):
            sheet_pegawai, sheet_form = setup_gsheets_from_secrets()
            pegawai_data = get_pegawai_data(sheet_pegawai)

        st.success(f"✅ Berhasil memuat data {len(pegawai_data)} pegawai")
    except Exception as e:
        st.error(
            "❌ Gagal menghubungkan ke Google Sheets.\n"
            "Pastikan `gcp_service_account` dan `app.spreadsheet_id` sudah benar di secrets, "
            "serta sheet `DataPegawai` dan `FormCuti` sudah ada."
        )
        st.code(str(e))
        st.stop()

    # =============================
    # FORM INPUT UTAMA
    # =============================
    st.header("📝 Isi Formulir Cuti")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Data Pegawai")
        nama_pegawai = st.selectbox(
            "Nama Pegawai *",
            options=list(pegawai_data.keys()),
        )

        info = None
        if nama_pegawai:
            info = pegawai_data[nama_pegawai]
            st.info(
                f"**NIP:** {info['nip']}\n\n"
                f"**Jabatan:** {info['jabatan']}\n\n"
                f"**Atasan:** {info['atasan']}\n\n"
                f"**NIP Atasan:** {info['nip_atasan']}"
            )

        tanggal_surat = st.date_input("Tanggal Surat *")
        tanggal_surat_str = tanggal_surat.strftime("%d-%B-%Y")

        masa_kerja = st.text_input(
            "Masa Kerja *",
            placeholder="Contoh: 5 tahun 3 bulan",
        )

        jumlah_hari = st.number_input(
            "Jumlah Hari Cuti *",
            min_value=1,
            value=1,
        )

        col_tgl1, col_tgl2 = st.columns(2)
        with col_tgl1:
            tanggal_mulai = st.date_input("Tanggal Mulai Cuti *")
        with col_tgl2:
            tanggal_selesai = st.date_input("Tanggal Selesai Cuti *")

        tanggal_mulai_str = tanggal_mulai.strftime("%d-%B-%Y")
        tanggal_selesai_str = tanggal_selesai.strftime("%d-%B-%Y")

        alasan_cuti = st.text_area(
            "Alasan Cuti *",
            placeholder="Tulis alasan cuti",
        )

    with col2:
        st.subheader("Sisa Cuti & Kontak")
        cuti_tahunan_sisa1 = st.number_input(
            "Sisa Cuti Tahunan 2025 *",
            min_value=0,
            value=0,
        )

        cuti_tahunan_sisa2 = st.number_input(
            "Sisa Cuti Tahunan 2026 *",
            min_value=0,
            value=0,
        )

        cuti_tambahan_sisa = st.number_input(
            "Sisa Cuti Tambahan 2026 *",
            min_value=0,
            value=0,
        )

        alamat_cuti = st.text_area(
            "Alamat Selama Cuti *",
            placeholder="Masukkan alamat lengkap",
        )

        telp_cuti = st.text_input(
            "Telepon Selama Cuti *",
            placeholder="Contoh: 081234567890",
        )

    st.divider()

    # =============================
    # BUTTON KIRIM KE SHEETS
    # =============================
    if st.button("📤 Kirim Data ke Google Sheets", type="primary", use_container_width=True):
        required = [
            nama_pegawai,
            masa_kerja,
            alasan_cuti,
            alamat_cuti,
            telp_cuti,
        ]
        if not all(required) or not info:
            st.error("⚠️ Mohon lengkapi semua field yang wajib diisi (*)")
        else:
            try:
                with st.spinner("⏳ Mengirim data ke sheet FormCuti..."):
                    timestamp = datetime.now().isoformat()

                    # Jika nomor surat ingin di-generate di Python, aktifkan baris ini:
                    # nomor_surat = get_next_nomor_surat_local()
                    # Jika nomor surat nanti diisi Apps Script, biarkan kosong:
                    nomor_surat = ""

                    row_values = [
                        timestamp,                # 1. Timestamp
                        nama_pegawai,             # 2. NamaPegawai
                        info["nip"],              # 3. NIPPegawai
                        info["jabatan"],          # 4. Jabatan
                        info["atasan"],           # 5. AtasanLangsung
                        info["nip_atasan"],       # 6. NIPAtasan
                        tanggal_surat_str,        # 7. TanggalSurat
                        masa_kerja,               # 8. MasaKerja
                        int(jumlah_hari),         # 9. JumlahHari
                        tanggal_mulai_str,        # 10. TanggalMulai
                        tanggal_selesai_str,      # 11. TanggalSelesai
                        alasan_cuti,              # 12. AlasanCuti
                        int(cuti_tahunan_sisa1),  # 13. CutiTahunanSisa1
                        int(cuti_tahunan_sisa2),  # 14. CutiTahunanSisa2
                        int(cuti_tambahan_sisa),  # 15. CutiTambahanSisa
                        alamat_cuti,              # 16. AlamatCuti
                        telp_cuti,                # 17. TelpCuti
                        nomor_surat,              # 18. NomorSurat (boleh kosong)
                        "PENDING",                # 19. Status
                        "",                       # 20. PDF URL
                    ]

                    sheet_form.append_row(row_values)

                st.success("✅ Data berhasil dikirim ke Google Sheets (FormCuti).")
                st.info(
                    "📄 PDF akan dibuat otomatis oleh Apps Script di Google Sheets.\n\n"
                    "- Status awal: `PENDING` di kolom Status.\n"
                    "- Setelah Apps Script jalan, Status menjadi `DONE` dan kolom `PDF URL` terisi link file PDF.\n"
                    "- Anda bisa membuka sheet `FormCuti` untuk melihat progres."
                )

            except Exception as e:
                st.error(f"❌ Terjadi error saat mengirim data ke Google Sheets: {str(e)}")

    # =============================
    # INFORMASI HYBRID
    # =============================
    st.markdown("---")
    st.subheader("ℹ️ Penjelasan Alur Hybrid")
    st.markdown(
        """
1. Aplikasi ini **tidak membuat PDF langsung** di Streamlit / server Python.  
2. Data yang Anda isi dikirim ke sheet **FormCuti** dengan status `PENDING`.  
3. **Google Apps Script** (yang berjalan di sisi Google Sheets) akan:
   - Membaca baris `PENDING`,
   - Mengisi template Google Docs,
   - Export ke PDF,
   - Mengisi kolom `PDF URL` & mengubah `Status` menjadi `DONE`,
   - (Opsional) mengirim email berisi PDF ke pegawai/atasan.
        """
    )


if __name__ == "__main__":
    main()

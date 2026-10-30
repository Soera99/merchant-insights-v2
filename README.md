# Merchant Dashboard — Free + Advanced

Satu aplikasi Streamlit, satu repository, satu image Docker, dan satu service Cloud Run.
Halaman default tetap Free sehingga URL iframe lama tetap membuka dashboard yang sama.
Tidak ada menu tambahan pada iframe. Pilihan dashboard ditentukan oleh web partner.

## Struktur

| Path | Tanggung jawab |
| --- | --- |
| `app.py` | Entry point Streamlit dan pemilihan halaman |
| `shared/routing.py` | Validasi parameter `dashboard`; hanya `free` dan `advanced` |
| `dashboards/free.py` | UI Free / Merchant Insights (Altair) |
| `dashboards/advanced.py` | UI Advanced dan lima tab intelligence (Plotly) |
| `services/free_data.py` | Repository mock/API free, kontrak data dan normalisasi |
| `services/advanced_data.py` | Model KPI dan lima adapter data demo advanced |
| `assets/free/` | Ikon PNG dashboard free |
| `tests/` | Test API free, routing, render, rerun, dan interaksi |
| `.streamlit/config.toml` | Tema light bersama dan konfigurasi server |
| `Dockerfile` | Container Python 3.12, non-root, port 8080 |
| `.github/workflows/deploy.yml` | Test, build image, dan deploy layanan yang sudah ada |
| `docs/DEPLOY_ID.md` | Langkah migrasi GitHub Desktop dan Cloud Run |
| `docs/FREE_API_REFERENCE.md` | Kontrak integrasi backend free dari README asal |
| `docs/ADVANCED_REFERENCE.md` | Referensi README advanced asal |
| `docs/MERGE_NOTES.md` | Ringkasan perubahan, batasan dan hasil validasi |

UI kedua dashboard tetap berada di file masing-masing. Tidak dipaksakan menjadi satu
renderer karena struktur datanya berbeda. Layer data dipisahkan dari UI supaya
integrasi backend berikutnya tidak perlu mengubah routing.

## Menjalankan lokal

Jalankan perintah dari root project:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS / Linux:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Port lokal default paket: **8080**. URL:

- Free (default): http://localhost:8080/
- Free eksplisit: http://localhost:8080/?dashboard=free
- Advanced: http://localhost:8080/?dashboard=advanced

Jalankan melalui `app.py`, bukan masing-masing file di `dashboards/`.
Parameter lain seperti `embed=true` dan `embed_options=light_theme` tetap diterima.
Route tidak dikenal menampilkan error, bukan menjalankan nama file dari URL.

## Data dan akses

Free memakai mock jika `DASHBOARD_DATA_MODE` tidak diisi atau bernilai `mock`.
Set `DASHBOARD_DATA_MODE=api` untuk mengaktifkan API asli, dengan konfigurasi
`DASHBOARD_API_BASE_URL`, `DASHBOARD_USER_ID`, `DASHBOARD_API_TIMEOUT_SECONDS`, dan
`DASHBOARD_API_BEARER_TOKEN` yang sudah didukung project asal. Integrasi repository
custom via `DASHBOARD_REPOSITORY_FACTORY` tetap didukung.

Advanced masih memakai lima adapter demo asli. Menggabungkan hosting tidak otomatis
menghubungkan advanced ke API free. Tidak ada kredensial yang perlu disalin ke kode.

**`dashboard=advanced` adalah pilihan tampilan, bukan bukti hak akses berbayar.**
Routing ini tidak menambahkan login atau entitlement baru. Sebelum advanced menampilkan
data terbatas, BE perlu memvalidasi sesi/token dan hak merchant di server. App free
saat ini memakai `DASHBOARD_USER_ID` dari environment; penggabungan tidak menjadikannya
multi-tenant. Jangan mengganti identitas dengan user ID mentah dari query string.
Jika nantinya per-user, pastikan kunci cache juga memuat identitas dan filter yang sah.

## Deploy

Workflow default meneruskan layanan yang sudah ada:

- Repo yang disarankan: `merchant-insights-v2` (nama repo dapat tetap demikian).
- Cloud Run service: `free-merchant-dashboard`.
- Registry: `anexa-be-repo`, region `asia-southeast2`.
- Satu image kini berisi kedua dashboard; tidak butuh service advanced terpisah.

Workflow mempertahankan env vars, secrets, IAM, dan runtime service account yang sudah
ada pada Cloud Run. Nilai `DASHBOARD_*` di GitHub tidak lagi diterapkan ulang pada
setiap deploy; kelola konfigurasi runtime melalui tim BE/Cloud Run/Secret Manager.
Lihat [panduan deploy](docs/DEPLOY_ID.md) sebelum commit ke main karena push ke main
menjalankan deploy otomatis.

## Test

```bash
python -m unittest discover -s tests -v
```

Test UI memakai Streamlit AppTest dengan data mock. API contract tests memakai respons
mock, bukan backend produksi. Uji browser iframe, WebSocket dan akses produksi tetap
perlu dilakukan setelah deploy.

# Mengganti repo Free menjadi dashboard gabungan

## Pilihan default

Gunakan repo GitHub **merchant-insights-v2** dan service Cloud Run yang sudah berjalan,
**free-merchant-dashboard**. Nama service lama tetap dipakai agar iframe Free yang ada
tidak perlu diganti. Walau namanya mengandung free, service ini melayani kedua UI.
Service advanced-merchant-dashboard dari paket sebelumnya tidak diperlukan untuk
arsitektur gabungan ini. Paket sebelumnya belum dideploy dari sesi ChatGPT.

Jangan menyalin kedua workflow dari paket lama dan paket baru sekaligus. Gunakan satu
workflow `.github/workflows/deploy.yml` dari project gabungan ini.

## 1. Coba lokal dahulu

1. Ekstrak ZIP; folder paling atas bernama `merchant-dashboard`.
2. Buka terminal pada folder tersebut, install requirements, lalu jalankan app.py
   mengikuti README. Gunakan data mock untuk uji awal.
3. Periksa http://localhost:8080/?dashboard=free dan
   http://localhost:8080/?dashboard=advanced.
4. Periksa filter dan seluruh tab advanced. Halaman tanpa parameter harus Free.

## 2. Salin ke repository yang sudah ada

1. GitHub Desktop > pilih merchant-insights-v2 > Repository > Show in Explorer/Finder.
2. Buat branch `merge-free-advanced` untuk review dan uji sebelum masuk main.
3. Salin ISI folder merchant-dashboard hasil ekstrak ke root repo, sejajar dengan
   app.py lama. Pilih replace untuk app.py, requirements.txt, README.md, Dockerfile,
   .dockerignore, .gitignore, .streamlit/config.toml, workflow dan env example.
4. Sertakan folder baru dashboards/, services/, shared/, assets/free/, tests/, docs/.
   Tampilkan hidden files agar .github dan .streamlit ikut tersalin.
5. Setelah memeriksa hasil, hapus file root lama data_access.py dan test_data_access.py,
   serta enam PNG lama yang masih langsung di assets/ (add-group.png, checked.png,
   marketing.png, people.png, redeem.png, team.png). Versi aktifnya sudah berada di
   services/free_data.py, tests/test_free_data.py dan assets/free/.
   Jangan hapus aset tambahan milikmu yang tidak ada pada ZIP asal.
6. Jika repo memiliki perubahan baru di luar snapshot yang diunggah, gabungkan dulu
   perubahan tersebut. Paket didasarkan pada snapshot ZIP yang diberikan.
7. Jangan menimpa atau menghapus .git/, .env, atau .streamlit/secrets.toml lokal.
   Paket tidak membawa file-file tersebut. Jangan commit nilai secrets.
8. Commit: `Merge free and advanced dashboards into one Streamlit app`.
   Push branch, review perubahan dan hasil test lokal, kemudian merge ke main.
   Push/merge ke main memicu deploy produksi sesuai workflow.

ZIP ini berisi project lengkap, bukan sekadar file deploy tambahan.

## 3. Pemeriksaan konfigurasi BE

Workflow menggunakan tiga GitHub Repository Variables yang sama dengan repo Free:

| Variable | Keterangan |
| --- | --- |
| GCP_PROJECT_ID | Project ID GCP aktif; bukan project number |
| GCP_WI_PROVIDER | Full resource name provider Workload Identity |
| GCP_SERVICE_ACCOUNT | Email deployment service account |

Defaults yang diambil dari workflow Free unggahan:

| Pengaturan | Nilai |
| --- | --- |
| REGION | asia-southeast2 |
| REPOSITORY | anexa-be-repo |
| IMAGE_NAME | free-merchant-dashboard-image |
| SERVICE | free-merchant-dashboard |

Workflow memeriksa service sudah ada sebelum deploy. Tujuannya mempertahankan runtime
service account, env vars, Secret Manager bindings dan akses publik/private yang telah
berfungsi. Workflow tidak mengubah IAM dan tidak mengisi ulang env vars dari GitHub.
Jika BE selama ini memperbarui DASHBOARD_* dari GitHub Variables/Secrets, kini perubahan
runtime tersebut perlu diterapkan melalui Cloud Run atau source infra tim.

Dengan memakai repo dan service yang sama, WIF biasanya bisa dipakai ulang. BE tetap
perlu memastikan IAM masih mengizinkan push image dan update Cloud Run dengan runtime
SA yang ada. Jika memilih repo baru, tambahkan trust WIF dan binding repo baru; jangan
membuka trust untuk seluruh GitHub.

Jika ingin service bernama `merchant-dashboard`, ubah SERVICE dan IMAGE_NAME, lalu BE
harus provisioning service baru beserta runtime SA, env/secrets dan IAM terlebih dahulu.
Workflow ini tidak membuat service baru secara otomatis. Gunakan status.url layanan baru
untuk kedua iframe; URL lama tetap mengarah ke layanan lama.

## 4. Cloud Run tetap siap

Paket memakai service-level min=1, max=3, RAM 1Gi, CPU 1, session affinity aktif dan
request timeout 3600 detik. Minimum 1 menahan instance tetap siap saat sepi, dengan biaya
idle. Ini bukan jaminan uptime 100%; instance dapat restart. Ukuran resource perlu
ditinjau setelah uji beban karena kini satu service melayani dua dashboard.

WebSocket dibatasi timeout Cloud Run (maksimum 60 menit). Periksa reconnect sesudahnya;
state/cache di memori dapat hilang setelah restart atau perpindahan instance. Session
affinity bersifat best effort. Dua halaman berbagi pool resource dan siklus deploy.
Jika ada Terraform/pipeline infra lain, selaraskan konfigurasi ini agar tidak tertimpa.

## 5. Iframe web partner

Jika mempertahankan service dan project lama, Free yang sudah ada tetap valid:

```html
<iframe
  src="https://free-merchant-dashboard-735112988988.asia-southeast2.run.app/?embed=true&embed_options=light_theme"
  title="Business Insight Dashboard"
  loading="lazy"
  style="width: 100%; height: 1200px; border: 0;"
></iframe>
```

Advanced memakai host yang sama:

```html
<iframe
  src="https://free-merchant-dashboard-735112988988.asia-southeast2.run.app/?dashboard=advanced&embed=true&embed_options=light_theme"
  title="Advanced Merchant Dashboard"
  loading="lazy"
  style="width: 100%; height: 1200px; border: 0;"
></iframe>
```

Verifikasi URL aktual dari GitHub Actions Summary atau Cloud Run status.url. Contoh di
atas berdasarkan iframe yang diberikan pengguna; domain tidak diverifikasi dengan
akun GCP dari sesi ini. Kedua URL baru bekerja setelah kode gabungan berhasil dideploy.

Jika web memakai CSP frame-src, host tidak berubah pada opsi default ini. Login web
partner tidak otomatis mengamankan endpoint Streamlit. Jika advanced perlu dibatasi,
BE harus memasang otorisasi server, termasuk pembatasan data merchant. Embed dan pilihan
route tidak menyembunyikan halaman advanced dari pengguna yang tahu URL-nya.

## 6. Uji produksi dan rollback

- Cek URL Free lama, explicit dashboard=free, dan dashboard=advanced.
- Cek ikon, chart, filter, kelima tab advanced dan ukuran iframe di browser partner.
- Pastikan mode data Free sebelumnya tetap aktif dan API error tidak bertambah.
- Cek /_stcore/health dan koneksi WebSocket /_stcore/stream.
- Uji setelah idle dan sesi >60 menit; periksa reconnect dan filter.
- Periksa memory, latency dan concurrency sebelum memperbesar max instances.

Sebelum merge ke main, BE catat revision Cloud Run yang saat ini melayani traffic.
Jika ada masalah, BE arahkan traffic kembali ke revision tersebut lewat Cloud Run
Console > Revisions, lalu revert commit merge dan perbaiki di branch. Paket tidak
mematikan atau menghapus layanan lama yang mungkin sudah ada. Jika nanti mematikan
service terpisah yang tidak terpakai, lakukan setelah memeriksa dependensinya.

Referensi resmi:
- https://docs.streamlit.io/develop/api-reference/navigation/st.navigation
- https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest
- https://docs.cloud.google.com/run/docs/configuring/min-instances
- https://docs.cloud.google.com/run/docs/triggering/websockets

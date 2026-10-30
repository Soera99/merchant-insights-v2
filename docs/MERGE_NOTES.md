# Merge notes

## Snapshot inputs

- Free: merchant-insights-v2-main ZIP, GitHub archive commit
  265f38af51d5081a03478dee90fc27605851718e.
- Advanced: merchant-dashboard-advanced-main ZIP, GitHub archive commit
  2cbd5a48d30acaa3009e2e02bb1de1629c33b7d4.
- Tidak ada commit/push GitHub atau perubahan layanan GCP dari sesi penggabungan.

## Perubahan

- Root app.py menjadi router native Streamlit st.Page/st.navigation, dengan navigasi
  tersembunyi dan allowlist query parameter dashboard.
- Default Free mempertahankan kompatibilitas URL iframe lama.
- Free UI dipindah ke dashboards/free.py. Import data layer dan path aset disesuaikan;
  isi chart, logika UI dan API adapter tidak diubah.
- Free data_access.py dipindah utuh ke services/free_data.py.
- Advanced UI dipindah ke dashboards/advanced.py. Model KPI, make_kpis, seri trend demo
  serta kelima loader dipindah ke services/advanced_data.py. Token warna seri dipakai
  dari shared/theme.py. Isi dataset dan fungsi render asli dipertahankan.
- Ikon Free dipindahkan ke assets/free/. Aplikasi lain tidak membawa aset lokal.
- Dependency kedua aplikasi digabung dan versi langsung dikunci pada versi yang diuji:
  Streamlit 1.66.1, Altair 6.3.0, pandas 2.2.3, Plotly 6.9.0, Python 3.12.
  Dependency transitif belum dikunci penuh.
- Config server dan tema light disatukan; advanced theme menjadi dasar tema bersama.
  Native widgets Free kini mengikuti tema bersama, dengan CSS dashboard asli tetap ada.
- Docker memakai user non-root dan hanya menyalin folder runtime.
- Workflow deploy menguji kedua halaman dan mempertahankan service/registry Free yang
  ada. Env/secrets runtime tidak ditimpa dari GitHub saat deploy.
- Test Free lama disesuaikan dengan kontrak kode terkini: endpoint /api/v1/cep/dashboard,
  mode api harus eksplisit, dan target patch sesuai lokasi modul baru. Perubahan tersebut
  memperbaiki test yang sudah tertinggal dari snapshot kode; endpoint aplikasi tidak diganti.

## Validasi

- 19 unittest lulus: 9 kontrak/factory data Free, 3 routing, 7 smoke/interaction Streamlit.
- AppTest menjalankan entry point asli, memeriksa default Free, route eksplisit,
  rerun, perubahan route pada sesi yang sama, invalid route, filter province/city Free,
  serta Add Filter / Apply / Clear advanced. Seluruh lima tab advanced dirender.
- API tests memakai respons mock dan tidak menghubungi backend produksi.
- Sintaks semua file Python, konfigurasi TOML, workflow YAML dan shell workflow diperiksa.
- Data adapter Free identik byte dengan aslinya, PNG identik byte, dan model/loader
  advanced mempertahankan AST fungsi asli setelah dipindah.
- Server lokal diuji terpisah dari AppTest: health dan HTTP entry point kedua route.
  HTTP 200 memverifikasi server/shell; bukti render berasal dari AppTest.
- Build Docker dan deploy GCP belum dijalankan. Browser iframe produksi, CSP/cookie,
  reconnect WebSocket, cold start, IAM/WIF dan beban produksi perlu diuji setelah deploy.

## Batasan yang tetap ada

Advanced tetap demo; data Free bisa mock atau API sesuai env runtime lama.
Query parameter tidak menambahkan entitlement, login, atau isolasi tenant.
Konfigurasi user ID Free tetap bersifat environment aplikasi.
Filter advanced mempertahankan perilaku prototype asli; bukan bukti data sudah
terfilter dari backend. State/cache memori tidak persisten setelah instance restart.
Satu layanan berarti resource dan siklus deploy bersama. Kebutuhan isolasi yang lebih
kuat dapat menjadi alasan memisahkan service kembali di masa depan.

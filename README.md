# File Sharing Bot v4.5.0

Bot Telegram untuk menyimpan file dan berbagi melalui link khusus dengan fitur lengkap.

## 🌟 Fitur

- **File Sharing**: Simpan file di channel dan bagi melalui link khusus
- **Persistent Database**: PostgreSQL support untuk data yang tidak hilang saat redeploy
- **Multiple Force Subscriptions**: Support multiple channels/groups untuk force subscription
- **Join Request Auto-Approve**: Channel/group force-sub yang dipasangi mode "Approve New Members" otomatis di-approve bot (bot harus jadi admin di channel/group tersebut)
- **Real-time User Tracking**: Simpan status subscribe user secara real-time tanpa reset
- **Auto Command Registration**: Commands otomatis terdaftar di menu bot Telegram
- **Heroku Management**: Set/unset environment variables via bot
- **Speedtest**: Cek kecepatan server real-time
- **Admin Commands**: Management tools lengkap untuk admin
- **Broadcast**: Kirim pesan ke semua user sekaligus
- **User Management**: Statistik pengguna & profile management
- **Content Protection**: Proteksi file dengan custom limits
- **Custom Buttons**: Tambahkan tombol promosi kustom
- **Feedback System**: Sistem feedback & report dari user
- **Advanced Analytics**: Monitoring penggunaan & performa
- **Multi-Platform**: Support deployment di Heroku, VPS, Docker
- **Data Persistence**: Data user tersimpan aman meski redeploy
- **Database Backup/Restore**: Backup & restore database lengkap dengan data user
- **Persistent Button & Content Settings**: Custom button, custom message, protected content, dan limit konten tersimpan di database (bukan file lokal) sehingga aman dari redeploy
- **Persistent Profile & Feedback**: Statistik profil, feedback, dan laporan user tersimpan di database (bukan file lokal) sehingga aman dari redeploy
- **Media Broadcasting**: Support broadcast dengan media (photo/video/document)
- **Rich Message Formatting**: Format bold/italic/blockquote di `/broadcast` & `/setmsg` otomatis kepakai persis seperti teks yang diketik/copy-paste — gak perlu ngetik tag HTML manual
- **Enhanced /setmsg & /addbutton**: Support media attachments, plus tombol "➕ Tambah Button" buat nambah button secara interaktif (gak perlu ngetik format `[Text](URL)`)
- **Broadcast Preview**: `/broadcast` kirim preview ke admin dulu (placeholder udah keisi) sebelum kekirim ke semua user, tinggal konfirmasi lewat tombol
- **Personalized Messages**: Placeholder variables untuk pesan personal ({ID},{NAME},{USERNAME},{DATE}, dll)
- **Dynamic Content**: Real-time user data replacement di broadcast messages
- **File Search**: Cari file berdasarkan nama via `/search` atau inline query (`@botusername keyword`) langsung dari chat manapun
- **Anti-Leech Verification**: Verifikasi 2 langkah dalam bot (tanpa shortlink eksternal) sebelum user bisa ambil file, opsional & bisa diatur admin
- **Visual Analytics Dashboard**: `/analytics` generate grafik pertumbuhan user, downloads harian, distribusi rank, dan leaderboard sebagai gambar
- **Multi-Bahasa (ID/EN)**: Pesan inti (alur ambil file, /about, error/limit) otomatis mengikuti bahasa Telegram user (auto-detect), atau bisa diganti manual via `/language`
- **Adaptive Broadcast Throttling**: Delay & concurrency broadcast otomatis menyesuaikan saat FloodWait meningkat, lalu kembali normal saat aman

## 🚀 Deployment

### Heroku
1. Fork repository ini
2. Deploy ke Heroku
3. Set environment variables di Heroku dashboard
4. Use "bash start" sebagai start command

### Manual
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `sevalla-env-template.env` ke `.env`
3. Isi semua variabel environment yang diperlukan
4. Jalankan: `python main.py`

## ⚙️ Environment Variables

### Required
- `TG_BOT_TOKEN`: Token bot dari @BotFather
- `APP_ID`: API ID dari my.telegram.org
- `API_HASH`: API Hash dari my.telegram.org
- `CHANNEL_ID`: ID channel untuk database
- `OWNER`: ID owner bot

### Database (Choose One)
- `DATABASE_URL`: PostgreSQL URL untuk persistent data (Recommended)
  - Format: `postgresql://username:password@host:port/database`
  - Example: `postgresql://user:pass@localhost:5432/bot_db`
- Default: `sqlite:///bot_database.db` (local SQLite, data may reset on redeploy)

### Optional
- Untuk fitur inline search (`@botusername keyword`), aktifkan **Inline Mode** untuk bot melalui @BotFather (`/setinline`)
- `FORCE_SUB_CHANNEL1`: ID channel pertama untuk force subscription
- `FORCE_SUB_CHANNEL2`: ID channel kedua untuk force subscription (opsional)
- `FORCE_SUB_CHANNEL3`: ID channel ketiga untuk force subscription (opsional)
- `FORCE_SUB_GROUP1`: ID group pertama untuk force subscription
- `FORCE_SUB_GROUP2`: ID group kedua untuk force subscription (opsional)
- `FORCE_SUB_GROUP3`: ID group ketiga untuk force subscription (opsional)
  - Kalau channel/group force-sub-nya dipasangi mode Telegram "Approve New Members" (Join Request), bot otomatis approve request itu — tinggal pastikan bot jadi admin dengan izin "Add Users" di channel/group tersebut
- `ADMINS`: List ID admin bot (space separated)
- `HEROKU_APP_NAME`: Nama app Heroku
- `HEROKU_API_KEY`: API key Heroku
- `SEVALLA_API_KEY`, `SEVALLA_PROJECT_ID`, `SEVALLA_SERVICE_ID`: Diperlukan untuk `/setvar`, `/delvar`, `/getvar`, `/setdb`, `/usage` (ambil dari Sevalla dashboard)

## 📱 Commands

### 🤖 Bot Features
- **Auto Command Menu**: Semua commands otomatis terdaftar di menu bot Telegram
- **Real-time Tracking**: Status subscribe user tersimpan real-time
- **Persistent Data**: Data user aman dari redeploy

### User Commands
- `/start` - Mulai bot & generate file links
- `/about` - Informasi lengkap tentang bot
- `/help` - Bantuan lengkap semua perintah
- `/id` - Lihat informasi profile lengkap
- `/profile` - Lihat profil & statistik pengguna
- `/ping` - Test respons bot
- `/uptime` - Lihat status uptime bot
- `/feedback` - Kirim feedback ke developer
- `/report` - Laporkan masalah atau bug
- `/search <kata kunci>` - Cari file berdasarkan nama (juga bisa via inline `@botusername kata kunci`)
- `/language` - Ganti bahasa pesan inti bot (Indonesia/English)
- `/tutorial` - Panduan lengkap penggunaan bot
- `/stats` - Lihat statistik ringkas bot

### Admin Commands
- `/users` - Statistik pengguna bot
- `/broadcast` - Kirim pesan broadcast ke semua user
- `/ping` - Test ping bot
- `/uptime` - Lihat uptime bot
- `/logs` - Download file logs bot
- `/vars` - Lihat semua config variables
- `/speedtest` - Test kecepatan server
- `/info` - Informasi lengkap bot & statistik

### File Management
- Forward message/file ke bot untuk generate sharing link
- `/genlink` - Generate link untuk single file
- `/batch` - Generate link untuk multiple files (range)

### Admin Management
- `/addadmin` - Tambahkan admin baru
- `/deladmin` - Hapus admin dari daftar
- `/getadmin` - Lihat daftar admin

### Database Management
- `/getdb` - Informasi database
- `/setdb` - Set database configuration
- `/backupdb` - Backup database
- `/restoredb` - Restore database dari backup
- `/cleardb` - Clear database (PERINGATAN: BERBAHAYA!)

### Content & Button Management
- `/addbutton` - Tambahkan custom button
- `/delbutton` - Hapus custom button
- `/getbutton` - Lihat daftar custom buttons
- `/limitbutton` - Enable/disable custom button feature
- `/setmsg` - Set custom message untuk berbagai situasi
- `/addkonten` - Tambahkan file ke protected list
- `/delkonten` - Hapus file dari protected list
- `/getkonten` - Lihat daftar protected content
- `/limitkonten` - Set limit untuk konten tertentu

### User Limit Management (Admin)
- `/setlimit JUMLAH` - Set limit download harian global (0-50, 0 = nonaktifkan download untuk semua user)
- `/getlimit` - Lihat limit harian saat ini
- `/setuserlimit USER_ID LIMIT` - Set limit custom per user (0-1000, 0 = blokir user ini)
- `/deluserlimit USER_ID` - Hapus limit custom user (kembali ke limit global)
- `/getuserlimits` - Lihat semua user dengan limit custom
- `/userstats` - Statistik download semua user hari ini
- `/resetlimits` - Reset semua limit download user
- `/checkuser USER_ID` - Cek status limit user tertentu

### Anti-Leech Verification (Admin)
- `/setverify on|off` - Aktifkan/nonaktifkan verifikasi anti-leech
- `/setverifydelay DETIK` - Atur delay verifikasi (default 10 detik)

### Analytics (Admin)
- `/analytics` - Dashboard visual (grafik pertumbuhan user, downloads harian, distribusi rank, leaderboard)

### Heroku Management
- `/setvar VAR_NAME VAR_VALUE` - Set environment variable
- `/delvar VAR_NAME` - Hapus environment variable
- `/getvar VAR_NAME` - Lihat environment variable
- `/usage` - Monitoring aplikasi Heroku

### Feedback Management (Admin)
- `/viewfeedback` - Lihat feedback dari pengguna
- `/viewreports` - Lihat laporan masalah dari pengguna

## 🏗️ Structure

```
File-Sharing-Man/
├── main.py                 # Entry point aplikasi
├── bot.py                  # Main bot class & initialization
├── config.py              # Configuration, constants & helper functions
├── database/sql.py        # Database operations & user management
├── requirements.txt       # Python dependencies
├── sevalla-env-template.env # Template environment variables
├── Dockerfile            # Docker container configuration
├── start                 # Startup script untuk deployment
├── .gitignore           # Git ignore rules
├── .dockerignore        # Docker ignore rules
└── plugins/              # Bot plugins & features
    ├── start.py          # Start command, user management & broadcast
    ├── button.py         # UI buttons & force subscription
    ├── cbb.py           # Callback query handlers
    ├── channel_post.py   # Channel posting & file management
    ├── getid.py         # User ID lookup & statistics
    ├── heroku.py        # Heroku/Sevalla management tools
    ├── link_generator.py # Link generation untuk file sharing
    ├── search.py         # File search & inline query
    ├── verification.py   # Anti-leech verification
    ├── i18n.py            # ID/EN translations
    ├── language.py        # /language command
    ├── analytics.py        # Visual analytics dashboard
    ├── stats_utils.py      # Shared stats formatting helpers
    ├── speedtest.py     # Server speed test functionality
    ├── utils.py         # Utility functions & admin tools
    ├── admin_management.py    # Admin management system
    ├── button_management.py   # Custom button management
    ├── content_management.py  # Content protection & limits
    └── user_features.py       # User features (profile, feedback, etc.)
```

## 🛠️ Dependencies

- Pyrogram - Telegram client
- Pyromod - Pyrogram mod
- SQLAlchemy - Database ORM
- Heroku3 - Heroku API
- Speedtest - Network speed test
- Python-dotenv - Environment variables

## 📄 License

MIT License - Lihat file LICENSE untuk detail

## 👨‍💻 Credits

- Original Code: @mrismanaziz
- Repository: https://github.com/rabayarantahkiieee/File-Sharing-Mann
- Support: https://t.me/yawrenmaru

## 🔧 Support

Untuk bantuan dan support:
- Developer: https://t.me/yawrenmaru
- Repository: https://github.com/rabayarantahkiieee/File-Sharing-Mann

## 📝 Changelog

### v4.5.0 (Latest)
- ✅ **Media Support untuk Broadcast & Custom Messages**
  - `/broadcast` sekarang support media attachments (photo/video/document)
  - `/setmsg` support media untuk custom messages (welcome/error/limit messages)
  - Rich media broadcasting dengan caption support
  - Automatic media validation & error handling

- ✅ **Enhanced Message Formatting**
  - HTML formatting support di broadcast messages
  - Support untuk `<b>`, `<i>`, `<blockquote>`, `\n` formatting
  - Improved message parsing untuk rich text content
  - Better text rendering di Telegram

- ✅ **Improved /about Command**
  - Added comprehensive bot information
  - Developer credits & contact details
  - Feature overview dengan status indicators
  - Repository & support links

- ✅ **Personalized Broadcasting**
  - Placeholder variables support: {ID}, {NAME}, {SURNAME}, {NAMESURNAME}, {USERNAME}
  - Dynamic content: {MENTION}, {DATE}, {TIME}, {WEEKDAY}, {LANG}
  - Real-time user data replacement di broadcast messages
  - Intelligent placeholder detection untuk optimized performance

- ✅ **Code Optimizations**
  - Better error handling untuk media operations
  - Rate limiting untuk broadcast operations
  - Improved file size validation
  - Enhanced logging untuk media broadcasts

### v4.4.0
- ✅ **Real-time User Subscription Tracking**
  - Simpan status subscribe user secara real-time ke database
  - Tidak ada reset data saat bot restart atau redeploy
  - Persistent tracking untuk multiple channels/groups
  - Automatic user data synchronization

- ✅ **Auto Command Registration**
  - Commands otomatis terdaftar di menu bot Telegram
  - Menu command yang rapi dan terorganisir
  - Support untuk user dan admin commands
  - Dynamic command updates tanpa restart manual

- ✅ **Enhanced Database Management**
  - Improved backup & restore functionality
  - Real user data backup dengan metadata lengkap
  - Better error handling untuk database operations
  - Automatic backup scheduling support

- ✅ **Profile Command Fixes**
  - Fixed /profile command functionality
  - Better user statistics calculation
  - Improved activity tracking dan scoring
  - Enhanced user ranking system

### v4.3.0
- ✅ **Multiple Force Subscriptions Support**
  - Support unlimited channels/groups untuk force subscription
  - Environment variables: `FORCE_SUB_CHANNEL1`, `FORCE_SUB_CHANNEL2`, etc.
  - Automatic detection & configuration tanpa restart manual
  - Backward compatibility dengan single env lama

- ✅ **Enhanced Force Subscription Logic**
  - Refactored helper functions untuk multiple subscriptions
  - Improved button generation untuk semua channels/groups
  - Better subscription status checking di `/id` command
  - Optimized performance untuk multiple checks

- ✅ **Code Improvements**
  - Updated all plugins untuk support multiple force subscriptions
  - Better error handling & logging untuk subscription checks
  - Cleaner code structure dengan list-based processing

### v4.2.0
- ✅ **Persistent Database Implementation**
  - Full PostgreSQL support untuk data persistence
  - SQLAlchemy ORM untuk database operations
  - Data user aman dari redeploy
  - Automatic database migration support

- ✅ **Enhanced User Statistics**
  - Real-time user count & activity tracking
  - Daily active users monitoring
  - Improved `/stats` command dengan detail lengkap
  - Database type detection (PostgreSQL/SQLite)

- ✅ **User Features Enhancement**
  - Add `/profile` command untuk lihat statistik user
  - Add `/feedback` system untuk user feedback
  - Add `/report` untuk melaporkan masalah
  - Add `/tutorial` panduan lengkap penggunaan
  - Add `/donate` informasi dukungan pengembangan
  - Add user data persistence & analytics

- ✅ **Admin Management Expansion**
  - Add `/addadmin`, `/deladmin`, `/getadmin` untuk admin management
  - Add `/viewfeedback`, `/viewreports` untuk admin monitoring
  - Enhanced admin permission system

- ✅ **Content & Button Management**
  - Add custom button management (`/addbutton`, `/delbutton`, `/getbutton`)
  - Add content protection (`/addkonten`, `/delkonten`, `/getkonten`)
  - Add button limits & custom messages (`/limitbutton`, `/setmsg`, `/limitkonten`)

- ✅ **Help & Documentation**
  - Update comprehensive help system
  - Add categorized command listing
  - Enhanced user guidance & tutorials

- ✅ **Code Refactoring**
  - Factorized configuration & constants
  - Improved plugin structure
  - Better error handling & logging
  - Optimized database operations

### v4.0.0
- Add database support (SQLite/PostgreSQL)
- Add Heroku management tools
- Add auto-updater system
- Improve admin commands
- Add speedtest functionality
- Fix force subscription issues
- Add comprehensive error handling

---

**File Sharing Bot** - Bot Telegram untuk file sharing dengan fitur lengkap
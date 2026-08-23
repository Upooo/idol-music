"""Bahasa Indonesia strings for IDOL Music bot."""

# --- System ---
START = (
    "<b>IDOL Music</b> <code>v1.1.0</code>\n\n"
    "Bot musik simple & stabil untuk voice chat Telegram.\n\n"
    "Ketik <code>m!help</code> untuk melihat daftar perintah."
)

HELP = (
    "<b>IDOL Music</b> <code>v1.1.0</code>\n\n"
    "<b>Musik</b>\n"
    "<code>m!p &lt;judul&gt;</code> / <code>m!play &lt;judul&gt;</code> \u2014 putar atau antri\n"
    "<code>m!s</code> / <code>m!skip</code> \u2014 skip (vote / admin)\n"
    "<code>m!pause</code> \u2014 jeda\n"
    "<code>m!resume</code> \u2014 lanjutkan\n"
    "<code>m!np</code> \u2014 sedang diputar\n"
    "<code>m!q</code> / <code>m!queue</code> \u2014 lihat antrian\n"
    "<code>m!stop</code> \u2014 berhenti dan keluar\n"
    "<code>m!leave</code> \u2014 keluar dari voice chat\n"
    "<code>m!autoplay</code> \u2014 aktifkan autoplay\n\n"
    "<b>Sistem</b>\n"
    "<code>m!help</code> \u2014 pesan ini\n"
    "<code>m!ping</code> \u2014 latensi\n"
    "<code>m!lang [en|id]</code> \u2014 ubah bahasa\n"
    "<code>m!cv</code> \u2014 cek listener voice chat\n\n"
    "<b>Catatan</b>\n"
    "\u2022 Request manual selalu prioritas di atas autoplay.\n"
    "\u2022 Siapapun bisa vote skip; admin skip langsung.\n"
    "\u2022 Bot otomatis pause tanpa listener, keluar setelah 5 menit.\n"
    "\u2022 Autoplay tetap nyala sampai m!stop atau auto-leave.\n"
    "\u2022 Maksimal 5 antrian manual saat autoplay aktif."
)

HELP_DEV = (
    "<b>Developer</b>\n"
    "<code>m!restart</code> \u2014 restart bot\n"
    "<code>m!pull</code> \u2014 git pull\n"
    "<code>m!status</code> \u2014 uptime, sesi, info sistem\n"
    "<code>m!logs [n]</code> \u2014 lihat n baris log terakhir\n"
    "<code>m!bc &lt;text&gt;</code> \u2014 broadcast ke grup aktif\n"
    "<code>m!cookie</code> \u2014 lihat/ganti cookies.txt"
)

PING = "Pong! <code>{latency:.0f}ms</code>"

# --- Music ---
PLAY_PROVIDE_QUERY = (
    "Masukkan nama lagu atau URL.\n"
    "Contoh: <code>m!p never gonna give you up</code>"
)
PLAY_GROUPS_ONLY = "Perintah ini hanya bisa digunakan di grup."
PLAY_NOT_ALLOWED = "Kamu tidak diizinkan untuk memutar musik."
PLAY_SEARCHING = "Mencari\u2026"
PLAY_NOT_FOUND = "Lagu tidak ditemukan. Coba kata kunci lain."
PLAY_EXTRACTION_FAILED = (
    "Gagal mengekstrak lagu. Mungkin privat, dihapus, atau tidak didukung."
)
PLAY_QUEUE_FULL = "{error}"
PLAY_SOURCE_ERROR = "{error}"
PLAY_FAILED = (
    "Gagal memulai pemutaran.\n"
    "<i>Pastikan voice chat aktif dan assistant bisa bergabung.</i>"
)
NOW_PLAYING = (
    "<b>Sedang Diputar</b>\n"
    "<code>{title}</code>\n"
    "Durasi: <code>{duration}</code> \u00b7 Oleh: <code>{requester}</code>"
)
ADDED_TO_QUEUE = (
    "<b>Ditambahkan ke antrian</b>\n"
    "<code>{title}</code>\n"
    "Posisi: <code>{position}</code> \u00b7 Autoplay: <code>{autoplay}</code>"
)

# --- Skip ---
SKIP_ADMIN_ONLY = "Hanya admin grup yang bisa skip."
SKIP_NOTHING = "Tidak ada yang sedang diputar."
SKIP_DONE = "Diskip. Sekarang memutar: <code>{title}</code>"
SKIP_EMPTY = "Diskip. Antrian kosong."
SKIP_VOTE_ADDED = "Vote skip: <code>{votes}/{needed}</code>"
SKIP_VOTE_ALREADY = "Kamu sudah vote skip."
SKIP_VOTE_PASSED = "Vote lolos! Skipping..."

# --- Pause / Resume ---
PAUSE_ADMIN_ONLY = "Hanya admin grup yang bisa jeda."
PAUSE_DONE = "Pemutaran dijeda."
PAUSE_NOTHING = "Tidak ada yang sedang diputar."
RESUME_ADMIN_ONLY = "Hanya admin grup yang bisa lanjutkan."
RESUME_DONE = "Pemutaran dilanjutkan."
RESUME_NOTHING = "Tidak ada yang sedang dijeda."

# --- Now Playing ---
NP_NOTHING = "Tidak ada yang sedang diputar."
NP_DISPLAY = (
    "<b>Sedang Diputar</b>\n"
    "<code>{title}</code>\n"
    "Durasi: <code>{duration}</code> \u00b7 Oleh: <code>{requester}</code>"
)

# --- Queue ---
QUEUE_EMPTY = "Antrian kosong."
QUEUE_HEADER = "<b>Antrian</b> ({count} lagu)\n"
QUEUE_ITEM = "{pos}. <code>{title}</code> \u2014 <code>{duration}</code>\n"
QUEUE_NOW_PLAYING = "\U0001f3b5 Sekarang: <code>{title}</code>\n\n"

# --- Stop / Leave ---
STOP_ADMIN_ONLY = "Hanya admin grup yang bisa stop."
STOP_DONE = "Dihentikan. Antrian dibersihkan dan keluar dari voice chat."
LEAVE_ADMIN_ONLY = "Hanya admin grup yang bisa menggunakan leave."
LEAVE_DONE = "Keluar dari voice chat."
LEAVE_NOT_ACTIVE = "Tidak sedang di voice chat."

# --- Autoplay ---
AUTOPLAY_ADMIN_ONLY = "Hanya admin grup yang bisa mengaktifkan autoplay."
AUTOPLAY_ENABLED = "Autoplay <b>diaktifkan</b>. Tetap nyala sampai m!stop atau auto-leave."
AUTOPLAY_DISABLED = "Autoplay <b>dinonaktifkan</b>."
AUTOPLAY_ALREADY_ON = "Autoplay sudah aktif."

# --- Language ---
LANG_CURRENT = "Bahasa saat ini: <code>{lang}</code>"
LANG_SET = "Bahasa diubah ke <code>{lang}</code>."
LANG_INVALID = "Bahasa tidak valid. Tersedia: {languages}"
LANG_ADMIN_ONLY = "Hanya admin grup yang bisa mengubah bahasa."

# --- Check Voice ---
CV_ADMIN_ONLY = "Hanya admin grup yang bisa menggunakan perintah ini."
CV_CHECKING = "Mengecek voice chat\u2026"
CV_RESULT = "\U0001f3a7 Listener di voice chat: <code>{count}</code>"
CV_EMPTY = "\U0001f507 Tidak ada listener di voice chat (hanya assistant)."
CV_UNAVAILABLE = "\u26a0\ufe0f Tidak bisa membaca peserta voice chat."
CV_ERROR = "\u274c Error: <code>{error}</code>"

# --- Auto-leave ---
AUTO_LEAVE = "Tidak ada listener selama 5 menit. Keluar dari voice chat."

# --- Developer ---
DEV_ONLY = "Perintah ini khusus untuk developer."
DEV_RESTART = "Memulai ulang\u2026"
DEV_PULL = "Menarik perubahan terbaru\u2026"
DEV_PULL_RESULT = "<b>git pull</b>\n<code>{output}</code>"
DEV_BC_USAGE = "Gunakan: <code>m!bc &lt;pesan&gt;</code> atau reply ke pesan."
DEV_BC_NO_TARGETS = (
    "Belum ada grup aktif untuk broadcast.\n"
    "(Grup muncul setelah sesi musik dimulai.)"
)
DEV_BC_DONE = "Broadcast selesai. Berhasil: {ok} \u00b7 Gagal: {fail}"
DEV_STATUS = (
    "<b>Status IDOL Music</b>\n"
    "Uptime: <code>{uptime}</code>\n"
    "Sesi aktif: <code>{sessions}</code>\n"
    "Total plays: <code>{total_plays}</code>\n"
    "Python: <code>{python}</code>\n"
    "MongoDB: <code>{mongo}</code>\n"
    "Cookies: <code>{cookies}</code>"
)
DEV_LOGS_USAGE = "Gunakan: <code>m!logs [n]</code> \u2014 tampilkan n baris terakhir (default 50)."
DEV_LOGS_EMPTY = "File log tidak ditemukan."

# --- Cookie Management ---
DEV_COOKIE_STATUS = "Cookies: <code>{size}</code> bytes, <code>{lines}</code> lines."
DEV_COOKIE_NOT_FOUND = "Tidak ada cookies.txt. Reply ke pesan berisi cookie content atau kirim <code>m!cookie &lt;content&gt;</code>."
DEV_COOKIE_UPDATED = "Cookies diperbarui. <code>{lines}</code> baris ditulis."

# --- Log Group ---
LOG_STARTED = (
    "\U0001f7e2 <b>IDOL Music dimulai</b>\n"
    "Bot: @{username}\n"
    "Sesi: {sessions}\n"
    "MongoDB: {mongo}\n"
    "Cookies: {cookies}"
)
LOG_STOPPED = "\U0001f534 <b>IDOL Music berhenti</b> (restart diminta)"
LOG_ERROR = "\u26a0\ufe0f <b>Error di {location}</b>\n<code>{error}</code>"
LOG_SESSION_JOIN = "\U0001f3b5 Bergabung VC di <code>{chat_id}</code>"
LOG_SESSION_LEAVE = "\U0001f507 Keluar VC dari <code>{chat_id}</code>"
LOG_COOKIE_UPDATED = "\U0001f36a Cookies diperbarui via bot command. {lines} baris."
LOG_ASSISTANT_STARTED = "\U0001f916 <b>Assistant dimulai</b>\nNama: {name}\nID: <code>{user_id}</code>"

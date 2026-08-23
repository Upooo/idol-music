"""English strings for IDOL Music bot."""

# --- System ---
START = (
    "<b>IDOL Music</b> <code>v1.1.0</code>\n\n"
    "Simple & stable music bot for Telegram voice chats.\n\n"
    "Use <code>m!help</code> to see available commands."
)

HELP = (
    "<b>IDOL Music</b> <code>v1.1.0</code>\n\n"
    "<b>Music</b>\n"
    "<code>m!p &lt;query&gt;</code> / <code>m!play &lt;query&gt;</code> \u2014 play or queue\n"
    "<code>m!s</code> / <code>m!skip</code> \u2014 skip (vote / admin)\n"
    "<code>m!pause</code> \u2014 pause\n"
    "<code>m!resume</code> \u2014 resume\n"
    "<code>m!np</code> \u2014 now playing\n"
    "<code>m!q</code> / <code>m!queue</code> \u2014 view queue\n"
    "<code>m!stop</code> \u2014 stop and leave\n"
    "<code>m!leave</code> \u2014 leave voice chat\n"
    "<code>m!autoplay</code> \u2014 enable autoplay\n\n"
    "<b>System</b>\n"
    "<code>m!help</code> \u2014 this message\n"
    "<code>m!ping</code> \u2014 latency\n"
    "<code>m!lang [en|id]</code> \u2014 change language\n"
    "<code>m!cv</code> \u2014 check VC listeners\n\n"
    "<b>Notes</b>\n"
    "\u2022 Manual requests always have priority over autoplay.\n"
    "\u2022 Anyone can vote skip; admins skip instantly.\n"
    "\u2022 Bot auto-pauses with no listeners, leaves after 5 min.\n"
    "\u2022 Autoplay stays on until m!stop or auto-leave.\n"
    "\u2022 Max 5 manual queue items when autoplay is on."
)

HELP_DEV = (
    "<b>Developer</b>\n"
    "<code>m!restart</code> \u2014 restart bot\n"
    "<code>m!pull</code> \u2014 git pull\n"
    "<code>m!status</code> \u2014 uptime, sessions, system info\n"
    "<code>m!logs [n]</code> \u2014 show last n log lines\n"
    "<code>m!bc &lt;text&gt;</code> \u2014 broadcast to active groups\n"
    "<code>m!cookie</code> \u2014 view/replace cookies.txt"
)

PING = "Pong! <code>{latency:.0f}ms</code>"

# --- Music ---
PLAY_PROVIDE_QUERY = (
    "Provide a song name or URL.\n"
    "Example: <code>m!p never gonna give you up</code>"
)
PLAY_GROUPS_ONLY = "This command works in groups only."
PLAY_NOT_ALLOWED = "You're not allowed to play music."
PLAY_SEARCHING = "Searching\u2026"
PLAY_NOT_FOUND = "Track not found. Try different keywords."
PLAY_EXTRACTION_FAILED = (
    "Failed to extract track. It might be private, deleted, or unsupported."
)
PLAY_QUEUE_FULL = "{error}"
PLAY_SOURCE_ERROR = "{error}"
PLAY_FAILED = (
    "Couldn't start playback.\n"
    "<i>Make sure a voice chat is active and the assistant "
    "has permission to join.</i>"
)
NOW_PLAYING = (
    "<b>Now Playing</b>\n"
    "<code>{title}</code>\n"
    "Duration: <code>{duration}</code> \u00b7 By: <code>{requester}</code>"
)
ADDED_TO_QUEUE = (
    "<b>Added to queue</b>\n"
    "<code>{title}</code>\n"
    "Position: <code>{position}</code> \u00b7 Autoplay: <code>{autoplay}</code>"
)

# --- Skip ---
SKIP_ADMIN_ONLY = "Only group admins can skip."
SKIP_NOTHING = "Nothing is playing."
SKIP_DONE = "Skipped. Now playing: <code>{title}</code>"
SKIP_EMPTY = "Skipped. Queue empty."
SKIP_VOTE_ADDED = "Vote skip: <code>{votes}/{needed}</code>"
SKIP_VOTE_ALREADY = "You already voted to skip."
SKIP_VOTE_PASSED = "Vote passed! Skipping..."

# --- Pause / Resume ---
PAUSE_ADMIN_ONLY = "Only group admins can pause."
PAUSE_DONE = "Playback paused."
PAUSE_NOTHING = "Nothing is playing."
RESUME_ADMIN_ONLY = "Only group admins can resume."
RESUME_DONE = "Playback resumed."
RESUME_NOTHING = "Nothing is paused."

# --- Now Playing ---
NP_NOTHING = "Nothing is playing."
NP_DISPLAY = (
    "<b>Now Playing</b>\n"
    "<code>{title}</code>\n"
    "Duration: <code>{duration}</code> \u00b7 By: <code>{requester}</code>"
)

# --- Queue ---
QUEUE_EMPTY = "Queue is empty."
QUEUE_HEADER = "<b>Queue</b> ({count} tracks)\n"
QUEUE_ITEM = "{pos}. <code>{title}</code> \u2014 <code>{duration}</code>\n"
QUEUE_NOW_PLAYING = "\U0001f3b5 Now: <code>{title}</code>\n\n"

# --- Stop / Leave ---
STOP_ADMIN_ONLY = "Only group admins can stop."
STOP_DONE = "Stopped. Queue cleared and left voice chat."
LEAVE_ADMIN_ONLY = "Only group admins can use leave."
LEAVE_DONE = "Left voice chat."
LEAVE_NOT_ACTIVE = "Not currently in a voice chat."

# --- Autoplay ---
AUTOPLAY_ADMIN_ONLY = "Only group admins can enable autoplay."
AUTOPLAY_ENABLED = "Autoplay <b>enabled</b>. Stays on until m!stop or auto-leave."
AUTOPLAY_DISABLED = "Autoplay <b>disabled</b>."
AUTOPLAY_ALREADY_ON = "Autoplay is already active."

# --- Language ---
LANG_CURRENT = "Current language: <code>{lang}</code>"
LANG_SET = "Language changed to <code>{lang}</code>."
LANG_INVALID = "Invalid language. Available: {languages}"
LANG_ADMIN_ONLY = "Only group admins can change language."

# --- Check Voice ---
CV_ADMIN_ONLY = "Only group admins can use this command."
CV_CHECKING = "Checking voice chat\u2026"
CV_RESULT = "\U0001f3a7 Listeners in voice chat: <code>{count}</code>"
CV_EMPTY = "\U0001f507 No listeners in voice chat (assistant only)."
CV_UNAVAILABLE = "\u26a0\ufe0f Couldn't read voice chat participants."
CV_ERROR = "\u274c Error: <code>{error}</code>"

# --- Auto-leave ---
AUTO_LEAVE = "No listeners for 5 minutes. Left voice chat."

# --- Developer ---
DEV_ONLY = "This command is for developers only."
DEV_RESTART = "Restarting\u2026"
DEV_PULL = "Pulling latest changes\u2026"
DEV_PULL_RESULT = "<b>git pull</b>\n<code>{output}</code>"
DEV_BC_USAGE = "Usage: <code>m!bc &lt;message&gt;</code> or reply to a message."
DEV_BC_NO_TARGETS = (
    "No active groups for broadcast.\n"
    "(Groups appear after a music session starts.)"
)
DEV_BC_DONE = "Broadcast done. Success: {ok} \u00b7 Failed: {fail}"
DEV_STATUS = (
    "<b>IDOL Music Status</b>\n"
    "Uptime: <code>{uptime}</code>\n"
    "Sessions: <code>{sessions}</code>\n"
    "Total plays: <code>{total_plays}</code>\n"
    "Python: <code>{python}</code>\n"
    "MongoDB: <code>{mongo}</code>\n"
    "Cookies: <code>{cookies}</code>"
)
DEV_LOGS_USAGE = "Usage: <code>m!logs [n]</code> \u2014 show last n lines (default 50)."
DEV_LOGS_EMPTY = "Log file not found."

# --- Cookie Management ---
DEV_COOKIE_STATUS = "Cookies: <code>{size}</code> bytes, <code>{lines}</code> lines."
DEV_COOKIE_NOT_FOUND = "No cookies.txt found. Reply to a message with cookie content or send <code>m!cookie &lt;content&gt;</code>."
DEV_COOKIE_UPDATED = "Cookies updated. <code>{lines}</code> lines written."

# --- Log Group ---
LOG_STARTED = (
    "\U0001f7e2 <b>IDOL Music started</b>\n"
    "Bot: @{username}\n"
    "Sessions: {sessions}\n"
    "MongoDB: {mongo}\n"
    "Cookies: {cookies}"
)
LOG_STOPPED = "\U0001f534 <b>IDOL Music stopped</b> (restart requested)"
LOG_ERROR = "\u26a0\ufe0f <b>Error in {location}</b>\n<code>{error}</code>"
LOG_SESSION_JOIN = "\U0001f3b5 Joined VC in <code>{chat_id}</code>"
LOG_SESSION_LEAVE = "\U0001f507 Left VC from <code>{chat_id}</code>"
LOG_COOKIE_UPDATED = "\U0001f36a Cookies updated via bot command. {lines} lines."
LOG_ASSISTANT_STARTED = "\U0001f916 <b>Assistant started</b>\nName: {name}\nID: <code>{user_id}</code>"

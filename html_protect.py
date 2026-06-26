import telebot
import os, re, base64, random, string, tempfile, time, threading, hashlib, traceback, json
from telebot import types
from datetime import datetime, date

# ══════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════
BOT_TOKEN    = os.environ.get("BOT_TOKEN", "")
ADMIN_ID     = int(os.environ.get("ADMIN_ID", "7741897793"))
OUTPUT_NAME  = "KOHLIPAPA.html"
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@KohliHtmlToolBot")
DEVELOPER    = "@xxLEGEND_KOHLI"
CHANNEL      = "https://t.me/+4t2T50i_ewM2NDY1"

# Railway volume pe persist hoga — /data folder
os.makedirs("/data", exist_ok=True)
DATA_FILE = "/data/bot_data.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

stats = {
    "total_files": 0,
    "total_users": set(),
    "start_time":  datetime.now(),
}
_pending = {}

# ══════════════════════════════════════════════
#  PERSISTENT DATA (JSON)
# ══════════════════════════════════════════════

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                d = json.load(f)
                d.setdefault("force_channels", [])
                d.setdefault("user_credits", {})
                d.setdefault("user_last_daily", {})
                d.setdefault("user_unlimited_until", {})
                d.setdefault("gift_codes", {})
                d.setdefault("total_files", 0)
                d.setdefault("bot_enabled", True)
                d.setdefault("banned_users", [])
                d.setdefault("all_users", [])
                return d
        except Exception:
            pass
    return {
        "force_channels": [],
        "user_credits": {},
        "user_last_daily": {},
        "user_unlimited_until": {},
        "gift_codes": {},
        "total_files": 0,
        "bot_enabled": True,
        "banned_users": [],
        "all_users": [],
    }

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        print(f"Save error: {e}")

db = load_data()
stats["total_files"] = db["total_files"]
stats["total_users"] = set(int(u) for u in db.get("all_users", []))

def track_user(uid):
    """Add user to in-memory stats AND persist permanently to disk."""
    try:
        uid = int(uid)
    except Exception:
        return
    if uid not in stats["total_users"]:
        stats["total_users"].add(uid)
        db["all_users"] = list(stats["total_users"])
        save_data()

# ══════════════════════════════════════════════
#  CUSTOM EMOJI IDs
# ══════════════════════════════════════════════
E_CHECK  = "6240150347906554903"
E_EYES   = "6118311901064597000"
E_STAR   = "6118640912739339856"
E_COOL   = "6118672240230797020"
E_FIRE   = "6237558987978447573"
E_ZAP    = "6237621548472081271"
E_TIMER  = "6237689872811825394"
E_SHIELD = "6237624421805201754"
E_GLASS  = "6239867227957370986"
E_GIFT   = "6239894475229895983"

def ce(emoji_id, char="✦"):
    return f'<tg-emoji emoji-id="{emoji_id}">{char}</tg-emoji>'

CE_GLASS   = "6239867227957370986"
CE_REFRESH = "6240172522822704149"
CE_PLAY    = "6239829071467911642"
CE_BOOM    = "6237587317582733178"
CE_CHART_U = "6237997426829958116"
CE_CHART_D = "6240181641038275281"
CE_GIFT    = "6239894475229895983"
CE_SPARK   = "6239810212266516014"
CE_FIRE    = "6239994440593710297"
CE_CROWN1  = "6237700747669019068"
CE_CROWN2  = "6237736563401300947"
CE_CROWN3  = "6237931640815884961"
CE_LOCK    = "6238040728690235936"
CE_GEM1    = "6240299744048978030"
CE_GEM2    = "6240228563555983558"
CE_GEM3    = "6237505507045677625"
CE_LION    = "6239755820800678558"
CE_FREE    = "6239847209114804323"
CE_MEDAL   = "6239895377173029470"
CE_BATT1   = "6239753553057945368"
CE_BATT2   = "6239992348944636289"
CE_BATT3   = "6237866902773832349"
CE_SEARCH  = "6239790794719370356"
CE_CHECK   = "6239884622574918094"
CE_CAL1    = "6240203369277824249"
CE_CAL2    = "6240027791014765668"
CE_SMILE   = "6237638728341266737"
CE_ROCKET  = "6239826438652959074"
CE_PARTY   = "6237945805618027418"
CE_SLEEP   = "6239846165437749217"
CE_MAIL    = "6237547619200014867"
CE_CANDLE  = "6237588838001156275"
CE_WINE    = "6237510794150419802"
CE_GUN     = "6239826357048580966"
CE_BAG     = "6237585956078099911"
CE_RED     = "6239824497327740999"

# ══════════════════════════════════════════════
#  CREDIT SYSTEM
# ══════════════════════════════════════════════
DAILY_FREE_CREDITS = 5
CREDIT_PRICE_INR   = 20

def get_user_credits(uid: str) -> int:
    uid   = str(uid)
    today = str(date.today())
    if db["user_last_daily"].get(uid) != today:
        db["user_last_daily"][uid] = today
        current = db["user_credits"].get(uid, 0)
        db["user_credits"][uid] = current + DAILY_FREE_CREDITS
        save_data()
    return db["user_credits"].get(uid, 0)

def is_unlimited(uid: str) -> bool:
    uid       = str(uid)
    until_str = db["user_unlimited_until"].get(uid)
    if not until_str:
        return False
    try:
        until = datetime.strptime(until_str, "%Y-%m-%d %H:%M:%S")
        return datetime.now() < until
    except Exception:
        return False

def use_credit(uid: str) -> bool:
    uid = str(uid)
    if is_unlimited(uid):
        return True
    credits = get_user_credits(uid)
    if credits <= 0:
        return False
    db["user_credits"][uid] = credits - 1
    save_data()
    return True

def add_credits(uid: str, amount: int):
    uid = str(uid)
    db["user_credits"][uid] = db["user_credits"].get(uid, 0) + amount
    save_data()

def remove_credits(uid: str, amount: int):
    uid     = str(uid)
    current = db["user_credits"].get(uid, 0)
    db["user_credits"][uid] = max(0, current - amount)
    save_data()

def set_unlimited(uid: str, days: int):
    from datetime import timedelta
    uid   = str(uid)
    until = datetime.now() + timedelta(days=days)
    db["user_unlimited_until"][uid] = until.strftime("%Y-%m-%d %H:%M:%S")
    save_data()

# ══════════════════════════════════════════════
#  BAN SYSTEM
# ══════════════════════════════════════════════

def is_banned(uid) -> bool:
    return str(uid) in [str(x) for x in db.get("banned_users", [])]

def ban_user(uid):
    uid = str(uid)
    if uid not in [str(x) for x in db["banned_users"]]:
        db["banned_users"].append(uid)
        save_data()

def unban_user(uid):
    uid = str(uid)
    db["banned_users"] = [str(x) for x in db["banned_users"] if str(x) != uid]
    save_data()

# ══════════════════════════════════════════════
#  BOT ON/OFF
# ══════════════════════════════════════════════

def bot_is_enabled() -> bool:
    return db.get("bot_enabled", True)

def set_bot_enabled(val: bool):
    db["bot_enabled"] = val
    save_data()

# ══════════════════════════════════════════════
#  FORCE JOIN SYSTEM
# ══════════════════════════════════════════════

def check_user_joined(uid: int) -> list:
    not_joined = []
    for ch in db["force_channels"]:
        try:
            member = bot.get_chat_member(ch["id"], uid)
            if member.status in ['left', 'kicked', 'banned']:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)
    return not_joined

def force_join_keyboard(not_joined: list) -> types.InlineKeyboardMarkup:
    mk = types.InlineKeyboardMarkup(row_width=1)
    for ch in not_joined:
        name = ch.get("name", ch["id"])
        link = ch.get("link", f"https://t.me/{str(ch['id']).lstrip('@')}")
        mk.add(types.InlineKeyboardButton(f"Join {name}", url=link, icon_custom_emoji_id=CE_PLAY))
    mk.add(types.InlineKeyboardButton("I've Joined!", callback_data="check_joined", icon_custom_emoji_id=CE_CHECK))
    return mk

def get_channel_info(channel_id: str, custom_link: str = None) -> dict:
    try:
        chat = bot.get_chat(channel_id)
        name = chat.title or channel_id
        if custom_link:
            link = custom_link
        elif chat.username:
            link = f"https://t.me/{chat.username}"
        else:
            link = f"https://t.me/c/{str(chat.id).replace('-100', '')}"
        return {"id": channel_id, "name": name, "link": link}
    except Exception:
        link = custom_link or f"https://t.me/{str(channel_id).lstrip('@')}"
        return {"id": channel_id, "name": channel_id, "link": link}

# ══════════════════════════════════════════════
#  GIFT CODE SYSTEM
# ══════════════════════════════════════════════

def create_gift_code(credits: int, max_users: int) -> str:
    code = 'KXM-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    db["gift_codes"][code] = {
        "credits":    credits,
        "max_users":  max_users,
        "used_by":    [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_data()
    return code

def redeem_gift_code(uid: str, code: str):
    uid  = str(uid)
    code = code.upper().strip()
    if code not in db["gift_codes"]:
        return False, "Invalid gift code!"
    gc = db["gift_codes"][code]
    if uid in gc["used_by"]:
        return False, "You have already used this code!"
    if len(gc["used_by"]) >= gc["max_users"]:
        return False, "This gift code has expired (max users reached)!"
    gc["used_by"].append(uid)
    add_credits(uid, gc["credits"])
    save_data()
    return True, f"{gc['credits']} credits have been added to your account!"

# ══════════════════════════════════════════════
#  CRASH-PROOF AUTO-RESTART
# ══════════════════════════════════════════════

def safe_polling():
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Bot polling started...")
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=30,
                allowed_updates=["message", "callback_query"],
                restart_on_change=False,
            )
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Polling crashed: {e}")
            traceback.print_exc()
            print("Restarting in 5 seconds...")
            time.sleep(5)

def notify_admin_start():
    try:
        bot.send_message(ADMIN_ID,
            f"{ce(CE_ROCKET,'🚀')} <b>Bot Started / Restarted</b>\n\n"
            f"{ce(CE_CAL1,'🗓')} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{ce(CE_LION,'🦁')} {BOT_USERNAME}\n"
            f"{ce(CE_GEM2,'💎')} <b>Saved Users Loaded:</b> <code>{len(stats['total_users'])}</code>\n"
            f"{ce(CE_GIFT,'🎁')} <b>Saved Files Count:</b> <code>{stats['total_files']}</code>",
            reply_markup=main_kb(True)
        )
    except Exception:
        pass

# ══════════════════════════════════════════════
#  KEYBOARDS
#  NOTE: When icon_custom_emoji_id is set on a button, the button TEXT
#  must NOT also contain a regular unicode emoji — otherwise Telegram
#  renders both the custom emoji icon AND the unicode emoji, causing
#  a "double emoji" look. Below, all keyboard/inline button labels are
#  plain text and only the custom emoji icon is shown.
# ══════════════════════════════════════════════

def make_btn(text, emoji_id, style=None):
    btn = types.KeyboardButton(text)
    btn.icon_custom_emoji_id = emoji_id
    if style:
        btn.style = style
    return btn

def main_kb(is_admin=False):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(make_btn("Protect My HTML File", E_SHIELD, "primary"))
    m.row(
        make_btn("My Credits",  E_STAR,  "success"),
        make_btn("Redeem Code", E_GIFT,  "success"),
    )
    m.row(
        make_btn("How it Works", E_ZAP,  "success"),
        make_btn("Help",         E_STAR,  "success"),
    )
    m.row(
        make_btn("About Bot",      E_COOL,  "primary"),
        make_btn("Privacy Policy", E_CHECK, "primary"),
    )
    if is_admin:
        m.add(make_btn("Admin Panel", E_FIRE, "danger"))
    return m

def admin_inline_kb():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("Statistics",   callback_data="adm_stats",     style="primary", icon_custom_emoji_id=E_STAR),
        types.InlineKeyboardButton("Force Join",   callback_data="adm_forcejoin", style="success", icon_custom_emoji_id=E_SHIELD),
    )
    m.add(
        types.InlineKeyboardButton("Credits",      callback_data="adm_credits",   style="success", icon_custom_emoji_id=E_CHECK),
        types.InlineKeyboardButton("Gift Code",    callback_data="adm_giftcode",  style="primary", icon_custom_emoji_id=E_GIFT),
    )
    m.add(
        types.InlineKeyboardButton("Broadcast",    callback_data="adm_broadcast", style="primary", icon_custom_emoji_id=E_ZAP),
        types.InlineKeyboardButton("Decode File",  callback_data="adm_decode_on", style="success", icon_custom_emoji_id=E_CHECK),
    )
    m.add(
        types.InlineKeyboardButton("Ban User",     callback_data="adm_ban",       style="danger",  icon_custom_emoji_id=E_FIRE),
        types.InlineKeyboardButton("Unban User",   callback_data="adm_unban",     style="success", icon_custom_emoji_id=E_CHECK),
    )
    status_label = "Turn Bot OFF" if bot_is_enabled() else "Turn Bot ON"
    m.add(
        types.InlineKeyboardButton(status_label,    callback_data="adm_toggle_bot",style="danger",  icon_custom_emoji_id=E_TIMER),
        types.InlineKeyboardButton("Clear Cache",  callback_data="adm_clear",     style="danger",  icon_custom_emoji_id=E_TIMER),
    )
    m.add(
        types.InlineKeyboardButton("Banned Users", callback_data="adm_banlist",   style="primary", icon_custom_emoji_id=E_EYES),
        types.InlineKeyboardButton("Bot Info",     callback_data="adm_info",      style="primary", icon_custom_emoji_id=E_EYES),
    )
    m.add(
        types.InlineKeyboardButton("Close Panel",  callback_data="adm_close",     style="danger",  icon_custom_emoji_id=E_FIRE),
    )
    return m

def forcejoin_manage_kb():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("Add Channel",    callback_data="adm_fj_add",        icon_custom_emoji_id=CE_PLAY),
        types.InlineKeyboardButton("Remove Channel", callback_data="adm_fj_remove",      icon_custom_emoji_id=E_FIRE),
    )
    m.add(
        types.InlineKeyboardButton("Change Link",    callback_data="adm_fj_changelink",  icon_custom_emoji_id=CE_SPARK),
        types.InlineKeyboardButton("List Channels",  callback_data="adm_fj_list",        icon_custom_emoji_id=E_EYES),
    )
    m.add(types.InlineKeyboardButton("Back", callback_data="adm_back", icon_custom_emoji_id=CE_PLAY))
    return m

def credit_manage_kb():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("Add Credits",      callback_data="adm_cr_add",        icon_custom_emoji_id=CE_GEM2),
        types.InlineKeyboardButton("Remove Credits",   callback_data="adm_cr_remove",      icon_custom_emoji_id=E_FIRE),
    )
    m.add(
        types.InlineKeyboardButton("Unlimited Access", callback_data="adm_cr_unlimited",   icon_custom_emoji_id=CE_GEM1),
        types.InlineKeyboardButton("Check Credits",    callback_data="adm_cr_check",       icon_custom_emoji_id=CE_SEARCH),
    )
    m.add(types.InlineKeyboardButton("Back", callback_data="adm_back", icon_custom_emoji_id=CE_PLAY))
    return m

# ══════════════════════════════════════════════
#  LOADING ANIMATION
# ══════════════════════════════════════════════

STEPS = [
    "Deriving encryption key...",
    "Applying XOR+ROT cipher...",
    "Base64 multi-pass encoding...",
    "Hex string obfuscation...",
    "Mangling variable names...",
    "Injecting dead code...",
    "Wrapping with poly-eval...",
    "Splitting & shuffling chunks...",
    "Finalizing output...",
]
BARS = [
    "▱▱▱▱▱▱▱▱▱", "▰▱▱▱▱▱▱▱▱", "▰▰▱▱▱▱▱▱▱",
    "▰▰▰▱▱▱▱▱▱", "▰▰▰▰▱▱▱▱▱", "▰▰▰▰▰▱▱▱▱",
    "▰▰▰▰▰▰▱▱▱", "▰▰▰▰▰▰▰▱▱", "▰▰▰▰▰▰▰▰▱",
    "▰▰▰▰▰▰▰▰▰",
]

def loading_animation(chat_id, msg_id, label="Processing"):
    stop = threading.Event()
    def run():
        fi = bi = si = 0
        while not stop.is_set():
            try:
                pct = int((bi / (len(BARS) - 1)) * 100)
                bot.edit_message_text(
                    f"<code>{BARS[min(bi, len(BARS)-1)]}</code>  <b>{pct}%</b>\n\n"
                    f"{ce(CE_GEM1,'💎')} <b>{label}</b>\n"
                    f"<i>{STEPS[min(si, len(STEPS)-1)]}</i>",
                    chat_id, msg_id, parse_mode='HTML'
                )
            except Exception:
                pass
            fi += 1
            if fi % 3 == 0: bi = min(bi + 1, len(BARS) - 1)
            if fi % 4 == 0: si = min(si + 1, len(STEPS) - 1)
            time.sleep(0.5)
    threading.Thread(target=run, daemon=True).start()
    return stop

# ══════════════════════════════════════════════
#  CRYPTO ENGINE
# ══════════════════════════════════════════════

MASTER_KEY  = "KXM_ULTRA_PROT_2025_##XZY_KOHLIPAPA_$ECR3T_V6"
SALT        = "KXM_S4LT_V6_##2025_PR3MIUM"
B64_PASSES  = 6
SIZE_FACTOR = 20

def derive_key(length=64) -> bytes:
    return hashlib.pbkdf2_hmac(
        'sha256', MASTER_KEY.encode(), SALT.encode(), 100_000, dklen=length
    )

def encrypt_bytes(data: bytes, key: bytes) -> bytes:
    r  = bytearray(data)
    kl = len(key)
    for i in range(len(r)):
        r[i] = ((r[i] + 17) % 256) ^ key[i % kl]
    r = bytearray(reversed(r))
    for i in range(len(r)):
        r[i] ^= key[(i * 3 + 7) % kl]
    for i in range(len(r)):
        b = r[i]
        r[i] = ((b & 0x0F) << 4) | ((b & 0xF0) >> 4)
    return bytes(r)

def decrypt_bytes(data: bytes, key: bytes) -> bytes:
    r  = bytearray(data)
    kl = len(key)
    for i in range(len(r)):
        b = r[i]; r[i] = ((b & 0x0F) << 4) | ((b & 0xF0) >> 4)
    for i in range(len(r)):
        r[i] ^= key[(i * 3 + 7) % kl]
    r = bytearray(reversed(r))
    for i in range(len(r)):
        r[i] = ((r[i] ^ key[i % kl]) - 17 + 256) % 256
    return bytes(r)

def b64_enc(data: bytes, n: int) -> str:
    r = data
    for _ in range(n): r = base64.b64encode(r)
    return r.decode('ascii')

def b64_dec(s: str, n: int) -> bytes:
    r = s.encode('ascii')
    for _ in range(n): r = base64.b64decode(r)
    return r

# ══════════════════════════════════════════════
#  JS HELPERS
# ══════════════════════════════════════════════

def rv(n=10):
    return '_0x' + ''.join(random.choices('abcdef0123456789', k=n))

def hx(s: str) -> str:
    return ''.join(f'\\x{ord(c):02x}' for c in s)

def junk(target: int) -> str:
    parts, cur = [], 0
    tpls = [
        lambda: f"var {rv()}={''.join(random.choices(string.ascii_letters, k=random.randint(40,120)))!r};",
        lambda: f"var {rv()}=[{','.join(str(random.randint(0,65535)) for _ in range(random.randint(8,25)))}];",
        lambda: f"if(false){{{rv()}={rv()}+{random.randint(0,999)};}}",
        lambda: f"/* {''.join(random.choices(string.ascii_letters+' ', k=random.randint(30,100)))} */",
        lambda: f"var {rv()}=function(){{{rv()}=null;return {random.randint(0,9)};}}",
        lambda: f"try{{}}catch({rv()}){{{rv()}=null;}}",
        lambda: f"var {rv()}=Math.floor(Math.random()*{random.randint(1000,9999)});",
        lambda: f"for(var {rv()}=0;false;){{{rv()}++;}}",
        lambda: f"var {rv()}=Object.freeze({{k:{random.randint(0,9999)},v:'{rv(6)}'}});",
        lambda: f"var {rv()}=typeof window!=='undefined'?window:{{}};",
        lambda: f"var {rv()}=new Map();",
        lambda: f"switch({random.randint(0,5)}){{{' '.join(f'case {i}:break;' for i in range(3))}}}",
    ]
    while cur < target:
        p = random.choice(tpls)()
        parts.append(p)
        cur += len(p)
    return '\n'.join(parts)

# ══════════════════════════════════════════════
#  WATERMARK
# ══════════════════════════════════════════════

def build_watermark_script() -> str:
    wm_id = rv(8)
    return f"""
<style>
#{wm_id}{{
  position:fixed;bottom:0;left:0;right:0;
  background:linear-gradient(90deg,#0f0c29,#302b63,#24243e);
  color:#fff;font-family:'Segoe UI',Arial,sans-serif;
  font-size:12px;line-height:1;padding:7px 16px;
  z-index:2147483647;display:flex;align-items:center;
  justify-content:space-between;border-top:1.5px solid #6c5ce7;
  letter-spacing:0.3px;transition:opacity 1s ease;opacity:1;
}}
#{wm_id} .wm-l{{font-weight:600;}}
#{wm_id} .wm-r{{color:#a29bfe;font-size:11px;}}
#{wm_id} .wm-dot{{
  width:7px;height:7px;border-radius:50%;background:#6c5ce7;
  display:inline-block;margin-right:6px;vertical-align:middle;
  animation:kxmpulse 1.2s infinite;
}}
@keyframes kxmpulse{{0%,100%{{opacity:1;}}50%{{opacity:0.3;}}}}
</style>
<div id="{wm_id}">
  <span class="wm-l"><span class="wm-dot"></span>KXM Protected · {BOT_USERNAME}</span>
  <span class="wm-r">{DEVELOPER} | {CHANNEL}</span>
</div>
<script>
(function(){{
  var _wm=document.getElementById('{wm_id}');
  if(!_wm)return;
  setTimeout(function(){{
    _wm.style.opacity='0';
    setTimeout(function(){{if(_wm&&_wm.parentNode)_wm.parentNode.removeChild(_wm);}},1000);
  }},10000);
}})();
</script>"""

def inject_watermark(html: str) -> str:
    meta = (
        f'<!-- KXM-PROTECTED | {BOT_USERNAME} | {DEVELOPER} -->\n'
        f'<meta name="generator" content="KXM HTML Protector v6.0">\n'
        f'<meta name="author" content="{DEVELOPER}">\n'
    )
    wm_block = build_watermark_script()
    if '<head>' in html:
        html = html.replace('<head>', '<head>\n' + meta, 1)
    elif '<HEAD>' in html:
        html = html.replace('<HEAD>', '<HEAD>\n' + meta, 1)
    else:
        html = meta + html
    if '</body>' in html:
        html = html.replace('</body>', wm_block + '\n</body>', 1)
    elif '</BODY>' in html:
        html = html.replace('</BODY>', wm_block + '\n</BODY>', 1)
    else:
        html += '\n' + wm_block
    return html

# ══════════════════════════════════════════════
#  MAIN OBFUSCATOR
# ══════════════════════════════════════════════

def obfuscate_html(original_html: str) -> str:
    html_wm   = inject_watermark(original_html)
    key       = derive_key()
    encrypted = encrypt_bytes(html_wm.encode('utf-8'), key)
    b64       = b64_enc(encrypted, B64_PASSES)
    csz       = random.randint(50, 80)
    chunks    = [b64[i:i+csz] for i in range(0, len(b64), csz)]

    vC=rv(); vJ=rv(); vB=rv(); vR=rv()
    vK=rv(); vI=rv(); vT=rv(); vA=rv()
    vFn=rv(); vD=rv(); vOu=rv(); vEv=rv()

    key_arr   = '[' + ','.join(str(b) for b in key) + ']'
    chunks_js = '[' + ','.join(f'"{hx(c)}"' for c in chunks) + ']'

    cipher_fn = f"""
function {vFn}({vB},{vK}){{
  var {vR}=new Uint8Array({vB}.length),kl={vK}.length,{vI},{vA};
  for({vI}=0;{vI}<{vB}.length;{vI}++){{{vA}={vB}[{vI}];{vR}[{vI}]=(({vA}&0x0F)<<4)|(({vA}&0xF0)>>4);}}
  for({vI}=0;{vI}<{vR}.length;{vI}++){{{vR}[{vI}]^={vK}[({vI}*3+7)%kl];}}
  {vR}=new Uint8Array(Array.from({vR}).reverse());
  for({vI}=0;{vI}<{vR}.length;{vI}++){{{vR}[{vI}]=(({vR}[{vI}]^{vK}[{vI}%kl])-17+256)%256;}}
  return {vR};
}}"""
    atob_fn = f"function {vD}(s,n){{var r=s;for(var p=0;p<n;p++)r=atob(r);return r;}}"

    inner_js = f"""
(function(){{
  {cipher_fn}
  {atob_fn}
  var {vC}={chunks_js};
  var {vJ}={vC}.join('');
  var {vT}={vD}({vJ},{B64_PASSES});
  var {vB}=new Uint8Array({vT}.length);
  for(var {vI}=0;{vI}<{vT}.length;{vI}++){{{vB}[{vI}]={vT}.charCodeAt({vI});}}
  var {vK}=new Uint8Array({key_arr});
  var {vR}={vFn}({vB},{vK});
  var _html=new TextDecoder('utf-8').decode({vR});
  document.open('text/html','replace');
  document.write(_html);
  document.close();
}})();"""

    ib64     = base64.b64encode(inner_js.encode()).decode()
    t        = len(ib64) // 3
    p1, p2, p3 = ib64[:t], ib64[t:2*t], ib64[2*t:]
    outer_js = (
        f"var {vOu}=['{hx(p1)}','{hx(p2)}','{hx(p3)}'];"
        f"(function(){{"
        f"var {vEv}=atob({vOu}[0]+{vOu}[1]+{vOu}[2]);"
        f"(new Function({vEv}))();"
        f"}})();"
    )
    junk_code = junk(len(original_html) * (SIZE_FACTOR - 1))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<title>Loading...</title>
</head>
<body>
<script>
{junk_code}
{outer_js}
</script>
</body>
</html>"""

# ══════════════════════════════════════════════
#  REMOVE PROTECTION
# ══════════════════════════════════════════════

def remove_protection(html: str):
    try:
        def unhex(s):
            return re.sub(r'\\x([0-9a-fA-F]{2})',
                          lambda m: chr(int(m.group(1), 16)), s)
        m = re.search(
            r"var\s+\S+\s*=\s*\['([^']+)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\]", html)
        if not m:
            return None, "Outer wrapper not found"
        ib64     = unhex(m.group(1)) + unhex(m.group(2)) + unhex(m.group(3))
        inner_js = base64.b64decode(ib64).decode('utf-8')
        cm = re.search(
            r'\[((?:"(?:\\x[0-9a-fA-F]{2})+")'
            r'(?:\s*,\s*"(?:\\x[0-9a-fA-F]{2})+")*)\]', inner_js)
        if not cm:
            return None, "Chunks not found"
        raw    = re.findall(r'"((?:\\x[0-9a-fA-F]{2})+)"', cm.group(0))
        joined = ''.join(unhex(c) for c in raw)
        enc    = b64_dec(joined, B64_PASSES)
        key    = derive_key()
        result = decrypt_bytes(enc, key).decode('utf-8')
        if '<' in result:
            return result, None
        return None, "Result doesn't look like HTML"
    except Exception as e:
        return None, str(e)

# ══════════════════════════════════════════════
#  SAFE SEND
# ══════════════════════════════════════════════

def safe_send_document(chat_id, filepath, filename, caption, reply_markup=None, retries=3):
    for attempt in range(retries):
        try:
            with open(filepath, 'rb') as f:
                kwargs = dict(visible_file_name=filename, caption=caption, parse_mode='HTML')
                if reply_markup:
                    kwargs['reply_markup'] = reply_markup
                bot.send_document(chat_id, f, **kwargs)
            return True
        except Exception as e:
            print(f"send_document attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return False

# ══════════════════════════════════════════════
#  BROADCAST
# ══════════════════════════════════════════════

def do_broadcast(text: str):
    all_users = list(stats["total_users"])
    sent = failed = 0
    for uid in all_users:
        if is_banned(uid):
            continue
        try:
            bot.send_message(uid,
                f"📣 <b>Broadcast from Admin</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"{text}\n\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"{ce(CE_LION,'🦁')} {BOT_USERNAME}"
            )
            sent += 1
            time.sleep(0.05)
        except Exception:
            failed += 1
    return sent, failed

# ══════════════════════════════════════════════
#  GUARD DECORATOR
# ══════════════════════════════════════════════

def guard(msg):
    """Returns True if message should be blocked (bot off or user banned)."""
    uid = msg.from_user.id
    if uid == ADMIN_ID:
        return False
    if is_banned(uid):
        bot.reply_to(msg,
            f"🚫 <b>You have been banned from using this bot.</b>\n\n"
            f"Contact {DEVELOPER} if you think this is a mistake."
        )
        return True
    if not bot_is_enabled():
        bot.reply_to(msg,
            f"🔴 <b>Bot is currently offline for maintenance.</b>\n\n"
            f"Please try again later.\n"
            f"{ce(CE_LION,'🦁')} {BOT_USERNAME}"
        )
        return True
    return False

# ══════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    uid      = msg.from_user.id
    is_admin = uid == ADMIN_ID
    name     = msg.from_user.first_name or "User"
    track_user(uid)

    if guard(msg):
        return

    not_joined = check_user_joined(uid)
    if not_joined and not is_admin:
        bot.send_message(msg.chat.id,
            f"┌─────────────────────────┐\n"
            f"│  {ce(CE_GEM1,'💎')}  <b>KXM HTML PROTECTOR</b>  │\n"
            f"└─────────────────────────┘\n\n"
            f"{ce(CE_LOCK,'🔒')} <b>Join all channels below to use the bot:</b>\n\n"
            f"{ce(CE_PLAY,'▶️')} After joining, tap <b>I've Joined!</b>",
            reply_markup=force_join_keyboard(not_joined)
        )
        return

    adm         = f"\n{ce(CE_CROWN1,'👑')} <b>Admin Mode Active</b>" if is_admin else ""
    credits     = get_user_credits(str(uid))
    unlimited   = is_unlimited(str(uid))
    credit_line = "♾️ <b>Unlimited Access Active!</b>" if unlimited else \
                  f"{ce(CE_GEM2,'💎')} <b>Your Credits:</b> <code>{credits}</code>"

    bot.send_message(msg.chat.id,
        f"┌─────────────────────────┐\n"
        f"│  {ce(CE_GEM1,'💎')}  <b>KXM HTML PROTECTOR</b>  │\n"
        f"│      <i>v6.0 Premium</i>         │\n"
        f"└─────────────────────────┘\n\n"
        f"{ce(CE_SPARK,'✨')} Welcome, <b>{name}</b>!{adm}\n\n"
        f"<b>What I do:</b>\n"
        f"{ce(CE_LOCK,'🔒')} Ultra-encrypt your HTML files\n"
        f"{ce(CE_CHART_U,'📈')} Files work in all browsers\n"
        f"{ce(CE_GEM2,'💎')} Source code becomes unreadable\n"
        f"{ce(CE_SPARK,'✨')} KXM Watermark auto-embedded\n\n"
        f"💳 {credit_line}\n"
        f"🎁 Get <b>5 free credits</b> every day!\n\n"
        f"{ce(CE_ROCKET,'🚀')} <b>Send your</b> <code>.html</code> <b>file to get started!</b>\n\n"
        f"<i>{ce(CE_CANDLE,'🕯')} Files may be reviewed for quality assurance.</i>",
        reply_markup=main_kb(is_admin)
    )

# ══════════════════════════════════════════════
#  KEYBOARD TEXT HANDLERS
#  NOTE: matched against the new plain-text button labels above.
# ══════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text and "Protect My HTML File" in m.text)
def kb_protect_prompt(m):
    if guard(m): return
    uid        = m.from_user.id
    not_joined = check_user_joined(uid)
    if not_joined and uid != ADMIN_ID:
        bot.send_message(m.chat.id,
            f"{ce(CE_LOCK,'🔒')} <b>Please join all channels first:</b>",
            reply_markup=force_join_keyboard(not_joined)
        )
        return
    bot.send_message(m.chat.id,
        f"{ce(CE_ROCKET,'🚀')} <b>Send your <code>.html</code> file now!</b>\n\n"
        f"{ce(CE_LOCK,'🔒')} I'll encrypt and protect it for you.",
        reply_markup=main_kb(uid == ADMIN_ID)
    )

@bot.message_handler(func=lambda m: m.text and m.text.strip() == "My Credits")
def kb_my_credits(m):
    if guard(m): return
    uid       = str(m.from_user.id)
    credits   = get_user_credits(uid)
    unlimited = is_unlimited(uid)
    until_str = db["user_unlimited_until"].get(uid, "")

    if unlimited:
        until_disp = ""
        try:
            until      = datetime.strptime(until_str, "%Y-%m-%d %H:%M:%S")
            until_disp = until.strftime("%d %b %Y, %H:%M")
        except Exception:
            pass
        credit_msg = f"♾️ <b>Unlimited Access Active!</b>\n⏰ Expires: <code>{until_disp}</code>"
    else:
        credit_msg = f"💳 <b>Your Credits:</b> <code>{credits}</code>"

    bot.send_message(m.chat.id,
        f"{ce(CE_GEM1,'💎')} <b>Credit Information</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"{credit_msg}\n\n"
        f"{ce(CE_FREE,'🆓')} <b>Daily Free:</b> 5 credits/day\n"
        f"{ce(CE_GIFT,'🎁')} <b>Gift Code:</b> Tap Redeem Code button\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Need more credits?</b>\n"
        f"{ce(CE_ROCKET,'🚀')} <b>₹20 = 1 Day Unlimited Credits</b>\n"
        f"Contact: {DEVELOPER}",
        reply_markup=main_kb(m.from_user.id == ADMIN_ID)
    )

@bot.message_handler(func=lambda m: m.text and m.text.strip() == "Redeem Code")
def kb_redeem_prompt(m):
    if guard(m): return
    _pending[f"redeem_{m.from_user.id}"] = True
    bot.send_message(m.chat.id,
        f"{ce(CE_GIFT,'🎁')} <b>Redeem Gift Code</b>\n\n"
        f"Please send your gift code now.\n\n"
        f"Example: <code>KXM-ABC12345</code>",
        reply_markup=types.ForceReply(selective=True)
    )

@bot.message_handler(func=lambda m: m.text and m.text.strip() == "Help")
def kb_help(m):
    if guard(m): return
    bot.send_message(m.chat.id,
        f"{ce(CE_GIFT,'🎁')} <b>Help & Usage Guide</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Steps:</b>\n"
        f"{ce(CE_PLAY,'▶️')} Tap <b>Protect My HTML File</b>\n"
        f"{ce(CE_PLAY,'▶️')} Send your <code>.html</code> file\n"
        f"{ce(CE_PLAY,'▶️')} Watch the encryption animation\n"
        f"{ce(CE_PLAY,'▶️')} Receive your protected file\n\n"
        f"<b>Credits System:</b>\n"
        f"{ce(CE_FREE,'🆓')} Get 5 free credits every day\n"
        f"{ce(CE_GIFT,'🎁')} Earn extra credits via gift codes\n"
        f"💰 ₹20 = 1 day unlimited (Contact {DEVELOPER})\n\n"
        f"<b>Notes:</b>\n"
        f"{ce(CE_SEARCH,'🔍')} Only <code>.html</code> files accepted\n"
        f"{ce(CE_SPARK,'✨')} KXM watermark shows for 10s then hides\n"
        f"{ce(CE_LOCK,'🔒')} Source code is fully unreadable\n\n"
        f"{ce(CE_LION,'🦁')} {BOT_USERNAME} | {ce(CE_CROWN1,'👑')} {DEVELOPER}",
        reply_markup=main_kb(m.from_user.id == ADMIN_ID)
    )

@bot.message_handler(func=lambda m: m.text and "How it Works" in m.text)
def kb_how(m):
    if guard(m): return
    bot.send_message(m.chat.id,
        f"{ce(CE_GEM1,'💎')} <b>KXM Protection Engine</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"Your HTML goes through multiple protection layers:\n\n"
        f"{ce(CE_CROWN1,'👑')} <b>Key Derivation</b> — PBKDF2-SHA256 (100k rounds)\n"
        f"{ce(CE_LOCK,'🔒')} <b>XOR + ROT Cipher</b> — 3-round byte encryption\n"
        f"{ce(CE_BATT1,'🔋')} <b>Base64 × 6</b> — Multi-pass encoding\n"
        f"{ce(CE_SEARCH,'🔍')} <b>Hex Obfuscation</b> — String hiding\n"
        f"{ce(CE_SPARK,'✨')} <b>Variable Mangling</b> — Random names\n"
        f"{ce(CE_BOOM,'💥')} <b>Dead Code Injection</b> — ~20× size inflation\n"
        f"{ce(CE_REFRESH,'🔄')} <b>Double Eval Wrap</b> — 2-layer JS shell\n\n"
        f"<b>Result:</b> Source code = completely unreadable {ce(CE_LOCK,'🔒')}\n\n"
        f"{ce(CE_LION,'🦁')} {BOT_USERNAME} | {ce(CE_CROWN2,'👑')} {DEVELOPER}",
        reply_markup=main_kb(m.from_user.id == ADMIN_ID)
    )

@bot.message_handler(func=lambda m: m.text and "About Bot" in m.text)
def kb_about(m):
    if guard(m): return
    up   = datetime.now() - stats["start_time"]
    hrs  = int(up.total_seconds() // 3600)
    mins = int((up.total_seconds() % 3600) // 60)
    status = "🟢 Online" if bot_is_enabled() else "🔴 Offline"
    bot.send_message(m.chat.id,
        f"{ce(CE_GEM1,'💎')} <b>KXM HTML Protector</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"{ce(CE_MEDAL,'🎖️')} <b>Version</b>   : <code>6.0 Premium</code>\n"
        f"{ce(CE_LION,'🦁')} <b>Bot</b>       : {BOT_USERNAME}\n"
        f"{ce(CE_CROWN1,'👑')} <b>Developer</b> : {DEVELOPER}\n"
        f"{ce(CE_CHART_U,'📈')} <b>Channel</b>   : {CHANNEL}\n"
        f"{ce(CE_CANDLE,'🕯')} <b>Output</b>    : <code>{OUTPUT_NAME}</code>\n"
        f"🔵 <b>Status</b>    : {status}\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{ce(CE_CHECK,'✔️')} All browsers compatible\n"
        f"{ce(CE_CHECK,'✔️')} Daily 5 free credits\n"
        f"{ce(CE_CHECK,'✔️')} Gift code system\n"
        f"{ce(CE_CHECK,'✔️')} Force join channels\n"
        f"{ce(CE_CHECK,'✔️')} Crash-proof 24/7 uptime\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{ce(CE_BATT1,'🔋')} <b>Uptime</b>    : {hrs}h {mins}m\n"
        f"{ce(CE_GIFT,'🎁')} <b>Files</b>     : {stats['total_files']}\n"
        f"{ce(CE_SPARK,'✨')} <b>Users</b>     : {len(stats['total_users'])}",
        reply_markup=main_kb(m.from_user.id == ADMIN_ID)
    )

@bot.message_handler(func=lambda m: m.text and "Privacy Policy" in m.text)
def kb_privacy(m):
    if guard(m): return
    bot.send_message(m.chat.id,
        f"{ce(CE_CANDLE,'🕯')} <b>Privacy Policy</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"{ce(CE_GEM3,'💎')} Your <code>.html</code> files are:\n"
        f"   {ce(CE_CHECK,'✔️')} Encrypted and returned to you\n"
        f"   {ce(CE_SEARCH,'🔍')} Reviewed by admin for QA\n"
        f"   {ce(CE_RED,'🟥')} <b>Not permanently stored</b>\n\n"
        f"{ce(CE_GEM3,'💎')} Credit data saved securely.\n"
        f"{ce(CE_GEM3,'💎')} No personal data shared with 3rd parties.\n\n"
        f"{ce(CE_MAIL,'💌')} Questions? Contact {DEVELOPER}",
        reply_markup=main_kb(m.from_user.id == ADMIN_ID)
    )

@bot.message_handler(func=lambda m: m.text and "Admin Panel" in m.text and m.from_user.id == ADMIN_ID)
def kb_admin(m):
    up   = datetime.now() - stats["start_time"]
    hrs  = int(up.total_seconds() // 3600)
    mins = int((up.total_seconds() % 3600) // 60)
    status = "🟢 Online" if bot_is_enabled() else "🔴 Offline"
    bot.send_message(m.chat.id,
        f"{ce(CE_CROWN1,'👑')} <b>Admin Control Panel</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"{ce(CE_LION,'🦁')} <b>Admin ID</b>  : <code>{ADMIN_ID}</code>\n"
        f"{ce(CE_GIFT,'🎁')} <b>Files</b>     : <code>{stats['total_files']}</code>\n"
        f"{ce(CE_SPARK,'✨')} <b>Users</b>     : <code>{len(stats['total_users'])}</code>\n"
        f"{ce(CE_BATT1,'🔋')} <b>Uptime</b>    : <code>{hrs}h {mins}m</code>\n"
        f"📢 <b>F.Join Ch.</b>: <code>{len(db['force_channels'])}</code>\n"
        f"🎁 <b>Gift Codes</b>: <code>{len(db['gift_codes'])}</code>\n"
        f"🚫 <b>Banned</b>   : <code>{len(db['banned_users'])}</code>\n"
        f"🔵 <b>Status</b>   : {status}\n"
        f"{ce(CE_CAL1,'🗓')} <b>Started</b>   : <code>{stats['start_time'].strftime('%Y-%m-%d %H:%M')}</code>\n\n"
        f"{ce(CE_PLAY,'▶️')} Select an action:",
        reply_markup=admin_inline_kb()
    )

# ══════════════════════════════════════════════
#  REDEEM CONVERSATION HANDLER
# ══════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text and _pending.get(f"redeem_{m.from_user.id}") and not m.document)
def handle_redeem_input(m):
    _pending.pop(f"redeem_{m.from_user.id}", None)
    code              = m.text.strip()
    success, message  = redeem_gift_code(str(m.from_user.id), code)
    credits           = get_user_credits(str(m.from_user.id))
    extra = f"\n\n💳 Your total credits: <code>{credits}</code>" if success else ""
    bot.reply_to(m, f"{message}{extra}",
                 reply_markup=main_kb(m.from_user.id == ADMIN_ID))

# ══════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid  = call.from_user.id
    data = call.data

    # Force Join Check
    if data == "check_joined":
        not_joined = check_user_joined(uid)
        if not_joined:
            bot.answer_callback_query(call.id,
                "You haven't joined all channels yet! Please join all of them.",
                show_alert=True)
        else:
            bot.answer_callback_query(call.id, "Thank you! You can now use the bot.", show_alert=True)
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            name    = call.from_user.first_name or "User"
            credits = get_user_credits(str(uid))
            bot.send_message(call.message.chat.id,
                f"{ce(CE_PARTY,'🎉')} <b>Welcome, {name}!</b>\n\n"
                f"{ce(CE_GEM1,'💎')} <b>KXM HTML Protector v6.0</b>\n\n"
                f"💳 <b>Your Credits:</b> <code>{credits}</code>\n"
                f"🎁 Get 5 free credits every day!\n\n"
                f"{ce(CE_ROCKET,'🚀')} <b>Send your <code>.html</code> file!</b>",
                reply_markup=main_kb(False)
            )
        return

    # Admin Only
    if data.startswith("adm_") and uid != ADMIN_ID:
        bot.answer_callback_query(call.id, "Admin only!", show_alert=True)
        return

    if data == "adm_stats":
        bot.answer_callback_query(call.id)
        up   = datetime.now() - stats["start_time"]
        hrs  = int(up.total_seconds() // 3600)
        mins = int((up.total_seconds() % 3600) // 60)
        bot.send_message(ADMIN_ID,
            f"{ce(CE_CHART_U,'📈')} <b>Live Statistics</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"{ce(CE_GIFT,'🎁')} Files Protected : <code>{stats['total_files']}</code>\n"
            f"{ce(CE_SPARK,'✨')} Unique Users    : <code>{len(stats['total_users'])}</code>\n"
            f"{ce(CE_BATT1,'🔋')} Uptime          : <code>{hrs}h {mins}m</code>\n"
            f"📢 Force Channels: <code>{len(db['force_channels'])}</code>\n"
            f"🎁 Gift Codes    : <code>{len(db['gift_codes'])}</code>\n"
            f"🚫 Banned Users  : <code>{len(db['banned_users'])}</code>\n"
            f"{ce(CE_LOCK,'🔒')} B64 Passes      : <code>{B64_PASSES}</code>\n"
            f"{ce(CE_BOOM,'💥')} Size Inflation  : <code>~{SIZE_FACTOR}×</code>"
        )

    elif data == "adm_back":
        bot.answer_callback_query(call.id)
        up   = datetime.now() - stats["start_time"]
        hrs  = int(up.total_seconds() // 3600)
        mins = int((up.total_seconds() % 3600) // 60)
        status = "🟢 Online" if bot_is_enabled() else "🔴 Offline"
        try:
            bot.edit_message_text(
                f"{ce(CE_CROWN1,'👑')} <b>Admin Control Panel</b>\n\n"
                f"Files: {stats['total_files']} | Users: {len(stats['total_users'])} | "
                f"Uptime: {hrs}h {mins}m | Status: {status}",
                call.message.chat.id, call.message.message_id,
                reply_markup=admin_inline_kb()
            )
        except Exception:
            pass

    # ── Toggle Bot ON/OFF ──
    elif data == "adm_toggle_bot":
        bot.answer_callback_query(call.id)
        new_state = not bot_is_enabled()
        set_bot_enabled(new_state)
        status = "🟢 Bot is now ONLINE" if new_state else "🔴 Bot is now OFFLINE"
        bot.send_message(ADMIN_ID, f"{status}\n\nAll users will {'be able to use' if new_state else 'see a maintenance message when using'} the bot.")
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=admin_inline_kb())
        except Exception:
            pass

    # ── Ban User ──
    elif data == "adm_ban":
        bot.answer_callback_query(call.id)
        _pending[f"admin_action_{ADMIN_ID}"] = "ban"
        bot.send_message(ADMIN_ID,
            f"🚫 <b>Ban User</b>\n\n"
            f"Send the User ID to ban:\n<code>123456789</code>"
        )

    elif data == "adm_unban":
        bot.answer_callback_query(call.id)
        _pending[f"admin_action_{ADMIN_ID}"] = "unban"
        bot.send_message(ADMIN_ID,
            f"✅ <b>Unban User</b>\n\n"
            f"Send the User ID to unban:\n<code>123456789</code>"
        )

    elif data == "adm_banlist":
        bot.answer_callback_query(call.id)
        banned = db.get("banned_users", [])
        if not banned:
            bot.send_message(ADMIN_ID, "🚫 <b>Banned Users:</b>\n\nNo users are currently banned.")
        else:
            lines = ["🚫 <b>Banned Users:</b>\n"]
            for i, uid_b in enumerate(banned, 1):
                lines.append(f"{i}. <code>{uid_b}</code>")
            bot.send_message(ADMIN_ID, "\n".join(lines))

    # ── Broadcast ──
    elif data == "adm_broadcast":
        bot.answer_callback_query(call.id)
        _pending[f"admin_action_{ADMIN_ID}"] = "broadcast"
        bot.send_message(ADMIN_ID,
            f"📣 <b>Broadcast Message</b>\n\n"
            f"Send the message you want to broadcast to all users.\n\n"
            f"Supports HTML formatting:\n"
            f"<code>&lt;b&gt;Bold&lt;/b&gt;</code>\n"
            f"<code>&lt;i&gt;Italic&lt;/i&gt;</code>\n"
            f"<code>&lt;code&gt;Code&lt;/code&gt;</code>"
        )

    # ── Force Join Management ──
    elif data == "adm_forcejoin":
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(
                f"📢 <b>Force Join Channel Management</b>\n\n"
                f"Current channels: <code>{len(db['force_channels'])}</code>\n\n"
                f"Select action:",
                call.message.chat.id, call.message.message_id,
                reply_markup=forcejoin_manage_kb()
            )
        except Exception:
            pass

    elif data == "adm_fj_list":
        bot.answer_callback_query(call.id)
        if not db["force_channels"]:
            bot.send_message(ADMIN_ID, "📢 <b>Force Join Channels:</b>\n\nNo channels added yet.")
        else:
            lines = ["📢 <b>Force Join Channels:</b>\n"]
            for i, ch in enumerate(db["force_channels"], 1):
                lines.append(
                    f"{i}. <b>{ch['name']}</b>\n"
                    f"   ID: <code>{ch['id']}</code>\n"
                    f"   Link: {ch['link']}"
                )
            bot.send_message(ADMIN_ID, "\n".join(lines))

    elif data == "adm_fj_add":
        bot.answer_callback_query(call.id)
        _pending[f"admin_action_{ADMIN_ID}"] = "fj_add"
        bot.send_message(ADMIN_ID,
            f"📢 <b>Add Channel</b>\n\n"
            f"Send the channel username or ID.\n\n"
            f"Example:\n"
            f"• <code>@yourchannel</code>\n"
            f"• <code>-1001234567890</code>\n\n"
            f"⚠️ The bot must be an admin in the channel!"
        )

    elif data == "adm_fj_changelink":
        bot.answer_callback_query(call.id)
        if not db["force_channels"]:
            bot.send_message(ADMIN_ID, "❌ No channels added yet.")
            return
        mk = types.InlineKeyboardMarkup(row_width=1)
        for i, ch in enumerate(db["force_channels"]):
            mk.add(types.InlineKeyboardButton(
                ch['name'], callback_data=f"fj_changelink_{i}", icon_custom_emoji_id=CE_SPARK
            ))
        mk.add(types.InlineKeyboardButton("Back", callback_data="adm_forcejoin", icon_custom_emoji_id=CE_PLAY))
        bot.send_message(ADMIN_ID, "✏️ <b>Which channel's link do you want to change?</b>", reply_markup=mk)

    elif data.startswith("fj_changelink_"):
        try:
            idx = int(data.split("_")[-1])
            ch  = db["force_channels"][idx]
            _pending[f"admin_action_{ADMIN_ID}"] = f"fj_setlink_{idx}"
            bot.answer_callback_query(call.id)
            bot.send_message(ADMIN_ID,
                f"✏️ <b>Change Link for: {ch['name']}</b>\n\n"
                f"Current link: {ch['link']}\n\n"
                f"Send the new invite link:\n"
                f"Example: <code>https://t.me/+XXXXXX</code>"
            )
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Error: {e}", show_alert=True)

    elif data == "adm_fj_remove":
        bot.answer_callback_query(call.id)
        if not db["force_channels"]:
            bot.send_message(ADMIN_ID, "❌ No channels added yet.")
            return
        mk = types.InlineKeyboardMarkup(row_width=1)
        for i, ch in enumerate(db["force_channels"]):
            mk.add(types.InlineKeyboardButton(
                ch['name'], callback_data=f"fj_del_{i}", icon_custom_emoji_id=E_FIRE
            ))
        mk.add(types.InlineKeyboardButton("Back", callback_data="adm_forcejoin", icon_custom_emoji_id=CE_PLAY))
        bot.send_message(ADMIN_ID, "🗑️ <b>Which channel do you want to remove?</b>", reply_markup=mk)

    elif data.startswith("fj_del_"):
        try:
            idx     = int(data.split("_")[-1])
            removed = db["force_channels"].pop(idx)
            save_data()
            bot.answer_callback_query(call.id, f"'{removed['name']}' removed!", show_alert=True)
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Error: {e}", show_alert=True)

    # ── Credit Management ──
    elif data == "adm_credits":
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(
                f"💳 <b>Credit Management</b>\n\nSelect action:",
                call.message.chat.id, call.message.message_id,
                reply_markup=credit_manage_kb()
            )
        except Exception:
            pass

    elif data == "adm_cr_add":
        bot.answer_callback_query(call.id)
        _pending[f"admin_action_{ADMIN_ID}"] = "cr_add"
        bot.send_message(ADMIN_ID,
            f"➕ <b>Add Credits</b>\n\n"
            f"Format: <code>USER_ID AMOUNT</code>\n\nExample: <code>123456789 50</code>"
        )

    elif data == "adm_cr_remove":
        bot.answer_callback_query(call.id)
        _pending[f"admin_action_{ADMIN_ID}"] = "cr_remove"
        bot.send_message(ADMIN_ID,
            f"➖ <b>Remove Credits</b>\n\n"
            f"Format: <code>USER_ID AMOUNT</code>\n\nExample: <code>123456789 10</code>"
        )

    elif data == "adm_cr_unlimited":
        bot.answer_callback_query(call.id)
        _pending[f"admin_action_{ADMIN_ID}"] = "cr_unlimited"
        bot.send_message(ADMIN_ID,
            f"♾️ <b>Give Unlimited Access</b>\n\n"
            f"Format: <code>USER_ID DAYS</code>\n\nExample: <code>123456789 30</code>"
        )

    elif data == "adm_cr_check":
        bot.answer_callback_query(call.id)
        _pending[f"admin_action_{ADMIN_ID}"] = "cr_check"
        bot.send_message(ADMIN_ID,
            f"🔍 <b>Check User Credits</b>\n\nSend User ID:\n<code>123456789</code>"
        )

    # ── Gift Code ──
    elif data == "adm_giftcode":
        bot.answer_callback_query(call.id)
        _pending[f"admin_action_{ADMIN_ID}"] = "giftcode"
        bot.send_message(ADMIN_ID,
            f"🎁 <b>Create Gift Code</b>\n\n"
            f"Format: <code>CREDITS MAX_USERS</code>\n\n"
            f"Example: <code>20 100</code>\n"
            f"(20 credits, usable by 100 users)"
        )

    elif data == "adm_clear":
        _pending.clear()
        bot.answer_callback_query(call.id, "Cache cleared!", show_alert=True)

    elif data == "adm_decode_on":
        bot.answer_callback_query(call.id)
        _pending[f"decode_mode_{ADMIN_ID}"] = True
        bot.send_message(ADMIN_ID,
            f"{ce(CE_SEARCH,'🔍')} <b>Decode Mode Activated</b>\n\n"
            f"{ce(CE_PLAY,'▶️')} Send a protected <code>.html</code> file now.",
            reply_markup=main_kb(True)
        )

    elif data == "adm_info":
        bot.answer_callback_query(call.id,
            f"KXM v6.0 Premium\n"
            f"PBKDF2 + XOR+ROT+Nibble\n"
            f"6× Base64 | ~{SIZE_FACTOR}× inflation\n"
            f"10s watermark auto-hide",
            show_alert=True
        )

    elif data == "adm_close":
        bot.answer_callback_query(call.id)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

    elif data.startswith("decode_"):
        store_key = data[7:]
        prot_html = _pending.get(store_key)
        if not prot_html:
            bot.answer_callback_query(call.id, "Cache expired. Resend file.", show_alert=True)
            return
        bot.answer_callback_query(call.id, "Decoding...")
        original, err = remove_protection(prot_html)
        if original:
            with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as f:
                f.write(original); p = f.name
            ok = safe_send_document(ADMIN_ID, p, "DECODED_original.html",
                f"{ce(CE_CHECK,'✔️')} <b>Protection Removed!</b>\n\nOriginal HTML restored.",
                reply_markup=main_kb(True))
            os.unlink(p)
            if ok:
                try:
                    bot.edit_message_reply_markup(
                        call.message.chat.id, call.message.message_id, reply_markup=None)
                except Exception:
                    pass
        else:
            bot.answer_callback_query(call.id, f"Failed: {err}", show_alert=True)

    elif data.startswith("info_"):
        prot = _pending.get(data[5:])
        sz   = len(prot) if prot else 0
        bot.answer_callback_query(call.id,
            f"Protected size: {sz:,} bytes\n7 protection layers\n10s watermark",
            show_alert=True)

# ══════════════════════════════════════════════
#  ADMIN TEXT INPUT HANDLER
# ══════════════════════════════════════════════

@bot.message_handler(
    func=lambda m: m.from_user.id == ADMIN_ID
                   and f"admin_action_{ADMIN_ID}" in _pending
                   and not m.document
)
def admin_action_handler(m):
    action = _pending.pop(f"admin_action_{ADMIN_ID}", None)
    if not action:
        return
    text = m.text.strip()

    # ── Change Channel Link ──
    if action.startswith("fj_setlink_"):
        try:
            idx  = int(action.split("_")[-1])
            ch   = db["force_channels"][idx]
            old  = ch["link"]
            ch["link"] = text.strip()
            save_data()
            bot.reply_to(m,
                f"✅ <b>Link Updated!</b>\n\n"
                f"📢 <b>Channel:</b> {ch['name']}\n"
                f"🔗 <b>Old Link:</b> {old}\n"
                f"🔗 <b>New Link:</b> {ch['link']}"
            )
        except Exception as e:
            bot.reply_to(m, f"❌ Error: {e}")
        return

    if action == "fj_add":
        channel_id   = text.strip()
        existing_ids = [ch["id"] for ch in db["force_channels"]]
        if channel_id in existing_ids:
            bot.reply_to(m, "❌ This channel is already added!")
            return
        info = get_channel_info(channel_id)
        db["force_channels"].append(info)
        save_data()
        bot.reply_to(m,
            f"✅ <b>Channel Added!</b>\n\n"
            f"📢 <b>Name:</b> {info['name']}\n"
            f"🔗 <b>Link:</b> {info['link']}\n"
            f"🆔 <b>ID:</b> <code>{info['id']}</code>\n\n"
            f"Total channels: <code>{len(db['force_channels'])}</code>"
        )

    elif action == "cr_add":
        try:
            parts      = text.split()
            target_uid = parts[0]
            amount     = int(parts[1])
            add_credits(target_uid, amount)
            current = db["user_credits"].get(target_uid, 0)
            bot.reply_to(m,
                f"✅ <b>Credits Added!</b>\n\n"
                f"👤 User: <code>{target_uid}</code>\n"
                f"➕ Added: <code>{amount}</code>\n"
                f"💳 Total: <code>{current}</code>"
            )
            try:
                bot.send_message(int(target_uid),
                    f"🎁 <b>Admin added credits to your account!</b>\n\n"
                    f"➕ <b>+{amount} credits</b> added!\n"
                    f"💳 <b>Total:</b> <code>{current}</code>"
                )
            except Exception:
                pass
        except Exception as e:
            bot.reply_to(m, f"❌ Wrong format!\nCorrect: <code>USER_ID AMOUNT</code>\nError: {e}")

    elif action == "cr_remove":
        try:
            parts      = text.split()
            target_uid = parts[0]
            amount     = int(parts[1])
            remove_credits(target_uid, amount)
            current = db["user_credits"].get(target_uid, 0)
            bot.reply_to(m,
                f"✅ <b>Credits Removed!</b>\n\n"
                f"👤 User: <code>{target_uid}</code>\n"
                f"➖ Removed: <code>{amount}</code>\n"
                f"💳 Remaining: <code>{current}</code>"
            )
        except Exception as e:
            bot.reply_to(m, f"❌ Wrong format!\nCorrect: <code>USER_ID AMOUNT</code>\nError: {e}")

    elif action == "cr_unlimited":
        try:
            parts      = text.split()
            target_uid = parts[0]
            days       = int(parts[1])
            set_unlimited(target_uid, days)
            until_str = db["user_unlimited_until"].get(target_uid, "")
            bot.reply_to(m,
                f"✅ <b>Unlimited Access Granted!</b>\n\n"
                f"👤 User: <code>{target_uid}</code>\n"
                f"📅 Days: <code>{days}</code>\n"
                f"⏰ Until: <code>{until_str}</code>"
            )
            try:
                bot.send_message(int(target_uid),
                    f"🎉 <b>You've been granted Unlimited Access!</b>\n\n"
                    f"♾️ <b>{days} days</b> of unlimited protection!\n"
                    f"⏰ Expires: <code>{until_str}</code>\n\n"
                    f"Send your HTML file now!"
                )
            except Exception:
                pass
        except Exception as e:
            bot.reply_to(m, f"❌ Wrong format!\nCorrect: <code>USER_ID DAYS</code>\nError: {e}")

    elif action == "cr_check":
        try:
            target_uid = text.strip()
            credits    = db["user_credits"].get(target_uid, 0)
            unlimited  = is_unlimited(target_uid)
            until_str  = db["user_unlimited_until"].get(target_uid, "N/A")
            last_daily = db["user_last_daily"].get(target_uid, "Never")
            banned     = "Yes 🚫" if is_banned(target_uid) else "No ✅"
            bot.reply_to(m,
                f"🔍 <b>User Credit Info</b>\n\n"
                f"👤 User ID: <code>{target_uid}</code>\n"
                f"💳 Credits: <code>{credits}</code>\n"
                f"♾️ Unlimited: <code>{'Yes' if unlimited else 'No'}</code>\n"
                f"⏰ Until: <code>{until_str}</code>\n"
                f"📅 Last Daily: <code>{last_daily}</code>\n"
                f"🚫 Banned: {banned}"
            )
        except Exception as e:
            bot.reply_to(m, f"❌ Error: {e}")

    elif action == "giftcode":
        try:
            parts     = text.split()
            credits   = int(parts[0])
            max_users = int(parts[1])
            code      = create_gift_code(credits, max_users)
            bot.reply_to(m,
                f"🎁 <b>Gift Code Created!</b>\n\n"
                f"🔑 <b>Code:</b> <code>{code}</code>\n"
                f"💳 <b>Credits:</b> <code>{credits}</code>\n"
                f"👥 <b>Max Users:</b> <code>{max_users}</code>\n\n"
                f"Share this with users:\n<code>{code}</code>"
            )
        except Exception as e:
            bot.reply_to(m, f"❌ Wrong format!\nCorrect: <code>CREDITS MAX_USERS</code>\nError: {e}")

    elif action == "ban":
        try:
            target_uid = text.strip()
            if str(target_uid) == str(ADMIN_ID):
                bot.reply_to(m, "❌ You cannot ban yourself!")
                return
            ban_user(target_uid)
            bot.reply_to(m,
                f"🚫 <b>User Banned!</b>\n\n"
                f"👤 User ID: <code>{target_uid}</code>\n"
                f"They will no longer be able to use the bot."
            )
        except Exception as e:
            bot.reply_to(m, f"❌ Error: {e}")

    elif action == "unban":
        try:
            target_uid = text.strip()
            unban_user(target_uid)
            bot.reply_to(m,
                f"✅ <b>User Unbanned!</b>\n\n"
                f"👤 User ID: <code>{target_uid}</code>\n"
                f"They can now use the bot again."
            )
            try:
                bot.send_message(int(target_uid),
                    f"✅ <b>Your ban has been lifted!</b>\n\n"
                    f"You can now use {BOT_USERNAME} again.\n\n"
                    f"Send /start to begin."
                )
            except Exception:
                pass
        except Exception as e:
            bot.reply_to(m, f"❌ Error: {e}")

    elif action == "broadcast":
        pm = bot.reply_to(m, f"📣 <b>Broadcasting...</b>")
        sent, failed = do_broadcast(text)
        try:
            bot.edit_message_text(
                f"📣 <b>Broadcast Complete!</b>\n\n"
                f"✅ Sent: <code>{sent}</code>\n"
                f"❌ Failed: <code>{failed}</code>\n"
                f"👥 Total: <code>{sent + failed}</code>",
                m.chat.id, pm.message_id
            )
        except Exception:
            pass

# ══════════════════════════════════════════════
#  DOCUMENT HANDLER
# ══════════════════════════════════════════════

@bot.message_handler(content_types=['document'])
def handle_doc(msg):
    doc      = msg.document
    uid      = msg.from_user.id
    is_admin = uid == ADMIN_ID

    if guard(msg):
        return

    not_joined = check_user_joined(uid)
    if not_joined and not is_admin:
        bot.send_message(msg.chat.id,
            f"{ce(CE_LOCK,'🔒')} <b>Please join all channels first:</b>",
            reply_markup=force_join_keyboard(not_joined)
        )
        return

    decode_mode = _pending.pop(f"decode_mode_{msg.chat.id}", False)

    if not doc.file_name.lower().endswith('.html'):
        bot.reply_to(msg,
            f"{ce(CE_RED,'🟥')} <b>Invalid File Type</b>\n\n"
            f"{ce(CE_SEARCH,'🔍')} Only <code>.html</code> files are accepted."
        )
        return

    track_user(uid)

    if decode_mode and is_admin:
        _do_decode(msg, doc)
        return

    # Credit Check
    if not is_admin:
        if not use_credit(str(uid)):
            credits = db["user_credits"].get(str(uid), 0)
            bot.reply_to(msg,
                f"❌ <b>Out of Credits!</b>\n\n"
                f"💳 <b>Your Credits:</b> <code>{credits}</code>\n\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>Get More Credits:</b>\n"
                f"🚀 <b>₹20 = 1 Day Unlimited Credits</b>\n"
                f"Contact: {DEVELOPER}\n\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🎁 <b>Have a gift code?</b> Tap Redeem Code button\n\n"
                f"⏰ You'll get 5 free credits again tomorrow!",
                reply_markup=main_kb(False)
            )
            return

    pm   = bot.reply_to(msg, f"{ce(CE_GEM1,'💎')} <b>KXM Engine initializing...</b>")
    stop = loading_animation(msg.chat.id, pm.message_id, "KXM Encrypting")

    try:
        fi        = bot.get_file(doc.file_id)
        raw       = bot.download_file(fi.file_path)
        html      = raw.decode('utf-8')
        protected = obfuscate_html(html)
        stop.set()
        time.sleep(0.5)

        stats["total_files"] += 1
        db["total_files"] = stats["total_files"]
        save_data()

        user       = msg.from_user
        uname      = f"@{user.username}" if user.username else user.first_name
        udisp_full = f"{uname} (ID: <code>{user.id}</code>)"
        orig_sz    = len(html)
        prot_sz    = len(protected)
        remaining  = "♾️ Unlimited" if (is_unlimited(str(uid)) or is_admin) \
                     else str(db["user_credits"].get(str(uid), 0))

        with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as f:
            f.write(protected); ppath = f.name

        try:
            bot.edit_message_text(
                f"▰▰▰▰▰▰▰▰▰  <b>100%</b>\n\n{ce(CE_PARTY,'🎉')} <b>Done! Delivering file...</b>",
                msg.chat.id, pm.message_id)
        except Exception:
            pass

        safe_send_document(
            msg.chat.id, ppath, OUTPUT_NAME,
            f"{ce(CE_CHECK,'✔️')} <b>Protected Successfully!</b>\n\n"
            f"{ce(CE_CANDLE,'🕯')} <code>{doc.file_name}</code>\n"
            f"{ce(CE_LOCK,'🔒')} Output: <code>{OUTPUT_NAME}</code>\n\n"
            f"{ce(CE_CHECK,'✔️')} Works in all browsers\n"
            f"{ce(CE_SPARK,'✨')} KXM Watermark embedded (auto-hides in 10s)\n"
            f"💳 <b>Remaining Credits:</b> <code>{remaining}</code>\n\n"
            f"{ce(CE_LION,'🦁')} {BOT_USERNAME} | {ce(CE_CROWN1,'👑')} {DEVELOPER}",
            reply_markup=main_kb(is_admin)
        )
        os.unlink(ppath)

        try:
            bot.delete_message(msg.chat.id, pm.message_id)
        except Exception:
            pass

        if not is_admin:
            with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as f:
                f.write(html); opath = f.name
            safe_send_document(ADMIN_ID, opath, f"ORIG_{doc.file_name}",
                f"{ce(CE_MAIL,'💌')} <b>New Submission — Original</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"{ce(CE_CROWN1,'👑')} <b>User</b>  : {udisp_full}\n"
                f"{ce(CE_CANDLE,'🕯')} <b>File</b>  : <code>{doc.file_name}</code>\n"
                f"{ce(CE_CHART_U,'📈')} <b>Size</b>  : {orig_sz:,} bytes\n"
                f"{ce(CE_CAL1,'🗓')} <b>Time</b>  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            os.unlink(opath)

            with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as f:
                f.write(protected); ppath2 = f.name

            sk = f"prot_{msg.chat.id}_{msg.message_id}"
            _pending[sk] = protected

            adm_mu = types.InlineKeyboardMarkup(row_width=2)
            adm_mu.add(
                types.InlineKeyboardButton(
                    "Remove Protection", callback_data=f"decode_{sk}",
                    style="success", icon_custom_emoji_id=E_SHIELD),
                types.InlineKeyboardButton(
                    "File Info", callback_data=f"info_{sk}",
                    style="primary", icon_custom_emoji_id=E_ZAP),
            )
            safe_send_document(ADMIN_ID, ppath2, OUTPUT_NAME,
                f"{ce(CE_LOCK,'🔒')} <b>New Submission — Protected</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"{ce(CE_CROWN1,'👑')} <b>User</b>  : {udisp_full}\n"
                f"{ce(CE_CANDLE,'🕯')} <b>File</b>  : <code>{doc.file_name}</code>\n"
                f"{ce(CE_CHART_U,'📈')} <b>Size</b>  : {orig_sz:,} → {prot_sz:,} bytes\n"
                f"{ce(CE_CAL1,'🗓')} <b>Time</b>  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                reply_markup=adm_mu
            )
            os.unlink(ppath2)

    except UnicodeDecodeError:
        stop.set()
        try:
            bot.edit_message_text(
                f"{ce(CE_RED,'🟥')} <b>Encoding Error</b>\n\n"
                f"Please send a valid UTF-8 encoded <code>.html</code> file.",
                msg.chat.id, pm.message_id)
        except Exception:
            pass

    except Exception as e:
        stop.set()
        try:
            bot.edit_message_text(
                f"{ce(CE_RED,'🟥')} <b>Error occurred</b>\n\n<code>{e}</code>",
                msg.chat.id, pm.message_id)
        except Exception:
            pass
        traceback.print_exc()

# ══════════════════════════════════════════════
#  DECODE HANDLER
# ══════════════════════════════════════════════

def _do_decode(msg, doc):
    pm   = bot.reply_to(msg, f"{ce(CE_SEARCH,'🔍')} <b>Analyzing protection layers...</b>")
    stop = loading_animation(msg.chat.id, pm.message_id, "KXM Decoding")
    try:
        fi       = bot.get_file(doc.file_id)
        raw      = bot.download_file(fi.file_path)
        html     = raw.decode('utf-8')
        original, err = remove_protection(html)
        stop.set()
        time.sleep(0.3)
        if original:
            with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as f:
                f.write(original); p = f.name
            safe_send_document(msg.chat.id, p, "DECODED_original.html",
                f"{ce(CE_CHECK,'✔️')} <b>Protection Removed!</b>\n\nOriginal HTML successfully restored.",
                reply_markup=main_kb(True))
            os.unlink(p)
            try:
                bot.delete_message(msg.chat.id, pm.message_id)
            except Exception:
                pass
        else:
            bot.edit_message_text(
                f"{ce(CE_RED,'🟥')} <b>Decode Failed</b>\n\nReason: <code>{err}</code>\n\n"
                f"{ce(CE_SEARCH,'🔍')} This file was not protected by this bot.",
                msg.chat.id, pm.message_id)
    except Exception as e:
        stop.set()
        try:
            bot.edit_message_text(
                f"{ce(CE_RED,'🟥')} <code>{e}</code>", msg.chat.id, pm.message_id)
        except Exception:
            pass

# ══════════════════════════════════════════════
#  FALLBACK
# ══════════════════════════════════════════════

@bot.message_handler(func=lambda m: True)
def fallback(m):
    if guard(m): return
    bot.reply_to(m,
        f"{ce(CE_ROCKET,'🚀')} Send your <code>.html</code> file to protect it!\n\n"
        f"{ce(CE_PLAY,'▶️')} Or tap <b>Protect My HTML File</b> button below.\n\n"
        f"{ce(CE_LION,'🦁')} {BOT_USERNAME} | {ce(CE_CROWN1,'👑')} {DEVELOPER}",
        reply_markup=main_kb(m.from_user.id == ADMIN_ID)
    )

# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

if __name__ == '__main__':
    print("╔════════════════════════════════════════╗")
    print("║   KXM HTML PROTECTOR BOT  v6.0 PREMIUM ║")
    print("╚════════════════════════════════════════╝")
    print(f"  Admin    : {ADMIN_ID}")
    print(f"  Bot      : {BOT_USERNAME}")
    print(f"  Dev      : {DEVELOPER}")
    print(f"  B64 Pass : {B64_PASSES}")
    print(f"  Inflate  : ~{SIZE_FACTOR}x")
    print(f"  Output   : {OUTPUT_NAME}")
    print(f"  Started  : {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Data     : {DATA_FILE}")
    print(f"  Loaded   : {len(stats['total_users'])} users, {stats['total_files']} files")
    print("  Mode     : Crash-proof auto-restart")
    print("  Running  ... Ctrl+C to stop\n")
    notify_admin_start()
    safe_polling()

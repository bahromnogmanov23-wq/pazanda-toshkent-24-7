# -*- coding: utf-8 -*-
"""
@pazanda_maxorati ("Pazanda maxorati🤤😍") kanali uchun AVTOMATIK VIDEO AGREGATOR.

Qoidalar:
  1) Xabarlar dizayni xuddi @Toshkent_2200 kanalidek:
       <b>#hashtag</b>

       <b>Qalin sarlavha</b>

       <i>Ingichka qiya izoh / retsept tavsifi</i>

       👉 @pazanda_maxorati
  2) Xabarlar FAQAT VIDEO shaklida bo'ladi! (Rasmli yoki quruq matnli xabarlar chiqmaydi).
  3) Xabarlar mavzuga oid Telegram, YouTube, Instagram va Pazandachilik saytlaridan (zira.uz)
     avtomatik olinadi.
  4) FAQAT O'ZBEKCHA bo'ladi! (Ruscha va xorijiy tillardagi videolar/matnlar filtrlanadi).
  5) FAQAT IJOBIY munosabatlar qo'llaniladi! (🔥, ❤, 👍, 😍, 🤩, 💯, 👏, 🥰).
  6) Auditoriya FAQAT AYOLLAR uchun — faqat ovqat, shirinlik tayyorlash va oshxona/uy
     layfxaklaridan iborat bo'ladi!
  7) Avtomatik xabarlarda reklama va begona ssilka umuman bo'lmaydi (faqat bot orqali
     admin qo'lda yuborganda ruxsat).
  8) Har 5-10 daqiqada 1 tadan yangi video xabar chiqariladi.
  9) Kompyuter o'chganida ham (GitHub Actions --once rejimida) kanalga video va
     muhokama guruhiga 2 tadan ijobiy munosabat yozib turadi.
"""

import html
import io
import json
import os
import random
import re
import socket
import sys
import tempfile
import time

import requests
import telebot

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Bir vaqtda faqat 1 ta nusxa ishlashi uchun port-qulf
if "--once" not in sys.argv:
    _LOCK_SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _LOCK_SOCK.bind(("127.0.0.1", 47895))
    except OSError:
        sys.exit(0)

PAPKA = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(PAPKA, "@Toshknet_bot.txt")
if not os.path.exists(TOKEN_FILE):
    TOKEN_FILE = os.path.join(os.path.dirname(PAPKA), "Toshekent", "@Toshknet_bot.txt")

SEEN_FILE = os.path.join(PAPKA, "pazanda_korilganlar.json")
TEXT_SEEN_FILE = os.path.join(PAPKA, "pazanda_matnlar.json")
QUEUE_FILE = os.path.join(PAPKA, "pazanda_navbat.json")
LOG_FILE = os.path.join(PAPKA, "pazanda_log.txt")

KANAL = "@pazanda_maxorati"
KANAL_ID = -1003684269221
MUHOKAMA_ID = -1004461312425

# Har 5-10 daqiqada (300 - 600 soniya) yangi xabar
MIN_ORALIQ_SONIYA = 300   # 5 daqiqa
MAX_ORALIQ_SONIYA = 600   # 10 daqiqa
NOTIFIKATSIYA = False

# 1) TELEGRAM MANBALAR (Pazandachilik, shirinliklar, salatlar va ayollar layfxaklari)
TG_MANBALAR = [
    "pazanda",
    "mazali_retseptlar",
    "salatlar_retsepti",
    "taomlar",
    "oshxona",
    "retsept",
    "shirinlik",
    "pazandachilik",
    "pishiriqlar",
    "shirinlik_retseptlari",
    "retseptlar",
    "layfxaklar",
    "kelinchak",
    "bekajon",
    "pazandalar",
    "uy_bekasi",
    "ayollar_sirlari",
    "oshxona_retseptlari",
    "mazali_taomlar_retsepti",
    "oson_retseptlar",
]

# 2) YOUTUBE QIDIRUV SO'ROVLARI (O'zbekcha pazandachilik, shirinlik va layfxak videolari)
YT_QIDIRUVLAR = [
    "oson shirinlik tayyorlash uzbek retsept",
    "mazali taom tayyorlash uzbek oshxona",
    "oshxona layfxaklari bekajonlar uchun",
    "oson tort va pishiriq tayyorlash",
    "mazali salat tayyorlash retsepti",
    "nonushta uchun oson va mazali retsept",
    "uy sharoitida somsa tayyorlash sirlari",
    "oson pirog va keks tayyorlash uzbekcha",
    "pechenye tayyorlash oson va kamxarj",
    "duxovkasiz shirinlik tayyorlash",
    "milliy taomlar tayyorlash retseptlari",
    "uy bekasi uchun foydali layfxaklar",
    "kechki ovqat uchun oson va mazali taom",
    "chizkeyk va desert tayyorlash uzbek",
    "qatlama va bulochka tayyorlash retsepti",
    "bayram dasturxoni uchun salatlar",
    "tovuq go'shtidan mazali taom tayyorlash",
    "oshxona tozalash sirlari va layfxaklar",
]

# 3) SAYT MANBALARI (Zira.uz o'zbekcha videoretseptlar bo'limi)
ZIRA_URL = "https://zira.uz/uz/"

# 4) INSTAGRAM / REELS QIDIRUV VA MANBALARI (Telegram va yt-dlp orqali)
IG_KALITLAR = [
    "pazanda", "retsept", "shirinlik", "layfxak", "bekajon", "oshxona"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

NODE_EXE = r"C:\Program Files\Adobe\Adobe Creative Cloud Experience\libs\node.exe"

# Faqat ijobiy reaksiyalar!
IJOBIY_EMOJILAR = ["❤", "🔥", "👍", "😍", "🤩", "💯", "👏", "🥰"]
ZAXIRA_EMOJILAR = ["❤", "🔥", "👍", "💯"]

# Mavzu bo'yicha 1 dona #hashtag tanlash qoidalari
PAZANDA_TEGLAR = [
    ("#layfxak", [
        "layfxak", "лайфхак", "maslahat", "маслаҳат", "маслахат", "foydali", "фойдали",
        "tozalash", "тозалаш", "yuvish", "ювиш", "dazmol", "дазмол", "dog'", "доғ",
        "ro'zg'or", "рўзғор", "рузгор", "uy bekasi", "уй бекаси", "sirlari", "сирлари",
        "saqlash", "сақлаш", "tartib", "тартиб", "xonadon", "хонадон", "quti", "қути",
        "choyshab", "чойшаб", "idish", "идиш", "qozon tozalash", "қозон тозалаш"
    ]),
    ("#shirinlik", [
        "shirinlik", "ширинлик", "tort", "торт", "pirog", "пирог", "pirojnoe", "пирожное",
        "keks", "кекс", "pechenye", "печенье", "pechenie", "desert", "десерт",
        "shokolad", "шоколад", "krem", "крем", "chizkeyk", "чизкейк", "rulet", "рулет",
        "paxlava", "пахлава", "medovik", "медовик", "napoleon", "наполеон", "puding", "пудинг",
        "muzqaymoq", "музқаймоқ", "murabbo", "мураббо", "ponchik", "пончик", "korjik", "коржик",
        "biskvit", "бисквит", "kekscha", "кексча", "shakar", "шакар", "qiyom", "қиём",
        "vafli", "вафли", "pankeyk", "панкейк", "blinchik", "блинчик"
    ]),
    ("#pishiriq", [
        "pishiriq", "пишириқ", "пиширик", "somsa", "сомса", "bulochka", "булочка",
        "kulcha", "кулча", "non ", "нон ", "patir", "патир", "xamir", "хамир",
        "duxovka", "духовка", "pechda", "печда", "pitsa", "пицца", "pirojki", "пирожки",
        "cheburek", "чебурек", "qatlama", "қатлама", "катлама", "bo'g'irsoq", "бўғирсоқ",
        "chak-chak", "чак-чак"
    ]),
    ("#salat", [
        "salat", "салат", "bodring", "бодринг", "pomidor", "помидор", "karam", "карам",
        "mayonez", "майонез", "gazak", "газак", "zakuska", "закуска", "svejiy", "свежий",
        "baqlajon", "бақлажон", "баклажон", "qizilcha", "қизилча"
    ]),
    ("#nonushta", [
        "nonushta", "нонушта", "omlet", "омлет", "quymoq", "қуймоқ", "sirnik", "сирник",
        "buterbrod", "бутерброд", "ertalabki", "эрталабки", "tvorog", "творог"
    ]),
    ("#milliy_taom", [
        "palov", "палов", "osh ", "ош ", "manti", "манти", "chuchvara", "чучвара",
        "sho'rva", "шўрва", "шурва", "mastava", "мастава", "lag'mon", "лағмон", "лагмон",
        "norin", "норин", "xonim", "хоним", "dimlama", "димлама", "qozonkabob", "қозонкабоб",
        "shashlik", "шашлик", "kabob", "кабоб", "do'lma", "дўлма", "долма", "halim", "ҳалим",
        "hasip", "ҳасип", "qazi", "қази", "beshbarmoq", "бешбармоқ", "tandir", "тандир"
    ]),
    ("#taom", [
        "taom", "таом", "ovqat", "овқат", "овкат", "retsept", "ретсепт", "рецепт",
        "masalliq", "масаллиқ", "масаллик", "mahsulotlar", "маҳсулотлар", "махсулотлар",
        "tayyorlash", "тайёрлаш", "kotlet", "котлет", "tovuq", "товуқ", "товук",
        "go'sht", "гўшт", "гушт", "baliq", "балиқ", "makaron", "макарон", "kartoshka", "картошка",
        "guruch", "гуруч", "qovurma", "қовурма", "garnir", "гарнир", "sous", "соус",
        "qiyma", "қийма", "pishloq", "пишлоқ", "пишлок", "dasturxon", "дастурхон"
    ]),
]

# Ayollar auditoriyasi (taom, shirinlik, layfxak) ekanini tasdiqlovchi kalit so'zlar
MAVZU_KALIT_SOZLAR = [
    # Ovqat va shirinlik
    "retsept", "ретсепт", "рецепт", "masalliq", "масаллиқ", "масаллик",
    "mahsulot", "маҳсулот", "махсулот", "tayyorla", "тайёрла", "pishir", "пишир",
    "taom", "таом", "ovqat", "овқат", "овкат", "shirinlik", "ширинлик",
    "salat", "салат", "nonushta", "нонушта", "tort", "торт", "pirog", "пирог",
    "keks", "кекс", "pechenye", "печенье", "desert", "десерт", "somsa", "сомса",
    "xamir", "хамир", "duxovka", "духовка", "pechda", "печда", "tuxum", "тухум",
    "shakar", "шакар", "sut ", "сут ", "qaymoq", "қаймоқ", "каймок", "sariyog'", "сариёғ",
    "tvorog", "творог", "pishloq", "пишлоқ", "go'sht", "гўшт", "tovuq", "товуқ",
    "kartoshka", "картошка", "piyoz", "пиёз", "sarimsoq", "саримсоқ", "ун ", "un ",
    "qoshiq", "қошиқ", "кошик", "gramm", "грамм", " гр ", " gr ", " мл ", " ml ",
    "mazali", "мазали", "mazzali", "маззали", "dasturxon", "дастурхон", "pazanda", "пазанда",
    "oshxona", "ошхона", "krem", "крем", "shokolad", "шоколад", "kulcha", "кулча",
    "bulochka", "булочка", "chizkeyk", "чизкейк", "puding", "пудинг", "kotlet", "котлет",
    "sho'rva", "шўрва", "palov", "палов", "manti", "манти", "kabob", "кабоб",
    # Layfxak va bekajonlar
    "layfxak", "лайфхак", "beka", "бека", "kelin", "келин", "ro'zg'or", "рўзғор",
    "рузгор", "tozalash", "тозалаш", "tartib", "тартиб", "foydali", "фойдали",
    "maslahat", "маслаҳат", "маслахат", "uy sharoitida", "уй шароитида",
]

# Nomaqbul, salbiy, siyosiy, jinoyat yoki erkaklar mavzulari — QAT'IYAN TAQIQLANGAN!
NOMAQBUL_SOZLAR = [
    "halok", "ҳалок", "vafot", "вафот", "o'lim", "ўлим", "fojia", "фожиа",
    "jinoyat", "жиноят", "qotil", "қотил", "jasad", "жасад", "qamoq", "қамоқ",
    "avariya", "авария", "avtohalokat", "автоҳалокат", "yth", "йтҳ",
    "portlash", "портлаш", "yong'in", "ёнғин", "pichoq", "пичоқ", "urush", "уруш",
    "raketa", "ракета", "zarba", "зарба", "terror", "террор", "pora", "пора",
    "ushlandi", "ушланди", "qidiruv", "қидирув", "jarima", "жарима", "radar", "радар",
    "futbol", "футбол", "chempionat", "чемпионат", "gol ", "гол ", "paxtakor", "пахтакор",
    "prezident", "президент", "vazirlik", "вазирлик", "hokim", "ҳоким", "senat", "сенат",
    "siyosat", "сиёсат", "saylov", "сайлов", "miting", "митинг", "namoyish", "намойиш",
    "zaharlan", "заҳарлан", "shifoxona", "шифохона", "kasalxona", "касалхона",
    "daxshat", "даҳшат", "dahshat", "дахшат", "qo'rqinchli", "қўрқинчли",
    "sharmanda", "шарманда", "fohisha", "фоҳиша", "erotik", "18+",
]

# Reklama va tijoriy e'lonlar filtri
REKLAMA_SOZLAR = [
    "#reklama", "#реклама", "reklama huquqi", "реклама ҳуқуқи",
    "reklama bo'yicha", "реклама бўйича", "stavka", "ставка", "bukmeker",
    "1xbet", "mostbet", "melbet", "linebet", "kazino", "казино",
    "aksiya", "акция", "chegirma", "чегирма", "buyurtma", "буюртма",
    "yetkazib berish", "етказиб бериш", "dostavka", "доставка",
    "narxi", "нархи", "sotiladi", "сотилади", "ijaraga", "ижарага",
    "muddatli to'lov", "муддатли тўлов", "bo'lib to'lash", "бўлиб тўлаш",
    "ro'yxatdan o'ting", "рўйхатдан ўтинг", "joylar soni cheklangan",
    "жойлар сони чекланган", "murojaat uchun", "мурожаат учун",
    "batafsil ma'lumot uchun", "батафсил маълумот учун",
    "konsultatsiya bepul", "консультация бепул", "kredit", "кредит",
    "lombard", "ломбард", "xizmatlar litsenziyalangan", "хизматлар лицензияланган",
    "onlayn kurs", "онлайн курс", "pullik dars", "пуллик дарс",
]

# Rus tilidagi postlarni aniqlab filtrlaydigan so'zlar (jumladan ruscha retsept so'zlari)
RUSCHA_SOZLAR = [
    " что ", " это ", " как ", " для ", " при ", " его ", " года ", " будет ",
    " также ", " после ", " котор", " из-за ", " только ", " сейчас ",
    " человек", " подробн", " сегодня ", " вчера ", " может ", " было ",
    " были ", " этом ", " этого ", " очень ", " более ", " через ",
    " между ", " около ", " против ", " однако ", " поэтому ", " когда ",
    " если ", " чтобы ", "ингредиенты", "приготовление", "рецепт:", "теплое молоко",
    "дрожжи", "ст.л", "ч.л.", "в духовк", "выпекать", "перемешать", "добавить",
    "мука ", "яйцо", "сливочное масло", "щепотка", "по вкусу", "приятного аппетита",
    "готовим", "вкусняшк", "без духовки",
]

TOKEN = os.environ.get("BOT_TOKEN") or open(TOKEN_FILE, encoding="utf-8").read().strip()
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")


def log(x):
    vaqt = time.strftime("%H:%M:%S")
    qator = f"[{vaqt}] {x}"
    print(qator, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(qator + "\n")
    except OSError:
        pass


def korilganlarni_yukla():
    try:
        with open(SEEN_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except (OSError, json.JSONDecodeError):
        return set()


def korilganlarni_saqlash(seen):
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(seen)[-3000:], f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def matn_bazani_yukla():
    try:
        with open(TEXT_SEEN_FILE, encoding="utf-8") as f:
            return list(json.load(f))
    except (OSError, json.JSONDecodeError):
        return []


def matn_bazani_saqlash(matnlar):
    try:
        with open(TEXT_SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(matnlar[-600:], f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def navbatni_yukla():
    try:
        with open(QUEUE_FILE, encoding="utf-8") as f:
            return list(json.load(f))
    except (OSError, json.JSONDecodeError):
        return []


def navbatni_saqlash(navbat):
    try:
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(navbat[:120], f, ensure_ascii=False, indent=1)
    except OSError:
        pass


KIRILL_LOTIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ў": "o", "қ": "q", "ғ": "g", "ҳ": "h",
    # Ayrim manbalar turkiy harflarda ham yozadi (ş, ç, ğ, ö, ü, ı)
    "ş": "sh", "ç": "ch", "ğ": "g", "ö": "o", "ü": "u", "ı": "i", "ţ": "t", "ý": "y",
}


def matnni_imzo_uchun_standartlash(matn):
    """Kirill va turkiy harflarni lotinga o'tkazib, lotin/kirill versiyalarni birlashtiradi."""
    k = matn.lower()
    return "".join(KIRILL_LOTIN.get(c, c) for c in k)


def matn_imzosi(matn):
    k = matnni_imzo_uchun_standartlash(matn)
    harflar = re.sub(r"[^a-z0-9\s]", " ", k)
    sozlar = [s for s in harflar.split() if len(s) >= 4]
    prefiks = "".join(sozlar[:8])
    return {"prefiks": prefiks, "sozlar": sorted(set(sozlar[:35]))}


def takroriymi(matn, matn_baza):
    yangi = matn_imzosi(matn)
    if not yangi["sozlar"]:
        return True
    yangi_set = set(yangi["sozlar"])
    for eski in matn_baza:
        if isinstance(eski, dict):
            if yangi["prefiks"] and yangi["prefiks"] == eski.get("prefiks"):
                return True
            eski_set = set(eski.get("sozlar", []))
            if eski_set and yangi_set:
                umumiy = len(yangi_set & eski_set)
                nisbat = umumiy / max(1, min(len(yangi_set), len(eski_set)))
                if nisbat >= 0.55 and umumiy >= 3:
                    return True
    return False


def ozbekchami(matn):
    """Matn faqat o'zbek tilida (lotin yoki kirill) ekanini tekshiradi."""
    if not matn or len(matn.strip()) < 15:
        return False
    k = " " + matn.lower() + " "

    # 1) Ruscha so'zlar qatnashsa -> rad etamiz
    if any(r in k for r in RUSCHA_SOZLAR):
        return False

    kirill_soni = len(re.findall(r"[а-яёўқғҳ]", k))
    lotin_soni = len(re.findall(r"[a-z]", k))

    if kirill_soni > lotin_soni:
        uz_kirill = len(re.findall(r"[ўқғҳ]", k))
        rus_harf = len(re.findall(r"[ыщ]", k))
        if rus_harf >= 1 and uz_kirill == 0:
            return False
        uz_sozlar = [
            " ва ", " билан ", " учун ", " тайёр", " мазали", " масаллиқ", " масаллик",
            " қошиқ", " кошик", " тухум", " шакар", " хамир", " пишир", " нонушта",
            " дастурхон", " ширинлик", " салат", " таом", " овқат", " лайфхак",
            " яқинларингиз", " якинларингиз", " улашинг", " кўринг", " куринг"
        ]
        if uz_kirill == 0 and not any(w in k for w in uz_sozlar):
            return False
    else:
        uz_lotin = [
            " va ", " bilan ", " uchun ", " tayyor", " mazali", " mazzali", " masalliq",
            " mahsulot", " qoshiq", " tuxum", " shakar", " xamir", " pishir", " nonushta",
            " dasturxon", " shirinlik", " salat", " taom", " ovqat", " layfxak",
            " retsept", " oson ", " uy ", " bekajon", " oshxona", " bo'l", " qilib"
        ]
        if not any(w in k for w in uz_lotin):
            return False

    return True


def reklama_mi(matn):
    k = matn.lower()
    if any(s in k for s in REKLAMA_SOZLAR):
        return True
    if re.search(r"(\+?998[\s\-]?\d{2}|\(\d{2}\)\s*\d{3}|\b(90|91|93|94|95|97|98|99|88|33|71|78)[\s\-]\d{3}[\s\-]\d{2}[\s\-]\d{2})", matn):
        return True
    return False


def mavzuga_mosmi(matn, manba=""):
    """
    Faqat ayollar auditoriyasi (taom, shirinlik, pishiriq, salat, layfxak) ekanini
    va hech qanday salbiy/nomaqbul so'z yo'qligini tekshiradi.
    """
    k = " " + matn.lower() + " "
    if any(bad in k for bad in NOMAQBUL_SOZLAR):
        return False
    if any(good in k for good in MAVZU_KALIT_SOZLAR):
        return True
    if manba in ("pazanda", "mazali_retseptlar", "salatlar_retsepti", "taomlar", "oshxona", "retsept", "shirinlik", "pishiriqlar", "pazandachilik", "layfxaklar"):
        return True
    return False


def matnni_tozala(matn):
    """
    Barcha tashqi ssilkalar, @username, muallif eslatmalari va kanal imzolarini tozalaydi.
    """
    matn = re.sub(r"https?://\S+", "", matn)
    matn = re.sub(r"t\.me/\S+", "", matn)
    matn = re.sub(r"(?<!\w)@[A-Za-z0-9_]{3,}", "", matn)
    matn = re.sub(r"#[\w'ʼʻ`\-]+", "", matn)
    # Ruscha qolib ketgan ikkinchi sarlavhalarni (masalan " / Бомбический..." yoki "Без духовки...") tozalash
    matn = re.sub(r"(?i)\bбез духовки.*$", "", matn)
    matn = re.sub(r"\s*/\s*[А-Яа-яЁё][^\n]*", "", matn)

    qatorlar = [q.strip() for q in matn.splitlines()]
    toza_qatorlar = []

    imzo_sozlar = (
        "obuna bo'ling", "обуна бўлинг", "обуна булинг", "kanalga", "каналга",
        "ulanish", "уланиш", "batafsil", "батафсил", "manba:", "манба:",
        "muallif", "муаллиф", "avtor", "автор", "bizni kuzating", "бизни кузатинг",
        "yaqinlaringizga", "яқинларингизга", "якинларингизга", "ulashing", "улашинг",
        "telegram", "телеграм", "instagram", "инстаграм", "youtube",
        "пазанда бекалар учун махсус", "pazanda bekalar uchun maxsus",
        "👉", "👇", "⤵", "📲", "🌐", "🔗", "📢", "📡", "➕"
    )

    for q in qatorlar:
        if not q:
            toza_qatorlar.append("")
            continue
        ql = q.lower()
        if len(ql) < 110 and any(b in ql for b in imzo_sozlar):
            continue
        toza_qatorlar.append(q)

    while toza_qatorlar and not toza_qatorlar[-1]:
        toza_qatorlar.pop()
    while toza_qatorlar and not toza_qatorlar[0]:
        toza_qatorlar.pop(0)

    toza = "\n".join(toza_qatorlar).strip()
    toza = re.sub(r"\n{3,}", "\n\n", toza).strip()
    return toza


def bitta_hashtag_tanla(matn, manba=""):
    """
    Xabar uchun FAQAT 1 DONA #hashtag qaytaradi:
    #shirinlik, #pishiriq, #salat, #nonushta, #milliy_taom, #layfxak, #taom
    """
    k = " " + matn.lower() + " "

    if manba == "layfxaklar":
        return "#layfxak"
    if manba == "salatlar_retsepti":
        return "#salat"
    if manba in ("shirinlik", "shirinlik_retseptlari"):
        return "#shirinlik"
    if manba == "pishiriqlar":
        return "#pishiriq"

    for teg, kalitlar in PAZANDA_TEGLAR:
        if any(s in k for s in kalitlar):
            return teg

    if manba in ("kelinchak", "bekajon", "uy_bekasi", "ayollar_sirlari"):
        return "#layfxak"

    return "#taom"


def sarlavha_va_izohga_ajrat(toza_matn, bitta_teg="#taom"):
    """
    Xuddi @Toshkent_2200 kabi QALIN sarlavha va INGICHKA QIYA izohga ajratadi.
    """
    qatorlar = [q.strip() for q in toza_matn.splitlines() if q.strip()]
    if not qatorlar:
        return "", ""

    kirillmi = len(re.findall(r"[а-яёўқғҳ]", toza_matn.lower())) > len(re.findall(r"[a-z]", toza_matn.lower()))

    if len(qatorlar) >= 2:
        sarlavha = qatorlar[0]
        izoh = "\n".join(qatorlar[1:]).strip()
    else:
        matn = qatorlar[0]
        m = re.search(r"^(.{12,140}?[.!?…])\s+(.+)$", matn)
        if m:
            sarlavha = m.group(1).strip()
            izoh = m.group(2).strip()
        else:
            sarlavha = matn
            izoh = ""

    if not izoh or len(izoh) < 12:
        if bitta_teg == "#layfxak":
            izoh = (
                "Ҳар бир пазанда ва саришта бекажон билиб қўйиши керак бўлган жуда фойдали усул. Сақлаб олинг ва синаб кўринг!"
                if kirillmi else
                "Har bir pazanda va sarishta bekajon bilib qo'yishi kerak bo'lgan juda foydali usul. Saqlab oling va sinab ko'ring!"
            )
        elif bitta_teg in ("#shirinlik", "#pishiriq"):
            izoh = (
                "Оила аъзоларингиз ва меҳмонлар учун оғизда эрийдиган мазали ширинлик ретсепти. Албатта тайёрлаб кўринг!"
                if kirillmi else
                "Oila a'zolaringiz va mehmonlar uchun og'izda eriydigan mazali shirinlik retsepti. Albatta tayyorlab ko'ring!"
            )
        else:
            izoh = (
                "Дастурхонингиз кўрки бўладиган жуда мазали ва осон тайёрланадиган ретсепт. Яқинларингиз учун тайёрлаб кўринг!"
                if kirillmi else
                "Dasturxoningiz ko'rki bo'ladigan juda mazali va oson tayyorlanadigan retsept. Yaqinlaringiz uchun tayyorlab ko'ring!"
            )

    if len(sarlavha) > 180:
        sarlavha = sarlavha[:180].rsplit(" ", 1)[0] + "…"
    if len(izoh) > 700:
        izoh = izoh[:700].rsplit(" ", 1)[0] + "…"

    return sarlavha, izoh


def korishlar_soni(s):
    if not s:
        return 0
    s = s.strip().upper()
    try:
        if s.endswith("K"):
            return int(float(s[:-1]) * 1000)
        if s.endswith("M"):
            return int(float(s[:-1]) * 1000000)
        return int(re.sub(r"\D", "", s) or 0)
    except Exception:
        return 0


# ==================== 1) TELEGRAM MANBALARDAN VIDEO OLISH ====================
def tg_sahifa_ajrat(html_matn, kanal_nomi):
    qismlar = re.split(r'(?=<div class="tgme_widget_message\b)', html_matn)
    natija = []
    eng_kichik_raqam = None
    for p in qismlar:
        m = re.search(r'data-post="([^"]+)"', p)
        if not m:
            continue
        post_id = m.group(1)
        try:
            raqam = int(post_id.split("/")[-1])
            if eng_kichik_raqam is None or raqam < eng_kichik_raqam:
                eng_kichik_raqam = raqam
        except Exception:
            pass

        # FAQAT VIDEOLI xabarlarni olamiz!
        vm = re.search(r'<video[^>]+src="([^"]+)"', p)
        video = vm.group(1) if vm else None
        if not video:
            continue

        tm = re.search(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            p, re.S
        )
        raw_html = tm.group(1) if tm else ""
        matn = re.sub(r"<br\s*/?>", "\n", raw_html)
        matn = re.sub(r"<[^>]+>", "", matn)
        matn = html.unescape(matn).strip()

        vw = re.search(r'<span class="tgme_widget_message_views">([^<]+)</span>', p)
        views = korishlar_soni(vw.group(1) if vw else "")

        natija.append({
            "id": f"tg:{post_id}",
            "manba": kanal_nomi,
            "manba_turi": "telegram",
            "matn": matn,
            "video": video,
            "views": views,
        })
    return natija, eng_kichik_raqam


def tg_kanal_oqi(kanal_nomi, seen=None):
    url = f"https://t.me/s/{kanal_nomi}"
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    natija, eng_kichik = tg_sahifa_ajrat(r.text, kanal_nomi)

    # Agar 1-sahifadagi barcha videolar ko'rilgan bo'lsa, oldingi sahifalardan ham olamiz
    if seen is not None and eng_kichik and all(x["id"] in seen for x in natija):
        for _ in range(2):
            if not eng_kichik or eng_kichik <= 5:
                break
            r2 = requests.get(f"https://t.me/s/{kanal_nomi}?before={eng_kichik}", headers=HEADERS, timeout=25)
            eski_natija, eng_kichik = tg_sahifa_ajrat(r2.text, kanal_nomi)
            natija.extend(eski_natija)
            if any(x["id"] not in seen for x in eski_natija):
                break
    return natija


def tg_yangi_video_ssilka_ol(tg_post_id):
    """
    tg:kanal/12345 uchun eskirgan CDN token o'rniga yangi video ssilkasini oladi.
    """
    toza_id = tg_post_id.replace("tg:", "", 1)
    try:
        r = requests.get(f"https://t.me/{toza_id}?embed=1&mode=tme", headers=HEADERS, timeout=20)
        vm = re.search(r'<video[^>]+src="([^"]+)"', r.text)
        if vm:
            return vm.group(1)
    except Exception:
        pass
    return None


# ==================== 2) SAYTLARDAN (ZIRA.UZ) VIDEORETSEPTLAR OLISH ====================
def zira_uz_videolar_oqi():
    if yt_dlp is None:
        return []
    natija = []
    try:
        r = requests.get(ZIRA_URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
        linklar = sorted(set(re.findall(r'href="(https://zira\.uz/uz/recipe/videoretsept-[^"#]+)', r.text)))
        for link in linklar[:8]:
            try:
                pr = requests.get(link, headers=HEADERS, timeout=20)
                ym = re.search(r'youtube\.com/embed/([A-Za-z0-9_\-]{11})', pr.text)
                if not ym:
                    continue
                yt_id = ym.group(1)
                tm = re.search(r'<meta property="og:title" content="([^"]+)"', pr.text)
                dm = re.search(r'<meta property="og:description" content="([^"]+)"', pr.text)
                title = html.unescape(tm.group(1)).strip() if tm else ""
                desc = html.unescape(dm.group(1)).strip() if dm else ""
                title = re.sub(r"(?i)^videoretsept:\s*", "", title).strip()
                if not title:
                    continue
                matn = f"{title} 😋\n\n{desc}" if desc else title
                natija.append({
                    "id": f"zira:{yt_id}",
                    "manba": "zira.uz",
                    "manba_turi": "sayt",
                    "matn": matn,
                    "video": f"https://www.youtube.com/watch?v={yt_id}",
                    "views": 8000,
                })
            except Exception:
                continue
    except Exception as e:
        log(f"⚠️ Zira.uz o'qishda xato: {e}")
    return natija


# ==================== 3) YOUTUBE DAN PAZANDA VA LAYFXAK VIDEOLARINI OLISH ====================
def youtube_videolar_oqi():
    if yt_dlp is None:
        return []
    natija = []
    sorov = random.choice(YT_QIDIRUVLAR)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch6:{sorov}", download=False)
            for e in info.get("entries", []) or []:
                vid_id = e.get("id")
                title = (e.get("title") or "").strip()
                dur = e.get("duration") or 0
                # 15 soniyadan 6 daqiqagacha bo'lgan qisqa va oson ko'riladigan videolar
                if not vid_id or not title or dur > 380 or (dur and dur < 10):
                    continue
                title_clean = re.sub(r"#\S+", "", title).strip()
                if len(title_clean) < 15:
                    continue
                matn = (
                    f"{title_clean}\n\n"
                    f"Pazanda bekajonlarimiz uchun uyda oson va tez tayyorlanadigan ajoyib videoretsept. "
                    f"Oila a'zolaringiz uchun albatta tayyorlab ko'ring!"
                )
                natija.append({
                    "id": f"yt:{vid_id}",
                    "manba": "youtube",
                    "manba_turi": "youtube",
                    "matn": matn,
                    "video": f"https://www.youtube.com/watch?v={vid_id}",
                    "views": int(e.get("view_count") or 6000),
                })
    except Exception as e:
        log(f"⚠️ YouTube qidiruvda xato: {e}")
    return natija


# ==================== VIDEO YUKLAB OLISH (TELEGRAM MP4 + YOUTUBE/INSTAGRAM/SAYT) ====================
def video_yuklab_ol(url, max_mb=45):
    if not url:
        return None

    # 1) Agar YouTube / Instagram / tashqi platforma ssilkasi bo'lsa -> yt-dlp orqali MP4 yuklaymiz
    if any(x in url for x in ("youtube.com/", "youtu.be/", "instagram.com/")):
        if yt_dlp is None:
            return None
        tmp_path = os.path.join(
            tempfile.gettempdir(),
            f"pazanda_vid_{int(time.time())}_{random.randint(1000, 9999)}.mp4"
        )
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": f"best[ext=mp4][filesize<{max_mb}M]/18/best[ext=mp4]/best",
            "outtmpl": tmp_path,
            "noplaylist": True,
        }
        if os.path.exists(NODE_EXE):
            ydl_opts["js_runtimes"] = {"node": {"path": NODE_EXE}}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            if os.path.exists(tmp_path) and 10_000 < os.path.getsize(tmp_path) <= max_mb * 1024 * 1024:
                with open(tmp_path, "rb") as f:
                    buf = io.BytesIO(f.read())
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
                buf.seek(0)
                return buf
        except Exception as e:
            log(f"⚠️ yt-dlp video yuklashda xato ({url}): {e}")
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
        return None

    # 2) Bevosita MP4 video URL (Telegram CDN va h.k.)
    try:
        r = requests.get(url, headers=HEADERS, timeout=50, stream=True)
        r.raise_for_status()
        buf = io.BytesIO()
        hajm = 0
        for chunk in r.iter_content(65536):
            hajm += len(chunk)
            if hajm > max_mb * 1024 * 1024:
                return None
            buf.write(chunk)
        if hajm < 10_000:
            return None
        buf.seek(0)
        return buf
    except Exception:
        return None


def ijobiy_reaksiya_qoy(chat_id, message_id):
    """Faqat ijobiy emoji reaksiya qo'yadi."""
    for ro_yxat in (IJOBIY_EMOJILAR, ZAXIRA_EMOJILAR):
        tanlov = random.choice(ro_yxat)
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/setMessageReaction",
                data={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "reaction": json.dumps([{"type": "emoji", "emoji": tanlov}]),
                },
                timeout=10,
            ).json()
            if resp.get("ok"):
                return
        except Exception:
            pass


def pazanda_ikki_ijobiy_izoh(teg="#taom"):
    """Ayollar auditoriyasi uchun 2 ta samimiy, 100% ijobiy o'zbekcha munosabat qaytaradi."""
    if teg in ("#shirinlik", "#pishiriq"):
        birinchi = [
            "Вой қандай ажойиб ширинлик экан, кўринишидан оғизда эрийдиган бўлибди 😍🍰",
            "Қўлингиз дард кўрмасин, жуда чиройли ва иштаҳа очар пишириқ чиқибди ❤️👏",
            "Болажонлар ва оила аъзолари учун чой устига энг зўр ширинлик экан 😋🔥",
            "Масаллиқлари ҳам оддий ва ҳамёнбоп экан, албатта пишириб кўраман 🥰👍",
        ]
        ikkinchi = [
            "Қизларжон, сизлар ҳам шу усулда тайёрлаб кўрганмисиз? Изоҳда ёзинг 👇😊",
            "Сақлаб олдим, бугун албатта оилам учун тайёрлаб кўраман! Сизга ҳам ёқдими? ❤️",
            "Дастурхонингизга доим файз ва барака кирсин, бекажонлар! 🥰🌸",
            "Яна қандай ширинлик ретсептларини кутяпсизлар, пазандалар? 👇🍰",
        ]
    elif teg == "#layfxak":
        birinchi = [
            "Жуда фойдали лайфхак экан, ҳар бир уй бекасига асқотади 😍👍",
            "Ошхонада ва рўзғорда ишни анча енгиллаштирадиган зўр усул экан, раҳмат! 🔥👏",
            "Шунча вақт билмай юрган эканман, жуда ақлли ва осон ечим бўлибди 💯🥰",
            "Пазанда ва саришта бекажонлар учун энг керакли маслаҳат экан 🌸❤️",
        ]
        ikkinchi = [
            "Қизларжон, сизлар ҳам рўзғорда шу усулдан фойдаланасизми? 👇😊",
            "Дугоналарга ҳам юбориб қўямиз, уларга ҳам фойдаси тегсин 🥰🤝",
            "Сизда ҳам шундай ошхона сирлари бўлса, изоҳларда бўлишинг бекажонлар! 👇🌸",
            "Ишингизни унумли ва осон қиладиган ажойиб тавсия, сақлаб қўйинг 📌❤️",
        ]
    else:
        birinchi = [
            "Жуда мазали ва тўйимли таом бўлибди, иштаҳани очиб юборди 😋🔥",
            "Қўлингиз гул экан, жуда чиройли ва осон тушунтирилибди ❤️👍",
            "Бугун нима овқат қилсам экан деб ўйлаб тургандим, айни муддао бўлди 😍🍽",
            "Оила даврасида маза қилиб ейдиган ажойиб ретсепт экан 💯🥰",
        ]
        ikkinchi = [
            "Бекажонлар, бугун сизлар нима таом тайёрлаяпсиз? Фикр алмашамиз 👇😊",
            "Мен ҳам шу ретсепт бўйича қилиб кўраман, жуда ёқди! Қўлингиз дард кўрмасин 🌸🤝",
            "Ҳар бир хонадонда қозон доим қайнаб турсин, дастурхонингиз тўкин бўлсин 🤲❤️",
            "Пазанда қизлар, сиз бу таомга яна нималар қўшасиз? Изоҳда ўртоқлашинг 👇🥰",
        ]
    return random.choice(birinchi), random.choice(ikkinchi)


def bot_lokal_ishlayaptimi():
    """Kompyuterda bot.py (47892-port) ishlayotganini tekshiradi."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", 47892)) == 0
    except Exception:
        return False
    finally:
        s.close()


def cloud_muhokama_izoh_yoz(bitta_teg="#taom"):
    """
    Agar kompyuter o'chiq bo'lsa (GitHub Actions --once rejimida),
    kanaldan muhokama guruhiga tushgan xabarni topib 2 ta ijobiy izoh va reaksiya yozadi.
    """
    if bot_lokal_ishlayaptimi():
        return
    time.sleep(4)
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params={"timeout": 2, "allowed_updates": json.dumps(["message"])},
            timeout=10,
        ).json()
        for upd in reversed(r.get("result") or []):
            msg = upd.get("message") or {}
            chat = msg.get("chat") or {}
            sender_chat = msg.get("sender_chat") or {}
            if chat.get("id") == MUHOKAMA_ID and (
                msg.get("is_automatic_forward") or sender_chat.get("id") == KANAL_ID
            ):
                mid = msg.get("message_id")
                ijobiy_reaksiya_qoy(MUHOKAMA_ID, mid)
                iz1, iz2 = pazanda_ikki_ijobiy_izoh(bitta_teg)
                m1 = bot.send_message(MUHOKAMA_ID, iz1, reply_to_message_id=mid, disable_notification=True)
                ijobiy_reaksiya_qoy(MUHOKAMA_ID, m1.message_id)
                time.sleep(1.5)
                m2 = bot.send_message(MUHOKAMA_ID, iz2, reply_to_message_id=mid, disable_notification=True)
                ijobiy_reaksiya_qoy(MUHOKAMA_ID, m2.message_id)
                log(f"💬 Cloud muhokama ({mid}) ga 2 ta ijobiy munosabat yozildi.")
                break
    except Exception as e:
        log(f"⚠️ Cloud muhokama izohda xato: {e}")


def kanalga_video_yubor(post):
    """
    FAQAT VIDEO shaklida va xuddi @Toshkent_2200 dizaynida @pazanda_maxorati ga yuboradi.
    """
    video_url = post.get("video")
    if not video_url:
        return False

    raw_matn = post.get("matn") or ""
    toza_matn = matnni_tozala(raw_matn)
    if len(toza_matn) < 12:
        return False

    bitta_teg = bitta_hashtag_tanla(raw_matn, post.get("manba", ""))
    sarlavha, izoh = sarlavha_va_izohga_ajrat(toza_matn, bitta_teg)
    if not sarlavha:
        return False

    caption = (
        f"<b>{html.escape(bitta_teg)}</b>\n\n"
        f"<b>{html.escape(sarlavha)}</b>\n\n"
        f"<i>{html.escape(izoh)}</i>\n\n"
        f"👉 @pazanda_maxorati"
    )

    vbuf = video_yuklab_ol(video_url, max_mb=45)
    if not vbuf and str(post.get("id", "")).startswith("tg:"):
        yangi_url = tg_yangi_video_ssilka_ol(post["id"])
        if yangi_url:
            vbuf = video_yuklab_ol(yangi_url, max_mb=45)
    if not vbuf:
        return False

    vbuf.name = "pazanda_video.mp4"
    try:
        sent = bot.send_video(
            KANAL,
            vbuf,
            caption=caption,
            supports_streaming=True,
            timeout=120,
            disable_notification=not NOTIFIKATSIYA,
        )
        if sent:
            ijobiy_reaksiya_qoy(KANAL, sent.message_id)
            if "--once" in sys.argv:
                cloud_muhokama_izoh_yoz(bitta_teg)
            return True
    except Exception as e:
        log(f"⚠️ Video yuborishda xato: {e}")

    return False


def ustuvorlik_bali(post):
    matn = (post.get("matn") or "").lower()
    ball = 50
    if any(s in matn for s in ["masalliq", "масаллиқ", "масаллик", "retsept", "ретсепт", "tayyorlash", "тайёрлаш", "layfxak", "лайфхак"]):
        ball += 35
    if post.get("manba_turi") in ("sayt", "youtube"):
        ball += 20
    ball += min(30, int(post.get("views", 0) / 1000))
    return ball


def yangi_videolarni_yig(seen, matn_baza):
    nomzodlar = []

    # 1) Telegram kanallaridan
    kanallar = list(TG_MANBALAR)
    random.shuffle(kanallar)
    for kanal in kanallar:
        try:
            postlar = tg_kanal_oqi(kanal, seen=seen)
        except Exception as e:
            log(f"⚠️ TG ({kanal}) xato: {e}")
            continue

        for p in postlar:
            if p["id"] in seen:
                continue
            matn = p.get("matn") or ""
            if not matn or reklama_mi(matn) or not ozbekchami(matn):
                seen.add(p["id"])
                continue
            if not mavzuga_mosmi(matn, kanal):
                seen.add(p["id"])
                continue
            toza = matnni_tozala(matn)
            if len(toza) < 15 or takroriymi(toza, matn_baza):
                seen.add(p["id"])
                continue
            p["ball"] = ustuvorlik_bali(p)
            nomzodlar.append(p)

    # 2) Zira.uz saytidan videoretseptlar
    try:
        for p in zira_uz_videolar_oqi():
            if p["id"] in seen:
                continue
            matn = p.get("matn") or ""
            if not matn or reklama_mi(matn) or not ozbekchami(matn):
                seen.add(p["id"])
                continue
            toza = matnni_tozala(matn)
            if len(toza) < 15 or takroriymi(toza, matn_baza):
                seen.add(p["id"])
                continue
            p["ball"] = ustuvorlik_bali(p)
            nomzodlar.append(p)
    except Exception as e:
        log(f"⚠️ Sayt manba xato: {e}")

    # 3) YouTube qidiruvdan o'zbekcha pazanda/layfxak videolari
    try:
        for p in youtube_videolar_oqi():
            if p["id"] in seen:
                continue
            matn = p.get("matn") or ""
            if not matn or reklama_mi(matn) or not ozbekchami(matn):
                seen.add(p["id"])
                continue
            if not mavzuga_mosmi(matn, "youtube"):
                seen.add(p["id"])
                continue
            toza = matnni_tozala(matn)
            if len(toza) < 15 or takroriymi(toza, matn_baza):
                seen.add(p["id"])
                continue
            p["ball"] = ustuvorlik_bali(p)
            nomzodlar.append(p)
    except Exception as e:
        log(f"⚠️ YouTube manba xato: {e}")

    # Har xil manba va mavzular (ovqat, shirinlik, salat, layfxak, sayt, youtube) ketma-ket
    # almashib chiqishi uchun manbalar bo'yicha aralashtirib saralaymiz
    manba_guruhlari = {}
    for p in sorted(nomzodlar, key=lambda x: x.get("ball", 0), reverse=True):
        m = p.get("manba", "boshqa")
        manba_guruhlari.setdefault(m, []).append(p)

    aralash = []
    while any(manba_guruhlari.values()):
        for m in list(manba_guruhlari.keys()):
            if manba_guruhlari[m]:
                aralash.append(manba_guruhlari[m].pop(0))
            else:
                del manba_guruhlari[m]
    return aralash


def kanal_oxirgi_holatini_tekshir(matn_baza):
    """
    @pazanda_maxorati kanalining jonli holatini tekshiradi:
      1) Kanaldagi mavjud postlarni matn_baza ga qo'shadi (kompyuter va bulut bir xil post chiqarmasligi uchun).
      2) Agar oxirgi post 4 daqiqadan kam vaqt oldin chiqqan bo'lsa, False qaytaradi.
    """
    from datetime import datetime, timezone
    try:
        r = requests.get("https://t.me/s/pazanda_maxorati", headers=HEADERS, timeout=20)
        qismlar = re.split(r'(?=<div class="tgme_widget_message\b)', r.text)
        oxirgi_vaqt = None
        for p in qismlar:
            tm = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', p, re.S)
            if tm:
                m_txt = html.unescape(re.sub(r"<[^>]+>", " ", tm.group(1))).strip()
                toza = matnni_tozala(m_txt)
                if len(toza) >= 15 and not takroriymi(toza, matn_baza):
                    matn_baza.append(matn_imzosi(toza))
            dt_m = re.search(r'<time[^>]+datetime="([^"]+)"', p)
            if dt_m:
                try:
                    oxirgi_vaqt = datetime.fromisoformat(dt_m.group(1))
                except Exception:
                    pass
        if oxirgi_vaqt is not None:
            farq = (datetime.now(timezone.utc) - oxirgi_vaqt).total_seconds()
            if 0 <= farq < 240:
                log(f"⏳ Kanalda {int(farq)} soniya oldin video chiqqan — navbatdagi siklni kutamiz.")
                return False
    except Exception:
        pass
    return True


def bitta_navbatdagi_videoni_chiqar(seen, matn_baza):
    """
    Navbatdan yoki yangi manbalardan FAQAT 1 TA eng sifatli videoni kanalga chiqaradi.
    Har 5-10 daqiqada 1 tadan video chiqishi uchun xizmat qiladi.
    """
    if not kanal_oxirgi_holatini_tekshir(matn_baza):
        return False

    navbat = navbatni_yukla()
    navbat = [p for p in navbat if p.get("id") not in seen]

    if len(navbat) < 5:
        yangilar = yangi_videolarni_yig(seen, matn_baza)
        mavjud_idlar = {x["id"] for x in navbat}
        for y in yangilar:
            if y["id"] not in mavjud_idlar:
                navbat.append(y)
                mavjud_idlar.add(y["id"])

    urinish = 0
    while navbat and urinish < 4:
        p = navbat.pop(0)
        pid = p["id"]
        toza = matnni_tozala(p.get("matn") or "")
        if len(toza) < 15 or takroriymi(toza, matn_baza):
            seen.add(pid)
            continue

        urinish += 1
        if kanalga_video_yubor(p):
            seen.add(pid)
            matn_baza.append(matn_imzosi(toza))
            matn_bazani_saqlash(matn_baza)
            korilganlarni_saqlash(seen)
            navbatni_saqlash(navbat)
            qisqa = toza.replace("\n", " ")[:65]
            log(f"✅ 🎬 VIDEO [{p.get('manba')}] {qisqa}")
            return True
        else:
            seen.add(pid)

    korilganlarni_saqlash(seen)
    navbatni_saqlash(navbat)
    log("… hozircha yangi mos video topilmadi.")
    return False


def asosiy():
    seen = korilganlarni_yukla()
    matn_baza = matn_bazani_yukla()
    log(f"▶️ Pazanda maxorati video-agregatori ishga tushdi. Kanal: {KANAL} (baza={len(seen)})")

    while True:
        try:
            bitta_navbatdagi_videoni_chiqar(seen, matn_baza)
        except Exception as e:
            log(f"❌ Siklda xato: {e}")

        if "--once" in sys.argv:
            break

        kutish = random.randint(MIN_ORALIQ_SONIYA, MAX_ORALIQ_SONIYA)
        log(f"⏳ Keyingi video {kutish // 60} daqiqa {kutish % 60} soniyadan so'ng yuboriladi...")
        time.sleep(kutish)


if __name__ == "__main__":
    asosiy()

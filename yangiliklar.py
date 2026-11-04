# -*- coding: utf-8 -*-
"""
@Toshknet_bot — @Toshkent_2200 kanali uchun AVTOMATIK AGREGATOR va FILTR.

Qoidalar:
  1) Har bir xabarda FAQAT 1 DONA #hashtag bo'ladi (boshida).
  2) Xabar sarlavhasi QALIN (<b>...</b>), tagidagi izoh esa INGICHKA QIYA (<i>...</i>) shriftda.
  3) Avtomatik xabarlarda REKLAMA va TASHQI SSILKA umuman bo'lmaydi (faqat bot orqali
     admin qo'lda kiritganda ruxsat).
  4) Faqat O'ZBEKCHA xabarlar o'tadi (ruscha/xorijiy xabarlar filtrlanadi).
  5) Takroriy xabarlar chiqmaydi (ham ID, ham matn o'xshashligi bo'yicha filtr).
  6) Qiziqarli, ko'p ko'riladigan VIDEOLAR va TOSHKENT ichidagi dolzarb xabarlar ustuvor.
  7) Har bir xabarga reaksiya va muhokama guruhiga kamida 2 ta munosabat yoziladi.
"""

import html
import io
import json
import os
import random
import re
import socket
import sys
import time
import xml.etree.ElementTree as ET

import requests
import telebot

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Bir vaqtda faqat 1 ta nusxa ishlashi uchun port-qulf
if "--once" not in sys.argv:
    _LOCK_SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _LOCK_SOCK.bind(("127.0.0.1", 47891))
    except OSError:
        sys.exit(0)

PAPKA = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(PAPKA, "@Toshknet_bot.txt")
SEEN_FILE = os.path.join(PAPKA, "korilganlar.json")
TEXT_SEEN_FILE = os.path.join(PAPKA, "korilgan_matnlar.json")
LOG_FILE = os.path.join(PAPKA, "yangiliklar_log.txt")

KANAL = "@Toshkent_2200"
KANAL_ID = -1004365200283
MUHOKAMA_ID = -1004389687204
REJAL_SONIYA = 60
NOTIFIKATSIYA = False

# Video va Toshkent xabarlariga boy manba kanallar
TG_MANBALAR = [
    "toshkentliklar",
    "Poytaxt_uz",
    "TezkorxabarUz_official",
    "qoraxabar",
    "MILITSIYA_UZB",
    "TYUZBEK",
    "yhxx_uz",
    "effectuz",
    "darakchi",
    "kunuzofficial",
    "xabaruzofficial",
]

RSS_URL = "https://kun.uz/news/rss?lang=uz"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    )
}

# Toshkent tumanlari va hududlari (1 dona #hashtag tanlashda 1-ustuvorlik)
TUMANLAR = [
    ("#Sergeli", ["sergeli", "сергели"]),
    ("#Yunusobod", ["yunusobod", "yunusobot", "юнусобод", "yunusabad"]),
    ("#Bektemir", ["bektemir", "бектемир"]),
    ("#Mirobod", ["mirobod", "миробод"]),
    ("#Mirzo-Ulug'bek", [
        "mirzo ulug'bek", "mirzo-ulug'bek", "mirzo ulugbek",
        "мирзо улуғбек", "мирзо-улуғбек", "мирзо улугбек", "qorasuv", "қорасув", "ttz", "ттз"
    ]),
    ("#Olmazor", ["olmazor", "олмазор", "qoraqamish", "қорақамиш"]),
    ("#Uchtepa", ["uchtepa", "учтепа", "farhod бозор", "фарҳод"]),
    ("#Chilonzor", ["chilonzor", "чилонзор", "chilanzar", "algoritm", "алгоритм", "qatortol", "қатортол"]),
    ("#Shayxontohur", ["shayxontohur", "шайхонтоҳур", "шайхантахур", "tashkent city", "beruniy", "беруний"]),
    ("#Yakkasaroy", ["yakkasaroy", "яккасарой", "qushbegi", "қушбеги"]),
    ("#Yangihayot", ["yangihayot", "янгиҳаёт", "yangi hayot"]),
    ("#sebzor", ["sebzor", "себзор"]),
    ("#qo'yliq", ["qo'yliq", "qoyliq", "қўйлиқ", "kuylyuk", "койлик", "food city"]),
    ("#ganga", ["ganga", "ганга", "chorsu", "чорсу", "xadra", "хадра"]),
]

TOSHKENT_SOZLAR = [
    "toshkent", "тошкент", "poytaxt", "пойтахт", "tashkent",
    "chirchiq", "чирчиқ", "olmaliq", "олмалиқ", "angren", "ангрен",
    "bekobod", "бекобод", "yangiyo'l", "янгийўл", "qibray", "қибрай",
    "zangiota", "зангиота", "parkent", "паркент", "bo'stonliq", "бўстонлиқ",
    "g'azalkent", "ғазалкент", "ohangaron", "оҳангарон", "chinoz", "чиноз",
    "piskent", "пискент", "chorvoq", "чорвоқ", "chimyon", "чимён",
    "nurafshon", "нурафшон", "to'ytepa", "тўйтепа", "keles", "келес",
    "nazarbek", "назарбек", "eshonguzar", "эшонгузар", "minor", "минор",
    "amir temur", "амир темур", "mustaqillik", "мустақиллик", "bunyodkor", "бунёдкор",
]

BOSHQA_VILOYATLAR = [
    "samarqand", "самарқанд", "buxoro", "бухоро", "andijon", "андижон",
    "farg'ona", "фарғона", "namangan", "наманган", "qashqadaryo", "қашқадарё",
    "qarshi", "қарши", "surxondaryo", "сурхондарё", "termiz", "термиз",
    "xorazm", "хоразм", "urganch", "урганч", "navoiy", "навоий",
    "jizzax", "жиззах", "sirdaryo", "сирдарё", "guliston", "гулистон",
    "qoraqalpog'iston", "қорақалпоғистон", "nukus", "нукус",
]

MAVZULAR = [
    ("#Ана_бўлмаса", [
        "ана бўлмаса", "ana bo'lmasa", "ana bolmasa", "ана булмаса",
        "g'aroyib", "ғаройиб", "antiqa", "антиқа", "sharmanda", "шарманда",
        "hayrat", "ҳайрат", "kutilmagan", "кутилмаган"
    ]),
    ("#daxshat", [
        "daxshat", "dahshat", "даҳшат", "дахшат", "fojia", "фожиа",
        "qotil", "қотил", "jasad", "жасад", "halok", "ҳалок", "portlash", "портлаш",
        "yong'in", "ёнғин", "pichoq", "пичоқ", "vafot", "вафот", "o'lim", "ўлим",
        "jinoyat", "жиноят", "ushlandi", "ушланди", "qamoq", "қамоқ", "yondi", "ёнди"
    ]),
    ("#avto", [
        "avto", "авто", "yth", "йтҳ", "avtohalokat", "автоҳалокат",
        "avariya", "авария", "mashina", "машина", "haydovchi", "ҳайдовчи",
        "radar", "радар", "jarima", "жарима", "svetofor", "светофор",
        "tirbandlik", "тирбандлик", "probka", "пробка", "metan", "метан",
        "zapravka", "заправка", "benzin", "бензин", "avtobus", "автобус",
        "metro", "метро", "taksi", "такси", "cobalt", "gentra", "malibu",
        "tracker", "onix", "damas", "matiz", "nexia", "spark", "byd", "yhxx", "йҳхх", "yama", "яма"
    ]),
    ("#Foydali", [
        "foydali", "фойдали", "maslahat", "маслаҳат", "eslatma", "эслатма",
        "diqqat", "диққат", "ogoh", "огоҳ", "ob-havo", "об-ҳаво", "kurs", "курс",
        "dollar", "доллар", "imtiyoz", "имтиёз", "qonun", "қонун", "qaror", "қарор",
        "dam olish", "дам олиш", "ta'til", "таътил"
    ]),
    ("#kayfiyat", [
        "kayfiyat", "кайфият", "kulgu", "кулгу", "hazil", "ҳазил",
        "tabassum", "табассум", "konsert", "концерт", "bayram", "байрам",
        "yulduz", "юлдуз", "qo'shiq", "қўшиқ", "to'y", "тўй", "raqs", "рақс",
        "xushxabar", "хушхабар", "tabrik", "табрик"
    ]),
    ("#Tarqating", [
        "tarqating", "тарқатинг", "ogohlantiring", "огоҳлантиринг",
        "yaqinlarga", "яқинларга", "barchaga yetkazing", "барчага етказинг",
        "qidirilmoqda", "қидирилмоқда", "yo'qoldi", "йўқолди"
    ]),
    ("#Tezkor", [
        "tezkor", "тезкор", "shoshilinch", "шошилинч", "hozirgina", "ҳозиргина",
        "ayni damda", "айни дамда", "rasmiy", "расмий", "tezkor xabar", "тезкор хабар"
    ]),
    ("#jahon", [
        "tramp", "трамп", "putin", "путин", "rossiya", "россия",
        "ukraina", "украина", "aqsh", "ақш", "xitoy", "хитой",
        "isroil", "исроил", "g'azo", "ғазо", "eron", "эрон",
        "turkiya", "туркия", "yevropa", "европа", "zelenskiy", "зеленский",
        "bmt", "бмт", "nato", "нато", "qozog'iston", "қозоғистон", "germaniya", "германия"
    ]),
]

# Kuchaytirilgan reklama va tijoriy e'lonlar filtri
REKLAMA_SOZLAR = [
    "#reklama", "#реклама", "reklama huquqi", "реклама ҳуқуқи",
    "reklama bo'yicha", "реклама бўйича", "stavka", "ставка", "bukmeker",
    "1xbet", "mostbet", "melbet", "linebet", "kazino", "казино",
    "kanalga obuna", "каналга обуна", "kanalimizga qo'shiling",
    "aksiya", "акция", "chegirma", "чегирма", "buyurtma", "буюртма",
    "yetkazib berish", "етказиб бериш", "dostavka", "доставка",
    "narxi", "нархи", "sotiladi", "сотилади", "ijaraga", "ижарага",
    "muddatli to'lov", "муддатли тўлов", "bo'lib to'lash", "бўлиб тўлаш",
    "ro'yxatdan o'ting", "рўйхатдан ўтинг", "joylar soni cheklangan",
    "жойлар сони чекланган", "murojaat uchun", "мурожаат учун",
    "batafsil ma'lumot uchun", "батафсил маълумот учун", "shoshiling", "шошилинг",
    "behad xursand", "konsultatsiya bepul", "консультация бепул",
    "kredit", "кредит", "avtokredit", "автокредит", "lombard", "ломбард",
    "xizmatlar litsenziyalangan", "хизматлар лицензияланган",
]

# Rus tilidagi xabarlarni aniqlab filtrlaydigan so'zlar
RUSCHA_SOZLAR = [
    " что ", " это ", " как ", " для ", " при ", " его ", " года ", " будет ",
    " также ", " после ", " котор", " из-за ", " только ", " сейчас ",
    " человек", " подробн", " сегодня ", " вчера ", " может ", " было ",
    " были ", " этом ", " этого ", " очень ", " более ", " через ",
    " между ", " около ", " против ", " однако ", " поэтому ", " когда ",
    " если ", " чтобы ", " ташкент", " узбекистан", " росси", " сооbщ", " сообщ",
    " по данным ", " в результате ", " в ташкенте ", " в узбекистане ",
    " напомним", " ранее ", " стало известно", " прокомментир",
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
            json.dump(sorted(seen)[-2500:], f, ensure_ascii=False, indent=1)
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
            json.dump(matnlar[-500:], f, ensure_ascii=False, indent=1)
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
    """Takroriy xabarlarni tutish uchun matnning asosiy so'zlari to'plami."""
    k = matnni_imzo_uchun_standartlash(matn)
    harflar = re.sub(r"[^a-z0-9\s]", " ", k)
    sozlar = [s for s in harflar.split() if len(s) >= 4]
    prefiks = "".join(sozlar[:8])
    return {"prefiks": prefiks, "sozlar": sorted(set(sozlar[:35]))}


def takroriymi(matn, matn_baza):
    """Matn avvalgi xabarlarga o'xshash (dublikat) ekanini текширади."""
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
                if nisbat >= 0.55 and umumiy >= 4:
                    return True
    return False


def ozbekchami(matn):
    """Matn faqat o'zbek tilida (lotin yoki kirill) ekanligini tekshiradi."""
    if not matn or len(matn.strip()) < 25:
        return False
    k = " " + matn.lower() + " "

    # 1) Ruscha so'zlar qatnashsa -> darhol rad etamiz
    if any(r in k for r in RUSCHA_SOZLAR):
        return False

    # 2) Agar kirill harflari ko'p bo'lsa, o'zbek kirill belgisi yoki so'zi bo'lishi shart
    kirill_soni = len(re.findall(r"[а-яёўқғҳ]", k))
    lotin_soni = len(re.findall(r"[a-z]", k))

    if kirill_soni > lotin_soni:
        # Ruscha 'ы' yoki 'щ' ko'p bo'lib, o'zbekcha 'ў/қ/ғ/ҳ' bo'lmasa -> ruscha
        uz_kirill = len(re.findall(r"[ўқғҳ]", k))
        rus_harf = len(re.findall(r"[ыщ]", k))
        if rus_harf >= 2 and uz_kirill == 0:
            return False
        uz_sozlar = [" ва ", " билан ", " учун ", " бўйича ", " туман", " шаҳар", " хабар", " тошкент", " сўм", " йил", " кун", " ҳам ", " деб ", " экан"]
        if uz_kirill == 0 and not any(w in k for w in uz_sozlar):
            return False
    else:
        # Lotin alifbosida o'zbekcha so'zlar bo'lishi shart
        uz_lotin = [
            " va ", " bilan ", " uchun ", " bo'yicha ", " böyiça ", " toshkent", " toşkent",
            " shahar", " şahar", " tuman", " xabar", " so'm", " söm", " yil", " kun",
            " ham ", " deb ", " ekan", " bo'lib", " bölib", " qilindi", " bo'ldi", " böldi",
            " o'zbek", " özbek", " ma'lum", " ning ", " dagi "
        ]
        if not any(w in k for w in uz_lotin):
            return False

    return True


def reklama_mi(matn):
    k = matn.lower()
    if any(s in k for s in REKLAMA_SOZLAR):
        return True
    # Telefon raqamlar (+998, 90 123 45 67, (71) 200-00-00) bo'lsa -> reklama/e'lon
    if re.search(r"(\+?998[\s\-]?\d{2}|\(\d{2}\)\s*\d{3}|\b(90|91|93|94|95|97|98|99|88|33|71|78)[\s\-]\d{3}[\s\-]\d{2}[\s\-]\d{2})", matn):
        return True
    return False


def toshkent_ustuvorlik_bali(matn, manba, video_bormi, korishlar):
    """
    Qiziqarli videolar va Toshkent ichidagi dolzarb xabarlarga yuqori ball beradi.
    """
    k = matn.lower()
    ball = 0
    if video_bormi:
        ball += 50
    if any(s in k for s in TOSHKENT_SOZLAR):
        ball += 40
    for _, kalitlar in TUMANLAR:
        if any(s in k for s in kalitlar):
            ball += 45
            break
    if manba in ("toshkentliklar", "Poytaxt_uz", "yhxx_uz"):
        ball += 25
    ball += min(30, int(korishlar / 1000))
    return ball


def toshkentga_aloqadormi(matn, manba):
    if manba in ("toshkentliklar", "Poytaxt_uz"):
        return True
    k = matn.lower()
    if any(s in k for s in TOSHKENT_SOZLAR):
        return True
    for _, kalitlar in TUMANLAR:
        if any(s in k for s in kalitlar):
            return True
    # Agar faqat boshqa viloyat nomi bo'lsa -> o'tkazib yuboramiz
    if any(v in k for v in BOSHQA_VILOYATLAR):
        return False
    return True


def matnni_tozala(matn):
    """
    Barcha tashqi ssilkalar, @username, #hashtag va kanal imzolarini 100% tozalaydi.
    """
    # URL va ssilkalarni olib tashlaymiz
    matn = re.sub(r"https?://\S+", "", matn)
    matn = re.sub(r"t\.me/\S+", "", matn)
    matn = re.sub(r"(?<!\w)@[A-Za-z0-9_]{3,}", "", matn)
    # Matn ichidagi barcha #hashtag larni olib tashlaymiz (faqat 1 dona o'zimiz boshiga qo'yamiz)
    matn = re.sub(r"#[\w'ʼʻ`\-]+", "", matn)

    qatorlar = [q.strip() for q in matn.splitlines()]

    imzo_sozlar = (
        "obuna bo'ling", "обуна бўлинг", "kanalga", "каналга", "ulanish", "уланиш",
        "batafsil", "батафсил", "manba:", "манба:", "rasmiy kanal", "расмий канал",
        "bizни кузатинг", "bizni kuzating", "telegram", "телеграм",
        "👉", "👇", "⤵", "📲", "🌐", "🔗", "📢", "📡"
    )
    while qatorlar:
        oxirgi = qatorlar[-1].lower()
        if not oxirgi:
            qatorlar.pop()
            continue
        if len(oxirgi) < 100 and any(b in oxirgi for b in imzo_sozlar):
            qatorlar.pop()
            continue
        break

    while qatorlar and not qatorlar[0]:
        qatorlar.pop(0)

    toza = "\n".join(qatorlar).strip()
    toza = re.sub(r"\n{3,}", "\n\n", toza).strip()
    return toza


def bitta_hashtag_tanla(matn, manba):
    """
    Xabar uchun FAQAT 1 DONA #hashtag, FAQAT ruxsat etilgan ro'yxatdan:
    #Tezkor, #Jahon, #Ана_бўлмаса, #Salomatlik, #Foydali
    """
    def t(s):
        # Matn va kalit so'zlar bir xil tarzda transibiratsiya qilib, apostroflarni olib tashlaymiz
        return matnni_imzo_uchun_standartlash(s).replace("'", "").replace("ʻ", "").replace("`", "")

    k = t(matn)

    SALOMATLIK_KALITLAR = [
        "sog", "sogolm", "sogliq", "саломатлик", "salomatlik",
        "shifokor", "шифокор", "dori", "дори", "vitamin", "витамин",
        "doktor", "доктор", "kasallik", "касаллик",
        "qandli", "қандли", "diabet", "диабет", "yurak", "юрак",
        "xolesterol", "холестерин", "infeks", "инфекс", "иммунитет",
        "fitnes", "фитнес", "parhez", "пархез", "vazn", "вазн",
        "tibbiyot", "тиббиёт", "davolash", "даволаш", "ogriq", "оғриқ",
        "revmatolog", "ревматолог", "davolan", "даволан"
    ]
    FOYDALI_KALITLAR = [
        "foydali", "фойдали", "maslahat", "маслаҳат", "eslatma", "эслатма",
        "diqqat", "диққат", "ogoh", "огоҳ", "ob-havo", "об-ҳаво", "kurs", "курс",
        "dollar", "доллар", "imtiyoz", "имтиёз", "qonun", "қонун", "qaror", "қарор",
        "dam olish", "дам олиш", "tatil", "таътил"
    ]
    JAHON_KALITLAR = [
        "tramp", "трамп", "putin", "путин", "rossiya", "россия",
        "ukraina", "украина", "aqsh", "ақш", "xitoy", "хитой",
        "isroil", "исроил", "gazo", "ғазо", "eron", "эрон",
        "turkiya", "туркия", "yevropa", "европа", "zelenskiy", "зеленский",
        "bmt", "бмт", "nato", "нато", "qozogiston", "қозоғистон", "germaniya", "германия"
    ]
    ANA_BOLMASA_KALITLAR = [
        "ана бўлмаса", "ana bolmasa", "ана булмаса",
        "garoyib", "ғаройиб", "antiqa", "антиқа", "sharmanda", "шарманда",
        "hayrat", "ҳайрат", "kutilmagan", "кутилмаган"
    ]

    if any(t(s) in k for s in SALOMATLIK_KALITLAR):
        return "#Salomatlik"
    if any(t(s) in k for s in ANA_BOLMASA_KALITLAR):
        return "#Ана_бўлмаса"
    if any(t(s) in k for s in JAHON_KALITLAR):
        return "#Jahon"
    if any(t(s) in k for s in FOYDALI_KALITLAR):
        return "#Foydali"
    # Shoshilinch/dolzarb yangilik hamda boshqalar — #Tezkor
    return "#Tezkor"


def sarlavha_va_izohga_ajrat(toza_matn):
    """
    Matnni QALIN sarlavha va INGICHKA QIYA izohga ajratadi.
    """
    qatorlar = [q.strip() for q in toza_matn.splitlines() if q.strip()]
    if not qatorlar:
        return "", ""

    if len(qatorlar) >= 2:
        sarlavha = qatorlar[0]
        izoh = "\n".join(qatorlar[1:]).strip()
    else:
        # Bitta paragraf bo'lsa, birinchi gapni sarlavha qilamiz
        matn = qatorlar[0]
        m = re.search(r"^(.{20,160}?[.!?…])\s+(.+)$", matn)
        if m:
            sarlavha = m.group(1).strip()
            izoh = m.group(2).strip()
        else:
            sarlavha = matn
            izoh = "Тошкент ва Ўзбекистон ҳаётига оид долзарб хабарлар."

    if len(sarlavha) > 200:
        sarlavha = sarlavha[:200].rsplit(" ", 1)[0] + "…"
    if len(izoh) > 650:
        izoh = izoh[:650].rsplit(" ", 1)[0] + "…"

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


def tg_kanal_oqi(kanal_nomi):
    url = f"https://t.me/s/{kanal_nomi}"
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    qismlar = re.split(r'(?=<div class="tgme_widget_message\b)', r.text)
    natija = []
    for p in qismlar:
        m = re.search(r'data-post="([^"]+)"', p)
        if not m:
            continue
        post_id = m.group(1)

        tm = re.search(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            p, re.S
        )
        raw_html = tm.group(1) if tm else ""
        matn = re.sub(r"<br\s*/?>", "\n", raw_html)
        matn = re.sub(r"<[^>]+>", "", matn)
        matn = html.unescape(matn).strip()

        pm = re.search(
            r"tgme_widget_message_photo_wrap[^>]+background-image:url\('([^']+)'\)",
            p
        )
        rasm = pm.group(1) if pm else None

        vm = re.search(r'<video[^>]+src="([^"]+)"', p)
        video = vm.group(1) if vm else None

        if not rasm and not video:
            vthumb = re.search(
                r"tgme_widget_message_video_thumb[^>]+background-image:url\('([^']+)'\)",
                p
            )
            if vthumb:
                rasm = vthumb.group(1)

        vw = re.search(r'<span class="tgme_widget_message_views">([^<]+)</span>', p)
        views = korishlar_soni(vw.group(1) if vw else "")

        natija.append({
            "id": f"tg:{post_id}",
            "manba": kanal_nomi,
            "matn": matn,
            "rasm": rasm,
            "video": video,
            "views": views,
        })
    return natija


def kun_uz_oqi():
    r = requests.get(RSS_URL, headers=HEADERS, timeout=25)
    r.raise_for_status()
    xml_matn = re.sub(r"&(?![a-zA-Z]+;|#\d+;)", "&amp;", r.text)
    negiz = ET.fromstring(xml_matn)
    natija = []
    for it in list(negiz.iter("item"))[:8]:
        title = html.unescape((it.findtext("title") or "").strip())
        link = (it.findtext("link") or "").strip()
        if not title or not link:
            continue
        natija.append({
            "id": link,
            "manba": "kun.uz",
            "link": link,
            "title": title,
        })
    natija.reverse()
    return natija


def kun_uz_maqola_boyit(item):
    link = item["link"]
    rasm, tavsif = None, ""
    try:
        r = requests.get(link, headers=HEADERS, timeout=20)
        m = re.search(r'property="og:image"[^>]+content="([^"]+)"', r.text)
        if m:
            rasm = m.group(1).replace("&amp;", "&")
        m = re.search(r'property="og:description"[^>]+content="([^"]+)"', r.text)
        if m:
            tavsif = html.unescape(m.group(1)).strip()
    except Exception:
        pass
    matn = item["title"]
    if tavsif and tavsif.lower() != "description":
        matn = f"{item['title']}\n\n{tavsif}"
    return {
        "id": item["id"],
        "manba": "kun.uz",
        "matn": matn,
        "rasm": rasm,
        "video": None,
        "views": 5000,
    }


def fayl_yuklab_ol(url, max_mb=45):
    try:
        r = requests.get(url, headers=HEADERS, timeout=45, stream=True)
        r.raise_for_status()
        buf = io.BytesIO()
        hajm = 0
        for chunk in r.iter_content(65536):
            hajm += len(chunk)
            if hajm > max_mb * 1024 * 1024:
                return None
            buf.write(chunk)
        buf.seek(0)
        return buf
    except Exception:
        return None


def reaksiya_qoy(chat_id, message_id, matn=""):
    k = (matn or "").lower()
    if any(s in k for s in ["halok", "ҳалок", "vafot", "вафот", "fojia", "фожиа", "daxshat", "даҳшат"]):
        emojilar = ["🙏", "🤝"]
    elif any(s in k for s in ["bayram", "байрам", "tabrik", "табрик", "xushxabar", "хушхабар", "kayfiyat"]):
        emojilar = ["🔥", "❤", "💯", "👍"]
    else:
        emojilar = ["🔥", "👍", "💯", "❤", "🤝"]
    tanlov = random.choice(emojilar)
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/setMessageReaction",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
                "reaction": json.dumps([{"type": "emoji", "emoji": tanlov}]),
            },
            timeout=10,
        )
    except Exception as e:
        log(f"⚠️ Reaksiya xato: {e}")


def kanalga_yubor(post):
    raw_matn = post["matn"]
    toza_matn = matnni_tozala(raw_matn)
    if len(toza_matn) < 25:
        return False

    bitta_teg = bitta_hashtag_tanla(raw_matn, post["manba"])
    sarlavha, izoh = sarlavha_va_izohga_ajrat(toza_matn)
    if not sarlavha:
        return False

    # 1 dona #hashtag + Qalin sarlavha + Ingichka qiya izoh (tashqi ssilkasiz!)
    if izoh:
        caption = (
            f"<b>{html.escape(bitta_teg)}</b>\n\n"
            f"<b>{html.escape(sarlavha)}</b>\n\n"
            f"<i>{html.escape(izoh)}</i>\n\n"
            f"👉 @Toshkent_2200"
        )
    else:
        caption = (
            f"<b>{html.escape(bitta_teg)}</b>\n\n"
            f"<b>{html.escape(sarlavha)}</b>\n\n"
            f"👉 @Toshkent_2200"
        )

    sent = None
    # 1) Video (ustuvor!)
    if post.get("video"):
        vbuf = fayl_yuklab_ol(post["video"], max_mb=45)
        if vbuf:
            vbuf.name = "video.mp4"
            try:
                sent = bot.send_video(
                    KANAL, vbuf, caption=caption,
                    supports_streaming=True,
                    timeout=120,
                    disable_notification=not NOTIFIKATSIYA,
                )
            except Exception as e:
                log(f"⚠️ Video yuborishda xato: {e}")

    # 2) Rasm
    if sent is None and post.get("rasm"):
        pbuf = fayl_yuklab_ol(post["rasm"], max_mb=10)
        if pbuf:
            pbuf.name = "photo.jpg"
            try:
                sent = bot.send_photo(
                    KANAL, pbuf, caption=caption,
                    timeout=60,
                    disable_notification=not NOTIFIKATSIYA,
                )
            except Exception as e:
                log(f"⚠️ Rasm yuborishda xato: {e}")

    # 3) Matn
    if sent is None:
        sent = bot.send_message(
            KANAL, caption,
            disable_web_page_preview=True,
            disable_notification=not NOTIFIKATSIYA,
        )

    if sent:
        reaksiya_qoy(KANAL, sent.message_id, raw_matn)
    return True


def barcha_manbalarni_tekshir(seen, matn_baza, birinchi_marta=False):
    nomzodlar = []

    for kanal in TG_MANBALAR:
        try:
            postlar = tg_kanal_oqi(kanal)
        except Exception as e:
            log(f"⚠️ {kanal} o'qishda xato: {e}")
            continue

        kanal_birinchi = not any(str(x).startswith(f"tg:{kanal}/") for x in seen)
        yangilar = [p for p in postlar if p["id"] not in seen]
        if (birinchi_marta or kanal_birinchi) and len(yangilar) > 1:
            for eski in yangilar[:-1]:
                seen.add(eski["id"])
            yangilar = yangilar[-1:]

        for p in yangilar:
            seen.add(p["id"])
            matn = p.get("matn") or ""
            if not matn or reklama_mi(matn):
                continue
            if not ozbekchami(matn):
                continue
            if not toshkentga_aloqadormi(matn, p["manba"]):
                continue
            toza = matnni_tozala(matn)
            if len(toza) < 25 or takroriymi(toza, matn_baza):
                continue
            p["ball"] = toshkent_ustuvorlik_bali(
                matn, p["manba"], bool(p.get("video")), p.get("views", 0)
            )
            nomzodlar.append(p)

    # Kun.uz RSS
    try:
        kun_items = kun_uz_oqi()
        kun_yangi = [i for i in kun_items if i["id"] not in seen]
        if birinchi_marta and len(kun_yangi) > 1:
            for eski in kun_yangi[:-1]:
                seen.add(eski["id"])
            kun_yangi = kun_yangi[-1:]
        for it in kun_yangi:
            seen.add(it["id"])
            p = kun_uz_maqola_boyit(it)
            matn = p.get("matn") or ""
            if not matn or reklama_mi(matn) or not ozbekchami(matn):
                continue
            if not toshkentga_aloqadormi(matn, "kun.uz"):
                continue
            toza = matnni_tozala(matn)
            if len(toza) < 25 or takroriymi(toza, matn_baza):
                continue
            p["ball"] = toshkent_ustuvorlik_bali(matn, "kun.uz", False, 5000)
            nomzodlar.append(p)
    except Exception as e:
        log(f"⚠️ Kun.uz xato: {e}")

    # Videoli va Toshkentga oid dolzarb xabarlarni birinchi o'ringa saralaymiz
    nomzodlar.sort(key=lambda x: x.get("ball", 0), reverse=True)
    return nomzodlar


def kanal_oxirgi_holatini_tekshir(matn_baza):
    """
    @Toshkent_2200 kanalining jonli holatini tekshiradi:
      1) Kanaldagi oxirgi ~60 ta post matnini matn_baza ga qo'shadi
         (kompyuter va bulut bir xil xabarni ikki marta chiqarmasligi uchun).
      2) Agar oxirgi post 4 daqiqadan kam vaqt oldin chiqqan bo'lsa, False qaytaradi.
    """
    from datetime import datetime, timezone
    qoshilgan = 0
    oxirgi_vaqt = None
    try:
        sahifalar = [None, None, None]
        eng_kichik = None
        for sahifa in sahifalar:
            url = "https://t.me/s/Toshkent_2200"
            if eng_kichik:
                try:
                    url += f"?before={int(eng_kichik.split('/')[-1])}"
                except (ValueError, AttributeError):
                    break
            r = requests.get(url, headers=HEADERS, timeout=20)
            qismlar = re.split(r'(?=<div class="tgme_widget_message\b)', r.text)
            sahifa_idlar = []
            for p in qismlar:
                pm = re.search(r'data-post="([^"]+)"', p)
                if not pm:
                    continue
                post_id = pm.group(1)
                sahifa_idlar.append(post_id)
                tm = re.search(
                    r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
                    p, re.S
                )
                m_txt = html.unescape(re.sub(r"<br\s*/?>", "\n", tm.group(1) if tm else ""))
                m_txt = re.sub(r"<[^>]+>", " ", m_txt)
                toza = matnni_tozala(m_txt.strip())
                if len(toza) >= 20 and not takroriymi(toza, matn_baza):
                    matn_baza.append(matn_imzosi(toza))
                    qoshilgan += 1
                dt_m = re.search(r'<time[^>]+datetime="([^"]+)"', p)
                if dt_m and sahifa is None:
                    try:
                        oxirgi_vaqt = datetime.fromisoformat(dt_m.group(1))
                    except ValueError:
                        pass
            if sahifa_idlar:
                eng_kichik = sahifa_idlar[0]
    except Exception:
        pass
    if qoshilgan:
        matn_bazani_saqlash(matn_baza)
        log(f"🔄 Kanal bilan sinxronlashdi: bazaga {qoshilgan} ta yangi imzo qo'shildi.")
    if oxirgi_vaqt is not None:
        try:
            farq = (datetime.now(timezone.utc) - oxirgi_vaqt).total_seconds()
            if 0 <= farq < 240:
                log(f"⏳ Kanalda {int(farq)} soniya oldin post chiqqan — siklni kutamiz.")
                return False
        except Exception:
            pass
    return True


def asosiy():
    seen = korilganlarni_yukla()
    matn_baza = matn_bazani_yukla()
    birinchi_marta = len(seen) < 10
    log(f"▶️ Toshkent 2200 agregatori ishga tushdi. Kanal: {KANAL} (baza={len(seen)})")

    while True:
        try:
            if not kanal_oxirgi_holatini_tekshir(matn_baza):
                if "--once" in sys.argv:
                    break
                time.sleep(REJAL_SONIYA)
                continue
            yangi_postlar = barcha_manbalarni_tekshir(seen, matn_baza, birinchi_marta=birinchi_marta)
            birinchi_marta = False
            korilganlarni_saqlash(seen)

            if yangi_postlar:
                log(f"🔔 {len(yangi_postlar)} ta saralangan xabar topildi...")
                for p in yangi_postlar:
                    toza = matnni_tozala(p["matn"])
                    if takroriymi(toza, matn_baza):
                        continue
                    try:
                        if kanalga_yubor(p):
                            matn_baza.append(matn_imzosi(toza))
                            matn_bazani_saqlash(matn_baza)
                            korilganlarni_saqlash(seen)
                            tur = "🎬 VIDEO" if p.get("video") else "📸 POST"
                            qisqa = toza.replace("\n", " ")[:60]
                            log(f"✅ {tur} [{p['manba']}] {qisqa}")
                            time.sleep(3)
                    except Exception as e:
                        log(f"❌ Yuborishda xato [{p['manba']}]: {e}")
            else:
                log("… yangi mos xabar yo'q.")
        except Exception as e:
            log(f"❌ Siklda xato: {e}")

        if "--once" in sys.argv:
            break
        time.sleep(REJAL_SONIYA)


if __name__ == "__main__":
    asosiy()

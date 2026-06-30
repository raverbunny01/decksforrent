import logging
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Estado por usuario en memoria
user_states: dict[int, dict] = {}

precios_base = {
    "setup": 200,
    "cdj": 150,
    "xone": 55,
}

multiplicador_dias = {
    "1": 1.0,
    "2": 1.9,
    "3": 2.7,
    "4plus": None,
}

recargo_corporativo = 0.25
recargo_rrss = 0.15

LANG_BUTTONS = {
    "🇪🇸 Español": "es",
    "🇬🇧 English": "en",
}

TEXTS = {
    "es": {
        "lang_prompt": "Elige tu idioma / Choose your language:",
        "welcome": (
            "🎛️ ¡Bienvenido a *DecksForRent*!\n\n"
            "Alquiler de equipo DJ profesional en Barcelona.\n"
            "Recogida en nuestro local — sin entrega a domicilio.\n\n"
            "¿Qué equipo necesitas?"
        ),
        "ask_dias": "¿Cuántos días necesitas el equipo?",
        "ask_evento": "¿Qué tipo de evento es?",
        "ask_rrss": "¿Tienes redes sociales donde se publicará el evento?",
        "ask_rrss_perfil": "¿Cuál es tu perfil principal?",
        "ask_fecha": "¿Cuál es la fecha del evento?",
        "ask_contacto": "Por último, indícanos tu nombre y teléfono de contacto:",
        "invalid_option": "Por favor, elige una opción del teclado.",
        "invalid_rrss": "Por favor, elige Sí o No.",
        "presupuesto_custom": (
            "Te prepararemos un presupuesto personalizado, "
            "nos ponemos en contacto contigo pronto."
        ),
        "presupuesto_title": "🎛️ PRESUPUESTO DESK FOR RENT",
        "presupuesto_equipo": "Equipo",
        "presupuesto_dias": "Días",
        "presupuesto_evento": "Tipo de evento",
        "presupuesto_fecha": "Fecha",
        "presupuesto_total": "💶 Total estimado",
        "presupuesto_footer": (
            "Presupuesto orientativo. Te confirmamos en menos de 2h.\n"
            "📩 ¿Dudas? Escríbenos aquí mismo."
        ),
        "iva": "+ IVA",
        "cancel": "Conversación cancelada. Escribe /start para empezar de nuevo.",
        "rrss_no": "No",
        "owner_title": "🔔 NUEVO PRESUPUESTO",
        "owner_cliente": "Cliente",
        "owner_idioma": "Idioma del cliente",
        "owner_rrss": "RRSS",
        "owner_equipo": "Equipo",
        "owner_dias": "Días",
        "owner_evento": "Evento",
        "owner_fecha": "Fecha",
        "owner_total": "Total",
        "owner_custom": "Presupuesto personalizado",
        "lang_name": "Español",
        "equipos": {
            "setup": "Setup completo (2x CDJ-3000 + Xone:96)",
            "cdj": "Solo 2x CDJ-3000",
            "xone": "Solo Xone:96",
        },
        "dias": {
            "1": "1 día",
            "2": "2 días",
            "3": "3 días",
            "4plus": "Más de 3 días",
        },
        "eventos": {
            "private": "Fiesta privada",
            "corporate": "Evento corporativo",
            "club": "Club / Festival",
            "studio": "Sesión de estudio",
        },
        "rrss": {
            "yes": "Sí",
            "no": "No",
        },
    },
    "en": {
        "lang_prompt": "Choose your language / Elige tu idioma:",
        "welcome": (
            "🎛️ Welcome to *DecksForRent*!\n\n"
            "Professional DJ equipment rental in Barcelona.\n"
            "Pickup at our location — no home delivery.\n\n"
            "Which equipment do you need?"
        ),
        "ask_dias": "How many days do you need the equipment?",
        "ask_evento": "What type of event is it?",
        "ask_rrss": "Do you have social media where the event will be promoted?",
        "ask_rrss_perfil": "What is your main profile?",
        "ask_fecha": "What is the event date?",
        "ask_contacto": "Finally, please share your name and phone number:",
        "invalid_option": "Please choose an option from the keyboard.",
        "invalid_rrss": "Please choose Yes or No.",
        "presupuesto_custom": (
            "We'll prepare a custom quote and get in touch with you soon."
        ),
        "presupuesto_title": "🎛️ DESK FOR RENT QUOTE",
        "presupuesto_equipo": "Equipment",
        "presupuesto_dias": "Days",
        "presupuesto_evento": "Event type",
        "presupuesto_fecha": "Date",
        "presupuesto_total": "💶 Estimated total",
        "presupuesto_footer": (
            "Indicative quote. We'll confirm within 2 hours.\n"
            "📩 Questions? Message us here."
        ),
        "iva": "+ VAT",
        "cancel": "Conversation cancelled. Type /start to begin again.",
        "rrss_no": "No",
        "owner_title": "🔔 NEW QUOTE",
        "owner_cliente": "Client",
        "owner_idioma": "Client language",
        "owner_rrss": "Social media",
        "owner_equipo": "Equipment",
        "owner_dias": "Days",
        "owner_evento": "Event",
        "owner_fecha": "Date",
        "owner_total": "Total",
        "owner_custom": "Custom quote",
        "lang_name": "English",
        "equipos": {
            "setup": "Full setup (2x CDJ-3000 + Xone:96)",
            "cdj": "2x CDJ-3000 only",
            "xone": "Xone:96 only",
        },
        "dias": {
            "1": "1 day",
            "2": "2 days",
            "3": "3 days",
            "4plus": "More than 3 days",
        },
        "eventos": {
            "private": "Private party",
            "corporate": "Corporate event",
            "club": "Club / Festival",
            "studio": "Studio session",
        },
        "rrss": {
            "yes": "Yes",
            "no": "No",
        },
    },
}

IDIOMA, EQUIPO, DIAS, EVENTO, RRSS, RRSS_PERFIL, FECHA, CONTACTO = range(8)


def _keyboard(options: list[str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[option] for option in options],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _reset_user(user_id: int) -> None:
    user_states[user_id] = {}


def _get_user(user_id: int) -> dict:
    if user_id not in user_states:
        user_states[user_id] = {}
    return user_states[user_id]


def _lang(user_id: int) -> str:
    return _get_user(user_id).get("lang", "es")


def _txt(user_id: int, key: str) -> str:
    return TEXTS[_lang(user_id)][key]


def _labels(user_id: int, category: str) -> list[str]:
    return list(TEXTS[_lang(user_id)][category].values())


def _key_from_label(user_id: int, category: str, label: str) -> str | None:
    for key, value in TEXTS[_lang(user_id)][category].items():
        if value == label:
            return key
    return None


def _label(user_id: int, category: str, key: str) -> str:
    return TEXTS[_lang(user_id)][category][key]


def _calcular_total(data: dict) -> int | None:
    if data.get("dias") == "4plus":
        return None

    base = precios_base[data["equipo"]]
    mult = multiplicador_dias[data["dias"]]
    total = base * mult

    if data.get("evento") == "corporate":
        total *= 1 + recargo_corporativo

    if data.get("tiene_rrss"):
        total *= 1 + recargo_rrss

    return round(total)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    _reset_user(user_id)

    await update.message.reply_text(
        TEXTS["es"]["lang_prompt"],
        reply_markup=_keyboard(list(LANG_BUTTONS.keys())),
    )
    return IDIOMA


async def idioma(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if choice not in LANG_BUTTONS:
        await update.message.reply_text(
            TEXTS["es"]["lang_prompt"],
            reply_markup=_keyboard(list(LANG_BUTTONS.keys())),
        )
        return IDIOMA

    user_id = update.effective_user.id
    lang = LANG_BUTTONS[choice]
    _get_user(user_id)["lang"] = lang

    await update.message.reply_text(
        TEXTS[lang]["welcome"],
        parse_mode="Markdown",
        reply_markup=_keyboard(_labels(user_id, "equipos")),
    )
    return EQUIPO


async def equipo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    choice = update.message.text
    key = _key_from_label(user_id, "equipos", choice)

    if key is None:
        await update.message.reply_text(
            _txt(user_id, "invalid_option"),
            reply_markup=_keyboard(_labels(user_id, "equipos")),
        )
        return EQUIPO

    _get_user(user_id)["equipo"] = key

    await update.message.reply_text(
        _txt(user_id, "ask_dias"),
        reply_markup=_keyboard(_labels(user_id, "dias")),
    )
    return DIAS


async def dias(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    choice = update.message.text
    key = _key_from_label(user_id, "dias", choice)

    if key is None:
        await update.message.reply_text(
            _txt(user_id, "invalid_option"),
            reply_markup=_keyboard(_labels(user_id, "dias")),
        )
        return DIAS

    _get_user(user_id)["dias"] = key

    await update.message.reply_text(
        _txt(user_id, "ask_evento"),
        reply_markup=_keyboard(_labels(user_id, "eventos")),
    )
    return EVENTO


async def evento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    choice = update.message.text
    key = _key_from_label(user_id, "eventos", choice)

    if key is None:
        await update.message.reply_text(
            _txt(user_id, "invalid_option"),
            reply_markup=_keyboard(_labels(user_id, "eventos")),
        )
        return EVENTO

    _get_user(user_id)["evento"] = key

    await update.message.reply_text(
        _txt(user_id, "ask_rrss"),
        reply_markup=_keyboard(_labels(user_id, "rrss")),
    )
    return RRSS


async def rrss(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    choice = update.message.text
    key = _key_from_label(user_id, "rrss", choice)

    if key is None:
        await update.message.reply_text(
            _txt(user_id, "invalid_rrss"),
            reply_markup=_keyboard(_labels(user_id, "rrss")),
        )
        return RRSS

    data = _get_user(user_id)
    data["tiene_rrss"] = key == "yes"

    if key == "yes":
        await update.message.reply_text(
            _txt(user_id, "ask_rrss_perfil"),
            reply_markup=ReplyKeyboardRemove(),
        )
        return RRSS_PERFIL

    data["rrss_perfil"] = _txt(user_id, "rrss_no")
    await update.message.reply_text(
        _txt(user_id, "ask_fecha"),
        reply_markup=ReplyKeyboardRemove(),
    )
    return FECHA


async def rrss_perfil(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    _get_user(user_id)["rrss_perfil"] = update.message.text

    await update.message.reply_text(_txt(user_id, "ask_fecha"))
    return FECHA


async def fecha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    _get_user(user_id)["fecha"] = update.message.text

    await update.message.reply_text(_txt(user_id, "ask_contacto"))
    return CONTACTO


async def _notify_owner(context: ContextTypes.DEFAULT_TYPE, data: dict, total: int | None) -> None:
    if not OWNER_CHAT_ID:
        logger.warning("OWNER_CHAT_ID no configurado")
        return

    lang = data.get("lang", "es")
    t = TEXTS[lang]
    iva = t["iva"]

    total_str = f"{total}€ {iva}" if total is not None else t["owner_custom"]

    owner_msg = (
        f"{t['owner_title']}\n\n"
        f"{t['owner_cliente']}: {data.get('contacto', '—')}\n"
        f"{t['owner_idioma']}: {t['lang_name']}\n"
        f"{t['owner_rrss']}: {data.get('rrss_perfil', t['rrss_no'])}\n"
        f"{t['owner_equipo']}: {t['equipos'][data['equipo']]}\n"
        f"{t['owner_dias']}: {t['dias'][data['dias']]}\n"
        f"{t['owner_evento']}: {t['eventos'][data['evento']]}\n"
        f"{t['owner_fecha']}: {data['fecha']}\n"
        f"{t['owner_total']}: {total_str}"
    )

    await context.bot.send_message(chat_id=int(OWNER_CHAT_ID), text=owner_msg)


async def contacto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    data = _get_user(user_id)
    data["contacto"] = update.message.text

    total = _calcular_total(data)
    t = TEXTS[_lang(user_id)]

    if total is None:
        await update.message.reply_text(
            t["presupuesto_custom"],
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        msg = (
            f"{t['presupuesto_title']}\n\n"
            f"{t['presupuesto_equipo']}: {t['equipos'][data['equipo']]}\n"
            f"{t['presupuesto_dias']}: {t['dias'][data['dias']]}\n"
            f"{t['presupuesto_evento']}: {t['eventos'][data['evento']]}\n"
            f"{t['presupuesto_fecha']}: {data['fecha']}\n\n"
            f"{t['presupuesto_total']}: {total}€ {t['iva']}\n\n"
            f"{t['presupuesto_footer']}"
        )
        await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())

    await _notify_owner(context, data, total)
    _reset_user(user_id)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    lang = _lang(user_id) if user_states.get(user_id, {}).get("lang") else "es"
    _reset_user(user_id)
    await update.message.reply_text(
        TEXTS[lang]["cancel"],
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main() -> None:
    if not TELEGRAM_TOKEN:
        raise SystemExit("TELEGRAM_TOKEN no encontrado en .env")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            IDIOMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, idioma)],
            EQUIPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, equipo)],
            DIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, dias)],
            EVENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, evento)],
            RRSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, rrss)],
            RRSS_PERFIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, rrss_perfil)],
            FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, fecha)],
            CONTACTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, contacto)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    logger.info("DecksForRentBot iniciado")
    app.run_polling()


if __name__ == "__main__":
    main()

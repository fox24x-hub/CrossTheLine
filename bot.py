#!/usr/bin/env python3
"""
CrossTheLine_ekb — бот для подбора беговых кроссовок
Автор: Андрей Потапов

Запуск:
    pip install -r requirements.txt
    BOT_TOKEN=... ADMIN_CHAT_ID=... python bot.py
"""

import os
import logging

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler, ContextTypes
)

if load_dotenv is not None:
    load_dotenv()
else:
    logging.warning("python-dotenv не установлен; .env файл не будет загружен")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не задана")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
if ADMIN_CHAT_ID is not None:
    try:
        ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
    except ValueError:
        logger.warning("ADMIN_CHAT_ID должен быть числом, получено: %s", ADMIN_CHAT_ID)
        ADMIN_CHAT_ID = None

# ---------- States ----------
(EXPERIENCE, FREQUENCY, MILEAGE, GOAL, SURFACE, WINTER,
 PROBLEMS, FLATFOOT, INSOLES, WIDTH,
 PREV_SHOES, PREV_FEEDBACK,
 SOFTNESS, WEIGHT_MATTERS, BUDGET,
 CLIENT_NAME, PHONE) = range(17)

PROBLEMS_DONE = "problems_done"

PROBLEMS_LABELS = {
    "pr_knees": "Колени",
    "pr_shin":  "Голень / надкостница",
    "pr_foot":  "Стопа / подошва",
    "pr_back":  "Спина",
    "pr_none":  "Нет проблем",
}


# ---------- Helpers ----------

def kb(rows: list[list[tuple]]) -> InlineKeyboardMarkup:
    """Строит InlineKeyboardMarkup из списка строк [(label, data), ...]"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=data) for label, data in row]
        for row in rows
    ])


def problems_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for data, label in PROBLEMS_LABELS.items():
        prefix = "✅ " if data in selected else ""
        buttons.append([InlineKeyboardButton(prefix + label, callback_data=data)])
    buttons.append([InlineKeyboardButton("Готово →", callback_data=PROBLEMS_DONE)])
    return InlineKeyboardMarkup(buttons)


# ---------- Handlers ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["problems"] = []

    await update.message.reply_text(
        "Привет! Я помогу подготовиться к консультации по подбору беговых кроссовок.\n\n"
        "Несколько вопросов — займёт 3-5 минут. Погнали?\n\n"
        "Ты сейчас бегаешь?",
        reply_markup=kb([
            [("Бегаю регулярно", "exp_regular"), ("Бегаю иногда", "exp_sometimes")],
            [("Только начинаю", "exp_beginner"), ("Раньше бегал, сейчас пауза", "exp_pause")],
        ])
    )
    return EXPERIENCE


async def experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    exp_map = {
        "exp_regular":  "Бегаю регулярно",
        "exp_sometimes": "Бегаю иногда",
        "exp_beginner": "Только начинаю",
        "exp_pause":    "Раньше бегал, сейчас пауза",
    }
    context.user_data["experience"] = exp_map[q.data]
    context.user_data["is_beginner"] = (q.data == "exp_beginner")

    if context.user_data["is_beginner"]:
        # Пропускаем частоту и километраж
        await q.edit_message_text(
            "Какая главная цель?",
            reply_markup=kb([
                [("Здоровье и удовольствие", "goal_health")],
                [("Первый старт (5-10 км)", "goal_first")],
                [("Полумарафон / марафон", "goal_half")],
                [("Ходьба и прогулки", "goal_walk")],
            ])
        )
        return GOAL
    else:
        await q.edit_message_text(
            "Сколько раз в неделю бегаешь?",
            reply_markup=kb([
                [("1-2 раза", "freq_12"), ("3-4 раза", "freq_34")],
                [("5 и больше", "freq_5plus")],
            ])
        )
        return FREQUENCY


async def frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    freq_map = {
        "freq_12":    "1-2 раза в неделю",
        "freq_34":    "3-4 раза в неделю",
        "freq_5plus": "5+ раз в неделю",
    }
    context.user_data["frequency"] = freq_map[q.data]

    await q.edit_message_text(
        "Примерный километраж в неделю?",
        reply_markup=kb([
            [("До 20 км", "km_20"), ("20-50 км", "km_50")],
            [("50+ км", "km_50plus"), ("Не считаю", "km_unknown")],
        ])
    )
    return MILEAGE


async def mileage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    km_map = {
        "km_20":      "До 20 км/нед",
        "km_50":      "20-50 км/нед",
        "km_50plus":  "50+ км/нед",
        "km_unknown": "Не считаю",
    }
    context.user_data["mileage"] = km_map[q.data]

    await q.edit_message_text(
        "Какая главная цель?",
        reply_markup=kb([
            [("Здоровье и удовольствие", "goal_health")],
            [("Первый старт (5-10 км)", "goal_first")],
            [("Полумарафон / марафон", "goal_half")],
            [("Тренировки на результат", "goal_perf")],
        ])
    )
    return GOAL


async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    goal_map = {
        "goal_health": "Здоровье и удовольствие",
        "goal_first":  "Первый старт (5-10 км)",
        "goal_half":   "Полумарафон / марафон",
        "goal_walk":   "Ходьба и прогулки",
        "goal_perf":   "Тренировки на результат",
    }
    context.user_data["goal"] = goal_map[q.data]

    await q.edit_message_text(
        "Где чаще всего бегаешь?",
        reply_markup=kb([
            [("Асфальт / город", "surf_asphalt")],
            [("Грунт / парк / лес", "surf_trail")],
            [("Смешанно", "surf_mixed")],
            [("Стадион / манеж", "surf_stadium")],
        ])
    )
    return SURFACE


async def surface(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    surf_map = {
        "surf_asphalt":  "Асфальт / город",
        "surf_trail":    "Грунт / парк / лес",
        "surf_mixed":    "Смешанно",
        "surf_stadium":  "Стадион / манеж",
    }
    context.user_data["surface"] = surf_map[q.data]

    await q.edit_message_text(
        "Планируешь бегать зимой?",
        reply_markup=kb([
            [("Да", "winter_yes"), ("Нет", "winter_no")],
            [("По-разному / не знаю", "winter_maybe")],
        ])
    )
    return WINTER


async def winter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    winter_map = {
        "winter_yes":   "Да",
        "winter_no":    "Нет",
        "winter_maybe": "По-разному",
    }
    context.user_data["winter"] = winter_map[q.data]

    await q.edit_message_text(
        "Есть ли проблемы с суставами или мышцами?\n"
        "Можно выбрать несколько, потом — «Готово»",
        reply_markup=problems_keyboard(context.user_data["problems"])
    )
    return PROBLEMS


async def problems(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    if q.data == PROBLEMS_DONE:
        if not context.user_data["problems"]:
            context.user_data["problems"] = ["pr_none"]

        await q.edit_message_text(
            "Плоскостопие диагностировали?",
            reply_markup=kb([
                [("Да", "flat_yes"), ("Нет", "flat_no")],
                [("Не знаю", "flat_unknown")],
            ])
        )
        return FLATFOOT

    selected = context.user_data["problems"]
    if q.data == "pr_none":
        selected.clear()
        selected.append("pr_none")
    else:
        if "pr_none" in selected:
            selected.remove("pr_none")
        if q.data in selected:
            selected.remove(q.data)
        else:
            selected.append(q.data)

    await q.edit_message_reply_markup(reply_markup=problems_keyboard(selected))
    return PROBLEMS


async def flatfoot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    flat_map = {
        "flat_yes":     "Да",
        "flat_no":      "Нет",
        "flat_unknown": "Не знаю",
    }
    context.user_data["flatfoot"] = flat_map[q.data]

    await q.edit_message_text(
        "Используешь ортопедические стельки?",
        reply_markup=kb([
            [("Да, свои стельки", "ins_yes")],
            [("Нет", "ins_no")],
            [("Не знаю, нужны ли", "ins_maybe")],
        ])
    )
    return INSOLES


async def insoles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    ins_map = {
        "ins_yes":   "Да, свои стельки",
        "ins_no":    "Нет",
        "ins_maybe": "Не знаю, нужны ли",
    }
    context.user_data["insoles"] = ins_map[q.data]

    await q.edit_message_text(
        "Какая у тебя стопа по ширине?",
        reply_markup=kb([
            [("Узкая", "w_narrow"), ("Средняя", "w_medium")],
            [("Широкая", "w_wide"), ("Не знаю", "w_unknown")],
        ])
    )
    return WIDTH


async def width(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    w_map = {
        "w_narrow":  "Узкая",
        "w_medium":  "Средняя",
        "w_wide":    "Широкая",
        "w_unknown": "Не знаю",
    }
    context.user_data["width"] = w_map[q.data]

    if context.user_data.get("is_beginner"):
        context.user_data["prev_shoes"] = "—"
        context.user_data["prev_feedback"] = "—"
        await q.edit_message_text(
            "Есть предпочтения по ощущению подошвы?",
            reply_markup=kb([
                [("Помягче", "soft_soft"), ("Поупруже", "soft_firm")],
                [("Без разницы / не знаю", "soft_unknown")],
            ])
        )
        return SOFTNESS
    else:
        await q.edit_message_text(
            "В каких кроссовках бегал раньше?\n\n"
            "Напиши марку и модель если помнишь, или просто опиши."
        )
        return PREV_SHOES


async def prev_shoes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["prev_shoes"] = update.message.text

    await update.message.reply_text(
        "Что нравилось, что нет?\n\n"
        "Например: мягкие, но скользили / жёсткие, натирали пятку / тесно в носке"
    )
    return PREV_FEEDBACK


async def prev_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["prev_feedback"] = update.message.text

    await update.message.reply_text(
        "Есть предпочтения по ощущению подошвы?",
        reply_markup=kb([
            [("Помягче", "soft_soft"), ("Поупруже", "soft_firm")],
            [("Без разницы / не знаю", "soft_unknown")],
        ])
    )
    return SOFTNESS


async def softness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    soft_map = {
        "soft_soft":    "Помягче",
        "soft_firm":    "Поупруже",
        "soft_unknown": "Без разницы",
    }
    context.user_data["softness"] = soft_map[q.data]

    await q.edit_message_text(
        "Важен ли вес кроссовка?",
        reply_markup=kb([
            [("Да, хочу полегче", "wt_yes"), ("Нет", "wt_no")],
            [("Без разницы", "wt_any")],
        ])
    )
    return WEIGHT_MATTERS


async def weight_matters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    wt_map = {
        "wt_yes": "Да, хочу полегче",
        "wt_no":  "Нет",
        "wt_any": "Без разницы",
    }
    context.user_data["weight"] = wt_map[q.data]

    await q.edit_message_text(
        "Бюджет на кроссовки?",
        reply_markup=kb([
            [("До 10 000 ₽", "bgt_10"), ("10 000 – 15 000 ₽", "bgt_15")],
            [("Выше 15 000 ₽", "bgt_high"), ("Ещё не думал", "bgt_open")],
        ])
    )
    return BUDGET


async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    bgt_map = {
        "bgt_10":    "До 10 000 ₽",
        "bgt_15":   "10 000 – 15 000 ₽",
        "bgt_high": "Выше 15 000 ₽",
        "bgt_open": "Ещё не думал",
    }
    context.user_data["budget"] = bgt_map[q.data]

    await q.edit_message_text("Отлично, почти готово!\n\nКак тебя зовут?")
    return CLIENT_NAME


async def client_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["client_name"] = update.message.text

    await update.message.reply_text(
        "И номер телефона или удобный способ для связи — "
        "чтобы договориться о встрече."
    )
    return PHONE


async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["phone"] = update.message.text
    d = context.user_data

    # Собираем проблемы в читаемый список
    problems_str = ", ".join(
        PROBLEMS_LABELS.get(p, p) for p in d.get("problems", [])
    ) or "—"

    summary = (
        f"🆕 Новая заявка на консультацию\n\n"
        f"👤 {d.get('client_name', '—')}\n"
        f"📞 {d.get('phone', '—')}\n\n"
        f"──────────────────\n"
        f"🏃 Опыт: {d.get('experience', '—')}\n"
        f"📅 Частота: {d.get('frequency', '—')}\n"
        f"📏 Километраж: {d.get('mileage', '—')}\n"
        f"🎯 Цель: {d.get('goal', '—')}\n\n"
        f"🌍 Покрытие: {d.get('surface', '—')}\n"
        f"❄️ Зима: {d.get('winter', '—')}\n\n"
        f"──────────────────\n"
        f"🦵 Проблемы: {problems_str}\n"
        f"👣 Плоскостопие: {d.get('flatfoot', '—')}\n"
        f"🩺 Стельки: {d.get('insoles', '—')}\n"
        f"📐 Ширина стопы: {d.get('width', '—')}\n\n"
        f"──────────────────\n"
        f"👟 Прошлые кроссовки: {d.get('prev_shoes', '—')}\n"
        f"💬 Что нравилось/нет: {d.get('prev_feedback', '—')}\n\n"
        f"⚙️ Подошва: {d.get('softness', '—')}\n"
        f"⚖️ Вес важен: {d.get('weight', '—')}\n"
        f"💰 Бюджет: {d.get('budget', '—')}"
    )

    if ADMIN_CHAT_ID is None:
        logger.error("ADMIN_CHAT_ID не задан: заявка не отправлена администратору")
        await update.message.reply_text(
            "Ошибка: ADMIN_CHAT_ID не настроен. Заявка не отправлена администратору."
        )
    else:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)
        await update.message.reply_text(
            f"Готово, {d.get('client_name', '')}! Анкета отправлена.\n\n"
            "Свяжусь с тобой в ближайшее время — договоримся о встрече. "
            "Консультация: 30 минут, 1 500 ₽. Уйдёшь с чёткими вариантами 👟"
        )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Окей, отменил. Напиши /start чтобы начать заново."
    )
    return ConversationHandler.END


async def measure_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📏 Как замерить стопу дома\n\n"
        "Тебе понадобится: лист бумаги А4, карандаш, линейка.\n\n"
        "1️⃣ Положи лист на твёрдый пол\n"
        "Встань на него босиком. Перенеси вес на ногу — стопа должна быть нагружена, "
        "как при беге.\n\n"
        "2️⃣ Обведи стопу карандашом\n"
        "Держи карандаш строго вертикально, веди вплотную к коже. "
        "Удобнее если кто-то поможет.\n\n"
        "3️⃣ Измерь длину\n"
        "От самой выступающей точки пятки до кончика самого длинного пальца. "
        "Это твой размер стопы в мм.\n\n"
        "4️⃣ Измерь ширину\n"
        "В самом широком месте — обычно это зона плюсны (основание пальцев).\n\n"
        "5️⃣ Повтори для второй ноги\n"
        "Стопы у большинства людей немного разные. "
        "Берём большее значение из двух.\n\n"
        "⏰ Лучше мерить вечером — после дня на ногах стопа чуть больше, "
        "это ближе к реальному размеру при беге.\n\n"
        "Пришли мне результаты:\n"
        "Длина: ___ мм\n"
        "Ширина: ___ мм\n\n"
        "Или приходи с этими данными на консультацию 👟"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Я помогу собрать данные для подбора беговых кроссовок.\n"
        "Команды:\n"
        "/start — начать опрос\n"
        "/measure — как замерить стопу дома\n"
        "/cancel — отменить текущий опрос\n"
        "/help — показать это сообщение"
    )


# ---------- Main ----------

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            EXPERIENCE:     [CallbackQueryHandler(experience)],
            FREQUENCY:      [CallbackQueryHandler(frequency)],
            MILEAGE:        [CallbackQueryHandler(mileage)],
            GOAL:           [CallbackQueryHandler(goal)],
            SURFACE:        [CallbackQueryHandler(surface)],
            WINTER:         [CallbackQueryHandler(winter)],
            PROBLEMS:       [CallbackQueryHandler(problems)],
            FLATFOOT:       [CallbackQueryHandler(flatfoot)],
            INSOLES:        [CallbackQueryHandler(insoles)],
            WIDTH:          [CallbackQueryHandler(width)],
            PREV_SHOES:     [MessageHandler(filters.TEXT & ~filters.COMMAND, prev_shoes)],
            PREV_FEEDBACK:  [MessageHandler(filters.TEXT & ~filters.COMMAND, prev_feedback)],
            SOFTNESS:       [CallbackQueryHandler(softness)],
            WEIGHT_MATTERS: [CallbackQueryHandler(weight_matters)],
            BUDGET:         [CallbackQueryHandler(budget)],
            CLIENT_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, client_name)],
            PHONE:          [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("measure", measure_command))
    app.add_handler(CommandHandler("help", help_command))
    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()

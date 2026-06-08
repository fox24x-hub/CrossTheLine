# CrossTheLine_ekb_bot — бот для подбора беговых кроссовок

## Быстрый старт

### 1. Создать бота
Написать @BotFather → /newbot → получить BOT_TOKEN

### 2. Узнать свой chat_id
Написать @userinfobot — пришлёт твой ADMIN_CHAT_ID

### 3. Установить зависимости
```bash
python -m pip install -r requirements.txt
```

### 4. Запустить
```bash
BOT_TOKEN=your_token ADMIN_CHAT_ID=your_chat_id python bot.py
```

Или через .env-файл:
```bash
copy .env.example .env
```

В файле `.env` заполнить:
```
BOT_TOKEN=your_token
ADMIN_CHAT_ID=your_chat_id
```

---

## Репозиторий
- https://github.com/fox24x-hub/CrossTheLine

---

## Логика ветвления

- Новички (Только начинаю) → пропускают вопросы про частоту, километраж и предыдущие кроссовки
- Вопрос про проблемы — мультивыбор с чекбоксами
- В конце сводка летит тебе в личку в удобном формате

## Команды клиента
- /start — начать опросник
- /cancel — отменить и начать заново

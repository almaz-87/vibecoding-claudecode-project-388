# Трекер цен с Claude


[![hexlet-check](https://github.com/almaz-87/vibecoding-claudecode-project-388/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/almaz-87/vibecoding-claudecode-project-388/actions)

Соберите на Claude-скиллах трекер цен: он сам следит за товарами и присылает в Telegram только значимые изменения.

Учебный проект Хекслета: https://ru.hexlet.io/programs/vibecoding-claudecode


## Как это работает

Вся логика трекера — в Claude-скиллах; код написан агентом в подходе вайбкодинга.

```
список URL ──► extract-price (по каждому URL) ──► таблица прогона
                                                      │
          tracker-data/<последний>.json ──► diff.py ◄─┘
                                              │
                         KNOWLEDGE.md ──► только значимые изменения
                                              │
              tracker-data/YYYY-MM-DD.json ◄──┴──► send.py ──► Telegram
```

1. **Сбор цен.** Скилл `tracker` обходит список URL и для каждого вызывает `extract-price`, который возвращает объект `{ regular_price, sale_price, has_credit }` (при ошибке — `null`).
2. **Предыдущий прогон.** `tracker` через GitHub MCP получает список файлов приватного репозитория `tracker-data` и читает последний `YYYY-MM-DD.json`.
3. **Diff.** `diff.py` сопоставляет товары по URL и сравнивает `regular_price`, `sale_price`, `has_credit`.
4. **Значимость.** Правила из `KNOWLEDGE.md` отбрасывают шум (колебания меньше 5%) и оставляют то, о чём стоит сообщить: изменение цены от 5%, появление и окончание скидки, изменение рассрочки, пропажу товара и его возвращение.
5. **Сохранение.** Свежий прогон записывается в `tracker-data` через GitHub MCP — один файл на день, каждая запись — отдельный коммит.
6. **Уведомление.** Сводка (одна строка на изменение) уходит в Telegram через `send.py`. Если изменений нет — приходит «Значимых изменений цен нет».

## Стек

- Claude Code — скиллы и агентный запуск
- GitHub MCP — хранение истории прогонов в репозитории `tracker-data`
- Python 3 (только стандартная библиотека) — `diff.py`, `send.py`
- Telegram Bot API — доставка уведомлений

## Структура

```
.claude/skills/
├── extract-price/SKILL.md   # один URL → { regular_price, sale_price, has_credit }
└── tracker/
    ├── SKILL.md             # обход списка URL, хранение, diff, Telegram
    └── diff.py              # сравнение двух прогонов по URL
KNOWLEDGE.md                 # правила значимости изменений цен
send.py                      # отправка сообщения в Telegram (urllib)
.env                         # токен и chat id — в .gitignore, не коммитится
```

История прогонов хранится отдельно, в приватном репозитории:

```
tracker-data/
└── YYYY-MM-DD.json          # один прогон в день
```

## Установка

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/almaz-87/vibecoding-claudecode-project-388.git
   cd vibecoding-claudecode-project-388
   ```

2. Создайте **приватный** репозиторий `tracker-data` у того же владельца — в нём будет копиться история прогонов.

3. Подключите GitHub MCP к Claude Code с доступом на запись к `tracker-data` (например, встроенную интеграцию GitHub в claude.ai). Если MCP подключается по личному токену — храните его в переменной окружения, а не в файлах репозитория.

4. Создайте Telegram-бота у [@BotFather](https://t.me/BotFather), напишите ему `/start` и узнайте свой chat id (например, у [@userinfobot](https://t.me/userinfobot)).

5. Создайте файл `.env` в корне проекта (он уже в `.gitignore`):

   ```dotenv
   TELEGRAM_BOT_TOKEN=<токен от BotFather>
   TELEGRAM_CHAT_ID=<ваш chat id>
   ```

6. Проверьте отправку — внешние зависимости не нужны:

   ```bash
   python3 send.py "Проверка связи"
   ```

Сайты магазинов должны быть доступны из окружения, где запускается Claude Code. Крупные маркетплейсы (Amazon, Wildberries, noon, Carrefour) блокируют автоматические запросы; магазины на конструкторах вроде Salla отдают цены в разметке JSON-LD и работают.

## Использование

Откройте проект в Claude Code и попросите запустить трекер со списком ссылок:

```
/tracker
https://store.alnejoum.com.sa/en/almarai-barista-1-liter-almarai-barista-long-life-full-fat-milk-1l/p26347689
https://store.alnejoum.com.sa/en/vimto-fruit-cordial-syrup-710-ml/p345193403
https://store.alnejoum.com.sa/en/machine-xs-white-piccolo-dolce-delonghi/p424888821
```

Цену одного товара можно получить отдельно:

```
/extract-price https://store.alnejoum.com.sa/en/vimto-fruit-cordial-syrup-710-ml/p345193403
```

```json
{ "regular_price": 16.88, "sale_price": 14.35, "has_credit": false }
```

Пример сводки, которая приходит в Telegram:

```
Трекер цен: 2026-11-02 vs 2026-11-01
❌ almarai-whipping-cream-1-liter — товар пропал (была цена 11.90)
📈 vimto-fruit-cordial-syrup-710-ml — цена со скидкой 13.20 → 14.35 (+8.7%)
```

Первый запуск сохраняет базовый прогон — сравнивать пока не с чем. Начиная со второго, трекер присылает только значимые изменения. Правила значимости (порог, события) настраиваются в [`KNOWLEDGE.md`](KNOWLEDGE.md).

## Безопасность

- Токен бота и chat id — только в `.env` (в `.gitignore`) или в секретах окружения; в скиллах, `send.py` и README их нет.
- Токен GitHub для MCP — только в переменных окружения.
- Данные прогонов — в приватном `tracker-data`, а не в этом репозитории.
- Если токен бота засветился — отзовите его в @BotFather командой `/revoke` и выпустите новый.

---

<details>
<summary>Автоматические тесты Хекслета</summary>

Тесты запускаются на каждый коммит. За запуск отвечает файл `.github/workflows/hexlet-check.yml` — не удаляйте и не переименовывайте ни его, ни репозиторий.

</details>

## О Хекслете

[Хекслет](https://ru.hexlet.io/) — школа программирования: авторские программы обучения с практикой, поддержкой наставников и реальными проектами, которые остаются в резюме. Этот репозиторий — один из таких проектов.

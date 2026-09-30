# Kuggriculture

Агент для среды соревнования Kaggle `kaggriculture`. Он выращивает морковь,
собирает урожай, продаёт его при выгодной цене и нанимает работников для
удаления сорняков, ягодных культур и ухода за животными. В Kaggriculture яйца
дают гуси (`GOOSE`), а не куры.

## Требования

- Python 3.12 или новее (версия проекта указана в `.python-version`);
- [uv](https://docs.astral.sh/uv/) — рекомендуемый менеджер зависимостей.

## Установка

Клонируйте репозиторий и перейдите в его каталог:

```bash
git clone <URL_РЕПОЗИТОРИЯ>
cd kuggriculture
```

Установите зафиксированные зависимости и создайте виртуальное окружение:

```bash
uv sync
```

Если `uv` не используется, можно создать окружение и установить проект через
`pip`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Локальный запуск

Запустите симуляцию против встроенного агента `starter`:

```bash
uv run python run_local.py
```

При установке через `pip` с активированным окружением используйте:

```bash
python run_local.py
```

Скрипт выводит награды и статусы игроков в терминал. После завершения он
создаёт `game.html` с визуализацией партии. Откройте этот файл в браузере.
Каждый новый запуск перезаписывает `game.html`.

## Структура

```text
main.py                         Точка входа агента для Kaggle Environments
run_local.py                    Локальная партия: наш агент против starter
src/kuggriculture/agent.py      Сборка действий агента
src/kuggriculture/carrot_farmer.py  Логика выращивания и торговли морковью
src/kuggriculture/strawberrymello_farmer.py  Рука для клубники и арбузов
src/kuggriculture/chickenfarmer.py  Рука для гусей и яиц
src/kuggriculture/cowboy.py        Рука для коров и молока
src/kuggriculture/livestock.py     Животные, ферма и выращивание пшеницы на корм
src/kuggriculture/weed_keeper.py    Логика работников и удаления сорняков
src/kuggriculture/board.py      Перемещение и поиск ближайшей клетки
```

## Изменение стратегии

Функция `agent(obs)` в `src/kuggriculture/agent.py` возвращает действия
фермера, работников и рынка. Меняйте её или вспомогательные модули, затем
повторно запускайте `run_local.py`, чтобы проверить стратегию.

# Artwork Auction Microservices

Монорепозиторий с тремя микросервисами для аукциона произведений искусства, развёрнутыми в Docker Compose.

## Структура проекта

```
artifact-auction-api/
├── docker-compose.yml          # Docker Compose конфигурация для всех сервисов
├── start.ps1                   # PowerShell скрипт для управления сервисами
├── .env                        # Переменные окружения (НЕ коммитить!)
├── .env.example                # Пример переменных окружения
├── .gitignore                  # Git ignore rules
├── README.md                   # Этот файл
├── SETUP.md                    # Инструкции по установке
├── artwork_service/            # Сервис для работы с произведениями искусства
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── business.py
│   ├── seed.py
│   ├── azure-pipelines.yml     # Pipeline для CI/CD
│   └── tests/
├── bid_service/                # Сервис для управления ставками
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── config.py
│   ├── message_sender.py
│   ├── seed.py
│   ├── azure-pipelines.yml
│   └── tests/
└── dispute_service/            # Сервис для разрешения споров
    ├── main.py
    ├── Dockerfile
    ├── requirements.txt
    ├── models.py
    ├── schemas.py
    ├── database.py
    ├── config.py
    ├── message_reader.py
    ├── seed.py
    ├── azure-pipelines.yml
    └── tests/
```

## Быстрый старт

### Требования

- Docker Desktop (версия 29.4+)
- Docker Compose (версия 5.1+)
- PowerShell (для Windows) или Bash (для Linux/Mac)

### Установка и запуск

1. **Клонируйте репозиторий:**

```bash
git clone https://dev.azure.com/<ваш-org>/<ваш-проект>/_git/artifact-auction-api
cd artifact-auction-api
```

2. **Создайте .env файл:**

```bash
cp .env.example .env
# Отредактируйте .env с вашими значениями
```

3. **Запустите сервисы:**

```powershell
.\start.ps1 -Build
```

Или напрямую:

```bash
docker-compose up -d --build
```

4. **Откройте в браузере:**

- Artwork Service: http://localhost:8001/docs
- Bid Service: http://localhost:8002/docs
- Dispute Service: http://localhost:8003/docs
- Database: localhost:1433

### Команды управления

```powershell
# Запустить и собрать образы
.\start.ps1 -Build

# Просмотреть логи
.\start.ps1 -Logs

# Запустить тесты
.\start.ps1 -Test

# Остановить сервисы
.\start.ps1 -Stop
```

## Архитектура

### Artwork Service (8001)

- Управление произведениями искусства
- Создание, обновление и удаление артворков
- API endpoints: `/artworks`, `/categories`, `/artists`

### Bid Service (8002)

- Управление ставками на произведения
- Интеграция с Azure Service Bus для отправки событий
- API endpoints: `/bids`, `/auctions`

### Dispute Service (8003)

- Разрешение споров между участниками
- Слушает события от Bid Service
- API endpoints: `/disputes`

## База данных

- **MSSQL Server 2022**: localhost:1433
- **Credentials**: sa / 61YcGTqd
- **Database**: pr2

Каждый сервис имеет свою схему:

- Artwork Service: `ArtworkSchema_Polina`
- Bid Service: `BidSchema_Polina`
- Dispute Service: `DisputeSchema_Polina`

## Azure DevOps Pipeline

Каждый сервис имеет свой `azure-pipelines.yml` со следующими этапами:

1. **SyntaxCheck** - проверка синтаксиса Python кода
2. **Test** - запуск unit тестов с pytest

Результаты тестов публикуются в Azure DevOps.

## Разработка

### Добавление нового endpoint

1. Добавьте функцию в соответствующий сервис
2. Определите Pydantic схему в `schemas.py`
3. Добавьте тест в `tests/`
4. Запустите локально: `.\start.ps1 -Build`

### Запуск тестов локально

```bash
cd artwork_service
pip install -r requirements.txt
pytest tests/ -v
```

## Коммит в Azure DevOps

```bash
git add .
git commit -m "feat: description of changes"
git push origin main
```

⚠️ **Не коммитьте:**

- `.env` (используйте `.env.example` вместо этого)
- `__pycache__/`
- `.venv/`
- `mssql-data/` (том Docker)

## Развертывание

### Локально с Docker Compose (текущий способ)

```bash
docker-compose up -d --build
```

### В облаке Azure (будущее)

1. Создайте Azure Container Registry
2. Залейте образы в ACR
3. Разверните на Azure Container Apps или App Service

### GitHub Actions / Azure Pipelines

Используйте `azure-pipelines.yml` в каждом сервисе для CI/CD.

## Поиск и исправление проблем

### Сервис не запускается

```bash
docker-compose logs artwork-service
docker-compose logs bid-service
docker-compose logs dispute-service
```

### Ошибка подключения к БД

- Проверьте значения в `.env`
- Убедитесь, что MSSQL работает: `docker-compose logs mssql-db`
- Проверьте порт: `netstat -an | grep 1433`

### Очистить всё и начать заново

```bash
docker-compose down -v
docker-compose up -d --build
```

## Документация

- [Setup](SETUP.md) - подробная инструкция установки
- [Security](SECURITY.md) - рекомендации по безопасности
- [API Examples](API_EXAMPLES.md) - примеры API запросов
- [Requirements](REQUIREMENTS.md) - зависимости проекта
- [Checklist](CHECKLIST.md) - чек-лист для сдачи

## Контакты

- Разработчик: Полина
- Email: your-email@domain.com
- Azure DevOps: [ссылка на ваш проект]

## Лицензия

MIT License - см. [LICENSE](LICENSE) файл для деталей

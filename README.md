**FastApi Backend Template**

Данный бекенд написан на FastApi с использованием лучших практик Роберта Мартина, таких как:
- SOLID
- Clean Code
- Clean Architecture
- Testing with DI

**А так же асинхронного кода**

Запуск осуществляется через Docker Compose:

```
docker-compose up --build
```
Тестирование осуществляется через Pytest:
```
pytest -v
```

FastApi запускается на 4 воркерах Uvicorn

Структура проекта:
```
├── .env
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
├── tree.py
├── alembic/
│   ├── env.py
│   ├── README
│   ├── script.py.mako
├── backups/
├── logs/
│   ├── app.log
├── scripts/
│   ├── alembic_genetare.py
├── src/
│   ├── main.py
│   ├── core/
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── logging_config.py
│   │   ├── di/
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── entity/
│   │   │   │   ├── user.py
│   │   │   ├── repository/
│   │   │   │   ├── interface_user_repository.py
│   │   ├── exceptions/
│   │   │   ├── exceptions.py
│   │   ├── middleware/
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── base.py
│   │   │   ├── connection.py
│   │   │   ├── init_db.py
│   │   │   ├── schemas.py
│   │   ├── repository/
│   │   │   ├── user_repository.py
│   ├── logs/
│   │   ├── app.log
│   ├── presentation/
│   │   ├── api/
│   │   │   ├── health.py
│   │   │   ├── __init__.py
│   │   │   ├── user/
│   │   │   │   ├── user_router.py
│   ├── services/
│   │   ├── haser_service.py
│   │   ├── JWT_service.py
│   │   ├── user_service.py
├── tests/
│   ├── conftest.py
│   ├── pytest.ini
│   ├── integration/
│   │   ├── test_integeration_user_api.py
│   │   ├── logs/
│   │   │   ├── app.log
│   ├── k6/
│   │   ├── k6_user_users_test.js
│   ├── unit/
│   │   ├── test_user_api.py
│   │   ├── logs/
│   │   │   ├── app.log
```
_**Документация доступна по адресу:
localhost:8000/docs**_


 **Производительность**

 Порядка 40-120 RPS на **1 ядро CPU** (1 воркер) (_В зависимости от запроса!_)

Данная производительность достигается за счет использования асинхронного кода и фреймворка FastApi

Основной способ увеличения производительности - горизонтальное масштабирование (увеличить количество воркеров/экземпляров приложения)

**_Нагрузочные тесты проводились с помощью k6_**
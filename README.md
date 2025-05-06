# Foodgram - Продуктовый помощник

## О проекте

Foodgram - это веб-приложение "Продуктовый помощник", которое позволяет пользователям публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а также формировать список покупок для выбранных рецептов.

Ключевые возможности:
- Регистрация и авторизация пользователей
- Создание, просмотр, редактирование и удаление рецептов
- Добавление рецептов в избранное
- Подписка на авторов рецептов
- Формирование и скачивание списка покупок
- Фильтрация рецептов по тегам
- Поиск ингредиентов по названию
- Удобные короткие ссылки на рецепты
- Административный интерфейс для управления данными

## Установка и запуск

### Предварительные требования
- Docker и Docker Compose
- Git

### Шаги по установке

1. Клонировать репозиторий:
   ```
   git clone https://github.com/tpopova13x/foodgram.git
   cd foodgram
   ```

2. Создать .env файл в директории infra/ со следующими переменными:
   ```
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=ваш_пароль
   DB_HOST=db
   DB_PORT=5432
   SECRET_KEY=ваш_секретный_ключ
   DEBUG=False
   ALLOWED_HOSTS=localhost,127.0.0.1,myhostforfinalapp.zapto.org
   CSRF_TRUSTED_ORIGINS=https://myhostforfinalapp.zapto.org
   ```

3. Запустить проект с помощью Docker Compose:
   ```
   cd foodgram
   docker-compose up -d
   ```

4. Выполнить миграции и создать суперпользователя:
   ```
   docker-compose exec backend python manage.py migrate
   docker-compose exec backend python manage.py createsuperuser
   ```

### Доступ к проекту

После успешного запуска проект будет доступен по следующим адресам:
- Веб-интерфейс: http://localhost/ или http://myhostforfinalapp.zapto.org/
- API документация: http://localhost/api/docs/ или http://myhostforfinalapp.zapto.org/api/docs/
- Панель администратора: http://localhost/admin/ или http://myhostforfinalapp.zapto.org/admin/

## Используемые технологии

### Бэкенд
- Python 3.11
- Django 4.2
- Django REST Framework
- PostgreSQL
- Djoser (аутентификация)
- Django Filter

### Фронтенд
- React.js
- Redux
- JavaScript/TypeScript
- Axios

### Инфраструктура
- Docker и Docker Compose
- Nginx (веб-сервер)
- Gunicorn (WSGI-сервер)

### CI/CD
- GitHub Actions

## Особенности API

Проект предоставляет полноценный REST API с следующими основными эндпоинтами:
- `/api/users/` - работа с пользователями
- `/api/tags/` - получение списка тегов
- `/api/ingredients/` - работа с ингредиентами
- `/api/recipes/` - управление рецептами
- `/api/recipes/{id}/favorite/` - добавление/удаление рецептов из избранного
- `/api/recipes/{id}/shopping_cart/` - добавление/удаление рецептов из списка покупок
- `/api/recipes/download_shopping_cart/` - скачивание списка покупок
- `/api/recipes/{id}/get-link/` - получение короткой ссылки на рецепт
- `/s/{id}/` - короткая ссылка для доступа к рецепту

Полная документация API доступна по адресу `/api/docs/`.

## Автор

Tatiana Popova - Разработчик проекта Foodgram

GitHub: https://github.com/tpopova13x

Email: tpopova13x@example.com

myhostforfinalapp.zapto.org

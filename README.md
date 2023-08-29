# Foddgram — сайт «Продуктовый помощник».
Учебный проект Яндекс.Практикум.

[![Status](https://github.com/mai-teacher/foodgram-project-react/workflows/Main%20Foodgram%20workflow/badge.svg)](https://github.com/mai-teacher/foodgram-project-react/actions/workflows/main.yml)

## Описание проекта
На сайте «Продуктовый помощник» пользователи могут регистрироваться, могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.
## Используемые технологии:

* Python
* Django
* Nginx
* gunicorn
* ufw
* certbot
* Docker
* GitHub Actions

## Развертывание и запуск веб-приложения на удаленном сервере

### Клонирование проекта с GitHub на сервер
Подключитесь к удаленному серверу и клонируйте репозиторий: `git@github.com:mai-teacher/foodgram-project-react.git`

### Заполнение .env
Создайте конфигурационный файл ".env" и заполните его своими данными. Пример заполнения указан в корневой директории проекта в файле ".env.example":
```
# В .env хранятся следующие переменные
# Использование СУБД PostgreSQL (по умолчанию используется SQLite)
POSTGRES=True

# Имя базы данных
POSTGRES_DB=foodgram

# Имя Пользователя Базы
POSTGRES_USER=foodgram_user

# Пароль к базе
POSTGRES_PASSWORD=foodgram_password

#
DB_NAME=foodgram

# Имя контейнера, где запущен сервер БД
DB_HOST=db

# Порт соединения к БД
DB_PORT=5432

# Секретный ключ Django (без кавычек).
SECRET_KEY=

DEBUG=False

# Список разрешённых хостов, чтобы проект запустился через внешний интерфейс
# и для доступа к приложению по внутреннему интерфейсу.
# В таком виде: ALLOWED_HOSTS=123.123.123.123, 127.0.0.1, localhost, ***foodgram.ddns.net
ALLOWED_HOSTS=
```

### Настройка CI/CD

Для автоматизации процесса CI/CD использется сервис GitHub Actions.
Файл с описанием всех процессов по тестированию, развёртыванию и запуску веб-приложения находится в директории `.github/workflows`

Добавьте свои настройки подключения к удалённому серверу и телеграмму в секреты GitHub Actions:
```
DOCKER_USERNAME                # имя пользователя в DockerHub
DOCKER_PASSWORD                # пароль пользователя в DockerHub
HOST                           # ip_address сервера
USER                           # имя пользователя
SSH_KEY                        # приватный ssh-ключ (cat ~/.ssh/id_rsa)
SSH_PASSPHRASE                 # кодовая фраза (пароль) для ssh-ключа

TELEGRAM_TO                    # id телеграм-аккаунта (можно узнать у @userinfobot, команда /start)
TELEGRAM_TOKEN                 # токен бота (получить токен можно у @BotFather, /token, имя бота)
```

В случае успешного равёртывания веб-приложения Вы получите в телеграмме сообщение об этом событии.

## Автор
[Александр Макеев](https://github.com/mai-teacher)

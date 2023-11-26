# Введение

## Зависимости

```pip install flask```

```pip install psycopg2```

## Начало работы

* Обязательно иметь настроенный PostgreSQL на компе
* Создаем app/app.py
* Заполняем app.py пустышкой:

```angular2html
import psycopg2
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def get_db_connection():
conn = psycopg2.connect(host="localhost",
database="
<Ваше название БД>",
    user="postgres",
    password="
    <Ваш пароль от БД>")
        return conn

        @app.route("/")
        def main():
        # Проверяем что можем достать данные из какой-то таблицы
        conn = get_db_connection() # установка соединения
        cur = conn.cursor() # создание курсора
        cur.execute("SELECT * FROM public.
        <Ваша таблица> ORDER BY
            <По чему упорядочить> ASC")
                computers = cur.fetchall() # считываем все
                cur.close()
                conn.close()
                print(computers) # принтим
                return render_template('main.html') # у меня тут ошибку выдавало, т.к. я ничего не менял в html, главное
                чекнуть что данные идут
```

* Создаем разметку templates/main.html
* Создаем init_db.py (пустышка)

## Что есть что

* app.py - основной и единственный исполняемый файл ('бэкенд сайта'):
    * @app.route - Аннотация какая страница обрабатывается соответствующим методом
    * Основной метод для коннекта с БД:
        * ```angular2html
      def get_db_connection():
      conn = psycopg2.connect(host="localhost",
      database="computer_club",
      user="postgres",
      password="123cisco")
      return conn
      ```
        * cur.execute() - метод для SQL запросов на БД (можно юзать уже сделанные функции и тригерры и тд)
        * cur.fetchone() - метод получения 1 строки БД по запросу
        * cur.fetchall() - метод получения всех строк БД по запросу
    * render_template() - метод создания новой разметки
    * jsonify - отправляем с backend'а в разметку данные
    * redirect - переходим из 1 url в другой
* db_sample/computer_club - копия бд из postqresql (кидал видос как бэкапить, лучше сохранять навсякий случай)
  * templates/ - директория со всеми шаблонами:
      * /bootstrap/ - так и не понял как правильно делать, можно не добавлять папку
          * /alert:
            ![Изображение](https://i.imgur.com/O5o7blz.png "alert")
      * mainPanel - основной экран админа:
        ![Изображение](https://i.imgur.com/slCRUj4.png "alert")
      * signIn - экран входа:
        ![Изображение](https://i.imgur.com/941MImm.png "alert")
        P.S. Чтобы юзать alert.html добавить
        ```angular2html
          {% extends "bootstrap/alert.html" %}

        {% block content %}
        {% endblock %}
        ```
      * table_template - макет для просмотра таблиц в БД, чтобы понять как она работает открываем app.py и смотрим любой
        метод show...Table:
      ```@app.route("/<int:user_id>/mainPannel/clients", methods=['GET', 'POST'])
    def showClientsTable(user_id):
        if request.method == 'POST':
            # Ваша логика обработки POST-запроса
            pass
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM public.client ORDER BY id_client ASC ")
        clients = cur.fetchall()  # This fetches all the rows from the 'client' table
        cur.close()
        conn.close()
        print(clients)
    
        # Pass 'clients' to the template
        return render_template(
            'table_template.html',
            user_id=user_id,
            title="Таблица клиентов",
            table_headers=['ID', 'Дата рождения', 'Телефон', 'Часы', 'ФИО'],
            table_data=clients)```



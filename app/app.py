import os

import flask.cli
import psycopg2
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(host="localhost",
                            database="computer_club",
                            user="postgres",
                            password="123cisco")
    return conn


@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username, password)
        # Здесь вы можете добавить проверку правильности введенных данных
        # и, если вход успешен, перенаправить пользователя
        return redirect(url_for('signInSuccess', user_id=1))
    return render_template('signIn.html')


@app.route("/<int:user_id>/mainPannel")
def signInSuccess(user_id):
    return render_template('mainPanel.html', user_id=user_id)


@app.route("/<int:user_id>/mainPannel/clients", methods=['GET', 'POST'])
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
        title = "Таблица клиентов",
        table_headers=['ID', 'Дата рождения', 'Телефон', 'Часы', 'ФИО'],
        table_data=clients)

@app.route("/<int:user_id>/mainPannel/computers", methods=['GET', 'POST'])
def showComputersTable(user_id):
    if request.method == 'POST':
        # Ваша логика обработки POST-запроса
        pass
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM public.computer ORDER BY id_computer ASC")
    computers = cur.fetchall()  # This fetches all the rows from the 'client' table
    cur.close()
    conn.close()
    print(computers)
    # Pass 'clients' to the template
    return render_template(
        'table_template.html',
        user_id=user_id,
        title = "Таблица компьютеров",
        table_headers=['ID', 'Информация', 'Занятость', 'ID Тарифа'],
        table_data=computers)

if __name__ == "__main__":
    app.run()

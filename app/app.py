import os

import flask.cli
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = Flask(__name__)

app.secret_key = 'secret'


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
        conn = psycopg2.connect(
            host="localhost",
            database="computer_club",
            user="postgres",
            password="123cisco")  # It's better to use environment variables for passwords
        cur = conn.cursor()

        # Query the database to find the user
        cur.execute('SELECT * FROM employee WHERE fio = %s AND password = %s', (username, password))
        user = cur.fetchone()

        cur.close()
        conn.close()
        if user is not None:
            # Assuming the 'id_employee' is the first column in your employee table
            user_id = user[0]
            return redirect(url_for('signInSuccess', user_id=user_id))
        else:
            flash('Неверные данные для входа. Пожалуйста, попробуйте снова.', 'login')
            return redirect(url_for('main'))

    return render_template('signIn.html')


@app.route("/<int:user_id>/mainPannel")
def signInSuccess(user_id):
    return render_template('mainPanel.html', user_id=user_id)


@app.route('/<int:user_id>/mainPannel/open_shift', methods=['POST'])
def open_shift(user_id):
    # Connect to the database
    conn = get_db_connection()
    cur = conn.cursor()

    # The logic here depends on whether you're opening or closing the shift
    # For the sake of this example, let's assume we are opening a new shift
    # You would need to adjust this logic based on your application needs

    # Insert a new shift with the user_id and current timestamp
    cur.execute("SELECT openshift(%s)", (user_id,))
    msg = cur.fetchone()[0]
    conn.commit()
    print(msg)
    # You might also want to handle closing the shift here
    # ...
    # flash('Смена открыта: ' + str(msg), 'shift')
    cur.close()
    conn.close()

    return jsonify({'last_id': msg})


@app.route('/<int:user_id>/mainPannel/close_shift', methods=['POST'])
def close_shift(user_id):
    # Connect to the database
    conn = get_db_connection()
    cur = conn.cursor()

    # The logic here depends on whether you're opening or closing the shift
    # For the sake of this example, let's assume we are opening a new shift
    # You would need to adjust this logic based on your application needs

    # Insert a new shift with the user_id and current timestamp
    cur.execute("SELECT closelastshift()")
    msg = cur.fetchone()[0]
    conn.commit()
    print(msg)
    # You might also want to handle closing the shift here
    # ...

    cur.close()
    conn.close()

    # flash('Смена закрыта!', 'shift')
    return jsonify({'msg': msg})


@app.route('/<int:user_id>/mainPannel/get_shift_info/<int:shift_id>', methods=['GET'])
def get_shift_info(user_id, shift_id):
    # Connect to the database
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT employee.FIO, shift.date_start, shift.date_end, shift.revenue
        FROM employee
        JOIN shift ON employee.id_employee = shift.id_employee
        WHERE shift.id_shift = %s AND shift.date_end IS NULL
    """, (shift_id,))
    shift_info = cur.fetchone()

    cur.close()
    conn.close()

    print("312312312")
    print(shift_info)
    if shift_info:
        # Convert the shift information to a dictionary and return it as JSON
        shift_info_dict = {
            'admin_name': shift_info[0],
            'time_start': shift_info[1],
            'time_end': shift_info[2],
            'revenue': shift_info[3]
        }
        return jsonify(shift_info_dict)
    else:
        return jsonify({'error': 'Shift not found'}), 404


@app.route("/<int:user_id>/mainPannel/requests", methods=['GET', 'POST'])
def showRequestsTable(user_id):
    if request.method == 'POST':
        # Ваша логика обработки POST-запроса
        pass
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_shift FROM shift ORDER BY id_shift DESC LIMIT 1")
    current_shift_id = cur.fetchone()
    print(current_shift_id)
    cur.execute(
        "SELECT id_request, hours, money, date, id_tariff, id_computer, id_client FROM public.request WHERE request.id_shift = %s ORDER BY id_request ASC",
        (current_shift_id,))
    requests = cur.fetchall()  # This fetches all the rows from the 'client' table
    cur.close()
    conn.close()
    print(requests)

    # Pass 'clients' to the template
    return render_template(
        'table_template.html',
        user_id=user_id,
        title="Таблица заявок для смены №" + str(current_shift_id[0]),
        table_headers=['ID', 'Часы', 'Деньги', 'Дата', 'Тариф', 'ID Компьютера', 'ID Клиента'],
        table_data=requests)


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
        title="Таблица клиентов",
        table_headers=['ID', 'Дата рождения', 'Телефон', 'Часы', 'ФИО'],
        table_data=clients)


@app.route("/<int:user_id>/mainPannel/shifts", methods=['GET', 'POST'])
def showShiftsTable(user_id):
    if request.method == 'POST':
        # Ваша логика обработки POST-запроса
        pass
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM public.shift ORDER BY id_shift DESC ")
    shifts = cur.fetchall()  # This fetches all the rows from the 'client' table
    cur.close()
    conn.close()

    # Pass 'clients' to the template
    return render_template(
        'table_template.html',
        user_id=user_id,
        title="Таблица клиентов",
        table_headers=['ID', 'ID Администратора', 'Дата начала', 'Дата конца', 'Выручка'],
        table_data=shifts)


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
        title="Таблица компьютеров",
        table_headers=['ID', 'Информация', 'Занятость', 'ID Тарифа'],
        table_data=computers)


@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    phone = data['phone']
    fio = data['fio']
    birthday = data['birthday']

    conn = get_db_connection()
    cur = conn.cursor()
    result = ""
    cur.execute("CALL adduserwithhours(%s, %s, %s, %s)", (phone, fio, birthday, result))
    conn.commit()

    cur.close()
    conn.close()

    if result == "":
        result = "Клиент успешно добавлен!"

    return jsonify({'resulttext': result})


@app.route('/reserve_computer', methods=['POST'])
def reserve_computer():
    data = request.get_json()
    phone_number = data['phone_number']
    tariff_id = data['tariff_id']
    reserve_hours = data['reserve_hours']

    # Find the client ID based on the phone number
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_client FROM Client WHERE phone = %s", (phone_number,))
    client = cur.fetchone()
    if client is None:
        return jsonify({'message': 'Клиент не найден'}), 404

    client_id = client[0]

    # Call the reservecomputer function
    cur.execute("SELECT reservecomputer(%s, %s, %s)", (client_id, tariff_id, reserve_hours))

    resultText = cur.fetchone()  # Assuming the stored procedure returns these values
    cur.execute("SELECT revenue FROM shift WHERE date_end is NULL")
    newRevenue = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({'success': True, 'message': resultText, 'new_revenue': newRevenue})


@app.route("/tariffs")
def get_tariffs():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_tariff, cost, description FROM tariff ORDER BY id_tariff ASC")
    tariffs = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({'tariffs': [dict(row) for row in tariffs]})


if __name__ == "__main__":
    app.run()

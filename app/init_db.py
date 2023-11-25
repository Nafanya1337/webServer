import os
import psycopg2

# Establish a connection to the database
conn = psycopg2.connect(
    host="localhost",
    database="computer_club",
    user="postgres",
    password="123cisco")  # It's assumed that the password is stored in an environment variable

# Create a cursor object using the cursor() method
cur = conn.cursor()



# # Tables Creation
cur.execute('''
CREATE TABLE IF NOT EXISTS public.client
(
    id_client integer NOT NULL GENERATED ALWAYS AS IDENTITY (INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 999 CACHE 1),
    birthdate character varying(10) COLLATE pg_catalog."default" NOT NULL,
    phone character varying(10) COLLATE pg_catalog."default" NOT NULL,
    hours integer NOT NULL,
    fio character varying(50) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT client_pkey PRIMARY KEY (id_client)
)
TABLESPACE pg_default;
''')

cur.execute('''
CREATE OR REPLACE TRIGGER check_duplicate_phone_trigger
    BEFORE INSERT OR UPDATE
    ON public.client
    FOR EACH ROW
    EXECUTE FUNCTION public.check_duplicate_phone_number();
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS public.tariff
(
    id_tariff integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9 CACHE 1 ),
    cost integer NOT NULL,
    description character varying(50) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT tariff_pkey PRIMARY KEY (id_tariff)
)

TABLESPACE pg_default;
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS public.component_type
(
    id_component integer NOT NULL,
    type character varying(64) COLLATE pg_catalog."default",
    CONSTRAINT component_type_pkey PRIMARY KEY (id_component)
)

TABLESPACE pg_default;
''')



cur.execute('''
CREATE TABLE IF NOT EXISTS public.computer
(
    id_computer integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 99 CACHE 1 ),
    info character varying(64) COLLATE pg_catalog."default" NOT NULL,
    busyness integer NOT NULL,
    id_tariff integer,
    CONSTRAINT computer_pkey PRIMARY KEY (id_computer),
    CONSTRAINT fk_tariff FOREIGN KEY (id_tariff)
        REFERENCES public.tariff (id_tariff) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;
''')

cur.execute('''
CREATE OR REPLACE TRIGGER before_delete_computer
    BEFORE DELETE
    ON public.computer
    FOR EACH ROW
    EXECUTE FUNCTION public.before_delete_computer_trigger();
''')



cur.execute('''
CREATE TABLE IF NOT EXISTS public.computer_component
(
    id_computer integer NOT NULL,
    id_component integer NOT NULL,
    description character(64) COLLATE pg_catalog."default",
    CONSTRAINT computer_component_pkey PRIMARY KEY (id_computer, id_component),
    CONSTRAINT r_10 FOREIGN KEY (id_component)
        REFERENCES public.component_type (id_component) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT r_9 FOREIGN KEY (id_computer)
        REFERENCES public.computer (id_computer) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;
''')



cur.execute('''
CREATE TABLE IF NOT EXISTS public.employee
(
    id_employee integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 99 CACHE 1 ),
    fio character varying(50) COLLATE pg_catalog."default" NOT NULL,
    graph_work character varying(28) COLLATE pg_catalog."default" NOT NULL,
    birthdate character varying(10) COLLATE pg_catalog."default" NOT NULL,
    post character varying(32) COLLATE pg_catalog."default" NOT NULL,
    password character varying(16) COLLATE pg_catalog."default" NOT NULL DEFAULT '123cisco'::character varying,
    CONSTRAINT employee_pkey PRIMARY KEY (id_employee)
)

TABLESPACE pg_default;
''')


cur.execute('''
CREATE TABLE IF NOT EXISTS public.shift
(
    id_shift integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 99 CACHE 1 ),
    id_employee integer NOT NULL,
    date_start character varying(64) COLLATE pg_catalog."default" NOT NULL,
    date_end character varying(64) COLLATE pg_catalog."default",
    revenue integer NOT NULL,
    CONSTRAINT shift_pkey PRIMARY KEY (id_shift),
    CONSTRAINT r_13 FOREIGN KEY (id_employee)
        REFERENCES public.employee (id_employee) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;
''')


cur.execute('''
CREATE TABLE IF NOT EXISTS public.request
(
    id_request integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 99 CACHE 1 ),
    hours integer NOT NULL,
    money integer NOT NULL,
    date character varying(32) COLLATE pg_catalog."default" NOT NULL,
    id_tariff integer NOT NULL,
    id_computer integer NOT NULL,
    id_client integer NOT NULL,
    id_shift integer NOT NULL,
    CONSTRAINT request_pkey PRIMARY KEY (id_request),
    CONSTRAINT r_14 FOREIGN KEY (id_shift)
        REFERENCES public.shift (id_shift) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT r_3 FOREIGN KEY (id_tariff)
        REFERENCES public.tariff (id_tariff) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT r_4 FOREIGN KEY (id_computer)
        REFERENCES public.computer (id_computer) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT r_8 FOREIGN KEY (id_client)
        REFERENCES public.client (id_client) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;
''')

cur.execute('''
CREATE OR REPLACE TRIGGER updateshiftrevenuetrigger
    BEFORE INSERT
    ON public.request
    FOR EACH ROW
    EXECUTE FUNCTION public.updateshiftrevenue();
''')




cur.execute('''
CREATE OR REPLACE TRIGGER releasecomputersonshiftclose
    AFTER UPDATE
    ON public.shift
    FOR EACH ROW
    WHEN (new.date_end IS NOT NULL AND old.date_end IS NULL)
    EXECUTE FUNCTION public.releasecomputersonshiftclose();
''')



# Functions and Triggers Creation
cur.execute('''
CREATE OR REPLACE FUNCTION public.closelastshift()
RETURNS text
LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
    lastShiftID INT;
    shiftStart VARCHAR(64);
    shiftEnd VARCHAR(64);
    shiftRevenue INT;
    resultText TEXT;
BEGIN
    SELECT id_shift, date_start, date_end, revenue
    INTO lastShiftID, shiftStart, shiftEnd, shiftRevenue
    FROM shift
    WHERE date_end IS NULL
    ORDER BY date_start DESC
    LIMIT 1;
    UPDATE shift
    SET date_end = NOW()
    WHERE id_shift = lastShiftID;
    resultText := 'Смена закрыта. Начало: ' || shiftStart || ', Конец: ' || NOW() || ', Полученные деньги: ' || shiftRevenue;
    RETURN resultText;
END;
$BODY$;
''')

cur.execute('''
CREATE OR REPLACE FUNCTION public.delete_computer_by_id(p_computer_id integer)
RETURNS void
LANGUAGE 'plpgsql'
AS $BODY$
BEGIN
    DELETE FROM public.computer_component
    WHERE id_computer = p_computer_id;
    DELETE FROM public.Computer
    WHERE id_computer = p_computer_id;
END;
$BODY$;
''')

cur.execute('''
CREATE OR REPLACE FUNCTION public.openshift(employeeid integer)
RETURNS text
LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
    lastShiftID INT;
    shiftStart VARCHAR(64);
    shiftEnd VARCHAR(64);
    resultText TEXT;
BEGIN
    SELECT id_shift, date_start, date_end
    INTO lastShiftID, shiftStart, shiftEnd
    FROM shift
    WHERE id_employee = employeeID AND date_end IS NULL
    ORDER BY date_start DESC
    LIMIT 1;
    IF lastShiftID IS NOT NULL THEN
        resultText := 'Нельзя начать новую смену, если предыдущая не завершена. Последняя смена началась ' || shiftStart;
    ELSE
        INSERT INTO shift (id_employee, date_start, date_end, revenue)
        VALUES (employeeID, NOW(), NULL, 0);
        resultText := 'Новая смена начата.';
    END IF;
    RETURN resultText;
END;
$BODY$;
''')

cur.execute('''
CREATE OR REPLACE FUNCTION public.reservecomputer(
	clientid integer,
	tariffid integer,
	reservehours integer)
    RETURNS text
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
    totalMoney INT;
    computerID INT;
    resultText TEXT;
    clientRemainingHours INT;
BEGIN
    -- Получение ID свободного компьютера с выбранным тарифом
    SELECT id_computer INTO computerID
    FROM Computer
    WHERE Busyness = 0 AND id_tariff = tariffID
    LIMIT 1;

    -- Проверка, найден ли свободный компьютер
    IF computerID IS NULL THEN
        resultText := 'Нет доступных компьютеров с выбранным тарифом';
    ELSE
        -- Установка статуса занятости компьютера
        UPDATE Computer
        SET Busyness = 1
        WHERE id_computer = computerID;

        -- Проверка, достаточно ли часов у клиента
        SELECT Client.hours INTO clientRemainingHours
        FROM Client
        WHERE Client.id_client = clientID;

        IF clientRemainingHours < reserveHours THEN
            -- Подсчет суммы для оплаты
            SELECT Cost * (reserveHours - clientRemainingHours) INTO totalMoney
            FROM Tariff
            WHERE id_tariff = tariffID;
        ELSE
            -- Уменьшение количества часов у клиента
            UPDATE Client
            SET hours = clientRemainingHours - reserveHours
            WHERE id_client = clientID;
            totalMoney := 0;
        END IF;

        -- Вставка новой заявки
        INSERT INTO Request (Hours, Money, Date, id_tariff, id_computer, id_client, id_shift)
        VALUES (reserveHours, totalMoney, NOW(), tariffID, computerID, clientID, (SELECT MAX(id_shift) FROM shift));

        resultText := 'Компьютер забронирован. ID компьютера: ' || computerID || ', Сумма оплаты: ' || totalMoney;
    END IF;

    RETURN resultText;
END;
$BODY$;
''')

cur.execute('''
CREATE OR REPLACE PROCEDURE public.adduserwithhours(
	IN p_phone character varying,
	IN p_fio character varying,
	IN p_birthday character varying,
	OUT resulttext text)
LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
    clientID INT;
BEGIN
	-- Если клиент с указанным номером не существует, добавляем нового клиента
	INSERT INTO Client (Birthdate, Phone, Hours, FIO)
	VALUES (p_birthday, p_phone, 5, p_fio);
	resultText := 'Новый клиент добавлен.';
END;
$BODY$;
''')



cur.execute('''
CREATE OR REPLACE FUNCTION public.before_delete_computer_trigger()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    -- Проверка, занят ли компьютер
    IF EXISTS (
        SELECT 1
        FROM public.Computer
        WHERE id_computer = OLD.id_computer
        AND busyness = 1
    ) THEN
        RAISE EXCEPTION 'Нельзя удалить занятый компьютер';
    END IF;

    RETURN OLD;
END;
$BODY$;
''')

cur.execute('''
CREATE OR REPLACE FUNCTION public.check_duplicate_phone_number()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM client
        WHERE phone = NEW.phone
        ) THEN
        RAISE EXCEPTION 'Клиент с таким номером телефона уже существует в базе данных';
    END IF;

    RETURN NEW;
END;
$BODY$;
''')

cur.execute('''
CREATE OR REPLACE FUNCTION public.releasecomputersonshiftclose()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    -- Обновляем статус занятости компьютеров, связанных с закрываемой сменой
    UPDATE Computer
    SET Busyness = 0
    WHERE id_computer IN (SELECT id_computer FROM Request WHERE id_shift = OLD.id_shift);

    RETURN OLD;
END;
$BODY$;
''')

cur.execute('''
CREATE OR REPLACE FUNCTION public.updateshiftrevenue()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    DECLARE
        totalMoney INT;
    BEGIN
        -- Подсчет суммы для оплаты
        SELECT Cost * NEW.Hours INTO totalMoney FROM Tariff WHERE id_tariff = NEW.id_tariff;

        -- Обновление revenue в таблице shift
        UPDATE shift
        SET revenue = revenue + totalMoney
        WHERE id_shift = NEW.id_shift;

        RETURN NEW;
    END;
END;
$BODY$;
''')

# cur.execute(
#     '''
#     DROP TABLE public.component_type,
#     public.computer,
#     public.computer_component,
#     public.employee,
#     public.request,
#     public.shift,
#     public.client,
#     public.tariff CASCADE;
#     '''
# )

# cur.execute("SELECT * FROM public.tariff")
# pizda = cur.fetchall()
# print(pizda)


# cur.execute('''
# INSERT INTO public.client (birthdate, phone, hours, fio)
# VALUES ('23.12.2003', '9858765432', 0, 'Дёмин Иван Александрович'),
#        ('08.08.2003', '9851234567', 0, 'Хоров Николай Максимович'),
#        ('14.10.2003', '9151655533', 0, 'Абаба Максим Абобович'),
#        ('27.10.2003', '9150981234', 2, 'Дибровенко Ортём Олегович'),
#        ('12.12.2001', '9853451256', 0, 'Койков Максим Игоревич'),
#        ('01.01.2001', '9851234867', 2, 'Абаба Абобович Абобов'),
#        ('02.01.2007', '9857777777', 5, 'абв');
# ''')
#
#
# cur.execute('''
# INSERT INTO public.tariff (cost, description)
# VALUES
#     (250, '250 р/час, компьютер в основном зале'),
#     (500, '500 р/час, VIP компьютер');
# ''')
#
# cur.execute('''
# INSERT INTO public.component_type (id_component, type)
# VALUES (1, 'Видеокарта'),
#        (2, 'Процессор'),
#        (3, 'Оперативная память'),
#        (4, 'Монитор');
# ''')
#
#
# cur.execute('''
# INSERT INTO public.computer (info, busyness, id_tariff)
# VALUES ('Компьютер в основном зале', 0, 1),
#        ('Компьютер в основном зале', 0, 1),
#        ('Компьютер в основном зале', 0, 1),
#        ('Компьютер в основном зале', 0, 1),
#        ('Компьютер в VIP зоне', 0, 2),
#        ('Компьютер в VIP зоне', 0, 2);
# ''')
#
# cur.execute('''
# INSERT INTO computer_component (id_computer, id_component, description)
# VALUES (1, 1, 'RTX 3050 8Gb'),
#        (1, 2, 'Intel Core i5-12400F'),
#        (1, 3, '16 Gb DDR5 5200 MHz'),
#        (1, 4, 'MSI Optix G24C4 144 Hz IPS'),
#        (2, 1, 'RTX 3050 8Gb'),
#        (2, 2, 'Intel Core i5-12400F'),
#        (2, 3, '16 Gb DDR5 5200 MHz'),
#        (2, 4, 'MSI Optix G24C4 144 Hz IPS'),
#        (3, 1, 'RTX 3050 8Gb'),
#        (3, 2, 'Intel Core i5-12400F'),
#        (3, 3, '16 Gb DDR5 5200 MHz'),
#        (3, 4, 'MSI Optix G24C4 144 Hz IPS'),
#        (4, 1, 'RTX 3050 8Gb'),
#        (4, 2, 'Intel Core i5-12400F'),
#        (4, 3, '16 Gb DDR5 5200 MHz'),
#        (4, 4, 'MSI Optix G24C4 144 Hz IPS'),
#        (5, 1, 'RTX 3080 RTX 3080 16Gb'),
#        (5, 2, 'Intel Core i7-12600KF'),
#        (5, 3, '32 Gb DDR5 8000 MHz'),
#        (5, 4, 'MSI Optix G27C4X 265 Hz IPS'),
#        (6, 1, 'RTX 3080 RTX 3080 16Gb'),
#        (6, 2, 'Intel Core i7-12600KF'),
#        (6, 3, '32 Gb DDR5 8000 MHz'),
#        (6, 4, 'MSI Optix G27C4X 265 Hz IPS');
# ''')
#
# cur.execute('''
# INSERT INTO employee (fio, graph_work, birthdate, post, password)
# VALUES ('Дамарад Даниил Васильевич', 'Пн, Ср, Пт, Вс', '21.02.2003', 'Администратор', '123qwerty'),
#        ('Черняков Тимур Максимович', 'Вт, Чт, Сб', '17.04.2003', 'Администратор', '123987m'),
#        ('Шмаков Фёдор Михайлович', 'Пн. Чт, Сб', '01.06.2003', 'Гл. Администратор', 'zxcqwe123');
# ''')
#
# cur.execute('''
# INSERT INTO public.shift (id_employee, date_start, date_end, revenue)
# VALUES
#     (1, '2023-09-01 08:57', '2023-09-01 23:47', 500),
#     (2, '2023-09-02 08:33', '2023-09-02 23:55', 1500),
#     (1, '2023-09-03 08:42', '2023-09-03 23:58', 250),
#     (3, '2023-09-04 08:55', '2023-09-04 23:50', 5000),
#     (2, '2023-09-05 08:57', '2023-11-06 12:01:11.018835+03', 0),
#     (2, '2023-11-06 12:04:39.06372+03', '2023-11-06 12:05:38.344647+03', 1500),
#     (1, '2023-11-06 14:24:58.481993+03', '2023-11-06 14:26:27.012611+03', 500),
#     (2, '2023-11-06 14:37:01.284915+03', '2023-11-06 15:35:40.733097+03', 0),
#     (2, '2023-11-06 15:38:13.459497+03', '2023-11-06 15:38:36.380297+03', 0),
#     (2, '2023-11-06 15:38:58.125576+03', '2023-11-06 15:39:23.721959+03', 1500),
#     (1, '2023-11-06 15:40:08.676142+03', '2023-11-06 15:40:10.676142+03', 0),
#     (2, '2023-11-06 15:40:12.583551+03', '2023-11-06 19:40:12.583551+03', 3000);
# ''')
#
# cur.execute('''
# INSERT INTO request (hours, money, date, id_tariff, id_computer, id_client, id_shift)
# VALUES (2, 500, '01.09.2023', 1, 1, 1, 1),
#        (2, 1000, '02.09.2023', 2, 7, 1, 2),
#        (1, 500, '02.09.2023', 2, 6, 2, 2),
#        (1, 250, '03.09.2023', 1, 3, 5, 3),
#        (10, 2000, '04.09.2023', 2, 7, 4, 4),
#        (3, 1500, '2023-11-06', 2, 7, 3, 6),
#        (2, 500, '2023-11-06', 1, 3, 3, 7),
#        (3, 750, '2023-11-06', 1, 4, 3, 12),
#        (0, 0, '2023-11-06', 1, 1, 6, 12),
#        (0, 0, '2023-11-06', 1, 2, 4, 12),
#        (3, 0, '2023-11-13', 1, 3, 1, 12);
# ''')

# cur.execute('''
# DELETE FROM public.request
# ''')
# cur.execute('''
# DELETE FROM public.shift
# ''')
# cur.execute('''
# DELETE FROM public.employee
# ''')
# cur.execute('''
# DELETE FROM public.computer_component
# ''')
# cur.execute('''
# DELETE FROM public.computer
# ''')
# cur.execute('''
# DELETE FROM public.tariff
# ''')
# cur.execute('''
# DELETE FROM public.component_type
# ''')



# Commit the transaction
conn.commit()

# Close the cursor and connection
cur.close()
conn.close()

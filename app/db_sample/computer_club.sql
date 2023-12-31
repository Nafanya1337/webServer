PGDMP  )    &            
    {            computer_club    15.5    16.1 A    N           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            O           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            P           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            Q           1262    16398    computer_club    DATABASE     �   CREATE DATABASE computer_club WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Russian_Russia.1251';
    DROP DATABASE computer_club;
                postgres    false            �            1255    19263 I   adduserwithhours(character varying, character varying, character varying) 	   PROCEDURE       CREATE PROCEDURE public.adduserwithhours(IN p_phone character varying, IN p_fio character varying, IN p_birthday character varying, OUT resulttext text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    clientID INT;
BEGIN
	-- Если клиент с указанным номером не существует, добавляем нового клиента
	INSERT INTO Client (Birthdate, Phone, Hours, FIO)
	VALUES (p_birthday, p_phone, 5, p_fio);
	resultText := 'Новый клиент добавлен.';
END;
$$;
 �   DROP PROCEDURE public.adduserwithhours(IN p_phone character varying, IN p_fio character varying, IN p_birthday character varying, OUT resulttext text);
       public          postgres    false            �            1255    19264     before_delete_computer_trigger()    FUNCTION     �  CREATE FUNCTION public.before_delete_computer_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;
 7   DROP FUNCTION public.before_delete_computer_trigger();
       public          postgres    false            �            1255    19265    check_duplicate_phone_number()    FUNCTION     �  CREATE FUNCTION public.check_duplicate_phone_number() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;
 5   DROP FUNCTION public.check_duplicate_phone_number();
       public          postgres    false            �            1255    19266    closelastshift()    FUNCTION     �  CREATE FUNCTION public.closelastshift() RETURNS text
    LANGUAGE plpgsql
    AS $$
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
$$;
 '   DROP FUNCTION public.closelastshift();
       public          postgres    false            �            1255    19267    delete_computer_by_id(integer)    FUNCTION       CREATE FUNCTION public.delete_computer_by_id(p_computer_id integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    DELETE FROM public.computer_component
    WHERE id_computer = p_computer_id;
    DELETE FROM public.Computer
    WHERE id_computer = p_computer_id;
END;
$$;
 C   DROP FUNCTION public.delete_computer_by_id(p_computer_id integer);
       public          postgres    false            �            1255    19559    openshift(integer)    FUNCTION       CREATE FUNCTION public.openshift(employeeid integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    lastShiftID INT;
    shiftStart VARCHAR(64);
    shiftEnd VARCHAR(64);
BEGIN
    SELECT id_shift, date_start, date_end
    INTO lastShiftID, shiftStart, shiftEnd
    FROM shift
    WHERE id_employee = employeeID AND date_end IS NULL
    ORDER BY date_start DESC
    LIMIT 1;
    IF lastShiftID IS NOT NULL THEN
        -- Здесь можно добавить код для логирования сообщения, если нужно
        -- например, INSERT INTO log_table (log_message) VALUES ('Нельзя начать новую смену, если предыдущая не завершена.');
        RETURN -1;
    ELSE
        INSERT INTO shift (id_employee, date_start, date_end, revenue)
        VALUES (employeeID, NOW(), NULL, 0);
    END IF;
	SELECT id_shift
    INTO lastShiftID
    FROM shift
    WHERE date_end IS NULL
    ORDER BY date_start DESC
    LIMIT 1;
    RETURN lastShiftID;
END;
$$;
 4   DROP FUNCTION public.openshift(employeeid integer);
       public          postgres    false            �            1255    19269    releasecomputersonshiftclose()    FUNCTION     �  CREATE FUNCTION public.releasecomputersonshiftclose() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Обновляем статус занятости компьютеров, связанных с закрываемой сменой
    UPDATE Computer
    SET Busyness = 0
    WHERE id_computer IN (SELECT id_computer FROM Request WHERE id_shift = OLD.id_shift);

    RETURN OLD;
END;
$$;
 5   DROP FUNCTION public.releasecomputersonshiftclose();
       public          postgres    false            �            1255    19270 *   reservecomputer(integer, integer, integer)    FUNCTION     �  CREATE FUNCTION public.reservecomputer(clientid integer, tariffid integer, reservehours integer) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    totalMoney INT;
    computerID INT;
    resultText TEXT;
    clientRemainingHours INT;
	shiftID INT;
BEGIN
	SELECT id_shift INTO shiftID FROM shift WHERE date_end IS NULL;
	
	IF shiftID IS NULL THEN
        resultText := 'Нет действующих смен';
        RETURN resultText;
    END IF;
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
$$;
 `   DROP FUNCTION public.reservecomputer(clientid integer, tariffid integer, reservehours integer);
       public          postgres    false            �            1255    19271    updateshiftrevenue()    FUNCTION     �  CREATE FUNCTION public.updateshiftrevenue() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;
 +   DROP FUNCTION public.updateshiftrevenue();
       public          postgres    false            �            1259    19272    client    TABLE     �   CREATE TABLE public.client (
    id_client integer NOT NULL,
    birthdate character varying(10) NOT NULL,
    phone character varying(10) NOT NULL,
    hours integer NOT NULL,
    fio character varying(50) NOT NULL
);
    DROP TABLE public.client;
       public         heap    postgres    false            �            1259    19275    client_id_client_seq    SEQUENCE     �   ALTER TABLE public.client ALTER COLUMN id_client ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.client_id_client_seq
    START WITH 6
    INCREMENT BY 1
    MINVALUE 6
    MAXVALUE 999
    CACHE 1
);
            public          postgres    false    214            �            1259    19276    component_type    TABLE     j   CREATE TABLE public.component_type (
    id_component integer NOT NULL,
    type character varying(64)
);
 "   DROP TABLE public.component_type;
       public         heap    postgres    false            �            1259    19279    computer    TABLE     �   CREATE TABLE public.computer (
    id_computer integer NOT NULL,
    info character varying(64) NOT NULL,
    busyness integer NOT NULL,
    id_tariff integer
);
    DROP TABLE public.computer;
       public         heap    postgres    false            �            1259    19282    computer_component    TABLE     �   CREATE TABLE public.computer_component (
    id_computer integer NOT NULL,
    id_component integer NOT NULL,
    description character(64)
);
 &   DROP TABLE public.computer_component;
       public         heap    postgres    false            �            1259    19285    computer_id_computer_seq    SEQUENCE     �   ALTER TABLE public.computer ALTER COLUMN id_computer ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.computer_id_computer_seq
    START WITH 8
    INCREMENT BY 1
    MINVALUE 8
    MAXVALUE 99
    CACHE 1
);
            public          postgres    false    217            �            1259    19286    employee    TABLE     D  CREATE TABLE public.employee (
    id_employee integer NOT NULL,
    fio character varying(50) NOT NULL,
    graph_work character varying(28) NOT NULL,
    birthdate character varying(10) NOT NULL,
    post character varying(32) NOT NULL,
    password character varying(16) DEFAULT '123cisco'::character varying NOT NULL
);
    DROP TABLE public.employee;
       public         heap    postgres    false            �            1259    19290    employee_id_employee_seq    SEQUENCE     �   ALTER TABLE public.employee ALTER COLUMN id_employee ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.employee_id_employee_seq
    START WITH 4
    INCREMENT BY 1
    MINVALUE 4
    MAXVALUE 99
    CACHE 1
);
            public          postgres    false    220            �            1259    19291    public.request_id_request_seq    SEQUENCE     �   CREATE SEQUENCE public."public.request_id_request_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 6   DROP SEQUENCE public."public.request_id_request_seq";
       public          postgres    false            �            1259    19292    request    TABLE     #  CREATE TABLE public.request (
    id_request integer NOT NULL,
    hours integer NOT NULL,
    money integer NOT NULL,
    date character varying(32) NOT NULL,
    id_tariff integer NOT NULL,
    id_computer integer NOT NULL,
    id_client integer NOT NULL,
    id_shift integer NOT NULL
);
    DROP TABLE public.request;
       public         heap    postgres    false            �            1259    19295    request_id_request_seq    SEQUENCE        CREATE SEQUENCE public.request_id_request_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.request_id_request_seq;
       public          postgres    false            �            1259    19296    request_id_request_seq1    SEQUENCE     �   ALTER TABLE public.request ALTER COLUMN id_request ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.request_id_request_seq1
    START WITH 6
    INCREMENT BY 1
    MINVALUE 6
    MAXVALUE 99
    CACHE 1
);
            public          postgres    false    223            �            1259    19297    shift    TABLE     �   CREATE TABLE public.shift (
    id_shift integer NOT NULL,
    id_employee integer NOT NULL,
    date_start character varying(64) NOT NULL,
    date_end character varying(64),
    revenue integer NOT NULL
);
    DROP TABLE public.shift;
       public         heap    postgres    false            �            1259    19300    shift_id_shift_seq    SEQUENCE     �   ALTER TABLE public.shift ALTER COLUMN id_shift ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.shift_id_shift_seq
    START WITH 13
    INCREMENT BY 1
    MINVALUE 13
    MAXVALUE 99
    CACHE 1
);
            public          postgres    false    226            �            1259    19301    tariff    TABLE     �   CREATE TABLE public.tariff (
    id_tariff integer NOT NULL,
    cost integer NOT NULL,
    description character varying(50) NOT NULL
);
    DROP TABLE public.tariff;
       public         heap    postgres    false            �            1259    19304    tariff_id_tariff_seq    SEQUENCE     �   ALTER TABLE public.tariff ALTER COLUMN id_tariff ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tariff_id_tariff_seq
    START WITH 3
    INCREMENT BY 1
    MINVALUE 3
    MAXVALUE 9
    CACHE 1
);
            public          postgres    false    228            <          0    19272    client 
   TABLE DATA                 public          postgres    false    214   �a       >          0    19276    component_type 
   TABLE DATA                 public          postgres    false    216   {c       ?          0    19279    computer 
   TABLE DATA                 public          postgres    false    217   6d       @          0    19282    computer_component 
   TABLE DATA                 public          postgres    false    218   e       B          0    19286    employee 
   TABLE DATA                 public          postgres    false    220   Bf       E          0    19292    request 
   TABLE DATA                 public          postgres    false    223   �g       H          0    19297    shift 
   TABLE DATA                 public          postgres    false    226   bi       J          0    19301    tariff 
   TABLE DATA                 public          postgres    false    228   Ak       R           0    0    client_id_client_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.client_id_client_seq', 15, true);
          public          postgres    false    215            S           0    0    computer_id_computer_seq    SEQUENCE SET     G   SELECT pg_catalog.setval('public.computer_id_computer_seq', 8, false);
          public          postgres    false    219            T           0    0    employee_id_employee_seq    SEQUENCE SET     G   SELECT pg_catalog.setval('public.employee_id_employee_seq', 4, false);
          public          postgres    false    221            U           0    0    public.request_id_request_seq    SEQUENCE SET     N   SELECT pg_catalog.setval('public."public.request_id_request_seq"', 1, false);
          public          postgres    false    222            V           0    0    request_id_request_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.request_id_request_seq', 1, true);
          public          postgres    false    224            W           0    0    request_id_request_seq1    SEQUENCE SET     F   SELECT pg_catalog.setval('public.request_id_request_seq1', 22, true);
          public          postgres    false    225            X           0    0    shift_id_shift_seq    SEQUENCE SET     A   SELECT pg_catalog.setval('public.shift_id_shift_seq', 14, true);
          public          postgres    false    227            Y           0    0    tariff_id_tariff_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.tariff_id_tariff_seq', 3, false);
          public          postgres    false    229            �           2606    19306    client client_pkey 
   CONSTRAINT     W   ALTER TABLE ONLY public.client
    ADD CONSTRAINT client_pkey PRIMARY KEY (id_client);
 <   ALTER TABLE ONLY public.client DROP CONSTRAINT client_pkey;
       public            postgres    false    214            �           2606    19308 "   component_type component_type_pkey 
   CONSTRAINT     j   ALTER TABLE ONLY public.component_type
    ADD CONSTRAINT component_type_pkey PRIMARY KEY (id_component);
 L   ALTER TABLE ONLY public.component_type DROP CONSTRAINT component_type_pkey;
       public            postgres    false    216            �           2606    19310 *   computer_component computer_component_pkey 
   CONSTRAINT        ALTER TABLE ONLY public.computer_component
    ADD CONSTRAINT computer_component_pkey PRIMARY KEY (id_computer, id_component);
 T   ALTER TABLE ONLY public.computer_component DROP CONSTRAINT computer_component_pkey;
       public            postgres    false    218    218            �           2606    19312    computer computer_pkey 
   CONSTRAINT     ]   ALTER TABLE ONLY public.computer
    ADD CONSTRAINT computer_pkey PRIMARY KEY (id_computer);
 @   ALTER TABLE ONLY public.computer DROP CONSTRAINT computer_pkey;
       public            postgres    false    217            �           2606    19314    employee employee_pkey 
   CONSTRAINT     ]   ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_pkey PRIMARY KEY (id_employee);
 @   ALTER TABLE ONLY public.employee DROP CONSTRAINT employee_pkey;
       public            postgres    false    220            �           2606    19316    request request_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.request
    ADD CONSTRAINT request_pkey PRIMARY KEY (id_request);
 >   ALTER TABLE ONLY public.request DROP CONSTRAINT request_pkey;
       public            postgres    false    223            �           2606    19318    shift shift_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.shift
    ADD CONSTRAINT shift_pkey PRIMARY KEY (id_shift);
 :   ALTER TABLE ONLY public.shift DROP CONSTRAINT shift_pkey;
       public            postgres    false    226            �           2606    19320    tariff tariff_pkey 
   CONSTRAINT     W   ALTER TABLE ONLY public.tariff
    ADD CONSTRAINT tariff_pkey PRIMARY KEY (id_tariff);
 <   ALTER TABLE ONLY public.tariff DROP CONSTRAINT tariff_pkey;
       public            postgres    false    228            �           2620    19321    computer before_delete_computer    TRIGGER     �   CREATE TRIGGER before_delete_computer BEFORE DELETE ON public.computer FOR EACH ROW EXECUTE FUNCTION public.before_delete_computer_trigger();
 8   DROP TRIGGER before_delete_computer ON public.computer;
       public          postgres    false    217    246            �           2620    19322 $   client check_duplicate_phone_trigger    TRIGGER     �   CREATE TRIGGER check_duplicate_phone_trigger BEFORE INSERT OR UPDATE ON public.client FOR EACH ROW EXECUTE FUNCTION public.check_duplicate_phone_number();
 =   DROP TRIGGER check_duplicate_phone_trigger ON public.client;
       public          postgres    false    247    214            �           2620    19323 "   shift releasecomputersonshiftclose    TRIGGER     �   CREATE TRIGGER releasecomputersonshiftclose AFTER UPDATE ON public.shift FOR EACH ROW WHEN (((new.date_end IS NOT NULL) AND (old.date_end IS NULL))) EXECUTE FUNCTION public.releasecomputersonshiftclose();
 ;   DROP TRIGGER releasecomputersonshiftclose ON public.shift;
       public          postgres    false    226    243    226            �           2620    19324 !   request updateshiftrevenuetrigger    TRIGGER     �   CREATE TRIGGER updateshiftrevenuetrigger BEFORE INSERT ON public.request FOR EACH ROW EXECUTE FUNCTION public.updateshiftrevenue();
 :   DROP TRIGGER updateshiftrevenuetrigger ON public.request;
       public          postgres    false    244    223            �           2606    19325    computer fk_tariff    FK CONSTRAINT     {   ALTER TABLE ONLY public.computer
    ADD CONSTRAINT fk_tariff FOREIGN KEY (id_tariff) REFERENCES public.tariff(id_tariff);
 <   ALTER TABLE ONLY public.computer DROP CONSTRAINT fk_tariff;
       public          postgres    false    3233    217    228            �           2606    19330    computer_component r_10    FK CONSTRAINT     �   ALTER TABLE ONLY public.computer_component
    ADD CONSTRAINT r_10 FOREIGN KEY (id_component) REFERENCES public.component_type(id_component);
 A   ALTER TABLE ONLY public.computer_component DROP CONSTRAINT r_10;
       public          postgres    false    3221    216    218            �           2606    19335 
   shift r_13    FK CONSTRAINT     y   ALTER TABLE ONLY public.shift
    ADD CONSTRAINT r_13 FOREIGN KEY (id_employee) REFERENCES public.employee(id_employee);
 4   ALTER TABLE ONLY public.shift DROP CONSTRAINT r_13;
       public          postgres    false    226    3227    220            �           2606    19340    request r_14    FK CONSTRAINT     r   ALTER TABLE ONLY public.request
    ADD CONSTRAINT r_14 FOREIGN KEY (id_shift) REFERENCES public.shift(id_shift);
 6   ALTER TABLE ONLY public.request DROP CONSTRAINT r_14;
       public          postgres    false    3231    226    223            �           2606    19345    request r_3    FK CONSTRAINT     t   ALTER TABLE ONLY public.request
    ADD CONSTRAINT r_3 FOREIGN KEY (id_tariff) REFERENCES public.tariff(id_tariff);
 5   ALTER TABLE ONLY public.request DROP CONSTRAINT r_3;
       public          postgres    false    3233    228    223            �           2606    19350    request r_4    FK CONSTRAINT     z   ALTER TABLE ONLY public.request
    ADD CONSTRAINT r_4 FOREIGN KEY (id_computer) REFERENCES public.computer(id_computer);
 5   ALTER TABLE ONLY public.request DROP CONSTRAINT r_4;
       public          postgres    false    217    223    3223            �           2606    19355    request r_8    FK CONSTRAINT     t   ALTER TABLE ONLY public.request
    ADD CONSTRAINT r_8 FOREIGN KEY (id_client) REFERENCES public.client(id_client);
 5   ALTER TABLE ONLY public.request DROP CONSTRAINT r_8;
       public          postgres    false    223    3219    214            �           2606    19360    computer_component r_9    FK CONSTRAINT     �   ALTER TABLE ONLY public.computer_component
    ADD CONSTRAINT r_9 FOREIGN KEY (id_computer) REFERENCES public.computer(id_computer);
 @   ALTER TABLE ONLY public.computer_component DROP CONSTRAINT r_9;
       public          postgres    false    3223    218    217            <   �  x����j�@�Oqv*H��dr��B�Z�BW�[1 *V���n-�(���{���g8y����U Ð�L6_~�7W�J��Jy��-���Z^�݇�W��-3P�z�f��od������z��:iȗ���{��.�x[,e��|~u��=���H
]�B��I�9��-S����/�����7N�b�k���T[�񇸥O�9�>K�1�u�qC���%7����G8%�'���T�n`3Y*���aֺ!��fD~#�W�v�~�n)�y�hA*fk4
�b�V��
`���J�&����N�Tp��<H[�� .N
�&��"����f���yLYN�v�S�Q؀���R]Jˠ1gq�m��E���m��T�W �_�\]m��h�	H,!I]a��&3������e�*S��?l�)%      >   �   x���v
Q���W((M��L�K��-��K�+�/�,HU��L���(��4�}B]�4u�/L���[/컰���.lP״���h#���/6\�w���֋���*l2xޅ�@C��m�~Ӆ�@V�PpÅ=�/6]졂M& �� �e�@{���� 7��      ?   �   x���v
Q���W((M��L�K��-(-I-R��L��qt2���u�J�+�R�������Ģ̴4M�0נ OO?w����W_�0G�PW��a���~aօ}�\���b�Ŧ[/6(\ؤpa���{�2�����/l����VuCMk.Oz��xл�hл�dл���<@��t�QF�r����� �v�K      @   '  x���Ak�0���ق1���Ӱ]��Cm�P�A�T���O�tlcl�Yx������E�Ȧi�ȗh��CU\�c{��n{�i��1��ۏ��o[��S�Um_5�����4�( ���`i��1�2�����C�_�?��BaC���I!�an��BnMݗ$MW��.B.��Sh/?�7,b���<c��PH�+s�'�����y���CAޡ$�P�w(�;����c�P��m�w��:T������P�O�1��P�t��W��5y���CMޡ�;���
���      B   `  x�ő_K�`����N�1�,�
1(gAW⟕#ekfWӈn�ʺ���Da��3��:���N���y���=GOZ:z2��2_�
�Yq�v�4!b�˅��-���sJٺ�K���Z�������k�Ze��Ա�N�{zr�#�������P"1	���}�b�<�!X���k���M�H�8��t�tp&v�c�P��MM�1YQeUQ���G�پ8�������nL�_�M��GwB�Z
PE��8،p�s �q�)ݐ��m��
���)�@���g�������oo%*����b�K�wz����O��|�dz1�h������F��*�Թ 
}�K�      E   �  x�͕�n�0��<�� 5X�񖸧JEU�$�H=U]���}�:6�ЦwK��,�����p2�|4���,�خ�<�
z���q�����'�ڬ���_�"��zٕ��_�mV�CU��ò,֕_�?�EՇ�|8�����O����7���0O��	P����q��4�ם<\��/5x�k�y)&^�T+��sT�2���2NE�9&\UG��� ����Ș�S���P�\��ʒbFc������:&���0�Ғ�.�ZaBj�01ԑ���oe%9�L�g-�BŰ�-�b�R��1'��&2��@q�]dg����h�
@aej]�T���(�́xK9�;��;��T?)�B��-@G.�.A�$jI��::�P"�����3 sr�����:�o��@      H   �  x�ŖMk�@���{sB�e>v���BM��n����*5�iH�B�}g+,K�v/b5zA��ywV�z���L��]�Ǘ���/������\��V��U����ǯ�k�����>ú{�7���=�t���f�ٴo��;���ݭ>��7�?����\��pc��,$K@l f��F��& p�z��gH%�ħ����Z��Z#��H���C����q�0sQ����8�vX�k
�B��
�2)S�rw�x� e��
�1����t\�㞡��ɂ�@=��s�-;�]���@�ҹLN7�uS�|�LA�'����ǩ�j|�dX�.��Ы���)��M���Pdd�$��hS{��&;�?�56H"��çLla�T5���ؓ���K����N�}>�*���)^�Y��#�~P�J|�u��t�M�!Z<�����HP��¯lHV�(���hF����b����4      J   �   x���v
Q���W((M��L�+I,�LKS��L��0u��KtRR���2J2��4��\��<]<���#�C\}�}B]!d�����������:�T�ؠ����:
a�
v]�waυ�{.�]l���b���5�'��b��`d
r
�Dv
�3.lR���bㅽ@�M`r��6\�}a+ȍ\\ �zy�     
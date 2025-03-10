from db import *

# Отображение страницы входа
@app.route("/")
def login():
        return render_template("login.html")

# Функция проверки логина
@app.route("/", methods=["POST"])
def check_login():
    login = request.form["login"]
    password = request.form["password"]
    with Session() as db_session:  
        cashier = db_session.query(User).filter(User.login == login, User.password == password).first()
        if cashier:
            # Сохранение данных в сессии
            session["login"] = login
            session["password"] = password
            session["cashier_id"] = cashier.cass_id
            return redirect(url_for("exchange"))
        else:
            return "Пароль або логін введено невірно"

@app.route("/logout")
def logout():
    # Очистка данных сессии
    session.clear()
    return redirect(url_for("login"))

# Страница обмена
@app.route("/exchange")
def exchange():
    # Получение данных из сессии
    login = session.get("login")
    password = session.get("password")
    cashier_id = session.get("cashier_id")
    if login and password and cashier_id:
        # Использование данных для рендеринга шаблона
        with Session() as db_session:
            balances = db_session.query(Balance.currency, Balance.balance).join(Balance.user).filter(
                User.login == login, User.password == password).all()
            courses = db_session.query(Course.currency, Course.buy_rate, Course.sell_rate).filter(
                Course.cass_id == cashier_id).all()
            sell_transactions = db_session.query(SellTransaction).filter(
                SellTransaction.cass_id == cashier_id,
                SellTransaction.date >= func.now() - timedelta(minutes=15)
                ).order_by(SellTransaction.date.desc()).all()
            return render_template("exchange.html", balances=balances, courses=courses, sell_transactions=sell_transactions, cashier_number=cashier_id)
    else:
        return "Error of logining/ CODE 1"

# Обновление таблицы balances после продажи валюты
def update_balances_after_sell(cass_id, currency, amount, total_amount):
    with Session() as db_session:  # Відкриття нової сесії
        currency_balance = db_session.query(Balance).filter_by(cass_id=cass_id, currency=currency).first()
        uah_balance = db_session.query(Balance).filter_by(cass_id=cass_id, currency='UAH').first()

        if currency_balance and uah_balance:
            currency_balance.balance -= amount
            uah_balance.balance += total_amount

            # Отдельный сеанс для коммита
            try:
                db_session.commit()

                return True
            except Exception as e:
                db_session.rollback()
                return False

        return False


# Обновление таблицы balances после покупки валюты
def update_balances_after_buy(cass_id, currency, amount, total_amount):
    with Session() as db_session:  # Відкриття нової сесії
        currency_balance = db_session.query(Balance).filter_by(cass_id=cass_id, currency=currency).first()
        uah_balance = db_session.query(Balance).filter_by(cass_id=cass_id, currency='UAH').first()

        if currency_balance and uah_balance:
            currency_balance.balance += amount
            uah_balance.balance -= total_amount

            # Отдельный сеанс для коммита
            try:
                db_session.commit()

                return True
            except Exception as e:
                db_session.rollback()
                return False

        return False


# Добавление записи в таблицу операций после продажи валюты
def add_transaction_sell(date, cass_id, currency, amount, total_amount, rate):
    with Session() as db_session:  # Відкриття нової сесії
        transaction = SellTransaction(date=date, cass_id=cass_id, currency=currency, amount=amount, total_amount=total_amount, operation_type='Продаж', rate=rate)
        db_session.add(transaction)
        db_session.commit()

#Добавление записи после покупки
def add_transaction_buy(date, cass_id, currency, amount, total_amount, rate):
    with Session() as db_session:  # Відкриття нової сесії
        transaction = SellTransaction(date=date, cass_id=cass_id, currency=currency, amount=amount, total_amount=total_amount, operation_type='Купівля', rate=rate)
        db_session.add(transaction)
        db_session.commit()


# Обработка кнопки продать валюту
@app.route("/sell", methods=["POST"])
def sell_currency():
    data = request.get_json()
    currency = data.get('currency')
    amount = data.get('amount')
    rate = data.get('rate')
    total_amount = data.get('totalAmount')
    cashier_number = data.get('cashier_number')

    if currency is None or amount is None or total_amount is None or cashier_number is None:
        return jsonify({'success': False, 'message': 'Недостатньо даних для продажу валюти'})

    cass_id = int(cashier_number)
    try:
        amount = float(amount)
        total_amount = float(total_amount)
        if amount <= 0 or total_amount <= 0:
            return jsonify({'success': False, 'message': 'Некоректні дані для продажу валюти'})

        with Session() as db_session:  # Відкриття нової сесії
            # Проверка наличия достаточного баланса для продажи валюты
            balance = db_session.query(Balance).filter(
                Balance.cass_id == cass_id,
                Balance.currency == currency
            ).first()
            if balance is None or balance.balance < amount:
                return jsonify({'success': False, 'message': 'Недостатній баланс для продажу валюти'})

            if update_balances_after_sell(cass_id, currency, amount, total_amount):
                date = datetime.now()
                add_transaction_sell(date, cass_id, currency, amount, total_amount, rate)
                return jsonify({'success': True, 'message': 'Валюта успішно продана'})
            else:
                return jsonify({'success': False, 'message': 'Не вдалося оновити баланс після продажу валюти'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Некоректні дані для продажу валюти'})

#Переходник на страницу истории
@app.route("/history", methods=["GET"])
def history():
    cashier_id = session.get("cashier_id")
    with Session() as db_session:
        sell_transactions = db_session.query(SellTransaction).filter(
            SellTransaction.cass_id == cashier_id).order_by(SellTransaction.date.desc()).limit(20).all()
        return render_template("history.html", sell_transactions=sell_transactions, cashier_number=cashier_id)

#Переходник на страницу инкасации
@app.route("/incasation", methods=["GET"])
def incasation_page():
    cashier_id = session.get("cashier_id")
    with Session() as db_session:
        balances = db_session.query(Balance.currency, Balance.balance).join(Balance.user).filter(User.cass_id == cashier_id).all()
        recent_transactions = db_session.query(OperationHistory).filter(OperationHistory.cass_id == cashier_id).order_by(OperationHistory.data.desc()).limit(20).all()
        return render_template("incasation.html", balances=balances, cashier_number=cashier_id,recent_transactions=recent_transactions)

@app.route("/print/<int:transaction_id>", methods=["GET"])
def print_transaction(transaction_id):
    cashier_id = session.get("cashier_id")
    try:
        transaction_id = int(transaction_id)
        with Session() as db_session:
            transaction = (
                db_session.query(SellTransaction)
                .filter(SellTransaction.id == transaction_id)
                .first()
            )
            transaction_dict = {
                'operation_type': transaction.operation_type,
                'currency': transaction.currency,
                'amount': transaction.amount,
                'total_amount': transaction.total_amount,
                'rate': transaction.rate
            }

        return render_template("check.html", transaction=transaction_dict, cashier_number=cashier_id)
    except Exception as e:
        return "Error formatting check"



#Обработчик кнопки купить
@app.route("/buy", methods=["POST"])
def buy_currency():
    data = request.get_json()
    currency = data.get('currency')
    amount = data.get('amount')
    rate = data.get('rate')
    total_amount = data.get('totalAmount')
    cashier_number = data.get('cashier_number')

    if currency is None or amount is None or total_amount is None or cashier_number is None:
        return jsonify({'success': False, 'message': 'Недостатньо даних для купівлі валюти'})

    cass_id = int(cashier_number)
    try:
        amount = float(amount)
        total_amount = float(total_amount)
        if amount <= 0 or total_amount <= 0:
            return jsonify({'success': False, 'message': 'Некоректні дані для купівлі валюти'})

        with Session() as db_session:  # Відкриття нової сесії
            # Проверка наличия достаточного баланса для продажи валюты
            balance = db_session.query(Balance).filter(
                Balance.cass_id == cass_id,
                Balance.currency == 'UAH'
            ).first()
            if balance is None or balance.balance < total_amount:
                return jsonify({'success': False, 'message': 'Недостатній баланс для купівлі валюти'})

            if update_balances_after_buy(cass_id, currency, amount, total_amount):
                date = datetime.now()
                add_transaction_buy(date, cass_id, currency, amount, total_amount, rate)
                return jsonify({'success': True, 'message': 'Валюта успішно куплена'})
            else:
                return jsonify({'success': False, 'message': 'Не вдалося оновити баланс після купівлі валюти'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Некоректні дані для купівлі валюти'})


# Оновлення таблиці балансів для каси після операції
@app.route("/update_balances/<int:cass_id>", methods=["GET"])
def update_balances(cass_id):
    with Session() as db_session:  # Відкриття нової сесії
        balances = db_session.query(Balance).filter_by(cass_id=cass_id).all()
        balances_data = [{"currency": balance.currency, "balance": balance.balance} for balance in balances]
        return jsonify(balances_data)

# Отримання списку операцій за останні 15 хвилин для даної каси
@app.route("/transactions", methods=["GET"])
def get_recent_transactions():
    cass_id = request.args.get("cass_id")
    if cass_id is not None:
        cass_id = int(cass_id)
    with Session() as db_session:  # Відкриття нової сесії
        recent_transactions = db_session.query(SellTransaction).filter(
            SellTransaction.cass_id == cass_id,
            SellTransaction.date >= func.now() - timedelta(minutes=15)
        ).order_by(SellTransaction.date.desc()).all()

        transactions = []
        for transaction in recent_transactions:
            transactions.append({
                "id": transaction.id,
                "date": transaction.date.strftime("%Y-%m-%d %H:%M:%S"),
                "cass_id": transaction.cass_id,
                "currency": transaction.currency,
                "amount": transaction.amount,
                "rate": transaction.rate,
                "total_amount": transaction.total_amount,
                "operation_type": transaction.operation_type
            })

        return jsonify(transactions)
    

# Обработка кнопки подкреп валюту
@app.route("/adding", methods=["POST"])
def adding():
    data = request.get_json()
    currency = data.get('currency')
    amount = data.get('amount')
    cashier_number = data.get('cashier_number')

    if currency is None or amount is None or cashier_number is None:
        return jsonify({'success': False, 'message': 'Недостатньо даних для підкріплення валюти'})

    cass_id = int(cashier_number)
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Некоректні дані для підкріплення валюти'})

        with Session() as db_session:  # Відкриття нової сесії
            if update_balances_after_add(cass_id, currency, amount):
                date = datetime.now()
                add_operation_add(date, cass_id, currency, amount)
                return jsonify({'success': True, 'message': 'Валюта успішно підкріплена'})
            else:
                return jsonify({'success': False, 'message': 'Не вдалося оновити баланс після підкріплення валюти'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Некоректні дані для підкріплення валюти'})

# Обработка кнопки инкасация валюту
@app.route("/incas", methods=["POST"])
def incasation():
    data = request.get_json()
    currency = data.get('currency')
    amount = data.get('amount')
    cashier_number = data.get('cashier_number')

    if currency is None or amount is None or cashier_number is None:
        return jsonify({'success': False, 'message': 'Недостатньо даних для інкасації валюти'})

    cass_id = int(cashier_number)
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Некоректні дані для інкасації валюти'})

        with Session() as db_session:  # Відкриття нової сесії
            # Проверка наличия достаточного баланса для продажи валюты
            balance = db_session.query(Balance).filter(
                Balance.cass_id == cass_id,
                Balance.currency == currency
            ).first()
            if balance is None or balance.balance < amount:
                return jsonify({'success': False, 'message': 'Недостатній баланс для інкасації валюти'})
            
            if update_balances_after_incasation(cass_id, currency, amount):
                date = datetime.now()
                add_operation_incasation(date, cass_id, currency, amount)
                return jsonify({'success': True, 'message': 'Валюта успішно інкасована'})
            else:
                return jsonify({'success': False, 'message': 'Не вдалося оновити баланс після інкасації валюти'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Некоректні дані для інкасації валюти'})

# Добавление записи в таблицу операций после подкреп валюты
def add_operation_add(date, cass_id, currency, amount):
    with Session() as db_session:  # Відкриття нової сесії
        balance = db_session.query(Balance).filter_by(cass_id=cass_id, currency=currency).first()
        total_amount = balance.balance if balance else 0.0  # Получить числовое значение баланса
        transaction = OperationHistory(data=date, cass_id=cass_id, currency=currency, amount=amount, total_amount=total_amount, operation_type='Підкріплення')
        db_session.add(transaction)
        db_session.commit()

# Добавление записи в таблицу операций после инкачации валюты
def add_operation_incasation(date, cass_id, currency, amount):
    with Session() as db_session:  # Відкриття нової сесії
        balance = db_session.query(Balance).filter_by(cass_id=cass_id, currency=currency).first()
        total_amount = balance.balance if balance else 0.0  # Получить числовое значение баланса
        transaction = OperationHistory(data=date, cass_id=cass_id, currency=currency, amount=amount, total_amount=total_amount, operation_type='Інкасація')
        db_session.add(transaction)
        db_session.commit()

# Обновление таблицы balances после подкреп валюты
def update_balances_after_incasation(cass_id, currency, amount):
    with Session() as db_session:  # Відкриття нової сесії
        currency_balance = db_session.query(Balance).filter_by(cass_id=cass_id, currency=currency).first()
        

        if currency_balance:
            currency_balance.balance -= amount
            # Отдельный сеанс для коммита
            try:
                db_session.commit()

                return True
            except Exception as e:
                db_session.rollback()
                return False

        return False

# Обновление таблицы balances после подкреп валюты
def update_balances_after_add(cass_id, currency, amount):
    with Session() as db_session:  # Відкриття нової сесії
        currency_balance = db_session.query(Balance).filter_by(cass_id=cass_id, currency=currency).first()
        

        if currency_balance:
            currency_balance.balance += amount
            # Отдельный сеанс для коммита
            try:
                db_session.commit()

                return True
            except Exception as e:
                db_session.rollback()
                return False

        return False

#Получения списка подкреп/инкас
@app.route("/incasationget", methods=["GET"])
def incasation_get():
    cass_id = request.args.get("cass_id")
    if cass_id is not None:
        cass_id = int(cass_id)
    with Session() as db_session:  # Відкриття нової сесії
        recent_transactions = db_session.query(OperationHistory).filter(OperationHistory.cass_id == cass_id).order_by(
            OperationHistory.data.desc()).all()

        transactions = []
        for transaction in recent_transactions:
            transactions.append({
                "date": transaction.data.strftime("%Y-%m-%d %H:%M:%S"),
                "cass_id": transaction.cass_id,
                "currency": transaction.currency,
                "amount": transaction.amount,
                "total_amount": transaction.total_amount,
                "operation_type": transaction.operation_type
            })

        return jsonify(transactions)

#Обработчик отмены транзакции
def cancel_transaction(transaction_id):
    try:
        transaction_id = int(transaction_id)
        with Session() as db_session:  # Відкриття нової сесії
            transaction = db_session.query(SellTransaction).get(transaction_id)
            if transaction:
                # Перевірка часу проведення операції
                current_time = datetime.now()
                time_diff = current_time - transaction.date
                if time_diff.total_seconds() <= 900:  # 15 хвилин в секундах
                    # Отримання балансу каси до операції
                    currency_balance = db_session.query(Balance).filter_by(cass_id=transaction.cass_id, currency=transaction.currency).first()
                    uah_balance = db_session.query(Balance).filter_by(cass_id=transaction.cass_id, currency='UAH').first()

                    if currency_balance and uah_balance:
                        if transaction.operation_type == "Продаж":
                            # Суми, що повертаються після скасування операції Продаж
                            currency_balance.balance += transaction.amount
                            uah_balance.balance -= transaction.total_amount
                        elif transaction.operation_type == "Купівля":
                            # Суми, що повертаються після скасування операції Купівля
                            currency_balance.balance -= transaction.amount
                            uah_balance.balance += transaction.total_amount
                        else:
                            return 'Некоректний тип операції'

                        db_session.delete(transaction)
                        try:
                            db_session.commit()
                        except Exception as e:
                            db_session.rollback()
                            return "Error of commit cancel transaction/error code #105"
                        return True
                    else:
                        return False
                else:
                    return 'Прошло більше 15 хвилин'
            else:
                return 'Операція не знайдена'
    except ValueError:
        return 'Некоректний ідентифікатор операції'


# Видалення операції за ідентифікатором
@app.route("/transactions/<transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    result = cancel_transaction(transaction_id)
    if result is True:
        return jsonify({'success': True, 'message': 'Операція успішно скасована'})
    else:
        return jsonify({'success': False, 'message': result})


@app.route("/save_courses", methods=["POST"])
def save_courses():
    data = request.get_json()
    cashier_number = data.get('cashier_number')
    if cashier_number is None:
        return jsonify({'success': False, 'message': 'Номер каси не вказаний'})

    cass_id = int(cashier_number)
    courses = []
    prefix_lengths = {'buy_': 4, 'sell_': 5}
    with DBSession() as db_session:  # Відкриття нової сесії
        for currency, rate in data.items():
            for prefix, prefix_length in prefix_lengths.items():
                if currency.startswith(prefix):
                    currency = currency[prefix_length:]
                    rate = float(rate)
                    course = db_session.query(Course).filter_by(cass_id=cass_id, currency=currency).first()
                    if course is None or (course.buy_rate != rate and prefix == 'buy_') or (course.sell_rate != rate and prefix == 'sell_'):
                        if course is None:
                            course = Course(cass_id=cass_id, currency=currency, buy_rate=0, sell_rate=0)
                            db_session.add(course)
                        if prefix == 'buy_':
                            course.buy_rate = rate
                        else:
                            course.sell_rate = rate
                        course = {'currency': course.currency, 'buy_rate': course.buy_rate, 'sell_rate': course.sell_rate}
                        courses.append(course)
                        db_session.commit()
                    break
    
    if courses:
        return jsonify({'success': True, 'courses': courses, 'message': 'Курс змінено'})
    else:
        return jsonify({'success': False, 'message': 'Курс не змінився'})
    
# Обработка кнопки получить список операций
@app.route("/get_operations", methods=["POST"])
def get_operations():
    data = request.get_json()
    from_date = data.get('fromDate')
    to_date = data.get('toDate')

    if from_date is None or to_date is None:
        return jsonify({'success': False, 'message': 'Недостатньо данних для отримання списка оперцій, заповніть всі дані'})

    try:
        from_date = datetime.strptime(from_date, "%Y-%m-%d")
        to_date = datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({'success': False, 'message': 'Некоректний формат данних про дату'})

    with Session() as db_session:
        cashier_id = session.get("cashier_id")

        sell_transactions = db_session.query(SellTransaction).filter(
            SellTransaction.cass_id == cashier_id,
            SellTransaction.date >= from_date,
            SellTransaction.date <= to_date + timedelta(days=1)  # Включить операции до конца выбранного дня
        ).order_by(SellTransaction.date.desc()).all()

        transactions = []
        for transaction in sell_transactions:
            transactions.append({
                "id": transaction.id,
                "date": transaction.date.strftime("%Y-%m-%d %H:%M:%S"),
                "cass_id": transaction.cass_id,
                "currency": transaction.currency,
                "amount": transaction.amount,
                "rate": transaction.rate,
                "total_amount": transaction.total_amount,
                "operation_type": transaction.operation_type
            })

        return jsonify(transactions)
    

# Функция для создания и сохранения операций в файл Excel
def save_operations_to_excel(transactions, filename):
    # Создаем новую рабочую книгу
    workbook = Workbook()
    sheet = workbook.active

    # Задаем заголовки столбцов
    headers = ["Дата", "Номер каси", "Тип операції", "Валюта", "Сума", "Сума в грн", "Курс"]
    for col_num, header in enumerate(headers, 1):
        column_letter = get_column_letter(col_num)
        sheet[f"{column_letter}1"] = header
        sheet[f"{column_letter}1"].font = Font(bold=True)

    # Заполняем таблицу данными операций
    for row_num, transaction in enumerate(transactions, 2):
        sheet[f"A{row_num}"] = transaction["date"]
        sheet[f"B{row_num}"] = transaction["cass_id"]
        sheet[f"C{row_num}"] = transaction["operation_type"]
        sheet[f"D{row_num}"] = transaction["currency"]
        sheet[f"E{row_num}"] = transaction["amount"]
        sheet[f"F{row_num}"] = transaction["total_amount"]
        sheet[f"G{row_num}"] = transaction["rate"]

    # Сохраняем файл Excel
    workbook.save(filename)

def generate_random_string(length):
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

@app.route("/get_operations_excel", methods=["POST"])
def get_operations_excel():
    # Получаем данные запроса
    data = request.get_json()
    from_date = data.get('fromDate')
    to_date = data.get('toDate')

    if from_date is None or to_date is None:
        return jsonify({'success': False, 'message': 'Недостатньо данних для отримання списка оперцій, заповніть всі дані'})

    try:
        from_date = datetime.strptime(from_date, "%Y-%m-%d")
        to_date = datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({'success': False, 'message': 'Некоректний формат данних про дату'})

    with Session() as db_session:
        cashier_id = session.get("cashier_id")

        sell_transactions = db_session.query(SellTransaction).filter(
            SellTransaction.cass_id == cashier_id,
            SellTransaction.date >= from_date,
            SellTransaction.date <= to_date + timedelta(days=1)  # Включить операции до конца выбранного дня
        ).order_by(SellTransaction.date.desc()).all()

        transactions = []
        for transaction in sell_transactions:
            transactions.append({
                "id": transaction.id,
                "date": transaction.date.strftime("%Y-%m-%d %H:%M:%S"),
                "cass_id": transaction.cass_id,
                "currency": transaction.currency,
                "amount": transaction.amount,
                "rate": transaction.rate,
                "total_amount": transaction.total_amount,
                "operation_type": transaction.operation_type
            })

    # Создаем имя файла
    random_numbers = generate_random_string(4)
    # Создаем временный файл для сохранения операций
    directory = "C:\\Cass-service\\temp"
    # Сохраняем операции в файл Excel
    filename = os.path.join(directory, f"excel_operations_{random_numbers}.xlsx")
    save_operations_to_excel(transactions, filename)

    # Отправляем файл пользователю для скачивания
    return send_file(filename, as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Обработка кнопки получить список операций
@app.route("/get_incasations", methods=["POST"])
def get_incasations():
    data = request.get_json()
    from_date = data.get('fromDate')
    to_date = data.get('toDate')

    if from_date is None or to_date is None:
        return jsonify({'success': False, 'message': 'Недостатньо данних для отримання списка оперцій, заповніть всі дані'})

    try:
        from_date = datetime.strptime(from_date, "%Y-%m-%d")
        to_date = datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({'success': False, 'message': 'Некоректний формат данних про дату'})

    with Session() as db_session:
        cashier_id = session.get("cashier_id")

        sell_transactions = db_session.query(OperationHistory).filter(
            OperationHistory.cass_id == cashier_id,
            OperationHistory.data >= from_date,
            OperationHistory.data <= to_date + timedelta(days=1)  # Включить операции до конца выбранного дня
        ).order_by(OperationHistory.data.desc()).all()

        transactions = []
        for transaction in sell_transactions:
            transactions.append({
                "id": transaction.id,
                "date": transaction.data.strftime("%Y-%m-%d %H:%M:%S"),
                "cass_id": transaction.cass_id,
                "currency": transaction.currency,
                "amount": transaction.amount,
                "total_amount": transaction.total_amount,
                "operation_type": transaction.operation_type
            })

        return jsonify(transactions)
    

# Функция для создания и сохранения инкасаций в файл Excel
def save_incasations_to_excel(transactions, filename):
    # Создаем новую рабочую книгу
    workbook = Workbook()
    sheet = workbook.active

    # Задаем заголовки столбцов
    headers = ["Дата", "Каси", "Тип", "Валюта", "Сума операції", "Ітоговий баланс"]
    for col_num, header in enumerate(headers, 1):
        column_letter = get_column_letter(col_num)
        sheet[f"{column_letter}1"] = header
        sheet[f"{column_letter}1"].font = Font(bold=True)

    # Заполняем таблицу данными операций
    for row_num, transaction in enumerate(transactions, 2):
        sheet[f"A{row_num}"] = transaction["date"]
        sheet[f"B{row_num}"] = transaction["cass_id"]
        sheet[f"C{row_num}"] = transaction["operation_type"]
        sheet[f"D{row_num}"] = transaction["currency"]
        sheet[f"E{row_num}"] = transaction["amount"]
        sheet[f"F{row_num}"] = transaction["total_amount"]

    # Сохраняем файл Excel
    workbook.save(filename)


@app.route("/get_incasations_excel", methods=["POST"])
def get_incasations_excel():
    # Получаем данные запроса
    data = request.get_json()
    from_date = data.get('fromDate')
    to_date = data.get('toDate')

    if from_date is None or to_date is None:
        return jsonify({'success': False, 'message': 'Недостатньо данних для отримання списка оперцій, заповніть всі дані'})

    try:
        from_date = datetime.strptime(from_date, "%Y-%m-%d")
        to_date = datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({'success': False, 'message': 'Некоректний формат данних про дату'})

    with Session() as db_session:
        cashier_id = session.get("cashier_id")

        sell_transactions = db_session.query(OperationHistory).filter(
            OperationHistory.cass_id == cashier_id,
            OperationHistory.data >= from_date,
            OperationHistory.data <= to_date + timedelta(days=1)  # Включить операции до конца выбранного дня
        ).order_by(OperationHistory.data.desc()).all()

        transactions = []
        for transaction in sell_transactions:
            transactions.append({
                "id": transaction.id,
                "date": transaction.data.strftime("%Y-%m-%d %H:%M:%S"),
                "cass_id": transaction.cass_id,
                "currency": transaction.currency,
                "amount": transaction.amount,
                "total_amount": transaction.total_amount,
                "operation_type": transaction.operation_type
            })

    # Создаем имя файла
    random_numbers = generate_random_string(4)
    # Создаем временный файл для сохранения операций
    directory = "C:\\Cass-service\\temp"
    # Сохраняем операции в файл Excel
    filename = os.path.join(directory, f"excel_incasations_{random_numbers}.xlsx")
    save_incasations_to_excel(transactions, filename)

    # Отправляем файл пользователю для скачивания
    return send_file(filename, as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":

    app.run(debug=True, host='0.0.0.0')

#Удачі всім, хто буде розбиратись або підтримувати цей код))

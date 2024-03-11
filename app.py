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

@app.route("/adm", methods=["GET"])
def adm_log():
    return render_template("loginadm.html")

# Функция проверки логина
@app.route("/admin", methods=["POST"])
def admin_login():
    login = request.form["login"]
    password = request.form["password"]
    with Session() as db_session:  
        cashier = db_session.query(User).filter(User.login == login, User.password == password, User.permissions==1).first()
        if cashier:
            # Сохранение данных в сессии
            session["login"] = login
            session["password"] = password
            session["premission"] = cashier.permissions
            return redirect(url_for("admin_page"))
        else:
            return "Пароль або логін введено невірно"

@app.route("/adm-panel",methods=['GET'])
def admin_page():
    benefit_value=benefit()
    num_oper=num_operations()
    buy_rate, sell_rate = mid_rate()
    cass = cass_info()

    return render_template("adm-panel.html",benefit=benefit_value, num_operations=num_oper, buyrate=buy_rate, sellrate= sell_rate, cass=cass)

@app.route("/users", methods=['GET'])
def users_adm():
    data_user = users_data()
    print(data_user)
    return render_template("users-adm.html", data_user = data_user)

@app.route("/allinfo", methods=['GET'])
def allinfo_adm():

    cass = cass_info()

    return render_template("allinfo-adm.html", cass=cass)

@app.route("/operinfo", methods=['POST'])
def oper_info():
    data_info= request.get_json()
    cass_id = data_info['cass_id']
    from_date = data_info['from_date']
    to_date = data_info['to_date']
    data = data_oper_info(cass_id, from_date, to_date)
    print (data)

    return jsonify(data)

@app.route("/edituser", methods=['POST'])
def edit_data():
    user_info = request.get_json()
    old_login = user_info['old_login'] # Старий логін
    new_login = user_info['new_login'] # Новий логін
    password = user_info['password'] # Пароль
    permissions = user_info['permissions'] # Рівень доступу
    

    try:
        with Session() as db_session:
            # Знаходимо користувача за старим логіном
            user = db_session.query(User).filter(User.login == old_login).first()
            
            # Оновлюємо дані користувача
            if user:
                user.login = new_login # Оновлюємо логін
                user.password = password # Оновлюємо пароль
                user.permissions = permissions # Оновлюємо рівень доступу
                db_session.commit()
                return "Дані користувача оновлено успішно!"
            else:
                return "Користувача з таким логіном не знайдено"
    except Exception as e:
        return str(e)

@app.route("/edit_user", methods=['GET'])
def edit_user():
    login = request.args.get('login')  # Отримуємо логін користувача з параметру запиту
    user_data = edit_user_data(login)
    print(user_data)

    return user_data

def data_oper_info(cass_id, from_date, to_date):
    try: 
        from_date = datetime.strptime(from_date, "%Y-%m-%d")  # Перетворення рядка у datetime
        to_date = datetime.strptime(to_date, "%Y-%m-%d")  # Перетворення рядка у datetime
        
        with Session() as db_session:
            if cass_id == "all":  # Якщо cass_id = "all", витягуємо дані для всіх кас
                data = db_session.query(SellTransaction).filter(
                    SellTransaction.date >= from_date,
                    SellTransaction.date <= to_date + timedelta(days=1)  # Включить операції до кінця вибраного дня
                ).order_by(SellTransaction.date.desc()).all()
            else:  # В іншому випадку, витягуємо дані тільки для конкретної каси
                data = db_session.query(SellTransaction).filter(
                    SellTransaction.cass_id == cass_id,
                    SellTransaction.date >= from_date,
                    SellTransaction.date <= to_date + timedelta(days=1)  # Включить операції до кінця вибраного дня
                ).order_by(SellTransaction.date.desc()).all()

            transactions = []
            for transaction in data:
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
        
        return transactions
    except Exception as e:
        return "Помилка отримання даних про операції"


def cass_info():
    level_perm=0

    try:
        with Session() as db_session:
            data= db_session.query(User).filter(User.permissions == level_perm).all()
            
            return [cass.cass_id for cass in data]

    except Exception as e:
        return "Помилка отримання списку кас"

def edit_user_data(login):
    try:
        with Session() as db_session:
            # Отримуємо дані користувача за логіном
            user = db_session.query(User).filter(User.login == login).first()

            # Перевіряємо, чи користувач знайдений
            if user:
                if user.permissions == 1:  # Якщо permissions = 1 (адміністратор)
                    # Формуємо дані про користувача як адміністратора
                    user_info = {
                        "login": user.login,
                        "password": user.password,
                        "access": "Адміністратор"
                    }
                elif user.permissions == 0:  # Якщо permissions = 0 (касир)
                    # Отримуємо дані каси за її номером
                    cash_register = db_session.query(Balance).filter(Balance.cass_id == user.cass_id).all()

                    # Формуємо дані про касу
                    cash_info = {
                        "cass_id": user.cass_id,
                        "login": user.login,
                        "password": user.password,
                        "access": "Каса"
                    }
                    # Додаємо дані про валюти, які використовуються на цій касі
                    currencies = [balance.currency for balance in cash_register]
                    cash_info["currencies"] = currencies

                    user_info = cash_info

                else:
                    user_info = None
            else:
                user_info = None

    except Exception as e:
        # Обробляємо помилку
        return "Помилка отримання даних користувача"

    return user_info


def users_data():
    try:
        with Session() as db_session:
            data = db_session.query(User).all()

            user_info = []
            for transaction in data:
                if transaction.permissions == 1:
                    role = "Адміністратор"
                    cass_id = "-"
                else:
                    role = "Каса"
                    cass_id = transaction.cass_id

                data_user = {
                    "id": transaction.id,
                    "cass_id": cass_id,
                    "login": transaction.login,
                    "password": transaction.password,
                    "permissions": role
                }
                user_info.append(data_user)
        return user_info

    except Exception as e:
        return "Помилка формування даних про користувачів"



@app.route('/graf-data', methods=['POST'])
def process_data():
    # Отримуємо дані з запиту
    data = request.get_json()

    # Викликаємо функції для обробки даних та отримання результатів
    benefit_data = benefit_by_day(data['cass_id'],data['fromDate'], data['toDate'])
    operations_data = operations_by_day(data['cass_id'],data['fromDate'], data['toDate'])

    # Об'єднуємо дані про прибуток та кількість операцій в один об'єкт
    result_data = {
        "profit": benefit_data,
        "operations": operations_data
    }

    # Повертаємо дані у форматі JSON
    return jsonify(result_data)

@app.route('/adm-data', methods=['POST'])
def adm_data():
    # Отримуємо дані з запиту
    data = request.get_json()

    # Викликаємо функції для обробки даних та отримання результатів
    benefit_data = benefit(data['cass_id'],data['fromDate'], data['toDate'])
    operations_data = num_operations(data['cass_id'],data['fromDate'], data['toDate'])
    buy_rate_data, sell_rate_data = mid_rate(data['cass_id'],data['fromDate'], data['toDate'])
    # Об'єднуємо дані про прибуток та кількість операцій в один об'єкт
    result_data = {
        "profit": benefit_data,
        "operations": operations_data,
        "buy_rate": buy_rate_data,
        "sell_rate": sell_rate_data
    }

    # Повертаємо дані у форматі JSON
    return jsonify(result_data)

@app.route("/graf", methods=['GET'])
def diagrams_page():

    daily_profit=benefit_by_day()
    daily_operations=operations_by_day()
    cass = cass_info()

    return render_template("graf.html", daily_profit=daily_profit, daily_operations=daily_operations, cass=cass)

def benefit_by_day(cass_id=None ,start_date=None, end_date=None):
    if cass_id is None:
        cass_id = "all"
    if start_date is None:
        start_date = datetime.now() - relativedelta(months=1)
    if end_date is None:
        end_date = datetime.now()

    data = stat(cass_id, start_date, end_date)
    daily_profit = []

    for transaction in data:
        date_key = transaction.date.strftime('%Y-%m-%d')
        profit = 0
        num_operations = 0
        if transaction.operation_type == 'Продаж':
            profit += transaction.total_amount
            num_operations += 1
        elif transaction.operation_type == 'Купівля':
            profit -= transaction.total_amount
            num_operations += 1

        daily_profit.append((date_key, profit, num_operations))

    return daily_profit

def operations_by_day(cass_id=None, start_date=None, end_date=None):
    if cass_id is None:
        cass_id = "all"
    if start_date is None:
        start_date = datetime.now() - relativedelta(months=1)
    if end_date is None:
        end_date = datetime.now()

    data = stat(cass_id, start_date, end_date)
    daily_operations = defaultdict(int)

    for transaction in data:
        date_key = transaction.date.strftime('%Y-%m-%d')
        daily_operations[date_key] += 1

    return daily_operations

def num_operations(cass_id=None, start_date=None, end_date=None):
    try: 
        # Встановлення значень за замовчуванням, якщо дати не передані
        if start_date is None:
            start_date = datetime.now() - relativedelta(months=1)  # Попередній місяць
        if end_date is None:
            end_date = datetime.now()
        
        data = stat(cass_id, start_date, end_date)  # Отримання даних з бази даних
        num_operations = len(data)  # Кількість операцій

        return num_operations
        
    except Exception as e: 
        return "Помилка формування"

def mid_rate(cass_id=None, start_date=None, end_date=None):
    if cass_id is None:
        cass_id = "all"
    if start_date is None:
        start_date = datetime.now() - relativedelta(months=1)
    if end_date is None:
        end_date= datetime.now()
    
    jsn_data_list = []
    total_buycurrency = 0  # Ініціалізуємо змінну total_currency
    total_buyuah = 0  # Ініціалізуємо змінну total_uah

    data = stat(cass_id, start_date, end_date)
            
    try:
        for transaction in data:
            jsn_data = {
                "id": transaction.id,
                "date":transaction.date.strftime('%Y-%m-%d %H:%M:%S'),
                "cass_id":transaction.cass_id,
                "currency":transaction.currency,
                "amoutn":transaction.amount,
                "total_amount":transaction.total_amount,
                "operation_type":transaction.operation_type,
                "rate":transaction.rate
            }
            jsn_data_list.append(jsn_data)
    except Exception as e:
        return "Помилка формування"
        

    total_selluah=0
    total_sellcurrency=0

    for transaction in data:
        if transaction.operation_type == "Купівля":
            total_buycurrency += transaction.amount
            total_buyuah += transaction.total_amount
        elif transaction.operation_type == "Продаж":
            total_sellcurrency += transaction.amount
            total_selluah += transaction.total_amount


        # Перевіряємо, чи не дорівнює total_buycurrency нулю перед обчисленням
    if total_buycurrency != 0:
        total_buyrate = total_buyuah / total_buycurrency
    else:
        total_buyrate = 0

    # Перевіряємо, чи не дорівнює total_sellcurrency нулю перед обчисленням
    if total_sellcurrency != 0:
        total_sellrate = total_selluah / total_sellcurrency
    else:
        total_sellrate = 0

    mid_sellrate = "{:,.2f}".format(total_sellrate)
    mid_buyrate = "{:,.2f}".format(total_buyrate)



    return mid_buyrate, mid_sellrate

def benefit(cass_id=None, start_date=None, end_date=None):
    # Встановлення значень за замовчуванням, якщо дати не передані
    if cass_id is None:
        cass_id = "all"
    if start_date is None:
        start_date = datetime.now() - relativedelta(months=1)  # Попередній місяць
    if end_date is None:
        end_date = datetime.now()

    data = stat(cass_id, start_date, end_date)  # Отримання даних з бази даних
    jsn_data_list = []
    total_profit = 0
    try:
        for transaction in data:
            jsn_data = {
                "id": transaction.id,
                "date": transaction.date.strftime('%Y-%m-%d %H:%M:%S'),
                "cass_id": transaction.cass_id,
                "currency": transaction.currency,
                "amount": transaction.amount,
                "total_amount": transaction.total_amount,
                "operation_type": transaction.operation_type,
                "rate": transaction.rate
            }
            jsn_data_list.append(jsn_data)  # Додавання jsn_data в jsn_data_list

    except Exception as e:
        return "Помилка формування"

    # Розрахунок прибутку
    for transaction in data:
        if transaction.operation_type == 'Продаж':
            total_profit += transaction.total_amount
        elif transaction.operation_type == 'Купівля':
            total_profit -= transaction.total_amount

    formatted_profit = "{:,.2f}".format(total_profit)

    return formatted_profit

    
def stat(cass_id=None, start_date=None, end_date=None):
    try: 
        # Визначаємо дату за місяць назад від поточної дати, якщо аргументи не передані
        if cass_id is None:
            cass_id = "all"
        if start_date is None:
            start_date = datetime.now() - relativedelta(months=1)
        if end_date is None:
            end_date = datetime.now()
        
        with Session() as db_session:
            # Фільтруємо операції за переданим часовим проміжком та номером каси (якщо вказано)
            if cass_id == "all":
                data = db_session.query(SellTransaction).filter(
                    SellTransaction.date >= start_date,
                    SellTransaction.date <= end_date
                ).all()
            else:
                data = db_session.query(SellTransaction).filter(
                    SellTransaction.cass_id == cass_id,
                    SellTransaction.date >= start_date,
                    SellTransaction.date <= end_date
                ).all()
        
        return data
        
    except Exception as e: 
        return "помилка формування статистики: " + str(e)


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
    directory = "C:\\Users\\Anton\\Desktop\\webservice\\temp"
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
    directory = "C:\\Users\\Anton\\Desktop\\webservice\\temp"
    # Сохраняем операции в файл Excel
    filename = os.path.join(directory, f"excel_incasations_{random_numbers}.xlsx")
    save_incasations_to_excel(transactions, filename)

    # Отправляем файл пользователю для скачивания
    return send_file(filename, as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')


#Удачі всім, хто буде розбиратись або підтримувати цей код))
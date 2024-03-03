from flask import Flask, request, render_template, jsonify, session, redirect, url_for, send_file
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font
import secrets, tempfile, random, string, os
from collections import defaultdict
import json

app = Flask(__name__)

app.secret_key = secrets.token_hex(16) #Ключ сессии

# Подключение к базе данных
engine = create_engine('mysql+pymysql://root:2701172004@localhost/Users', echo=True)
Base = declarative_base()

# Определение классов для таблиц
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String(255), nullable=False)
    cass_id = Column(Integer, nullable=False)
    password = Column(String(255), nullable=False)
    permissions = Column(Integer, nullable=False)

    balances = relationship("Balance", back_populates="user")
    courses = relationship("Course", back_populates="user")
    selltransactions = relationship("SellTransaction", back_populates="user")
    operation_history = relationship("OperationHistory", back_populates="user")



class Balance(Base):
    __tablename__ = 'balances'

    id = Column(Integer, primary_key=True)
    cass_id = Column(Integer, ForeignKey('users.cass_id'), nullable=False)
    currency = Column(String(255), nullable=False)
    balance = Column(Float, nullable=False)

    user = relationship("User", back_populates="balances")


class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    cass_id = Column(Integer, ForeignKey('users.cass_id'), nullable=False)
    currency = Column(String(3), nullable=False)
    buy_rate = Column(Float, nullable=False)
    sell_rate = Column(Float, nullable=False)

    user = relationship("User", back_populates="courses")


class SellTransaction(Base):
    __tablename__ = 'selltransactions'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    cass_id = Column(Integer, ForeignKey('users.cass_id'), nullable=False)
    currency = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    operation_type = Column(String(50), nullable=False)
    rate = Column(Float, nullable=False)

    user = relationship("User", back_populates="selltransactions")

#Таблица инкас/подкреп
class OperationHistory(Base):
    __tablename__ = 'operation_history'

    id = Column(Integer, primary_key=True)
    data = Column(DateTime, nullable=False)
    cass_id = Column(Integer, ForeignKey('users.cass_id'), nullable=False)
    currency = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    operation_type = Column(String(50), nullable=False)
    total_amount = Column(Float, nullable=False)

    user = relationship("User", back_populates="operation_history")
    

#Класс который описывает контекстный менеджер управления сессиями в базе данных(Нужно доработать)
class DBSession:
    def __enter__(self):
        self.db_session = Session()  # Открываем сессию
        return self.db_session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.db_session.rollback()  # Откатываем изменения при возникновении ошибки
        else:
            self.db_session.commit()  # Фиксируем изменения
        self.db_session.close()  # Закрываем сессию

# Создание таблиц
Base.metadata.create_all(engine)

# Создание сессии
Session = sessionmaker(bind=engine)

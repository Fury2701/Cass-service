from flask import Flask, request, render_template, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta

app = Flask(__name__)

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

    balances = relationship("Balance", back_populates="user")
    courses = relationship("Course", back_populates="user")
    selltransactions = relationship("SellTransaction", back_populates="user")


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


# Создание таблиц
Base.metadata.create_all(engine)

# Создание сессии
Session = sessionmaker(bind=engine)

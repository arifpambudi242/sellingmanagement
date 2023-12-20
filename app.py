from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade, init
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session
import dotenv
import os
from datetime import datetime
from flask_bcrypt import Bcrypt
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

bcrypt = Bcrypt()

dotenv.load_dotenv()


SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG')
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)
migrate = Migrate(app, db)
with app.app_context():
    try:
        init()
    except:
        print('Error init')
        try:
            db.create_all()
        except:
            print('Error create')
            try:
                upgrade()
            except:
                print('Error upgrade')
                pass

class Investor(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    capital = Column(Float, nullable=False)

class Shopping(db.Model):
    id = Column(Integer, primary_key=True)
    investor_id = Column(Integer, ForeignKey('investor.id'), nullable=False)
    shopping_date = Column(DateTime, default=datetime.now, nullable=False)
    total_shopping = Column(Float, nullable=False)

class DetailedShopping(db.Model):
    id = Column(Integer, primary_key=True)
    item_name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(20), nullable=False)
    shopping_id = Column(Integer, ForeignKey('shopping.id'), nullable=False)
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    @hybrid_property
    def total(self):
        return self.price * self.quantity

    @total.expression
    def total(cls):
        return cls.price * cls.quantity

class Product(db.Model):
    id = Column(Integer, primary_key=True)
    product_name = Column(String(255), nullable=False)
    product_price = Column(Float, nullable=False)
    product_quantity = Column(Integer, nullable=False)
    product_description = Column(String(500), nullable=True)

class Production(db.Model):
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    production_date = Column(DateTime, default=datetime.now, nullable=False)
    production_quantity = Column(Integer, nullable=False)

class Sale(db.Model):
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    sale_date = Column(DateTime, default=datetime.now, nullable=False)
    sale_quantity = Column(Integer, nullable=False)
    total_sale = Column(Float, nullable=False)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

def convert_date(datestr):

    # Given datetime string
    datetime_str = datestr

    # Convert string to datetime object
    datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")

    # Format the datetime object
    formatted_datetime = datetime_obj.strftime("%A, %d %b %Y %H:%M")

    return formatted_datetime

def str_convert(strin):
    return f'{strin}'



@app.context_processor
def inject_data():
    current_year = datetime.now().year
    year = 2023

    if year < current_year:
        year_str = f"{year} - {current_year}"
    else:
        year_str = str(year)

    active_menu = request.endpoint  # Assuming endpoint names match your menu names
    menus = {
        'index' : 'Home',
        'penjualan' : 'Penjualan',
        'produksi' : 'Produksi',
        'belanja' : 'Belanja',
        'belanja_rinci' : 'Belanja Rinci',
        'modal' : 'Modal',
        'harga_jual' : 'Harga Jual',
    }
    active_title = ''
    
    tables = {
        'index' : [Modal, Belanja, Produksi, HargaJual, Jual],
        'penjualan' : Jual,
        'produksi' : Produksi,
        'belanja' : [Modal,Belanja],
        'belanja_rinci' : [Belanja, BelanjaRinci],
        'modal' : Modal,
        'harga_jual' : HargaJual,
    }

    for key, menu in menus.items():
        if active_menu in key:
            active_title = menu
            break
        else:
            active_title = ''
            continue
    datas = None
    for key, table in tables.items():
        if active_menu in key:
            if type(table) is not list:
                datas = table.query.all()
                break
            else:
                datas = {}
                for tab in table:
                    print(tab.__name__.lower())
                    datas[tab.__name__.lower()] = tab.query.all()
                break
        else:
            datas = None
            continue
    no = 0

    return dict(tahun=tahun_str, active_title=active_title, datas=datas, no=no)



@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'), 'favicon.ico', mimetype='image/png')

@app.route('/')
def index():
    datas = {
        'title' : 'Home'
    }
    return render_template('index.html', datas=datas)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=DEBUG)
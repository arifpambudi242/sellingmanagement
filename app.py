from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session
import dotenv
import os
from datetime import datetime
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

dotenv.load_dotenv()

USER_DB = os.getenv('USER_DB')
PASSWORD_DB = os.getenv('PASSWORD_DB')
HOST_DB = os.getenv('HOST_DB')
NAME_DB = os.getenv('NAME_DB')
SECRET_KEY = os.getenv('SECRET_KEY')
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)

class Sempol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    harga = db.Column(db.Float)
    waktu = db.Column(db.DateTime, default=datetime.now, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

class Modal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

class Belanja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    id_modal = db.Column(db.Integer, db.ForeignKey('modal.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    modal = db.relationship('Modal', backref=db.backref('Belanja', lazy=True))

class Produksi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_belanja = db.Column(db.Integer, db.ForeignKey('belanja.id'), nullable=False)
    jumlah_produksi = db.Column(db.Float, nullable=False)
    tanggal_produksi = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    belanja = db.relationship('Belanja', backref=db.backref('Produksi', lazy=True))

class HargaJual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    harga = db.Column(db.Float, nullable=False)
    tgl_berlaku = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class Jual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_produksi = db.Column(db.Integer, db.ForeignKey('produksi.id'), nullable=False)
    id_harga = db.Column(db.Integer, db.ForeignKey('harga_jual.id'), nullable=False)
    jumlah_penjualan = db.Column(db.Float, nullable=False)
    tanggal_penjualan = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    produksi = db.relationship('Produksi', backref=db.backref('Jual', lazy=True))
    harga_jual = db.relationship('HargaJual', backref=db.backref('Jual', lazy=True))



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
    tahun_sekarang = datetime.now().year
    tahun = 2023

    if tahun < tahun_sekarang:
        tahun_str = f"{tahun} - {tahun_sekarang}"
    else:
        tahun_str = str(tahun)

    active_menu = request.endpoint  # Assuming endpoint names match your menu names
    menus = {
        'index' : 'Home',
        'penjualan' : 'Penjualan',
        'produksi' : 'Produksi',
        'belanja' : 'Belanja',
        'modal' : 'Modal',
        'harga_jual' : 'Harga Jual',
    }
    active_title = ''
    
    tables = {
        'index' : [Modal, Belanja, Produksi, HargaJual, Jual],
        'penjualan' : Jual,
        'produksi' : Produksi,
        'belanja' : Belanja,
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
            datas = table.query.all()
            break
        else:
            datas = None
            continue
    no = 0

    return dict(tahun=tahun_str, active_title=active_title, datas=datas, no=no)

@app.route('/')
def index():
    sempol_data = Sempol.query.all()
    prices = 0
    for sempol in sempol_data:
        prices += sempol.harga
    return render_template('index.html', data={'prices' : prices,'sempol_data' : sempol_data}, convert_date=convert_date, str_convert=str_convert)

@app.route('/add_sale', methods=['POST'])
def add_sale():
    harga = request.form.get('harga')
    # Lakukan perhitungan otomatis sesuai logika bisnis Anda
    sempol = Sempol(harga=harga)
    db.session.add(sempol)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_modal', methods=['POST'])
def add_modal():
    nama = request.form.get('nama')
    jumlah = request.form.get('jumlah')
    keterangan = request.form.get('keterangan')
    # Lakukan perhitungan otomatis sesuai logika bisnis Anda
    modal = Modal(nama=nama, jumlah=jumlah, keterangan=keterangan)
    db.session.add(modal)
    db.session.commit()
    return redirect(url_for('modal'))


@app.route('/penjualan')
def penjualan():
    return "Ini adalah halaman Penjualan"

@app.route('/produksi')
def produksi():
    return "Ini adalah halaman Produksi"

@app.route('/belanja')
def belanja():
    return "Ini adalah halaman Belanja"

@app.route('/modal')
def modal():
    return render_template('modal.html')

@app.route('/harga_jual')
def harga_jual():
    return "Ini adalah halaman Harga Jual"


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

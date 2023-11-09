from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session
import dotenv
import os
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
    waktu = db.Column(db.DateTime, default=datetime.now)
    # Tambahkan kolom lain sesuai kebutuhan
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


@app.route('/')
def index():
    sempol_data = Sempol.query.all()
    return render_template('index.html', sempol_data=sempol_data)

@app.route('/add_sale', methods=['POST'])
def add_sale():
    harga = request.form.get('harga')
    # Lakukan perhitungan otomatis sesuai logika bisnis Anda
    sempol = Sempol(harga=harga)
    db.session.add(sempol)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

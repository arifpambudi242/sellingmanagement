from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session
import dotenv
import os

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


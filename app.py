from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate, upgrade, init
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session
import dotenv
import os
from datetime import datetime
from flask_bcrypt import Bcrypt
from currency_converter import ECB_URL, CurrencyConverter
c = CurrencyConverter(ECB_URL)



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

def convertToUsd(idr):
    return round(c.convert(idr, 'IDR', 'USD', None), 2)
class Modal(db.Model):
    __tablename__ = 'modal'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    @property
    def sisa(self):
        total_belanja_rinci = (
            db.session.query(func.sum(BelanjaRinci.harga * BelanjaRinci.jumlah))
            .select_from(Modal)
            .join(Belanja, Belanja.id_modal == Modal.id)
            .join(BelanjaRinci, BelanjaRinci.belanja_id == Belanja.id)
            .filter(Modal.id == self.id)
            .scalar()
        )
        return self.jumlah - (total_belanja_rinci or 0)
    
    @property
    def persentase(self):
        total_jumlah = (
            db.session.query(func.sum(Modal.jumlah))
            .select_from(Modal)
            .scalar()
        )
        return self.jumlah / total_jumlah * 100
    
    @property
    def jumlah_usd(self):
        return convertToUsd(self.jumlah)
    
    @property
    def sisa_usd(self):
        return convertToUsd(self.sisa)
    
    

class Belanja(db.Model):
    __tablename__ = 'belanja'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    id_modal = db.Column(db.Integer, db.ForeignKey('modal.id'), nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    modal = db.relationship('Modal', backref=db.backref('belanja', lazy=True))
    
    @property
    def total_belanja(self):
        total_belanja_rinci = (
            db.session.query(func.sum(BelanjaRinci.harga * BelanjaRinci.jumlah))
            .select_from(Belanja)
            .join(BelanjaRinci, BelanjaRinci.belanja_id == Belanja.id)
            .filter(Belanja.id == self.id)
            .scalar()
        )
        return total_belanja_rinci or 0
    
    @property
    def total_belanja_usd(self):
        return convertToUsd(self.total_belanja)
    
    @property
    def belanja_rinci_list(self):
        rincians = (
            db.session.query(BelanjaRinci)
            .filter(BelanjaRinci.belanja_id == self.id)
            .all()
        )
        
        return ', '.join([rincian.nama_barang for rincian in rincians])
    
    

class BelanjaRinci(db.Model):
    __tablename__ = 'belanja_rinci'
    id = db.Column(db.Integer, primary_key=True)
    nama_barang = db.Column(db.String(255), nullable=False)
    harga = db.Column(db.Float, nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    belanja_id = db.Column(db.Integer, db.ForeignKey('belanja.id'), nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    belanja = db.relationship('Belanja', backref=db.backref('belanja_rinci', lazy=True))

    @property
    def total(self):
        return self.jumlah * self.harga
    
    @property
    def total_usd(self):
        return convertToUsd(self.total)
    
    @property
    def harga_usd(self):
        return convertToUsd(self.harga)
    
    
class Produksi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_belanja = db.Column(db.Integer, db.ForeignKey('belanja.id'), nullable=False)
    jumlah_produksi = db.Column(db.Float, nullable=False)
    tanggal_produksi = db.Column(db.Date, nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    belanja = db.relationship('Belanja', backref=db.backref('Produksi', lazy=True))

class HargaJual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    harga = db.Column(db.Float, nullable=False)
    tgl_berlaku = db.Column(db.Date, nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    @property
    def harga_usd(self):
        return convertToUsd(self.harga)


class Jual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_produksi = db.Column(db.Integer, db.ForeignKey('produksi.id'), nullable=False)
    id_harga = db.Column(db.Integer, db.ForeignKey('harga_jual.id'), nullable=False)
    jumlah_penjualan = db.Column(db.Float, nullable=False)
    tanggal_penjualan = db.Column(db.Date, nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
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


# Global variable 
menus = {
        'index' : 'Home',
        'penjualan' : 'Penjualan',
        'produksi' : 'Produksi',
        'belanja' : 'Belanja',
        'belanja_rinci' : 'Belanja Rinci',
        'modal' : 'Modal',
        'harga_jual' : 'Harga Jual',
    }

tables = {
        'index' : [Modal, Belanja, Produksi, HargaJual, Jual, BelanjaRinci],
        'penjualan' : Jual,
        'produksi' : [Produksi, Belanja],
        'belanja' : [Modal,Belanja],
        'belanja_rinci' : [Belanja,BelanjaRinci],
        'modal' : Modal,
        'harga_jual' : HargaJual,
    }

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

def getdata(table, column, value):
    global menus, tables
    return tables[table].query.filter_by(belanja_id=1).first()


@app.context_processor
def inject_data():
    global menus, tables
    tahun_sekarang = datetime.now().year
    tahun_dibuat = 2023

    if tahun_dibuat < tahun_sekarang:
        tahun_str = f"{tahun_dibuat} - {tahun_sekarang}"
    else:
        tahun_str = str(tahun_dibuat)

    active_menu = request.endpoint  # Assuming endpoint names match your menu names
    
    active_title = ''
    
    

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
                last_url = request.url.split('/')[-1]
                datas = {}
                for tab in table:
                    try:
                        int(last_url) + 1
                        if 'belanja' in tab.__name__.lower():
                            datas[tab.__name__.lower()] = tab.query.get(int(last_url))
                        if 'belanjarinci' in tab.__name__.lower():
                            datas[tab.__name__.lower()] = tab.query.filter_by(belanja_id=int(last_url)).all()
                    except:
                        datas[tab.__name__.lower()] = tab.query.all()
                        
                break
        else:
            datas = None
            continue
    no = 0

    return dict(tahun=tahun_str, active_title=active_title, datas=datas, no=no)

@app.template_filter()
def format_currency(value):
    return "Rp. {:,.2f}".format(value)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'), 'favicon.ico', mimetype='image/png')



@app.route('/penjualan')
def penjualan():
    return "Ini adalah halaman Penjualan"

@app.route('/produksi')
def produksi():
    return render_template('produksi.html')
# belanja
@app.route('/belanja')
def belanja():
    return render_template('belanja.html')

@app.route('/add_belanja', methods=['POST'])
def add_belanja():
    nama = request.form.get('nama')
    keterangan = request.form.get('keterangan')
    id_modal = request.form.get('sumber_dana')
    # Lakukan perhitungan otomatis sesuai logika bisnis Anda
    belanja = Belanja(nama=nama, keterangan=keterangan, id_modal=id_modal)
    db.session.add(belanja)
    db.session.commit()
    return jsonify({'status_code' : 200,'message': 'Data Belanja berhasil ditambahkan'}), 200

@app.route('/delete_belanja/<int:belanja_id>', methods=['POST'])
def delete_belanja(belanja_id):
    belanja = Belanja.query.get(belanja_id)
    if belanja:
        try:
            db.session.delete(belanja)
            db.session.commit()
            return jsonify({'status_code' : 200,'message': 'Data Belanja berhasil dihapus'}), 200
        except Exception as e:
            return jsonify({'status_code' : 502,'message': 'Data masih digunakan di belanja rinci, anda tidak dapat menghapusnya'}), 200
    else:
        return jsonify({'status_code' : 404,'message': 'Data Belanja tidak ditemukan / sudah terhapus'}), 200

@app.route('/edit_belanja/<int:belanja_id>', methods=['GET','POST'])
def edit_belanja(belanja_id):
    if not request.method == 'POST':
        belanja = Belanja.query.get(belanja_id)
        if belanja:
            # If the belanja with the given ID exists, return its data
            return jsonify({'id': belanja.id, 'nama': belanja.nama, 'keterangan' : belanja.keterangan, 'sumber_dana' : belanja.id_modal})
        else:
            # If the belanja with the given ID does not exist, return an error message
            return jsonify({'error': 'belanja not found'}), 404
    else:
        belanja = Belanja.query.get(belanja_id)
        if belanja:
            # Get the updated data from the request
            updated_data = request.form

            # Update the belanja with the new data
            belanja.nama = updated_data.get('nama', belanja.nama)
            belanja.keterangan = updated_data.get('keterangan', belanja.keterangan)
            belanja.id_modal = updated_data.get('sumber_dana', belanja.id_modal)

            # Commit the changes to the database
            db.session.commit()

            return jsonify({'message': 'belanja updated successfully'})
        else:
            return jsonify({'error': 'belanja not found'}), 404

@app.route('/belanja_rinci/<int:blj_id>', methods=['GET','POST'])
def belanja_rinci(blj_id):
    if request.method == 'POST':
        nama_barang = request.form.get('nama_barang')
        harga = request.form.get('harga')
        jumlah = request.form.get('jumlah')
        keterangan = request.form.get('keterangan')
        belanja_id = blj_id,
        belanja_rinci = BelanjaRinci(nama_barang = nama_barang,harga = harga,jumlah = jumlah, belanja_id = blj_id, keterangan = keterangan)
        db.session.add(belanja_rinci)
        db.session.commit()
        return jsonify({'status_code' : 200, 'status' : 'success', 'message' : 'berhasil tambah rincian'}), 200
    # get data belanja rinci by kode belanja
    return render_template('belanja_rinci.html')

@app.route('/delete_belanja_rinci/<int:belanja_rinc_id>', methods=['POST'])
def delete_belanja_rinci(belanja_rinc_id):
    modal = BelanjaRinci.query.get(belanja_rinc_id)
    if modal:
        try:
            db.session.delete(modal)
            db.session.commit()
            return jsonify({'status_code' : 200,'message': 'Data Belanja Rinci berhasil dihapus'}), 200
        except Exception as e:
            return jsonify({'status_code' : 502,'message': 'Data masih digunakan di belanja, anda tidak dapat menghapusnya'}), 200
    else:
        return jsonify({'status_code' : 404,'message': 'Data Belanja Rinci tidak ditemukan / sudah terhapus'}), 200

@app.route('/edit_belanja_rinci/<int:belanja_rinci_id>', methods=['GET','POST'])
def edit_belanja_rinci(belanja_rinci_id):
    if not request.method == 'POST':
        belanja_rinci = BelanjaRinci.query.get(belanja_rinci_id)

        if belanja_rinci:
            # If the belanja_rinci with the given ID exists, return its data
            return jsonify({'id': belanja_rinci.id, 'nama_barang': belanja_rinci.nama_barang, 'harga' : belanja_rinci.harga, 'jumlah' : belanja_rinci.jumlah, 'keterangan' : belanja_rinci.keterangan, 'belanja_id' : belanja_rinci.belanja_id})
        else:
            # If the belanja_rinci with the given ID does not exist, return an error message
            return jsonify({'error': 'belanja_rinci not found'}), 404
    else:
        belanja_rinci = BelanjaRinci.query.get(belanja_rinci_id)
        if belanja_rinci:
            # Get the updated data from the request
            updated_data = request.form

            # Update the belanja_rinci with the new data
            belanja_rinci.nama_barang = updated_data.get('nama_barang', belanja_rinci.nama_barang)
            belanja_rinci.harga = updated_data.get('harga', belanja_rinci.harga)
            belanja_rinci.jumlah = updated_data.get('jumlah', belanja_rinci.jumlah)
            belanja_rinci.keterangan = updated_data.get('keterangan', belanja_rinci.keterangan)

            # Commit the changes to the database
            db.session.commit()

            return jsonify({'message': 'belanja_rinci updated successfully'})
        else:
            return jsonify({'error': 'belanja_rinci not found'}), 404
# end belanja
# modal
@app.route('/modal')
def modal():
    return render_template('modal.html', round=round)

@app.route('/add_modal', methods=['POST'])
def add_modal():
    nama = request.form.get('nama')
    jumlah = request.form.get('jumlah')
    keterangan = request.form.get('keterangan')
    # Lakukan perhitungan otomatis sesuai logika bisnis Anda
    modal = Modal(nama=nama, jumlah=jumlah, keterangan=keterangan)
    db.session.add(modal)
    db.session.commit()
    return jsonify({'status_code' : 200,'message': 'Data modal berhasil ditambahkan'}), 200

@app.route('/delete_modal/<int:modal_id>', methods=['POST'])
def delete_modal(modal_id):
    modal = Modal.query.get(modal_id)
    if modal:
        try:
            db.session.delete(modal)
            db.session.commit()
            return jsonify({'status_code' : 200,'message': 'Data modal berhasil dihapus'}), 200
        except Exception as e:
            return jsonify({'status_code' : 502,'message': 'Data masih digunakan di belanja, anda tidak dapat menghapusnya'}), 200
    else:
        return jsonify({'status_code' : 404,'message': 'Data modal tidak ditemukan / sudah terhapus'}), 200

@app.route('/edit_modal/<int:modal_id>', methods=['GET','POST'])
def edit_modal(modal_id):
    if not request.method == 'POST':
        modal = Modal.query.get(modal_id)

        if modal:
            # If the modal with the given ID exists, return its data
            return jsonify({'id': modal.id, 'nama': modal.nama, 'jumlah' : modal.jumlah, 'keterangan' : modal.keterangan})
        else:
            # If the modal with the given ID does not exist, return an error message
            return jsonify({'error': 'Modal not found'}), 404
    else:
        modal = Modal.query.get(modal_id)
        if modal:
            # Get the updated data from the request
            updated_data = request.form

            # Update the modal with the new data
            modal.nama = updated_data.get('nama', modal.nama)
            modal.jumlah = updated_data.get('jumlah', modal.jumlah)
            modal.keterangan = updated_data.get('keterangan', modal.keterangan)

            # Commit the changes to the database
            db.session.commit()

            return jsonify({'message': 'Modal updated successfully'})
        else:
            return jsonify({'error': 'Modal not found'}), 404

# end modal

@app.route('/harga_jual')
def harga_jual():
    return "Ini adalah halaman Harga Jual"


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=DEBUG)

import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Hotel, Booking
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from flask_migrate import Migrate
from forms import HotelForm
from datetime import datetime
from flask import blueprints
from flask.cli import with_appcontext

import click
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user


# Inisialisasi aplikasi Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = '740c8bb5b603ca519f3c26230dc722500c070f1d23b61e69c02fb6acbed3c539'

app.config.from_object(Config)

# Inisialisasi database dan migrasi
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)


# Konfigurasi folder upload gambar
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Fungsi untuk memeriksa ekstensi file gambar
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Fungsi untuk membuat akun admin baru
def create_admin_account(username, password):
    with app.app_context():  # Memastikan berada di dalam aplikasi context
        admin = User.query.filter_by(username=username).first()
        if not admin:
            hashed_password = generate_password_hash(password)  # Meng-hash password
            admin = User(username=username, password=hashed_password, role='admin')
            db.session.add(admin)  # Menambahkan admin ke database
            db.session.commit()  # Menyimpan perubahan
            click.echo(f"Akun admin {username} berhasil dibuat!")  # Memberikan feedback
        else:
            click.echo(f"Akun admin dengan username {username} sudah ada.")  # Jika akun sudah ada

# Fungsi untuk menghapus akun admin
def delete_admin_account(username):
    with app.app_context():  # Memastikan berada di dalam aplikasi context
        admin = User.query.filter_by(username=username).first()
        if admin:
            db.session.delete(admin)  # Menghapus akun admin dari database
            db.session.commit()  # Menyimpan perubahan ke database
            click.echo(f"Akun admin dengan username {username} berhasil dihapus!")
        else:
            click.echo(f"Akun admin dengan username {username} tidak ditemukan.")

# Menambahkan perintah CLI untuk menghapus akun admin
@app.cli.command("delete-admin")
@click.argument("username")
@with_appcontext
def delete_admin_cli(username):
    """Perintah untuk menghapus akun admin melalui terminal"""
    delete_admin_account(username)

# Menambahkan perintah CLI untuk membuat akun admin
@app.cli.command("create-admin")
@click.argument("username")
@click.argument("password")
@with_appcontext
def create_admin_cli(username, password):
    """Perintah untuk membuat akun admin baru melalui terminal"""
    create_admin_account(username, password)

# Fungsi valid_login untuk login (hapus salah satu definisi)
def valid_login(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return user
    return None

# Fungsi untuk memuat pengguna berdasarkan user_id (Flask-Login membutuhkan ini)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route untuk halaman booking
@app.route('/book/<int:hotel_id>', methods=['GET', 'POST'])
def book_hotel(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if not current_user.is_authenticated:  # Pastikan pengguna sudah login
        return redirect(url_for('login', next=request.url))  # Simpan URL tujuan di 'next'
    
    if request.method == 'POST':
        # Mengambil data tanggal dari form
        check_in_date_str = request.form['check_in_date']
        check_out_date_str = request.form['check_out_date']
        
        # Mengonversi string ke objek date
        check_in_date = datetime.strptime(check_in_date_str, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out_date_str, "%Y-%m-%d").date()

        # Pastikan pengguna sudah login
        user = current_user  # Pastikan pengguna sudah login dengan flask-login
        
        # Membuat pemesanan baru
        booking = Booking(
            hotel_id=hotel.id,
            user_id=user.id,
            check_in_date=check_in_date,
            check_out_date=check_out_date
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Mengarahkan ke halaman booking_receipt setelah pemesanan berhasil
        return redirect(url_for('booking_receipt', booking_id=booking.id))
    
    return render_template('book_hotel.html', hotel=hotel)


@app.route('/admin/bookings/edit/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):
    if not current_user.is_admin():  # Hanya admin yang bisa mengedit booking
        flash('Akses ditolak! Hanya admin yang dapat mengedit booking.', 'danger')
        return redirect(url_for('home'))  # Arahkan ke halaman utama jika bukan admin

    booking = Booking.query.get_or_404(booking_id)

    if request.method == 'POST':
        # Update data booking
        booking.check_in_date = request.form['check_in_date']
        booking.check_out_date = request.form['check_out_date']
        db.session.commit()

        return redirect(url_for('manage_bookings'))  # Redirect setelah sukses update booking

    return render_template('edit_booking.html', booking=booking)



@app.route('/admin/bookings/delete/<int:booking_id>', methods=['POST'])
@login_required
def delete_booking(booking_id):
    if not current_user.is_admin():
        return redirect(url_for('index'))

    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()

    return redirect(url_for('manage_bookings'))


@app.route('/admin/bookings')
@login_required  # Pengguna harus login untuk mengakses halaman ini
def manage_bookings():
    if not current_user.is_admin():  # Memeriksa jika pengguna adalah admin
        flash('Akses ditolak! Hanya admin yang dapat mengakses halaman ini.', 'danger')
        return redirect(url_for('home'))  # Arahkan ke halaman utama jika bukan admin
    bookings = Booking.query.all()  # Ambil data booking
    return render_template('admin_manage_bookings.html', bookings=bookings)



# Route untuk menampilkan nota booking setelah berhasil melakukan pemesanan
@app.route('/booking_receipt/<int:booking_id>')
def booking_receipt(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('booking_receipt.html', booking=booking)

# Route untuk halaman utama (Home)
@app.route('/')
def home():
    hotels = Hotel.query.limit(6).all()
    return render_template('home.html', hotels=hotels)

# Route untuk halaman Hotels (semua hotel)
@app.route('/hotels')
def hotels():
    hotels_list = Hotel.query.all()
    return render_template('hotels.html', hotels=hotels_list)

# Route untuk halaman Detail Hotel (per hotel)
@app.route('/hotel/<int:hotel_id>')
def detail_hotel(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    images = hotel.images.split(',') if hotel.images else []
    return render_template('detail_hotel.html', hotel=hotel, images=images)

# Route untuk halaman register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok!', 'danger')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username sudah terdaftar!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role='user')
        db.session.add(new_user)
        db.session.commit()

        flash('Pendaftaran berhasil! Silakan login.', 'success')
        next_page = request.args.get('next')  # Dapatkan URL yang disimpan di parameter 'next'
        return redirect(next_page or url_for('login'))  # Jika tidak ada 'next', arahkan ke halaman login

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifikasi kredensial login
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            print(f'User {user.username} logged in successfully.')
            
            # Jika admin, arahkan ke dashboard
            if user.is_admin():  # Pengecekan role admin
                return redirect(url_for('dashboard'))

            # Arahkan ke halaman user biasa atau halaman yang sesuai
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))

    return render_template('login.html')





# Route untuk logout
@app.route('/logout')
@login_required  # Pastikan hanya pengguna yang login yang bisa logout
def logout():
    logout_user()  # Mengakhiri sesi login pengguna
    flash('Anda telah berhasil logout', 'success')  # Menampilkan pesan sukses
    return redirect(url_for('login'))  # Redirect ke halaman login setelah logout


# Route untuk dashboard admin
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required  # Memastikan hanya pengguna yang login yang bisa mengakses
def dashboard():
    if current_user.role != 'admin':  # Ganti session['role'] menjadi current_user.role
        flash('Anda harus login sebagai admin!', 'danger')
        return redirect(url_for('login'))  # Redirect ke halaman login jika bukan admin

    if request.method == 'POST':
        hotel_name = request.form.get('name')
        location = request.form.get('location')
        description = request.form.get('description')
        price_per_night = request.form.get('price_per_night')

        images = []
        for file in request.files.getlist('images'):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                images.append(filename)

        images_str = ','.join(images)

        new_hotel = Hotel(
            name=hotel_name,
            location=location,
            description=description,
            price_per_night=price_per_night,
            images=images_str
        )
        db.session.add(new_hotel)
        db.session.commit()
        flash('Hotel berhasil ditambahkan!', 'success')
        return redirect(url_for('dashboard'))

    hotels = Hotel.query.all()
    return render_template('dashboard.html', hotels=hotels)


# Route untuk mengedit hotel (CRUD)
@app.route('/edit_hotel/<int:hotel_id>', methods=['GET', 'POST'])
def edit_hotel(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)

    if request.method == 'POST':
        hotel.name = request.form.get('name')
        hotel.location = request.form.get('location')
        hotel.description = request.form.get('description')
        hotel.price_per_night = request.form.get('price_per_night')

        images = []
        for file in request.files.getlist('images'):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                images.append(filename)

        if images:
            hotel.images = ','.join(images)

        db.session.commit()
        flash('Hotel berhasil diperbarui!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_hotel.html', hotel=hotel)

# Route untuk menghapus hotel
@app.route('/delete_hotel/<int:hotel_id>', methods=['POST'])
def delete_hotel(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    db.session.delete(hotel)
    db.session.commit()
    flash('Hotel berhasil dihapus!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        create_admin_account()  # Pastikan admin pertama hanya dibuat sekali
    app.run(debug=True)

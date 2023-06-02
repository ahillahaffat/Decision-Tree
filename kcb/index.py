from flask import Flask, render_template, request
import mysql.connector

def classify_kelas(nilai, sesi):
    if nilai <= 82.5:
        return 'D'
    elif nilai > 94.5:
        return 'A'
    elif nilai <= 89.5:
        if sesi > 58.5:
            return 'B'
        else:
            return 'C'
    elif nilai > 90.5:
        return 'B'
    else:
        return 'C'

app = Flask(__name__)

# Konfigurasi koneksi database
db_config = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': '',
    'database': 'data_siswa'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    id_siswa = int(request.form['id_siswa'])
    nama_siswa = request.form['nama_siswa']
    jumlah_sesi = int(request.form['jumlah_sesi'])
    nilai_rata_rata = float(request.form['nilai_rata_rata'])

    kelas = classify_kelas(nilai_rata_rata, jumlah_sesi)

    data_siswa = {
        'id_siswa': id_siswa,
        'nama_siswa': nama_siswa,
        'jumlah_sesi': jumlah_sesi,
        'nilai_rata_rata': nilai_rata_rata,
        'kelas': kelas
    }

    # Membuat koneksi ke database
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Menjalankan query INSERT untuk menyimpan data siswa ke tabel
        insert_query = "INSERT INTO siswa (id_siswa, nama_siswa, jumlah_sesi, nilai_rata_rata, kelas) VALUES (%s, %s, %s, %s, %s)"
        values = (id_siswa, nama_siswa, jumlah_sesi, nilai_rata_rata, kelas)
        cursor.execute(insert_query, values)
        connection.commit()

        # Menutup koneksi database
        cursor.close()
        connection.close()

        return render_template('result.html', data_siswa=data_siswa)
    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)
        return render_template('error.html')

if __name__ == '__main__':
    app.run(debug=False)

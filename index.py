from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import numpy as np
from sklearn.tree import DecisionTreeClassifier

app = Flask(__name__)

# Konfigurasi koneksi database
db_config = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': '',
    'database': 'data_siswa'
}

# Mengambil data latihan dari database
def get_training_data():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Mengambil data latihan dari tabel siswa
        select_query = "SELECT nilai_rata_rata, jumlah_sesi, kelas FROM siswa"
        cursor.execute(select_query)
        data = cursor.fetchall()

        # Memisahkan atribut dan label
        X_train = [(row[0], row[1]) for row in data]
        y_train = [row[2] for row in data]

        # Menutup koneksi database
        cursor.close()
        connection.close()

        return X_train, y_train
    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)

# Melakukan klasifikasi menggunakan Decision Tree
def classify_kelas(nilai, sesi):
    X_train, y_train = get_training_data()

    # Membangun model Decision Tree
    model = DecisionTreeClassifier()
    model.fit(X_train, y_train)

    # Melakukan prediksi kelas
    X_test = [(nilai, sesi)]
    kelas = model.predict(X_test)[0]

    return kelas, y_train

# Mendapatkan data Confusion Matrix dari database
def get_confusion_matrix():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Mengambil data Confusion Matrix dari tabel confusion_matrix
        select_query = "SELECT prediksi, true, count FROM confusion_matrix"
        cursor.execute(select_query)
        data = cursor.fetchall()

        # Menutup koneksi database
        cursor.close()
        connection.close()

        return data
    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)

# Menghitung persentase kelas
def calculate_class_percentages():
    _, y_train = get_training_data()
    unique_labels, label_counts = np.unique(y_train, return_counts=True)
    class_percentages = {}

    total_samples = np.sum(label_counts)
    for label, count in zip(unique_labels, label_counts):
        percentage = (count / total_samples) * 100
        class_percentages[label] = round(percentage, 2)

    return class_percentages

# Menghitung jumlah siswa dalam setiap kelas
def count_total_kelas():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Mengambil data jumlah siswa dalam setiap kelas dari tabel siswa
        select_query = "SELECT kelas, COUNT(*) FROM siswa GROUP BY kelas"
        cursor.execute(select_query)
        data = cursor.fetchall()

        # Menutup koneksi database
        cursor.close()
        connection.close()

        total_kelas = {}
        for row in data:
            kelas = row[0]
            count = row[1]
            total_kelas[kelas] = count

        return total_kelas
    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)

# Fungsi untuk mengarahkan ke halaman web decision tree
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    id_siswa = int(request.form['id_siswa'])
    nama_siswa = request.form['nama_siswa']
    jumlah_sesi = int(request.form['jumlah_sesi'])
    nilai_rata_rata = float(request.form['nilai_rata_rata'])

    prediksi_kelas, y_train = classify_kelas(nilai_rata_rata, jumlah_sesi)

    # Menghitung Confusion Matrix
    labels = np.unique(y_train)
    confusion_matrix = np.zeros((len(labels), len(labels)), dtype=int)

    for i in range(len(labels)):
        for j in range(len(labels)):
            confusion_matrix[i, j] = np.sum((y_train == labels[i]) & (prediksi_kelas == labels[j]))

    data_siswa = {
        'id_siswa': id_siswa,
        'nama_siswa': nama_siswa,
        'jumlah_sesi': jumlah_sesi,
        'nilai_rata_rata': nilai_rata_rata,
        'kelas': prediksi_kelas
    }

    # Membuat koneksi ke database
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Menjalankan query INSERT untuk menyimpan data siswa ke tabel
        insert_query = "INSERT INTO siswa (id_siswa, nama_siswa, jumlah_sesi, nilai_rata_rata, kelas) VALUES (%s, %s, %s, %s, %s)"
        values = (id_siswa, nama_siswa, jumlah_sesi, nilai_rata_rata, prediksi_kelas)
        cursor.execute(insert_query, values)
        connection.commit()

        # Mendapatkan data Confusion Matrix dari database
        confusion_matrix_data = get_confusion_matrix()

        # Menghitung persentase kelas
        class_percentages = calculate_class_percentages()

        # Logika pemilihan status siswa
        status_siswa = ''
        if prediksi_kelas == 'A':
            status_siswa = 'Lanjut ke kelas selanjutnya'
        elif prediksi_kelas == 'C':
            status_siswa = 'Perlu mengulang kelas'
        elif prediksi_kelas == 'D':
            status_siswa = 'Tidak lulus'

        # Menutup koneksi database
        cursor.close()
        connection.close()

        return render_template('result.html', data_siswa=data_siswa, confusion_matrix=confusion_matrix, labels=labels, confusion_matrix_data=confusion_matrix_data, class_percentages=class_percentages, status_siswa=status_siswa)
    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)
        return render_template('error.html')

@app.route('/decision_tree')
def decision_tree():
    # Mengarahkan ke halaman web decision tree
    return redirect("https://example.com/decision_tree", code=302)

@app.route('/show_table')
def show_table():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Mengambil data siswa dari tabel siswa
        select_query = "SELECT id_siswa, nama_siswa, jumlah_sesi, nilai_rata_rata, kelas FROM siswa"
        cursor.execute(select_query)
        data_siswa = cursor.fetchall()

        # Menutup koneksi database
        cursor.close()
        connection.close()

        # Menghitung jumlah siswa dalam setiap kelas
        total_kelas = count_total_kelas()

        return render_template('decision_tree.html', data_siswa=data_siswa, total_kelas=total_kelas)
    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)
        return render_template('error.html')

@app.route('/deskripsi-siswa/<int:id_siswa>')
def deskripsi_siswa(id_siswa):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Mengambil data siswa berdasarkan ID
        select_query = "SELECT * FROM siswa WHERE id_siswa = %s"
        cursor.execute(select_query, (id_siswa,))
        data_siswa = cursor.fetchone()

        # Menutup koneksi database
        cursor.close()
        connection.close()

        if data_siswa:
            id_siswa = data_siswa[0]
            nama_siswa = data_siswa[1]
            jumlah_sesi = data_siswa[2]
            nilai_rata_rata = data_siswa[3]
            kelas = data_siswa[4]

            return render_template('deskripsi_siswa.html', id_siswa=id_siswa, nama_siswa=nama_siswa, jumlah_sesi=jumlah_sesi, nilai_rata_rata=nilai_rata_rata, kelas=kelas)
        else:
            return render_template('error.html', message='Siswa tidak ditemukan')
    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)
        return render_template('error.html')

if __name__ == '__main__':
    app.run(debug=False)

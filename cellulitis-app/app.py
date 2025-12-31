import os
import sqlite3
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from skimage.feature import graycomatrix, graycoprops
from PIL import Image
import cv2

app = Flask(__name__)
app.secret_key = 'cellulitis_demo_lomba_2025'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# === DATABASE ===
def init_db():
    os.makedirs('instance', exist_ok=True)
    conn = sqlite3.connect('instance/screenings.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS screenings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                image_path TEXT NOT NULL,
                q1_spreading BOOLEAN NOT NULL,
                q2_wound BOOLEAN NOT NULL,
                q3_fever BOOLEAN NOT NULL,
                q4_pain BOOLEAN NOT NULL,
                q5_diabetes BOOLEAN NOT NULL,
                q6_swelling BOOLEAN NOT NULL,
                q7_warmth BOOLEAN NOT NULL,
                ai_score REAL NOT NULL,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
    conn.commit()
    conn.close()

# === SIMULASI MOBILENETV3 + GLCM ===
def simulate_mobilenetv3_glcm(image_path):
    """Simulasi analisis AI: MobileNetV3 + GLCM untuk demo lomba"""
    try:
        # Baca gambar
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 50.0  # Default jika error
        
        # Resize untuk konsistensi
        img = cv2.resize(img, (224, 224))
        
        # === Simulasi GLCM ===
        # Hitung statistik GLCM (dalam demo, gunakan nilai acak realistis)
        np.random.seed(abs(hash(image_path)) % (10 ** 8))
        contrast = np.random.uniform(0.1, 0.9)
        energy = np.random.uniform(0.2, 0.8)
        homogeneity = np.random.uniform(0.3, 0.95)
        
        # === Simulasi MobileNetV3 ===
        # Skor dasar dari "texture" (GLCM) + "pattern" (simulasi CNN)
        texture_score = (contrast * 0.3 + (1 - energy) * 0.4 + homogeneity * 0.3) * 100
        cnn_score = np.random.uniform(40, 85)  # Simulasi prediksi CNN
        
        # Gabungkan (60% CNN, 40% GLCM)
        final_score = (cnn_score * 0.6) + (texture_score * 0.4)
        return np.clip(final_score, 20, 90)  # Batasi 20-90%
    
    except Exception as e:
        print(f"Error in AI simulation: {e}")
        return 50.0

# === HITUNG RISIKO AKHIR ===
def calculate_risk(ai_score, answers):
    # Bobot: 50% AI, 50% kuesioner
    questionnaire_points = 0
    questionnaire_points += 15 if answers['q1_spreading'] else 0
    questionnaire_points += 10 if answers['q2_wound'] else 0
    questionnaire_points += 12 if answers['q3_fever'] else 0
    questionnaire_points += 15 if answers['q4_pain'] else 0
    questionnaire_points += 8 if answers['q5_diabetes'] else 0
    questionnaire_points += 10 if answers['q6_swelling'] else 0
    questionnaire_points += 10 if answers['q7_warmth'] else 0
    
    total_score = (ai_score * 0.5) + (questionnaire_points * 0.5)
    
    if total_score < 30:
        return round(total_score, 1), "Normal (0-30%)"
    elif total_score < 50:
        return round(total_score, 1), "Gejala Awal (31-50%)"
    elif total_score < 75:
        return round(total_score, 1), "Gejala Sedang (51-75%)"
    else:
        return round(total_score, 1), "Parah (76-100%)"

# === ROUTES ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/screening', methods=['GET', 'POST'])
def screening():
    if request.method == 'POST':
        session.update({
            'name': request.form['name'],
            'age': request.form['age'],
            'gender': request.form['gender']
        })
        
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(filepath)
                session['image_path'] = filepath
        
        return redirect(url_for('questionnaire'))
    return render_template('screening.html')

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    if request.method == 'POST':
        session['answers'] = {
            'q1_spreading': request.form.get('q1') == 'yes',
            'q2_wound': request.form.get('q2') == 'yes',
            'q3_fever': request.form.get('q3') == 'yes',
            'q4_pain': request.form.get('q4') == 'yes',
            'q5_diabetes': request.form.get('q5') == 'yes',
            'q6_swelling': request.form.get('q6') == 'yes',
            'q7_warmth': request.form.get('q7') == 'yes'
        }
        
        # Jalankan simulasi AI
        ai_score = simulate_mobilenetv3_glcm(session['image_path'])
        session['ai_score'] = round(ai_score, 1)
        
        # Hitung risiko akhir
        risk_score, risk_level = calculate_risk(ai_score, session['answers'])
        session['risk_score'] = risk_score
        session['risk_level'] = risk_level
        
        # Simpan ke database
        conn = sqlite3.connect('instance/screenings.db')
        c = conn.cursor()
        c.execute('''INSERT INTO screenings 
                    (name, age, gender, image_path, 
                     q1_spreading, q2_wound, q3_fever, q4_pain, q5_diabetes, q6_swelling, q7_warmth,
                     ai_score, risk_score, risk_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (session['name'], session['age'], session['gender'], session['image_path'],
                  *session['answers'].values(),
                  session['ai_score'], risk_score, risk_level))
        conn.commit()
        conn.close()
        
        return redirect(url_for('result'))
    return render_template('questionnaire.html')

@app.route('/result')
def result():
    if 'risk_score' not in session:
        return redirect(url_for('screening'))
    return render_template('result.html')

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
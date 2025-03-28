from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'parole123'

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///climate.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)

@app.route('/')
def index():
    datasets = Dataset.query.all()
    return render_template('index.html', datasets=datasets)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            flash('Nav izvēlēts fails!')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        new_data = Dataset(filename=filename)
        db.session.add(new_data)
        db.session.commit()

        flash('Fails veiksmīgi augšupielādēts!')
        return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/data/<int:id>')
def data(id):
    dataset = Dataset.query.get_or_404(id)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)

    df = pd.read_csv(file_path)

    table = df.head(50).to_html(classes='table table-bordered', index=False)

    return render_template('data.html', table=table, dataset=dataset)

@app.route('/visualize/<int:id>')
def visualize(id):
    dataset = Dataset.query.get_or_404(id)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], dataset.filename)

    df = pd.read_csv(file_path)

    STATIC_FOLDER = 'static'
    if not os.path.exists(STATIC_FOLDER):
        os.makedirs(STATIC_FOLDER)

    temp_hist_filename = None
    scatter_filename = None

    if 'Temperature' in df.columns:
        plt.figure(figsize=(8, 6))
        plt.hist(df['Temperature'], color='skyblue', edgecolor='black', bins=20)
        plt.xlabel('Temperatūra (°C)')
        plt.ylabel('Skaits')
        plt.title('Temperatūras histogramma')

        temp_hist_filename = f'temperature_hist_{id}.png'
        temp_hist_path = os.path.join(STATIC_FOLDER, temp_hist_filename)
        plt.savefig(temp_hist_path)
        plt.close()

    if 'Humidity' in df.columns and 'Temperature' in df.columns:
        plt.figure(figsize=(8, 6))
        plt.scatter(df['Temperature'], df['Humidity'], color='green')
        plt.xlabel('Temperatūra (°C)')
        plt.ylabel('Mitrums (%)')
        plt.title('Temperatūra pret Mitrumu')

        scatter_filename = f'temp_vs_humidity_{id}.png'
        scatter_path = os.path.join(STATIC_FOLDER, scatter_filename)
        plt.savefig(scatter_path)
        plt.close()

    return render_template('visualize.html',
                           dataset=dataset,
                           temp_hist=temp_hist_filename,
                           scatter=scatter_filename)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

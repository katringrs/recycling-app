from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from math import sqrt

app = Flask(__name__)

# SQLite-Datenbank konfigurieren
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Datenbankmodell
class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matrikelnummer = db.Column(db.String(20), nullable=False)
    bezeichnung = db.Column(db.String(100), nullable=False)
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)

# Datenbank erstellen
with app.app_context():
    db.create_all()

# Startseite
@app.route('/')
def index():
    return render_template('index.html')

# Eingabemaske
@app.route('/add', methods=['GET', 'POST'])
def add_model():
    if request.method == 'POST':
        matrikelnummer = request.form['matrikelnummer']
        bezeichnung = request.form['bezeichnung']
        length = float(request.form['length'])
        width = float(request.form['width'])
        height = float(request.form['height'])

        # Neues Modell speichern
        new_model = Model(matrikelnummer=matrikelnummer, bezeichnung=bezeichnung, length=length, width=width, height=height)
        db.session.add(new_model)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_model.html')

# Suchfunktion
@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        search_length = float(request.form['length'])
        search_width = float(request.form['width'])
        search_height = float(request.form['height'])

        # Alle Modelle laden
        models = Model.query.all()

        # Ähnlichkeit berechnen und sortieren
        results = sorted(models, key=lambda m: sqrt(
            (m.length - search_length)**2 +
            (m.width - search_width)**2 +
            (m.height - search_height)**2
        ))

    return render_template('search.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
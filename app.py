from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from math import sqrt
from sqlalchemy import text  # Import hinzufügen

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

        # Neues Modell erstellen und speichern
        new_model = Model(matrikelnummer=matrikelnummer, bezeichnung=bezeichnung, length=length, width=width, height=height)
        db.session.add(new_model)
        db.session.commit()

        # ID des neu erstellten Modells abrufen
        generated_id = new_model.id

        # Zeige eine Bestätigungsseite an, die die ID enthält
        return render_template('add_success.html', model_id=generated_id)

    return render_template('add_model.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Daten aus dem Formular abrufen
        model_id = request.form.get('id', type=int)  # Optional
        bezeichnung = request.form.get('bezeichnung')  # Optional
        length = request.form.get('length', type=float)
        width = request.form.get('width', type=float)
        height = request.form.get('height', type=float)

        # Debugging: Eingabedaten anzeigen
        print("Formulardaten:", request.form)

        # Abfrage für Modell-ID
        if model_id:
            query = "SELECT * FROM model WHERE id = :id"
            params = {"id": model_id}
        elif length is not None and width is not None and height is not None:
            # Abfrage für Maße
            query = "SELECT * FROM model WHERE length = :length AND width = :width AND height = :height"
            params = {"length": length, "width": width, "height": height}

            # Bezeichnung hinzufügen, falls vorhanden
            if bezeichnung:
                query += " AND bezeichnung LIKE :bezeichnung"
                params["bezeichnung"] = f"%{bezeichnung}%"
        else:
            # Fehler, wenn weder ID noch Maße vorhanden sind
            return "Bitte geben Sie entweder eine Modell-ID oder Länge, Breite und Höhe ein.", 400

        # Abfrage ausführen
        results = db.session.execute(text(query), params).fetchall()

        # Debugging: Abfrageergebnisse anzeigen
        print("Suchergebnisse:", results)

        return render_template('search.html', results=results)

    return render_template('search.html', results=None)

if __name__ == '__main__':
    app.run(debug=True)
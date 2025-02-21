from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine.url import make_url
from math import sqrt
from sqlalchemy import text  # Import hinzufügen
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = "geheimespasswort"  # Ändere das für mehr Sicherheit

# PostgreSQL-Verbindung aus der Umgebung einlesen
database_url = os.getenv('DATABASE_URL')

# Falls die URL nicht gesetzt ist, Fehler ausgeben
if not database_url:
    raise ValueError("DATABASE_URL ist nicht gesetzt!")

# Falls die URL mit "postgres://" beginnt, in "postgresql://" umwandeln
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 📌 MODELL-TABELLE
class Model(db.Model):
    __tablename__ = 'models'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Name des Modells
    matrikelnummer = db.Column(db.String(20), nullable=False)
    module_name = db.Column(db.String(100), nullable=False)
    # Beziehung: Ein Modell kann viele Materialien haben
    materials = db.relationship('Material', backref='model', lazy=True, cascade="all, delete")
    approved = db.Column(db.Boolean, default=False) 

# 📌 MATERIAL-TABELLE
class Material(db.Model):
    __tablename__ = 'materials'
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    reserved = db.Column(db.Boolean, default=False)  # 📌 Neu: Reservierung
    archived_at = db.Column(db.DateTime, nullable=True)  # 📌 Neu: Archivierungsdatum

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
        try:
            # Eingabedaten abrufen
            name = request.form['name'].strip()
            matrikelnummer = request.form['matrikelnummer'].strip()
            module_name = request.form['module_name'].strip()  # 📌 Neu hinzugefügt

            material_names = request.form.getlist('material_name[]')
            material_lengths = request.form.getlist('material_length[]')
            material_widths = request.form.getlist('material_width[]')
            material_heights = request.form.getlist('material_height[]')
            material_quantities = request.form.getlist('material_quantity[]')  # 📌 Neu hinzugefügt

            # Validierung: Keine leeren Namen oder Matrikelnummern erlauben
            if not name or not matrikelnummer or not module_name:
                raise ValueError("Name, Matrikelnummer und Modul dürfen nicht leer sein.")

            # Neues Modell erstellen und speichern
            new_model = Model(name=name, matrikelnummer=matrikelnummer, module_name=module_name)
            db.session.add(new_model)
            db.session.commit()
            db.session.refresh(new_model)

            # Materialien dem Modell zuordnen
            if material_names:
                for i in range(len(material_names)):
                    if material_names[i].strip():  # Leere Einträge ignorieren
                        new_material = Material(
                            model_id=new_model.id,
                            name=material_names[i].strip(),
                            length=float(material_lengths[i]),
                            width=float(material_widths[i]),
                            height=float(material_heights[i]),
                            quantity=int(material_quantities[i])  # 📌 Anzahl speichern
                        )
                        db.session.add(new_material)

                db.session.commit()  # Materialien speichern

            return redirect(url_for('all_models'))

        except Exception as e:
            db.session.rollback()  # Falls ein Fehler auftritt, Änderungen zurücknehmen
            print("Fehler beim Speichern des Modells:", str(e))
            return f"Fehler: {str(e)}", 500  # Fehler anzeigen

    return render_template('add_model.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        model_id = request.form.get('id', type=int)
        material_name = request.form.get('bezeichnung')
        module_name = request.form.get('module_name')
        min_quantity = request.form.get('quantity', type=int)
        length = request.form.get('length', type=float)
        width = request.form.get('width', type=float)
        height = request.form.get('height', type=float)

        query = db.session.query(Model).join(Material)

        if model_id:
            query = query.filter(Model.id == model_id)

        if material_name:
            query = query.filter(Material.name.ilike(f"%{material_name}%"))

        if module_name:
            query = query.filter(Model.module_name.ilike(f"%{module_name}%"))

        if min_quantity:
            query = query.filter(Material.quantity >= min_quantity)

        if length is not None and width is not None and height is not None:
            query = query.filter(
                Material.length == length,
                Material.width == width,
                Material.height == height
            )

        results = query.all()

        return render_template('search.html', results=results)

    return render_template('search.html', results=None)

@app.route('/all_models')
def all_models():
    models = Model.query.options(db.joinedload(Model.materials)).all()
    return render_template('all_models.html', models=models)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    try:
        print("DEBUG: Admin-Seite aufgerufen.")  # Prüfen, ob die Route erreicht wird

        if 'admin_logged_in' not in session:
            if request.method == 'POST':
                password = request.form.get("password")
                print(f"DEBUG: Eingegebenes Passwort: {password}")

                if password == "geheimespasswort":
                    session['admin_logged_in'] = True
                    print("DEBUG: Admin erfolgreich eingeloggt.")
                    return redirect(url_for('admin'))

                print("DEBUG: Falsches Passwort.")
                return render_template('login.html', error="❌ Falsches Passwort!")

            print("DEBUG: Zeige Login-Seite an.")
            return render_template('login.html')  # Sollte login.html anzeigen

        print("DEBUG: Zeige Admin-Dashboard an.")
        reserved_materials = Material.query.filter_by(reserved=True).all()
        pending_models = Model.query.filter_by(approved=False).all()

        return render_template('admin.html', reserved_materials=reserved_materials, pending_models=pending_models)

    except Exception as e:
        print(f"ERROR: {e}")
        return f"Interner Serverfehler: {str(e)}", 500

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin'))

@app.route('/release/<int:material_id>', methods=['POST'])
def release_material(material_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))

    material = Material.query.get_or_404(material_id)
    material.reserved = False
    db.session.commit()

    return redirect(url_for('admin'))

# 📌 Modell freigeben
@app.route('/approve/<int:model_id>', methods=['POST'])
def approve_model(model_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))

    model = Model.query.get_or_404(model_id)
    model.approved = True
    db.session.commit()

    return redirect(url_for('admin'))
# 📌 Modell löschen
@app.route('/delete/<int:model_id>', methods=['POST'])
def delete_model(model_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))

    model = Model.query.get_or_404(model_id)
    db.session.delete(model)
    db.session.commit()

    return redirect(url_for('admin'))

@app.route('/reserve/<int:material_id>', methods=['POST'])
def reserve_material(material_id):
    material = Material.query.get_or_404(material_id)
    
    if material.reserved:
        return "Dieses Material ist bereits reserviert.", 400

    material.reserved = True
    db.session.commit()

    return redirect(url_for('search'))

@app.route('/delete_old_archives', methods=['GET'])
def delete_old_archives():
    two_weeks_ago = datetime.utcnow() - timedelta(days=14)
    old_archived = Material.query.filter(Material.archived_at <= two_weeks_ago).all()

    for material in old_archived:
        db.session.delete(material)

    db.session.commit()

    return "Alte archivierte Materialien wurden gelöscht."
    
@app.route('/edit/<int:model_id>', methods=['GET', 'POST'])
def edit_model(model_id):
    # Modell abrufen oder Fehler auslösen
    model = Model.query.get_or_404(model_id)
    
    if request.method == 'POST':
        # Debugging: Eingabedaten prüfen
        print("Formulardaten:", request.form)
        
        # Formular-Daten verarbeiten
        model.matrikelnummer = request.form['matrikelnummer']
        model.bezeichnung = request.form['bezeichnung']
        model.length = float(request.form['length'])
        model.width = float(request.form['width'])
        model.height = float(request.form['height'])

        # Änderungen speichern
        db.session.commit()

        # Debugging: Erfolgreiche Bearbeitung anzeigen
        print(f"Modell {model_id} erfolgreich aktualisiert.")
        
        return redirect(url_for('all_models'))

    # Debugging: Zu bearbeitendes Modell anzeigen
    print("Zu bearbeitendes Modell:", model)
    
    return render_template('edit_model.html', model=model)

if __name__ == '__main__':
    app.run(debug=True)
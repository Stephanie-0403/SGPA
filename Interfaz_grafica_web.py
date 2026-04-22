from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'maracuya_secret_key'

@app.context_processor
def inject_fecha_actual():
    return {'fecha_actual': datetime.now().strftime('%Y-%m-%d')}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        if not usuario or not password:
            flash('No se permiten campos vacíos', 'error')
        elif usuario == 'admin' and password == 'admin': # Ejemplo de validación
            return redirect(url_for('menu'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/usuarios')
def usuarios():
    return render_template('usuarios.html')

@app.route('/materiales')
def materiales():
    return render_template('materiales.html')

@app.route('/prestamos')
def prestamos():
    return render_template('prestamos.html')

@app.route('/devoluciones')
def devoluciones():
    return render_template('devoluciones.html')

@app.route('/reportes')
def reportes():
    return render_template('reportes.html')

if __name__ == '__main__':
    # Flask app running on port 5000 by default
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import backend

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
        else:
            user = backend.validar_login(usuario, password)
            if user:
                return redirect(url_for('menu'))
            else:
                flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/usuarios')
def usuarios():
    usuarios_db = backend.obtener_usuarios()
    return render_template('usuarios.html', usuarios=usuarios_db)

@app.route('/materiales')
def materiales():
    materiales_db = backend.obtener_materiales()
    return render_template('materiales.html', materiales=materiales_db)

@app.route('/prestamos', methods=['GET', 'POST'])
def prestamos():
    if request.method == 'POST':
        id_usuario = request.form.get('id_usuario')
        id_material = request.form.get('id_material')
        fecha_vencimiento = request.form.get('fecha_vencimiento')
        
        exito, msj = backend.registrar_prestamo(id_usuario, id_material, fecha_vencimiento)
        if exito:
            flash(msj, 'success')
            return redirect(url_for('prestamos'))
        else:
            flash(msj, 'error')
            
    usuarios_db = backend.obtener_usuarios()
    materiales_db = backend.obtener_materiales()
    prestamos_activos = backend.obtener_prestamos_activos()
    return render_template('prestamos.html', usuarios=usuarios_db, materiales=materiales_db, prestamos=prestamos_activos)

@app.route('/devoluciones', methods=['GET', 'POST'])
def devoluciones():
    if request.method == 'POST':
        id_prestamo = request.form.get('id_prestamo')
        exito, msj = backend.registrar_devolucion(id_prestamo)
        if exito:
            flash(msj, 'success')
            return redirect(url_for('devoluciones'))
        else:
            flash(msj, 'error')
            
    prestamos_activos = backend.obtener_prestamos_activos()
    return render_template('devoluciones.html', prestamos=prestamos_activos)

@app.route('/reportes')
def reportes():
    return render_template('reportes.html')

if __name__ == '__main__':
    # Flask app running on port 5000 by default
    app.run(debug=True)

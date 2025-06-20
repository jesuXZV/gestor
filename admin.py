from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta' # Consider moving this to an environment variable
DATABASE = 'usuarios.db'
UPLOAD_FOLDER = 'archivos_tareas'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Tabla de usuarios
    cur.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nombre TEXT NOT NULL,
      apellido TEXT,
      nombre_usuario TEXT UNIQUE NOT NULL,
      curso TEXT NOT NULL,
      documento TEXT UNIQUE NOT NULL,
      correo TEXT UNIQUE NOT NULL,
      contrasena TEXT NOT NULL,
      rol TEXT DEFAULT 'rol_usuario',
      fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
      activo INTEGER DEFAULT 1,
      tema TEXT DEFAULT 'claro',
      idioma TEXT DEFAULT 'es',
      notificaciones INTEGER DEFAULT 1
    );''')

    # Tabla de profesores
    cur.execute('''
    CREATE TABLE IF NOT EXISTS profesores (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      usuario_id INTEGER UNIQUE NOT NULL,
      experiencia TEXT,
      materia TEXT,
      lider TEXT,
      telefono TEXT,
      direccion TEXT,
      FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    );''')

    # Tabla de tareas
    cur.execute('''
    CREATE TABLE IF NOT EXISTS tareas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      titulo TEXT NOT NULL,
      descripcion TEXT,
      fecha_vencimiento DATE,
      prioridad TEXT,
      estado TEXT DEFAULT 'pendiente',
      id_proyecto INTEGER,
      id_usuario_asignado INTEGER,
      ruta_archivo TEXT,
      curso_destino TEXT,
      FOREIGN KEY(id_usuario_asignado) REFERENCES usuarios(id) ON DELETE SET NULL
    );''')

    # Tabla de proyectos
    cur.execute('''
    CREATE TABLE IF NOT EXISTS proyectos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nombre TEXT NOT NULL,
      descripcion TEXT,
      fecha_inicio DATE,
      fecha_fin DATE,
      estado TEXT DEFAULT 'activo',
      id_usuario_creador INTEGER,
      FOREIGN KEY(id_usuario_creador) REFERENCES usuarios(id) ON DELETE SET NULL
    );''')

    #Tabla de mensajes
    cur.execute('''
    CREATE TABLE IF NOT EXISTS mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emisor_id INTEGER,
    emisor TEXT,
    receptor_id INTEGER,
    mensaje TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );''')

    # Tabla de notificaciones
    cur.execute('''
    CREATE TABLE IF NOT EXISTS notificaciones (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      mensaje TEXT NOT NULL,
      leido INTEGER DEFAULT 0,
      fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
      id_usuario INTEGER,
      FOREIGN KEY(id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE
    );''')

    # Insertar administrador si no existe
    cur.execute('SELECT COUNT(*) FROM usuarios WHERE nombre_usuario="admin"')
    if not cur.fetchone()[0]:
        cur.execute('''
        INSERT INTO usuarios (nombre, apellido, nombre_usuario, curso, documento, correo, contrasena, rol)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
          'Administrador', 'General', 'admin', 'N/A', '00000000',
          'admin@example.com', generate_password_hash('admin123'),
          'rol_administrador'
        ))

    # Insertar profesor1 si no existe
    cur.execute('SELECT COUNT(*) FROM usuarios WHERE nombre_usuario="profesor1"')
    if not cur.fetchone()[0]:
        cur.execute('''
        INSERT INTO usuarios (nombre, apellido, nombre_usuario, curso, documento, correo, contrasena, rol)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
          'Juan', 'Pérez', 'profesor1', 'Matemáticas', '12345678',
          'profesor1@example.com', generate_password_hash('profesor123'),
          'rol_profesor'
        ))
        profesor1_user_id = cur.lastrowid
        cur.execute('''
        INSERT INTO profesores (usuario_id, experiencia, materia, lider, telefono, direccion)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (profesor1_user_id, '10 años', 'Matemáticas', 'Equipo de Ciencias', '555-1234', 'Calle Falsa 123'))

    conn.commit()
    conn.close()

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Usuario(UserMixin):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM usuarios WHERE id=?', (user_id,)).fetchone()
    conn.close()
    return Usuario(**dict(row)) if row else None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u = request.form['nombre_usuario']
        p = request.form['contrasena']
        conn = get_db_connection()
        row = conn.execute('SELECT * FROM usuarios WHERE nombre_usuario=?', (u,)).fetchone()
        conn.close()
        if row and check_password_hash(row['contrasena'], p) and row['activo']:
            login_user(Usuario(**dict(row)))
            return redirect(url_for(row['rol'].replace('rol_','')))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/crear_usuario', methods=['GET','POST'])
def crear_usuario():
    if request.method=='POST':
        d = {k: request.form[k] for k in ['nombre','nombre_usuario','curso','documento','correo']}
        d['contrasena'] = generate_password_hash(request.form['contrasena'])
        d['rol'] = request.form.get('rol','rol_usuario')
        conn = get_db_connection()
        try:
            conn.execute('''
            INSERT INTO usuarios (nombre,nombre_usuario,curso,documento,correo,contrasena,rol)
            VALUES (:nombre,:nombre_usuario,:curso,:documento,:correo,:contrasena,:rol)
            ''', d)
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('El nombre de usuario, documento o correo ya existe')
        finally:
            conn.close()
    return render_template('crear_usuario.html')

@app.route('/administrador')
@login_required
def administrador():
    if current_user.rol!='rol_administrador':
        return redirect(url_for('index'))
    conn = get_db_connection()
    usuarios = conn.execute('SELECT COUNT(*) FROM usuarios WHERE rol="rol_usuario" AND activo=1').fetchone()[0]
    tareas   = conn.execute('SELECT COUNT(*) FROM tareas').fetchone()[0]
    proyectos= conn.execute('SELECT COUNT(*) FROM proyectos').fetchone()[0]
# ✅ Consulta de profesores activos
    profesores = conn.execute('SELECT id, nombre FROM usuarios WHERE rol="rol_profesor" AND activo=1').fetchall()
    
    conn.close()
    return render_template('admin.html', usuarios=usuarios, tareas=tareas, proyectos=proyectos,profesores=profesores)

@app.route('/profesor')
@login_required
def profesor():
    if current_user.rol != 'rol_profesor':
        return redirect(url_for('index'))
    conn = get_db_connection()
    admin = conn.execute('SELECT id FROM usuarios WHERE rol="rol_administrador" AND activo=1 LIMIT 1').fetchone()
    conn.close()
    return render_template('profesor.html', user=current_user, admin_id=admin['id'] if admin else 1)


@app.route('/api/profesores/count')
@login_required
def api_profesores_count():
    conn = get_db_connection()
    cnt = conn.execute('SELECT COUNT(*) FROM usuarios WHERE rol="rol_profesor" AND activo=1').fetchone()[0]
    conn.close()
    return jsonify(count=cnt)

@app.route('/api/profesores', methods=['GET', 'POST'])
@login_required
def api_profesores():
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            data = request.get_json()
            nombre = data['nombre']
            apellido = data['apellido']
            pwd_hash = generate_password_hash(data.get('contrasena', 'profesor123'))
            cur = conn.cursor()
            try:
               cur.execute('''
                INSERT INTO usuarios
                    (nombre, apellido, nombre_usuario, curso, documento, correo, contrasena, rol)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                data['nombre'], 
                data['apellido'],
                data['nombre_usuario'],
                data.get('curso', ''),
                data['documento'],
                data['correo'],
                pwd_hash,
                'rol_profesor'  # ✅ Este ahora sí está dentro de los 8 valores
                ))
            except sqlite3.IntegrityError:
                conn.rollback()
                return jsonify(error="El nombre de usuario, documento o correo ya existe"), 400
            usuario_id = cur.lastrowid
            cur.execute('''
              INSERT INTO profesores
                (usuario_id, experiencia, materia, lider, telefono, direccion)
              VALUES (?, ?, ?, ?, ?, ?)
            ''', (
              usuario_id,
              data['experiencia'],
              data['materia'],
              data['lider'],
              data['telefono'],
              data['direccion']
            ))
            conn.commit()
            return jsonify(success=True), 201
        else: # GET request
           rows = conn.execute('''
            SELECT
                u.id,
                u.nombre,
                u.apellido,
                u.nombre_usuario,
                u.documento,
                p.experiencia,
                p.materia,
                p.lider,
                u.correo,
                p.telefono,
                p.direccion,
                CASE u.activo WHEN 1 THEN 'Activo' ELSE 'Inactivo' END AS estado,
                u.fecha_registro AS fecha_de_registro
            FROM usuarios u
            JOIN profesores p ON p.usuario_id = u.id
            WHERE u.rol = "rol_profesor"
                AND u.activo = 1;
            ''').fetchall()
           return jsonify([dict(r) for r in rows]), 200
    finally:
        conn.close()

@app.route('/api/profesores/<int:profesor_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_profesor(profesor_id):
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            row = conn.execute('''
                SELECT
                    u.id,
                    u.nombre,
                    u.apellido,
                    u.nombre_usuario,
                    u.documento,
                    u.correo,
                    u.contrasena,
                    u.rol,
                    u.fecha_registro AS fecha_de_registro,
                    u.activo AS estado_activo,
                    p.experiencia,
                    p.materia,
                    p.lider,
                    p.telefono,
                    p.direccion
                FROM usuarios u
                JOIN profesores p ON p.usuario_id = u.id
                WHERE u.id = ? AND u.rol = 'rol_profesor'
            ''', (profesor_id,)).fetchone()

            if row:
                profesor_data = dict(row)
                profesor_data['estado'] = 'Activo' if profesor_data.pop('estado_activo') == 1 else 'Inactivo'
                profesor_data['fecha_de_registro'] = datetime.strptime(
                    profesor_data['fecha_de_registro'], '%Y-%m-%d %H:%M:%S'
                ).isoformat() if profesor_data['fecha_de_registro'] else None

                # Ya no hacer split, usamos el apellido real
                profesor_data['nombre_first'] = profesor_data['nombre']  # Opcional si lo usas en JS
                # profesor_data['apellido'] ya viene desde la base de datos correctamente

                # Imagen
                avatar_filename = f'{profesor_id}.png'
                avatar_path = os.path.join(app.static_folder, 'avatars', avatar_filename)
                if os.path.exists(avatar_path):
                    profesor_data['imagen'] = url_for('static', filename=f'avatars/{avatar_filename}')
                else:
                    profesor_data['imagen'] = url_for('static', filename='avatars/default.png')

                return jsonify(profesor_data), 200
            else:
                return jsonify({'error': 'Profesor no encontrado'}), 404

        elif request.method == 'PUT':
            data = request.get_json()
            if 'estado' in data:
                activo = 1 if data['estado'] == 'Activo' else 0
                conn.execute('UPDATE usuarios SET activo=? WHERE id=?', (activo, profesor_id))
            else:
                conn.execute('''
                    UPDATE usuarios
                    SET nombre=?, apellido=?, nombre_usuario=?, correo=?
                    WHERE id=?
                ''', (data['nombre'], data['apellido'], data['nombre_usuario'], data['correo'], profesor_id))
                conn.execute('''
                    UPDATE profesores
                    SET experiencia=?, materia=?, lider=?, telefono=?, direccion=?
                    WHERE usuario_id=?
                ''', (
                    data['experiencia'], data['materia'], data['lider'],
                    data['telefono'], data['direccion'], profesor_id
                ))
            conn.commit()
            return jsonify(success=True), 200

        elif request.method == 'DELETE':
            conn.execute('UPDATE usuarios SET activo = 0 WHERE id = ?', (profesor_id,))
            conn.commit()
            return jsonify(success=True), 200

    finally:
        conn.close()

@app.route('/crear_tarea_profesor', methods=['POST'])
@login_required
def crear_tarea_profesor():
    tarea_id    = request.form.get('id')
    titulo      = request.form['titulo']
    descripcion = request.form.get('descripcion')
    curso_dest  = request.form.get('curso_destino')
    fecha_venc  = request.form.get('fecha_vencimiento') or None
    prioridad   = request.form.get('prioridad')
    estado      = request.form.get('estado')
    archivo     = request.files.get('archivo')

    ruta_archivo = None
    if archivo and archivo.filename:
        filename = secure_filename(archivo.filename)
        archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    conn = get_db_connection()
    cur  = conn.cursor()
    if tarea_id:
        if ruta_archivo:
            cur.execute('''
                UPDATE tareas
                SET titulo=?, descripcion=?, curso_destino=?, fecha_vencimiento=?,
                    prioridad=?, estado=?, ruta_archivo=?
                WHERE id=?
            ''', (titulo, descripcion, curso_dest, fecha_venc, prioridad, estado,
                  ruta_archivo, tarea_id))
        else:
            cur.execute('''
                UPDATE tareas
                SET titulo=?, descripcion=?, curso_destino=?, fecha_vencimiento=?,
                    prioridad=?, estado=?
                WHERE id=?
            ''', (titulo, descripcion, curso_dest, fecha_venc, prioridad, estado, tarea_id))
    else:
        cur.execute('''
            INSERT INTO tareas
                (titulo, descripcion, curso_destino, fecha_vencimiento,
                 prioridad, estado, ruta_archivo, id_usuario_asignado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (titulo, descripcion, curso_dest, fecha_venc, prioridad,
              estado, ruta_archivo, current_user.id))
    conn.commit()
    conn.close()
    return redirect(url_for('profesor'))

@app.route('/api/profesor/<int:usuario_id>/tareas_por_curso')
@login_required
def api_tareas_por_profesor(usuario_id):
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT
          curso_destino AS curso,
          SUM(CASE WHEN ruta_archivo IS NOT NULL THEN 1 ELSE 0 END) AS entregadas,
          SUM(CASE WHEN ruta_archivo IS NULL THEN 1 ELSE 0 END)     AS pendientes
        FROM tareas
        WHERE id_usuario_asignado = ?
        GROUP BY curso_destino
    ''', (usuario_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/profesores/<int:profesor_id>/tareas', methods=['GET'])
@login_required
def get_profesor_tasks(profesor_id):
    # This endpoint is to fetch tasks assigned by a specific professor.
    # The 'curso' filter is for fetching tasks related to a specific course.
    curso_filter = request.args.get('curso')

    conn = get_db_connection()
    try:
        query = "SELECT id, titulo, descripcion, curso_destino, fecha_vencimiento, prioridad, estado, ruta_archivo FROM tareas WHERE id_usuario_asignado = ?"
        params = [profesor_id]

        if curso_filter and curso_filter != 'Todos':
            query += " AND curso_destino = ?"
            params.append(curso_filter)

        rows = conn.execute(query, params).fetchall()
        tasks = []
        for row in rows:
            task = dict(row)
            task['fecha_vencimiento'] = task['fecha_vencimiento'] # Already a string from DB or None
            # In a real app, you might also want to fetch the "promedio" or "pendiente"
            # which would involve joining with other tables or calculating on the fly.
            # For now, let's keep it simple based on the given log.
            tasks.append(task)
        return jsonify(tasks), 200
    finally:
        conn.close()


@app.route('/api/materia/<materia>/profesores')
@login_required
def api_profesores_por_materia(materia):
    conn = get_db_connection()
    rows = conn.execute('''
      SELECT
        u.id,
        u.nombre AS nombre,
        u.apellido AS apellido,
        u.correo,
        p.telefono,
        p.direccion
      FROM usuarios u
      JOIN profesores p ON p.usuario_id = u.id
      WHERE p.materia = ?
        AND u.activo = 1
    ''', (materia,)).fetchall()
    lista = []
    for r in rows:
        uid = r['id']
        avatar = f'avatars/{uid}.png'
        if not os.path.exists(os.path.join(app.static_folder, avatar)):
            avatar = 'avatars/default.png'
        lista.append({
            'id':        uid,
            'nombre':    r['nombre'],
            'apellido':  r['apellido'],
            'correo':    r['correo'],
            'telefono':  r['telefono'],
            'direccion': r['direccion'],
            'imagen':    url_for('static', filename=avatar)
        })
    conn.close()
    return jsonify(lista)



@app.route('/api/estudiantes/count')
def estudiantes_count():
    conn = get_db_connection()
    cnt = conn.execute('SELECT COUNT(*) FROM usuarios WHERE rol="rol_usuario" AND activo=1').fetchone()[0]
    conn.close()
    return jsonify(count=cnt)


@app.route('/api/materias/count')
def materias_count():
    conn = get_db_connection()
    # This query assumes 'materia' in the 'profesores' table holds distinct subjects
    # You might have a separate 'materias' table if your schema is more complex
    cnt = conn.execute('SELECT COUNT(DISTINCT materia) FROM profesores').fetchone()[0]
    conn.close()
    return jsonify(count=cnt)

# Ver mensajes para un profesor
@app.route('/mensajes_profesor/<int:receptor_id>')
@login_required
def mensajes_profesor(receptor_id):
    conn = get_db_connection()
    mensajes = conn.execute('''
        SELECT emisor, mensaje, fecha
        FROM mensajes
        WHERE receptor_id = ?
        ORDER BY fecha ASC
    ''', (receptor_id,)).fetchall()
    conn.close()
    return jsonify([dict(m) for m in mensajes])

@app.route('/mensajes_con/<int:otro_usuario_id>')
@login_required
def mensajes_con(otro_usuario_id):
    """
    Devuelve el historial de mensajes entre el usuario logueado (admin o profesor)
    y el usuario cuyo ID es 'otro_usuario_id'.
    """
    mi_id = current_user.id  # Puede ser admin o profesor
    conn = get_db_connection()
    mensajes = conn.execute('''
        SELECT emisor, mensaje, fecha
        FROM mensajes
        WHERE 
            (receptor_id = ? AND emisor_id = ?)
            OR
            (receptor_id = ? AND emisor_id = ?)
        ORDER BY fecha ASC
    ''', (mi_id, otro_usuario_id, otro_usuario_id, mi_id)).fetchall()
    conn.close()
    return jsonify([dict(m) for m in mensajes])


@app.route('/mensajes_admin')
@login_required
def mensajes_admin():
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT emisor, mensaje FROM mensajes
        WHERE receptor_id = ?
        ORDER BY fecha ASC
    ''', (current_user.id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# Enviar mensaje a un profesor
@app.route('/enviar_mensaje', methods=['POST'])
@login_required
def enviar_mensaje():
    data = request.get_json()
    emisor = current_user.nombre
    emisor_id = current_user.id   # Nuevo
    receptor_id = data['receptor_id']
    mensaje = data['mensaje']

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO mensajes (emisor, emisor_id, receptor_id, mensaje)
        VALUES (?, ?, ?, ?)
    ''', (emisor, emisor_id, receptor_id, mensaje))
    conn.commit()
    conn.close()
    return jsonify(success=True)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/actualizar_perfil', methods=['POST'])
@login_required
def actualizar_perfil():
    nombre = request.form['nombre']
    sobre_mi = request.form.get('sobre_mi', '')
    avatar = request.files.get('avatar')

    conn = get_db_connection()
    conn.execute('UPDATE usuarios SET nombre=?, sobre_mi=? WHERE id=?', (nombre, sobre_mi, current_user.id))
    conn.commit()
    conn.close()

    # Guardar avatar si se subió uno nuevo
    if avatar and avatar.filename:
        filename = f"{current_user.nombre_usuario}.png"
        avatar.save(os.path.join(app.static_folder, 'avatars', filename))

    flash('Perfil actualizado correctamente.')
    return redirect(url_for('administrador'))

if __name__=='__main__':
    init_db()
    app.run(debug=True)


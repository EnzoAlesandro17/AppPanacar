## Estructura del proyecto

```
AppPanacar/
├── RODO.txt                        # Notas personales del desarrollo: qué se hizo, qué falta, decisiones e ideas a futuro
├── readme.md                       # Este archivo
├── requirements.txt                 # Dependencias del proyecto (Flask, Flask-WTF)
├── app.py                           # Entrypoint: crea la app con create_app() y la corre (flask run / python app.py)
├── .gitignore                       # Ignora .venv/, data/, __pycache__/ y .env
├── data/
│   └── database.db                  # Base de datos SQLite local con los datos (se crea/usa en runtime, ignorada por git)
├── .venv/                           # Entorno virtual de Python (ignorado por git)
├── .vscode/
│   └── settings.json                 # Configuración del editor (selección del entorno de Python)
├── .claude/
│   └── settings.local.json           # Permisos locales de Claude Code para este repo
└── src/
    ├── __init__.py
    ├── app.py                        # create_app(): fábrica de la app Flask, crea las tablas y registra los blueprints
    ├── auth.py                       # login_required: exige sesión activa (flask.session) para acceder a una vista
    ├── config.py                     # Rutas base del proyecto, ubicación de la base de datos (DB_PATH) y SECRET_KEY
    ├── exceptions.py                 # ValidationError: excepción usada en todo el backend para errores de validación de negocio
    ├── permissions.py                # Reglas de qué rol (Admin/BackOffice/Asesor) puede hacer qué acción, centralizadas
    ├── constants/
    │   ├── settings.py                # Constantes generales: nombre y versión de la app, timeout, intentos máximos de login
    │   └── validations.py             # Validaciones genéricas reutilizables: email, teléfono, DNI, CUIT, fechas, edad mínima, campos obligatorios
    ├── db/
    │   ├── __init__.py
    │   └── connection.py              # Conexión centralizada a SQLite: GestorDB.conectar() y obtener_conexion() (context manager, con foreign_keys ON)
    ├── static/
    │   └── css/style.css              # Estilos mínimos compartidos por todas las páginas
    ├── templates/
    │   ├── base.html                  # Layout común: header con usuario logueado, nav, mensajes flash
    │   ├── administrar/index.html      # Índice de "Administrar" con los links a cada módulo
    │   ├── user/{login,listar,formulario,borrados}.html
    │   ├── branches/{listar,formulario,borrados}.html
    │   ├── clients/{listar,formulario,borrados}.html
    │   ├── products/{listar,formulario,borrados}.html
    │   ├── validaciones/index.html      # Índice de "Validaciones" con los links a cada catálogo
    │   ├── vehicle_brands/{listar,formulario,borrados}.html
    │   └── insurance_companies/{listar,formulario,borrados}.html
    └── modules/
        └── administrar/
            ├── __init__.py
            ├── routes.py               # Blueprint 'administrar': índice de la sección (/administrar)
            ├── branches/               # Módulo de sucursales
            │   ├── db.py                 # Creación de la tabla branches
            │   ├── logic.py              # CRUD y validaciones de sucursales (alta, edición, borrado lógico, búsqueda)
            │   └── routes.py             # Blueprint 'branches': vistas HTTP (/branches), CRUD completo (listar/nuevo/editar/borrar/reactivar)
            ├── clients/                 # Módulo de clientes
            │   ├── db.py                 # Creación de la tabla clients
            │   ├── logic.py              # CRUD y validaciones de clientes (DNI/CUIT, teléfono, email, borrado lógico)
            │   └── routes.py             # Blueprint 'clients': vistas HTTP (/clients), CRUD completo (listar/nuevo/editar/borrar/reactivar)
            ├── products/                # Módulo de productos
            │   ├── db.py                 # Creación de la tabla products
            │   ├── logic.py              # CRUD, validación de precios mayorista/minorista y manejo de stock (incluye productos sin stock físico)
            │   └── routes.py             # Blueprint 'products': vistas HTTP (/products), CRUD completo + compatibilidad con vehículos
            ├── user/                    # Módulo de usuarios
            │   ├── db.py                 # Creación de la tabla users (con role y branch_id como FK a branches)
            │   ├── logic.py              # CRUD de usuarios, hash de contraseñas (pbkdf2_hmac + salt) y lógica de login (iniciar_sesion)
            │   └── routes.py             # Blueprint 'user': login, logout y CRUD completo (/user), restringido a Admin/BackOffice salvo login/logout
            └── validaciones/            # Catálogos de referencia usados por otros módulos
                ├── routes.py              # Blueprint 'validaciones': índice de la sección (/validaciones)
                ├── vehicle_brands/        # Marcas de vehículos (FK desde product_compatibility)
                │   ├── db.py
                │   ├── logic.py            # CRUD y borrado lógico
                │   └── routes.py           # Blueprint 'vehicle_brands' (/vehicle-brands)
                └── insurance_companies/   # Compañías de seguro (catálogo, todavía sin usar desde otro módulo)
                    ├── db.py
                    ├── logic.py            # CRUD y borrado lógico
                    └── routes.py           # Blueprint 'insurance_companies' (/insurance-companies)
```

Nota: el frontend HTML recién arranca. Se removió la versión anterior en Tkinter (heredada de la copia del proyecto viejo) y ahora hay una capa web mínima con Flask: cada módulo trae su propio `routes.py` (blueprint) al lado de su `db.py`/`logic.py`, y sus templates viven en `src/templates/<módulo>/`. Sucursales, clientes, productos y usuarios ya tienen CRUD completo desde HTML (listar/nuevo/editar/borrar lógico/reactivar), incluida la compatibilidad de productos con vehículos. Pensado para funcionar en dos sucursales con equipos que no siempre tienen conexión a internet.

Además de esos 4 módulos, `src/modules/administrar/validaciones/` agrupa catálogos de referencia con el mismo patrón CRUD (db/logic/routes): **marcas de vehículos** y **compañías de seguro**. La compatibilidad de un producto con un vehículo (`product_compatibility.brand_vehicle_id`) ya referencia una marca cargada en el catálogo en vez de texto libre; la migración de `brand_vehicle` (texto) a `brand_vehicle_id` (FK) se hace sola al arrancar la app si detecta el esquema viejo (`crear_tabla_compatibilidad` en `products/db.py`). Compañías de seguro todavía no está enganchado a ningún otro módulo: la aseguradora va a ir asociada al futuro siniestro (cliente + vehículo + aseguradora), no al cliente directamente — ver RODO.txt.

Para correr la app: `python app.py` (o `flask --app app run`) desde la raíz, con el venv activado.

## Medidas de seguridad

- **Contraseñas hasheadas**: nunca se guarda texto plano. Se usa `pbkdf2_hmac` (SHA-256, 100.000 iteraciones) con salt aleatorio por usuario (`src/modules/administrar/user/logic.py`).
- **Política de contraseñas**: largo mínimo 8 y máximo 64 caracteres, siguiendo NIST SP 800-63B (el estándar actual de la comunidad). Sin reglas de complejidad forzada (mayúscula/número/símbolo) a propósito: ese mismo estándar las desaconseja porque en la práctica producen contraseñas predecibles sin mejorar la seguridad real (`validar_password` en `src/constants/validations.py`).
- **Login sin fuga de información**: si el usuario o la contraseña fallan, el mensaje de error es siempre el mismo genérico, para no revelar cuál de los dos estuvo mal. Tras `MAX_LOGIN_ATTEMPTS` (3) intentos fallidos seguidos, la cuenta se bloquea temporalmente por `TIMEOUT_SECONDS` (30 segundos) (`iniciar_sesion` en `user/logic.py`).
- **Permisos por rol**: quién puede gestionar usuarios o cambiar contraseñas de quién está centralizado en `src/permissions.py`, con una jerarquía real (Admin > BackOffice > Asesor) en vez de reglas sueltas repetidas por módulo. Por ahora todos los roles acceden a todos los módulos salvo la gestión de usuarios (reservada a Admin/BackOffice); el resto de las restricciones por rol se irán sumando más adelante.
- **Validación de documentos reales**: el CUIT valida su dígito verificador con el algoritmo módulo 11 (el mismo que usa AFIP), no solo la cantidad de dígitos — evita cargar CUITs inventados o mal tipeados (`validar_cuit`).
- **Teléfonos en formato estándar**: se valida contra E.164 (estándar internacional ITU-T), en vez de un formato fijo hardcodeado a un solo país (`validar_telefono`).
- **Borrado lógico**: ningún módulo hace `DELETE` real — todas las tablas tienen columna `status` (1 = activo, 0 = borrado), así nunca se pierden datos de auditoría por error.
- **Consultas parametrizadas**: todas las queries a SQLite usan placeholders (`?`), nunca se arma SQL concatenando texto ingresado por el usuario — evita inyección SQL.
- **Protección CSRF**: `Flask-WTF` (`CSRFProtect`) está activado globalmente en `create_app()` (`src/app.py`); todos los `<form method="post">` llevan su `csrf_token` oculto. Cualquier POST sin token válido responde 400 antes de llegar a la vista.

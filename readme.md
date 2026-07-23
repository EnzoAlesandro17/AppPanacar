## Estructura del proyecto

```
AppPanacar/
├── RODO.txt                        # Notas personales del desarrollo: qué se hizo, qué falta, decisiones e ideas a futuro
├── readme.md                       # Este archivo
├── requirements.txt                 # Dependencias del proyecto (Flask, Flask-WTF, psycopg, pytest)
├── pytest.ini                        # testpaths = tests
├── app.py                           # Entrypoint: crea la app con create_app() y la corre (flask run / python app.py)
├── .gitignore                       # Ignora .venv/, __pycache__/, .pytest_cache/ y .env
├── tests/                            # Un archivo de test por módulo/feature; ver tests/ para el detalle
│   └── conftest.py                   # Fixtures: app/client con un schema de Postgres propio y aislado por test,
│                                      # extraer_csrf(), fixtures de usuario logueado (admin/backoffice/asesor)
├── .env.example                     # Variables de entorno del deploy (DATABASE_URL, SECRET_KEY, etc.), documentadas
├── .venv/                           # Entorno virtual de Python (ignorado por git)
├── .vscode/
│   └── settings.json                 # Configuración del editor (selección del entorno de Python)
├── .claude/
│   └── settings.local.json           # Permisos locales de Claude Code para este repo
└── src/
    ├── __init__.py
    ├── app.py                        # create_app(): fábrica de la app Flask, crea las tablas y registra los blueprints
    ├── auth.py                       # login_required (con corte de sesión por día calendario), restringir_a_administracion,
    │                                  # requiere_ver_eliminados, requiere_ver_bitacora
    ├── permissions.py                 # Reglas de qué rol (IT/BackOffice/Asesor) puede hacer qué acción, centralizadas
    ├── config.py                     # IS_PRODUCTION (APP_ENV), DATABASE_URL y SECRET_KEY (obligatorios en producción)
    ├── exceptions.py                 # ValidationError y RegistroBorradoExistente, usadas en todo el backend
    ├── breadcrumbs.py                 # migas(): arma la lista (etiqueta, endpoint) que pinta el breadcrumb de navegación
    ├── cli.py                         # Comando `flask create-it`: bootstrap del primer usuario IT, sin depender de la UI
    ├── constants/
    │   ├── settings.py                # Constantes generales: nombre/versión de la app, timeout e intentos de login,
    │   │                               # duración de la cookie de sesión
    │   └── validations.py             # Validaciones genéricas reutilizables: email, teléfono, DNI, CUIT, fechas
    │                                   # (dd/mm/aaaa <-> ISO), edad mínima, campos obligatorios, password (NIST 800-63B)
    ├── db/
    │   └── connection.py              # Conexión centralizada a Postgres (GestorDB.conectar()/obtener_conexion()),
    │                                   # con una capa de compatibilidad para no reescribir cada módulo: placeholders
    │                                   # `?`, `cursor.lastrowid` vía RETURNING, `except sqlite3.IntegrityError`
    ├── static/
    │   ├── css/style.css              # Estilos compartidos por todas las páginas (variables de color, claro/oscuro)
    │   └── js/                        # Vanilla, sin librerías/CDN (la app tiene que poder andar offline):
    │       ├── reorder.js               # Arrastrar y soltar para reordenar listados (Pointer Events, anda en celular)
    │       ├── menu-usuario.js          # Dropdown de "Mi cuenta"/"Configuración"/"Salir" en el avatar del header
    │       ├── mostrar-password.js       # Ícono de ojo (abierto/cerrado) genérico para mostrar/ocultar contraseñas
    │       ├── buscador.js              # Filtro en vivo (sin ir al server) de filas de tabla o <option> de un <select>
    │       ├── combobox.js              # Combobox buscable con "+ Agregar nuevo" (cliente/vehículo en Siniestros)
    │       └── cancelar.js              # Botón "Cancelar" de los formularios: vuelve a la página anterior (history.back)
    ├── templates/
    │   ├── base.html                  # Layout común: header con usuario logueado, nav con breadcrumb, mensajes flash;
    │   │                               # <html data-theme="..."> según la preferencia guardada en sesión
    │   ├── _macros.html                 # Macro campo_password(): input + botón de ojo, reusado en login/formularios
    │   ├── administrar/index.html      # Pantalla principal "Sistema de gestión": Administración, Siniestros, Clientes,
    │   │                               # Vehículos, Stock, Links útiles
    │   ├── administracion/index.html    # Índice de "Administración": Sucursales, Empleados, Usuarios, Validaciones,
    │   │                               # Contabilidad, Preguntas frecuentes y (solo IT) Bitácora
    │   ├── configuracion/index.html      # Preferencia de tema (claro/oscuro) por usuario
    │   ├── contabilidad/index.html      # Placeholder (todavía sin diseñar)
    │   ├── preguntas_frecuentes/index.html # Contenido estático (<details>/<summary> agrupados por categoría, sin JS)
    │   ├── bitacora/listar.html         # Registro de actividad de todo el equipo (login/logout, altas, errores), solo IT
    │   ├── tasks/{listar,cerradas,formulario,detalle}.html # Tablón de tareas compartido
    │   ├── siniestros/{listar,formulario,actividad,borrados}.html # Núcleo de Siniestros + línea de tiempo de Actividad
    │   ├── user/{login,listar,formulario,borrados,perfil}.html
    │   ├── employees/{listar,formulario,borrados}.html
    │   ├── branches/{listar,formulario,borrados}.html
    │   ├── clients/{listar,formulario,borrados}.html
    │   ├── products/{listar,formulario,borrados}.html    # Tile/breadcrumb dice "Stock"; templates y rutas siguen en products
    │   ├── vehicles/{listar,formulario,borrados}.html
    │   ├── informacion_util/{listar,formulario,borrados}.html # "Links útiles" (nombre visible; por dentro informacion_util)
    │   ├── validaciones/index.html      # Índice de "Validaciones" con los links a cada catálogo
    │   ├── vehicle_brands/{listar,formulario,borrados}.html
    │   ├── insurance_companies/{listar,formulario,borrados}.html
    │   ├── claim_types/{listar,formulario,borrados}.html      # Tipo de siniestro (catálogo)
    │   └── claim_statuses/{listar,formulario,borrados}.html   # Estado de siniestro (catálogo)
    └── modules/
        └── administrar/
            ├── routes.py               # Blueprint 'administrar': pantalla principal "Sistema de gestión" (/)
            ├── administracion/          # Índice de "Administración" (agrupa sucursales/usuarios/validaciones/etc.)
            ├── branches/               # Sucursales
            ├── clients/                 # Clientes
            ├── products/                # Stock (por dentro sigue llamándose products)
            ├── vehicles/                # Vehículos concretos (patente, modelo, año; marca es FK a vehicle_brands)
            ├── user/                    # Usuarios: SOLO acceso al sistema (username/password/role/employee_id opcional)
            ├── employees/               # Empleados: ficha de personal, separada del acceso al sistema
            ├── informacion_util/        # "Links útiles"
            ├── preguntas_frecuentes/    # Contenido estático, dentro de Administración
            ├── contabilidad/            # Placeholder, dentro de Administración
            ├── configuracion/           # Preferencias por usuario (hoy: tema claro/oscuro)
            ├── bitacora/                # Registro de actividad de todo el equipo, solo IT
            ├── tasks/                   # Tablón de tareas compartido
            ├── siniestros/              # Núcleo de Siniestros + Actividad (línea de tiempo)
            └── validaciones/            # Catálogos de referencia usados por otros módulos
                ├── vehicle_brands/        # Marcas de vehículos
                ├── insurance_companies/   # Compañías de seguro
                ├── claim_types/           # Tipo de siniestro
                └── claim_statuses/        # Estado de siniestro
```

Cada módulo trae su propio `db.py` (esquema + migraciones), `logic.py` (validaciones y acceso a datos) y `routes.py` (blueprint con las vistas HTTP), con sus templates en `src/templates/<módulo>/`. Separar en db/logic/routes desde el arranque hizo que cada módulo nuevo fuera calcar el patrón anterior en vez de inventar de nuevo. Pensado para funcionar en dos sucursales con equipos que no siempre tienen conexión a internet — nada de JS de librerías externas ni CDN, todo vanilla.

### Roles y sucursales

Tres roles: **IT** (maneja todo, sin restricciones), **BackOffice** (igual que IT salvo que no ve listas de "eliminados" en ningún módulo ni la Bitácora) y **Asesor** (además, sin acceso a la sección Administración). Reglas centralizadas en `src/permissions.py`, aplicadas vía `src/auth.py` (`restringir_a_administracion` como `before_request` de cada blueprint de Administración, `requiere_ver_eliminados`/`requiere_ver_bitacora` como decorator en las vistas puntuales).

Los 3 roles quedan además acotados por las sucursales de las que forman parte (`user_branches`, N:N igual que `employee_branches`), guardadas en `session["branch_ids"]` al loguearse. Clientes, Vehículos y Stock tienen su propia relación N:N con sucursales y se filtran por eso; un registro sin ninguna sucursal asignada queda visible para todos (dato sin asignar, no oculto). Siniestros es distinto: la sucursal ahí es una FK simple (un siniestro se gestiona desde un único lugar), no N:N.

### Siniestros

Es la entidad que une **cliente + vehículo + aseguradora + tipo + estado**, con su propio historial. `/siniestros/nuevo` y `/siniestros/<id>/editar` usan un combobox buscable (`combobox.js`) para elegir el cliente/vehículo existente escribiendo su nombre/DNI/dominio, con una opción "+ Agregar nuevo" al final de la lista que despliega el alta inline (sin salir del formulario) si no existe todavía.

`/siniestros/<id>/actividad` es la línea de tiempo del siniestro: mezcla cronológicamente los cambios de estado (automáticos, con quién y cuándo) y observaciones libres que carga el equipo, y tiene un panel rápido para cambiar Estado/Sucursal/Aseguradora/Tipo sin ir al formulario completo. El historial de cambios de estado (`siniestro_status_history`) y los comentarios (`siniestro_comentarios`) son tablas separadas; `listar_actividad()` en `siniestros/logic.py` las combina.

Catálogos asociados (en Validaciones): **Tipo de siniestro** y **Estado de siniestro**, ambos con el mismo patrón CRUD + borrado lógico + orden editable que Marcas de vehículos/Compañías de seguro.

### Tareas y Bitácora

**Tareas** (`/tareas`) es un tablón compartido: título, descripción, sucursales y usuarios asignados, comentarios, y cerrar/reabrir (nunca se borra). El link "Tareas" del header muestra un contador de no vistas por el usuario logueado.

**Bitácora** (`/bitacora`, solo IT) registra actividad de todo el equipo — logueos, logout, y cualquier acción que deje un mensaje flash (altas, ediciones, errores de validación) — vía un `after_request` liviano en `create_app()`, sin tener que instrumentar cada vista a mano.

### Interfaz

- **Modo oscuro**: preferencia por usuario en `/configuracion` (columna `theme` en `users`), aplicada en sesión al loguearse (`<html data-theme="...">` en `base.html`). Los colores salen de variables CSS en `:root`, con overrides en `:root[data-theme="dark"]` — evita duplicar reglas de layout por tema. Paleta y tipografía/espaciado basados en el design system interno. Ver detalle completo en: https://github.com/EnzoAlesandro17/design-system
- **Buscadores**: Clientes, Vehículos, Stock y Siniestros tienen un filtro en vivo arriba de la tabla (`buscador.js`, sin ir al server) para no depender de scrollear listas largas.
- **Botón Cancelar**: todo formulario con "Guardar" tiene al lado un "Cancelar" que vuelve a la página anterior sin guardar nada (`cancelar.js`, `history.back()`).
- **Orden editable (arrastrar y soltar)**: sucursales, usuarios, marcas de vehículos, compañías de seguro, tipos y estados de siniestro tienen una columna `sort_order` y se reordenan arrastrando la fila desde el ícono ⠿ (`reorder.js`, Pointer Events — no la API nativa de HTML5, que no anda en touch). Clientes, productos, vehículos y siniestros no tienen esto: son listas que crecen mucho y no tiene sentido ordenarlas a mano (para esas están los buscadores).
- **Fechas** en los formularios en `dd/mm/aaaa` (`<input type="text">` con `pattern`, no `<input type="date">`: ese input respeta el idioma/región del navegador, no el `lang` de la página). `parsear_fecha_visual`/`formatear_fecha_visual` (`src/constants/validations.py`) hacen la conversión hacia/desde el `aaaa-mm-dd` que se guarda en la base; el filtro de Jinja `fecha_visual` se usa en los templates para mostrarlas.
- **Avatar del header** (dos letras: inicial del nombre + inicial del apellido) abre un dropdown con **Mi cuenta**, **Configuración** y **Salir**.
- El nav de todas las páginas (`base.html`) muestra un **breadcrumb** en vez de un botón fijo "Volver": cada tramo es un link a ese nivel salvo el último. Cada blueprint arma el suyo con un helper `_migas(*ultimos)` local, apoyado en `migas()` de `src/breadcrumbs.py`.
- Convención de URLs: todas en español, coinciden con el título visible de cada página (`/sucursales`, `/stock`, `/tipos-siniestro`, etc.); blueprints/tablas/módulos por dentro se quedan en inglés.

### Correr la app y los tests

Necesita Postgres corriendo (ver RODO.txt para el comando de Docker con el contenedor local). Copiar `.env.example` a `.env` y completar `DATABASE_URL` si no se usa el default de desarrollo.

Para correr la app: `python app.py` (o `flask --app app run`) desde la raíz, con el venv activado.

Para correr los tests: `pytest` desde la raíz, con el venv activado. Cada test crea su propio schema de Postgres (vacío y aislado) y lo borra al terminar (`tests/conftest.py` parchea `src.db.connection.SCHEMA`), así que nunca tocan datos reales.

## Medidas de seguridad

- **Contraseñas hasheadas**: nunca se guarda texto plano. Se usa `pbkdf2_hmac` (SHA-256, 100.000 iteraciones) con salt aleatorio por usuario (`src/modules/administrar/user/logic.py`).
- **Política de contraseñas**: largo mínimo 8 y máximo 64 caracteres, siguiendo NIST SP 800-63B. Sin reglas de complejidad forzada (mayúscula/número/símbolo) a propósito: ese mismo estándar las desaconseja porque en la práctica producen contraseñas predecibles sin mejorar la seguridad real (`validar_password`).
- **Login sin fuga de información**: mensaje de error genérico si usuario o contraseña fallan. Tras `MAX_LOGIN_ATTEMPTS` (3) intentos fallidos seguidos, la cuenta se bloquea temporalmente por `TIMEOUT_SECONDS` (30 segundos).
- **Sesión acotada por día**: `login_required` fuerza un nuevo login si la sesión sigue abierta de un día calendario anterior, aunque la cookie siga viva; la cookie en sí lleva `HttpOnly` y `SameSite=Lax`.
- **Permisos por rol**: IT/BackOffice/Asesor, con jerarquía real (IT > BackOffice > Asesor) centralizada en `src/permissions.py`. Toda la sección **Administración** es exclusiva de IT/BackOffice (`restringir_a_administracion` como `before_request` de cada blueprint, cubre rutas nuevas sin repetir el chequeo a mano); Clientes, Vehículos, Stock, Siniestros, Tareas, Links útiles, Configuración y Mi cuenta quedan afuera a propósito.
- **Ver eliminados y Bitácora restringidos a IT**: BackOffice y Asesor manejan todo lo demás, pero ninguno puede ver listas de eliminados en ningún módulo (`puede_ver_eliminados`) ni la Bitácora (`puede_ver_bitacora`). Si un BackOffice/Asesor intenta cargar un registro que choca con uno ya borrado (mismo DNI/CUIT, dominio, code, username o nombre de catálogo), el sistema levanta `RegistroBorradoExistente` y la vista ofrece reactivar el existente en vez de rechazar por duplicado.
- **Sucursales acotan Clientes/Vehículos/Stock/Siniestros**: cada usuario pertenece a una o varias sucursales (`user_branches`); `listar_*` filtra por esas sucursales y cada vista de edición/borrado repite el chequeo a nivel de fila, no solo lo oculta del listado.
- **Validación de documentos reales**: el CUIT valida su dígito verificador con el algoritmo módulo 11 (el mismo que usa AFIP). Teléfonos validados contra E.164.
- **Borrado lógico**: ningún módulo hace `DELETE` real — todas las tablas tienen columna `status` (1 = activo, 0 = borrado).
- **Consultas parametrizadas**: todas las queries a la base usan placeholders (`?`, traducidos a `%s` de Postgres en `src/db/connection.py`), nunca se arma SQL concatenando texto ingresado por el usuario.
- **Protección CSRF**: `Flask-WTF` (`CSRFProtect`) activado globalmente. Cualquier POST sin token válido responde 400 antes de llegar a la vista.
- **Usuarios (acceso) separado de Empleados (personal)**: `users` es solo username/password/role/`employee_id` opcional; los datos personales viven en `employees`. `/usuarios/perfil` ("Mi cuenta") solo deja tocar username y contraseña, nunca `role` ni `employee_id`.
- **Cambio de contraseña propia exige la contraseña actual**: solo en `/usuarios/perfil` (autogestión); la edición admin (`/usuarios/<id>/editar`, IT/BackOffice) no la exige.

## Estructura del proyecto

```
AppPanacar/
├── RODO.txt                        # Notas personales del desarrollo: qué se hizo, qué falta, decisiones e ideas a futuro
├── readme.md                       # Este archivo
├── requirements.txt                 # Dependencias del proyecto (Flask, Flask-WTF, pytest)
├── pytest.ini                        # testpaths = tests
├── app.py                           # Entrypoint: crea la app con create_app() y la corre (flask run / python app.py)
├── .gitignore                       # Ignora .venv/, data/, __pycache__/, .pytest_cache/ y .env
├── tests/
│   ├── conftest.py                   # Fixtures: app/client con una SQLite temporal por test (aislada de data/database.db), extraer_csrf(), fixture admin logueado
│   ├── test_validations.py           # Funciones puras de constants/validations.py (CUIT, DNI, email, teléfono, password, dominio, año)
│   ├── test_breadcrumbs.py           # migas() de src/breadcrumbs.py
│   ├── test_login.py                 # iniciar_sesion: credenciales, mensaje genérico, bloqueo tras MAX_LOGIN_ATTEMPTS, usuario borrado, y el flujo HTTP /usuarios/login
│   ├── test_branches.py              # CRUD + borrado lógico + reordenar_sucursales, como referencia del patrón repetido en los demás módulos
│   ├── test_reorder_http.py          # Endpoint POST /reordenar por HTTP: aplica el orden, exige CSRF (header) y login
│   ├── test_perfil.py                 # /usuarios/perfil ("Mi cuenta"): solo username/password, ignora intentos de escalar rol o vincularse a un empleado, exige la contraseña actual para cambiarla
│   ├── test_fecha_visual.py            # parsear_fecha_visual/formatear_fecha_visual (conversión dd/mm/aaaa <-> ISO)
│   ├── test_configuracion.py           # Placeholder /configuracion/: accesible para cualquier rol, exige login
│   ├── test_contabilidad.py            # Placeholder /contabilidad/: accesible para cualquier rol, exige login
│   ├── test_informacion_util.py        # CRUD + observaciones + reordenar_enlaces + tile ancho en home + URL oculta en el listado + CSRF del endpoint /reordenar
│   └── test_employees.py               # CRUD de empleados + vínculo employee_id con users + login usa el nombre del empleado vinculado
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
    ├── permissions.py                # Reglas de qué rol (IT/BackOffice/Asesor) puede hacer qué acción, centralizadas
    ├── breadcrumbs.py                 # migas(): arma la lista (etiqueta, endpoint) que pinta el breadcrumb de navegación en base.html
    ├── constants/
    │   ├── settings.py                # Constantes generales: nombre y versión de la app, timeout, intentos máximos de login
    │   └── validations.py             # Validaciones genéricas reutilizables: email, teléfono, DNI, CUIT, fechas, edad mínima, campos obligatorios
    ├── db/
    │   ├── __init__.py
    │   └── connection.py              # Conexión centralizada a SQLite: GestorDB.conectar() y obtener_conexion() (context manager, con foreign_keys ON)
    ├── static/
    │   ├── css/style.css              # Estilos mínimos compartidos por todas las páginas
    │   ├── js/reorder.js                # Arrastrar y soltar para reordenar listados
    │   ├── js/menu-usuario.js            # Dropdown de "Mi cuenta"/"Configuración"/"Salir" en el avatar del header
    │   └── js/mostrar-password.js        # Ícono de ojo (abierto/cerrado) genérico para mostrar/ocultar cualquier campo de contraseña
    ├── templates/
    │   ├── base.html                  # Layout común: header con usuario logueado (avatar + dropdown "Mi cuenta"/"Configuración"/"Salir"), nav con breadcrumb, mensajes flash
    │   ├── _macros.html                 # Macro campo_password(): input + botón de ojo, reusado en login/formulario de usuarios
    │   ├── administrar/index.html      # Pantalla principal "Sistema de gestión": Administración, Siniestros, Clientes, Vehículos, Stock
    │   ├── administracion/index.html    # Índice de "Administración": Sucursales, Empleados, Usuarios, Validaciones, Contabilidad y Preguntas frecuentes
    │   ├── siniestros/index.html         # Placeholder de "Siniestros" (módulo todavía sin diseñar, ver RODO.txt)
    │   ├── configuracion/index.html      # Placeholder de "Configuración" (todavía vacío, sin diseñar)
    │   ├── preguntas_frecuentes/index.html # Contenido estático de "Preguntas frecuentes" (<details>/<summary> agrupados por categoría, sin JS)
    │   ├── user/{login,listar,formulario,borrados,perfil}.html
    │   ├── employees/{listar,formulario,borrados}.html
    │   ├── branches/{listar,formulario,borrados}.html
    │   ├── clients/{listar,formulario,borrados}.html
    │   ├── products/{listar,formulario,borrados}.html    # Tile/breadcrumb dice "Stock"; los templates y rutas internas siguen llamándose products
    │   ├── vehicles/{listar,formulario,borrados}.html
    │   ├── validaciones/index.html      # Índice de "Validaciones" con los links a cada catálogo
    │   ├── vehicle_brands/{listar,formulario,borrados}.html
    │   ├── insurance_companies/{listar,formulario,borrados}.html
    │   └── claim_statuses/{listar,formulario,borrados}.html
    └── modules/
        └── administrar/
            ├── __init__.py
            ├── routes.py               # Blueprint 'administrar': pantalla principal "Sistema de gestión" (/)
            ├── administracion/          # Índice de "Administración" (agrupa sucursales/usuarios/validaciones)
            │   ├── __init__.py
            │   └── routes.py             # Blueprint 'administracion': índice de la sección (/administracion)
            ├── branches/               # Módulo de sucursales
            │   ├── db.py                 # Creación de la tabla branches
            │   ├── logic.py              # CRUD y validaciones de sucursales (alta, edición, borrado lógico, búsqueda)
            │   └── routes.py             # Blueprint 'branches': vistas HTTP (/sucursales), CRUD completo (listar/nuevo/editar/borrar/reactivar)
            ├── clients/                 # Módulo de clientes
            │   ├── db.py                 # Creación de la tabla clients
            │   ├── logic.py              # CRUD y validaciones de clientes (DNI/CUIT, teléfono, email, borrado lógico)
            │   └── routes.py             # Blueprint 'clients': vistas HTTP (/clientes), CRUD completo (listar/nuevo/editar/borrar/reactivar)
            ├── products/                # Módulo de productos
            │   ├── db.py                 # Creación de la tabla products
            │   ├── logic.py              # CRUD, validación de precios mayorista/minorista y manejo de stock (incluye productos sin stock físico)
            │   └── routes.py             # Blueprint 'products': vistas HTTP (/stock), CRUD completo + compatibilidad con vehículos
            ├── user/                    # Módulo de usuarios: SOLO acceso al sistema (username, password, role, employee_id opcional)
            │   ├── db.py                 # Creación de la tabla users; migración one-shot que reconstruye la tabla (dni/code tenían UNIQUE, SQLite no permite DROP COLUMN sobre eso) migrando los datos personales viejos a employees
            │   ├── logic.py              # CRUD de usuarios, hash de contraseñas (pbkdf2_hmac + salt) y lógica de login (iniciar_sesion)
            │   └── routes.py             # Blueprint 'user': login, logout y CRUD completo (/usuarios) restringido a IT/BackOffice, más /usuarios/perfil ("Mi cuenta": solo username/password, cualquier rol)
            ├── employees/               # Módulo de empleados: ficha de personal, separada del acceso al sistema
            │   ├── db.py                 # Creación de la tabla employees (position/name/last_name/dni obligatorios; birth_date/email/phone/contacto de emergencia opcionales) y de employee_branches (relación N a N con sucursales)
            │   ├── logic.py              # CRUD, validaciones (DNI, email, teléfono, mayoría de edad si hay fecha de nacimiento), borrado lógico, sincronización de sucursales asociadas
            │   └── routes.py             # Blueprint 'employees': vistas HTTP (/empleados), CRUD completo, selector múltiple de sucursales, dentro de Administración
            ├── preguntas_frecuentes/    # "Preguntas frecuentes", dentro de Administración
            │   └── routes.py             # Blueprint 'preguntas_frecuentes': índice de la sección (/preguntas-frecuentes), contenido estático
            ├── vehicles/                # Módulo de vehículos concretos (no marcas: patente, modelo, año, etc.)
            │   ├── db.py                 # Creación de la tabla vehicles (brand_id FK a vehicle_brands)
            │   ├── logic.py              # CRUD, validación de dominio (patente) y año, borrado lógico
            │   └── routes.py             # Blueprint 'vehicles': vistas HTTP (/vehiculos), CRUD completo
            └── validaciones/            # Catálogos de referencia usados por otros módulos
                ├── routes.py              # Blueprint 'validaciones': índice de la sección (/validaciones)
                ├── vehicle_brands/        # Marcas de vehículos (FK desde product_compatibility)
                │   ├── db.py
                │   ├── logic.py            # CRUD y borrado lógico
                │   └── routes.py           # Blueprint 'vehicle_brands' (/marcas-vehiculos)
                ├── insurance_companies/   # Compañías de seguro (catálogo, todavía sin usar desde otro módulo)
                │   ├── db.py
                │   ├── logic.py            # CRUD y borrado lógico
                │   └── routes.py           # Blueprint 'insurance_companies' (/companias-seguro)
                └── claim_statuses/        # Estados de siniestro (catálogo, todavía sin usar desde otro módulo)
                    ├── db.py
                    ├── logic.py            # CRUD y borrado lógico
                    └── routes.py           # Blueprint 'claim_statuses' (/estados-siniestro)
```

Nota: el frontend HTML recién arranca. Se removió la versión anterior en Tkinter (heredada de la copia del proyecto viejo) y ahora hay una capa web mínima con Flask: cada módulo trae su propio `routes.py` (blueprint) al lado de su `db.py`/`logic.py`, y sus templates viven en `src/templates/<módulo>/`. Sucursales, clientes, productos y usuarios ya tienen CRUD completo desde HTML (listar/nuevo/editar/borrar lógico/reactivar), incluida la compatibilidad de productos con vehículos. Pensado para funcionar en dos sucursales con equipos que no siempre tienen conexión a internet.

Además de esos 4 módulos, `src/modules/administrar/validaciones/` agrupa catálogos de referencia con el mismo patrón CRUD (db/logic/routes): **marcas de vehículos**, **compañías de seguro** y **estados de siniestro**. La compatibilidad de un producto con un vehículo (`product_compatibility.brand_vehicle_id`) ya referencia una marca cargada en el catálogo en vez de texto libre; la migración de `brand_vehicle` (texto) a `brand_vehicle_id` (FK) se hace sola al arrancar la app si detecta el esquema viejo (`crear_tabla_compatibilidad` en `products/db.py`). Compañías de seguro y estados de siniestro todavía no están enganchados a ningún otro módulo: van a ir asociados al futuro módulo de siniestros (cliente + vehículo + aseguradora + estado) — ver RODO.txt.

**Orden editable (arrastrar y soltar)**: sucursales, usuarios, marcas de vehículos, compañías de seguro y estados de siniestro tienen una columna `sort_order` (además de `status`) y se reordenan arrastrando la fila desde el ícono ⠿ de la primera columna. Es el primer uso de JavaScript en el proyecto: `src/static/js/reorder.js` (vanilla, sin librerías/CDN — la app debe poder andar offline) usa Pointer Events (no la API nativa de drag-and-drop HTML5, que no anda en touch) para que también funcione en celulares. Al soltar, manda por `fetch` la lista completa de ids en su nuevo orden a un endpoint `POST .../reordenar` de cada blueprint (con el token CSRF vía header `X-CSRFToken`, tomado de `<meta name="csrf-token">` en `base.html`); `reordenar_*` en cada `logic.py` reescribe `sort_order` según la posición recibida. Los registros nuevos se agregan siempre al final (`MAX(sort_order) + 1`). Clientes, productos y vehículos no tienen esto: siguen ordenados por nombre/dominio, ya que son listas que crecen mucho y no tiene sentido ordenarlas a mano.

`vehicles` (a la par de `clients`/`products`, no dentro de `validaciones/`) es la tabla de vehículos concretos: marca (FK a `vehicle_brands`), modelo y año obligatorios, dominio (patente) obligatorio y validado con formato argentino viejo (ABC123) o Mercosur (AB123CD), y color/número de chasis/número de motor opcionales. Todavía sin `client_id` (dueño) a propósito: esa relación se define recién con el futuro módulo de siniestros, igual que se decidió con `insurance_companies` — ver RODO.txt.

Navegación: la pantalla principal (`/`, título "Sistema de gestión") tiene, en orden, **Administración** (`/administracion`, agrupa lo más administrativo/config: Sucursales, Empleados, Usuarios, Validaciones, Contabilidad y Preguntas frecuentes — en ese orden, dos por fila), **Siniestros** (`/siniestros`, todavía un placeholder: el módulo real está sin diseñar, ver RODO.txt), **Clientes** (`/clientes`), **Vehículos** (`/vehiculos`), **Stock** (`/stock`; el módulo `products` por dentro, el nombre visible pasó de "Productos" a "Stock" en el tile, los títulos y el breadcrumb) y, como último tile, ancho y celeste claro, **Links útiles** (`/links-utiles`). Todas las URLs de la app están en español y coinciden con el título visible de cada página (`/sucursales`, `/usuarios`, `/marcas-vehiculos`, `/companias-seguro`, `/estados-siniestro`, `/preguntas-frecuentes`); por dentro los blueprints y las tablas siguen en inglés (branches, user, vehicle_brands, etc.) — solo el `url_prefix` de cada uno cambió, nunca el nombre del módulo ni de la tabla.

**Links útiles** (`src/modules/administrar/informacion_util/` por dentro — el nombre visible cambió de "Información Útil" a "Links útiles" pero el módulo/blueprint/tabla no, mismo criterio que Stock/products) es un catálogo de enlaces con el mismo patrón CRUD + borrado lógico + orden editable (drag & drop) que vehicle_brands/insurance_companies/claim_statuses, con tres campos por entrada: `label` (el texto del botón), `url` (el link) y `observations` (notas libres, opcional). La URL no se muestra como texto en el listado — solo queda en el `href` del botón "Abrir" (se abre en pestaña nueva) — para no tener contraseñas o links sensibles a la vista en la pantalla; la columna de observaciones ocupa el lugar donde antes se mostraba la URL. Por ahora `/links-utiles` es solo el gestor de esas entradas (alta/edición/borrado/reordenar); todavía no existe una pantalla separada que muestre los botones ya armados para clickear, eso queda para más adelante.

**Contabilidad** (`/contabilidad`, dentro de Administración) es, como Siniestros y Configuración, un placeholder vacío sin diseñar todavía.

**Preguntas frecuentes** (`/preguntas-frecuentes`, dentro de Administración, exclusiva de IT/BackOffice) es contenido estático pensado para alguien que nunca usó el sistema: preguntas agrupadas por categoría (primeros pasos, Mi cuenta, Administración, Clientes/Vehículos/Stock, convenciones de la app, módulos todavía sin terminar) con `<details>/<summary>` nativos del navegador — sin JavaScript, cada pregunta se expande sola al clickearla. No es un CRUD ni tiene datos en la base: es texto fijo en el template, para editarlo hay que tocar `src/templates/preguntas_frecuentes/index.html` directamente.

`employees` tiene una relación N a N con `branches` a través de `employee_branches` (un empleado puede estar en una sucursal, en varias, o en ninguna): en el formulario de alta/edición es un `<select multiple>` de sucursales, y el listado muestra los nombres separados por coma (`GROUP_CONCAT` en `listar_empleados`). `_sincronizar_sucursales` en `employees/logic.py` reemplaza el set completo en cada guardado; distingue `branch_ids=None` (no tocar las asociaciones existentes, usado en updates parciales) de `branch_ids=[]` (vaciarlas explícitamente).

El avatar del header (dos letras: inicial del nombre + inicial del apellido, `session['iniciales']`) abre un dropdown con **Mi cuenta** (`/usuarios/perfil`), **Configuración** (`/configuracion`, todavía una página vacía sin diseñar) y **Salir**. El nombre y el rol no se muestran sueltos en la barra: solo aparecen como tooltip nativo al pasar el mouse sobre el avatar, y como texto (no clickeable) arriba de los links dentro del dropdown.

Fechas en los formularios (nacimiento en usuarios, compra en stock) se muestran y se cargan en formato argentino `dd/mm/aaaa` (`<input type="text">` con `pattern`, no `<input type="date">`: ese tipo de campo respeta el idioma/región configurado en el navegador del que lo abre, no el `lang` de la página, así que en la práctica mostraba `mm/dd/yyyy` en muchos casos). `parsear_fecha_visual`/`formatear_fecha_visual` (`src/constants/validations.py`) hacen la conversión hacia/desde el `aaaa-mm-dd` que se guarda en la base; `validar_fecha`/`validar_mayor_edad` siguen trabajando en ISO sin cambios. El filtro de Jinja `fecha_visual` (registrado en `create_app()`) es el que se usa en los templates para mostrar el valor guardado.

Los `.form-card` (formularios de alta/edición) quedan centrados horizontalmente en la pantalla (`margin: 0 auto` en `style.css`), no pegados a la izquierda del contenido.

El nav de todas las páginas (`base.html`) muestra un breadcrumb (ej. "Sistema de gestión / Administración / Validaciones / Marcas de vehículos") en vez de un botón fijo "Volver": cada tramo del camino es un link a ese nivel, salvo el último (la página actual). Cada blueprint arma su propio breadcrumb con un helper `_migas(*ultimos)` local en su `routes.py`, apoyado en `migas()` de `src/breadcrumbs.py`.

Para correr la app: `python app.py` (o `flask --app app run`) desde la raíz, con el venv activado.

Para correr los tests: `pytest` desde la raíz, con el venv activado. Cada test arranca con una base SQLite temporal propia (`tests/conftest.py` parchea `src.db.connection.DB_PATH` con un archivo en un directorio temporal antes de crear la app), así que nunca tocan `data/database.db`.

## Medidas de seguridad

- **Contraseñas hasheadas**: nunca se guarda texto plano. Se usa `pbkdf2_hmac` (SHA-256, 100.000 iteraciones) con salt aleatorio por usuario (`src/modules/administrar/user/logic.py`).
- **Política de contraseñas**: largo mínimo 8 y máximo 64 caracteres, siguiendo NIST SP 800-63B (el estándar actual de la comunidad). Sin reglas de complejidad forzada (mayúscula/número/símbolo) a propósito: ese mismo estándar las desaconseja porque en la práctica producen contraseñas predecibles sin mejorar la seguridad real (`validar_password` en `src/constants/validations.py`).
- **Login sin fuga de información**: si el usuario o la contraseña fallan, el mensaje de error es siempre el mismo genérico, para no revelar cuál de los dos estuvo mal. Tras `MAX_LOGIN_ATTEMPTS` (3) intentos fallidos seguidos, la cuenta se bloquea temporalmente por `TIMEOUT_SECONDS` (30 segundos) (`iniciar_sesion` en `user/logic.py`).
- **Permisos por rol**: quién puede gestionar usuarios o cambiar contraseñas de quién está centralizado en `src/permissions.py`, con una jerarquía real (IT > BackOffice > Asesor) en vez de reglas sueltas repetidas por módulo. Toda la sección **Administración** (Sucursales, Empleados, Usuarios, Validaciones y sus 3 catálogos, Contabilidad, Preguntas frecuentes) es exclusiva de IT/BackOffice: `restringir_a_administracion()` (`src/auth.py`) se registra como `before_request` de cada uno de esos blueprints, así que queda bloqueado a nivel de ruta (no solo ocultando el link) sin repetir el chequeo en cada vista. Un Asesor que entra a una URL de Administración a mano recibe un redirect a `/` con un flash de error; el tile "Administración" de la pantalla principal también se oculta para ese rol (`administrar/routes.py` pasa `puede_acceder_administracion(role)` al template). Clientes, Vehículos, Stock, Siniestros, Links útiles, Configuración y Mi cuenta quedan afuera de esta restricción a propósito: no son parte de Administración.
- **Ver eliminados restringido a IT**: BackOffice y Asesor manejan todo lo demás, pero ninguno de los dos puede ver listas de registros eliminados en ningún módulo (`puede_ver_eliminados` en `src/permissions.py`, decorator `requiere_ver_eliminados` en `src/auth.py` sobre cada vista `borrados()`); el link "Ver borrados" también se oculta para ellos en cada listado. Si intentan cargar un registro que choca con uno ya borrado (mismo DNI/CUIT, dominio, code, username o nombre de catálogo), el sistema no lo rechaza por duplicado sin más: levanta `RegistroBorradoExistente` (`src/exceptions.py`) y la vista les ofrece reactivar el existente en vez de crear uno nuevo, sin necesidad de pasar por la lista de eliminados.
- **Sucursales acotan Clientes/Vehículos/Stock**: cada usuario pertenece a una o varias sucursales (`user_branches`, N:N igual que `employee_branches`), guardadas en `session["branch_ids"]` al loguearse. Clientes, Vehículos y Stock tienen su propia relación N:N con sucursales (`client_branches`, `vehicle_branches`, `product_branches`); `listar_*` filtra por esas sucursales y cada vista de edición/borrado/reactivación repite el chequeo a nivel de fila (`visible_para_sucursales` en cada `logic.py`), para que no alcance con ocultarlo del listado. Un registro sin ninguna sucursal asignada queda visible para todos a propósito (dato sin asignar, no oculto) — evita que los registros ya cargados antes de esta funcionalidad desaparezcan de golpe para todo el mundo.
- **Validación de documentos reales**: el CUIT valida su dígito verificador con el algoritmo módulo 11 (el mismo que usa AFIP), no solo la cantidad de dígitos — evita cargar CUITs inventados o mal tipeados (`validar_cuit`).
- **Teléfonos en formato estándar**: se valida contra E.164 (estándar internacional ITU-T), en vez de un formato fijo hardcodeado a un solo país (`validar_telefono`).
- **Borrado lógico**: ningún módulo hace `DELETE` real — todas las tablas tienen columna `status` (1 = activo, 0 = borrado), así nunca se pierden datos de auditoría por error.
- **Consultas parametrizadas**: todas las queries a SQLite usan placeholders (`?`), nunca se arma SQL concatenando texto ingresado por el usuario — evita inyección SQL.
- **Protección CSRF**: `Flask-WTF` (`CSRFProtect`) está activado globalmente en `create_app()` (`src/app.py`); todos los `<form method="post">` llevan su `csrf_token` oculto. Cualquier POST sin token válido responde 400 antes de llegar a la vista.
- **Usuarios (acceso) separado de Empleados (personal)**: `users` es solo username/password/role/`employee_id` (opcional, FK a `employees`); los datos personales (nombre, DNI, puesto, contacto de emergencia, etc.) viven en el módulo `employees`, dentro de Administración. `/usuarios/perfil` ("Mi cuenta", autogestión) refleja esta separación: solo deja tocar username y contraseña, nunca `role` ni `employee_id` — ni siquiera están en ese formulario (a diferencia de `/usuarios/<id>/editar`, reservado a IT/BackOffice, que sí puede vincular/desvincular un empleado y asignar sucursales). Probado en `tests/test_perfil.py`.
- **Cambio de contraseña propia exige la contraseña actual**: solo en `/usuarios/perfil` (autogestión) — si se manda una contraseña nueva sin la actual, o la actual no coincide (`verificar_contrasena` en `user/logic.py`), se rechaza con `ValidationError` antes de tocar la base. La edición admin (`/usuarios/<id>/editar`) sigue sin pedirla, porque ahí el cambio lo hace un IT/BackOffice, no el dueño de la cuenta.

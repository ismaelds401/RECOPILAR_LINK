# TechEvents Peru — Fase 1

Base del agregador de eventos tecnológicos. Esta fase crea únicamente el
entorno Python, el esquema seguro de Supabase y la prueba de conexión. Los
conectores, React, Cloudflare Pages y las automatizaciones pertenecen a fases
posteriores.

## Qué componentes se crean

- `backend/config.py`: carga y valida las variables de entorno.
- `backend/services/supabase_service.py`: crea el cliente privado de Supabase.
- `backend/scripts/check_supabase.py`: comprueba lectura y, opcionalmente,
  escritura con limpieza automática.
- `database/schema.sql`: tablas, relaciones, restricciones, índices y triggers.
- `database/policies.sql`: RLS y permisos públicos de solo lectura.
- `.env.example`: plantilla sin secretos.

No se crean todavía las tablas `user_preferences` ni `favorites`: necesitan una
decisión de producto sobre autenticación y se añadirán con esa funcionalidad.
Supabase Auth ya mantiene sus usuarios en `auth.users`, por lo que no se duplica
una tabla `public.users` en esta fase.

## 1. Requisitos en Windows

Instala:

1. Python 3.12 o superior desde <https://www.python.org/downloads/windows/>.
   Durante la instalación marca **Add python.exe to PATH**.
2. Git desde <https://git-scm.com/download/win>.
3. VS Code y la extensión oficial **Python** de Microsoft.
4. Una cuenta gratuita de GitHub y acceso al proyecto Supabase
   `RECOPILAR_LINK`.

Comprobación en una terminal nueva de PowerShell:

```powershell
python --version
git --version
code --version
```

En este equipo Git y VS Code ya responden, pero Python aún no estaba instalado
al preparar la fase.

## 2. Abrir y preparar el proyecto en VS Code

En PowerShell:

```powershell
cd "D:\Recopilacion de eventos"
code .
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Si PowerShell bloquea la activación, no es obligatorio cambiar su política. Usa
directamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## 3. Crear las tablas en RECOPILAR_LINK

Dónde: **Supabase Dashboard → RECOPILAR_LINK → SQL Editor → New query**.

1. Copia todo `database/schema.sql`, ejecútalo y espera `Success`.
2. Copia todo `database/policies.sql`, ejecútalo y espera `Success`.
3. En **Table Editor** deben aparecer `events`, `event_sources` y
   `scraping_logs`.

El script se puede volver a ejecutar. No elimina datos. Los nombres internos de
modalidad son `in_person`, `virtual` y `hybrid`; más adelante la interfaz los
mostrará en español.

## 4. Conectar Python con Supabase

En Supabase abre **Project Settings → API Keys** (la ubicación puede mostrarse
como **Data API / API Settings** según la versión del panel) y copia:

- Project URL → `SUPABASE_URL`.
- Secret key (`sb_secret_...`) → `SUPABASE_SECRET_KEY`.

Si tu proyecto solo presenta claves legacy, usa la clave `service_role` en
`SUPABASE_SERVICE_ROLE_KEY`. Ambas son credenciales exclusivas del backend.

Crea el archivo privado a partir de la plantilla:

```powershell
Copy-Item .env.example .env
```

Edita `.env` y reemplaza los valores de ejemplo. `.gitignore` excluye este
archivo. Nunca pegues una secret key/service-role en código, capturas, commits,
el frontend ni variables que comiencen por `VITE_`.

Prueba de lectura:

```powershell
python -m backend.scripts.check_supabase
```

Resultado esperado:

```text
OK: connection and SELECT succeeded. Events found: 0.
```

El número puede ser mayor que cero. Para validar también los permisos privados
de escritura:

```powershell
python -m backend.scripts.check_supabase --write-test
```

Esto inserta un evento `draft` único y lo elimina inmediatamente. Resultado:

```text
OK: connection and SELECT succeeded. Events found: 0.
OK: INSERT and DELETE succeeded; the test row was removed.
```

Ejecuta además las pruebas locales:

```powershell
python -m pytest
```

## 5. Crear el repositorio en GitHub

El repositorio Git local ya queda inicializado, pero no se crea ni publica un
repositorio remoto sin tu autorización y autenticación.

1. En GitHub selecciona **New repository**.
2. Nombre sugerido: `RECOPILAR_LINK`.
3. Elige público o privado; no marques README, `.gitignore` ni licencia porque
   ya existen localmente.
4. Copia la URL del repositorio y ejecuta:

```powershell
git add .
git commit -m "chore: initialize phase 1"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/RECOPILAR_LINK.git
git push -u origin main
```

Antes del commit, confirma que `.env` no aparece:

```powershell
git status --short
git check-ignore -v .env
```

## Diseño de datos inicial

- `events`: evento normalizado. `event_hash` es único para deduplicación global;
  `(source, source_event_id)` es único cuando el proveedor entrega ID.
- `event_sources`: configuración y estado de cada fuente.
- `scraping_logs`: historial de cada ejecución, enlazado a una fuente.
- Los índices cubren fecha, estado, categoría, ciudad, modalidad, organización y
  etiquetas.
- Solo los eventos `published` son legibles mediante la clave pública. Los roles
  cliente no reciben permisos de escritura ni acceso a fuentes o logs.

## Claves y seguridad

- Futuro frontend: URL + clave **publishable** (`sb_publishable_...`; en
  proyectos legacy, `anon`). Puede exponerse únicamente con RLS correcto.
- Backend: clave **secret** (`sb_secret_...`; legacy, `service_role`). Omite RLS
  y jamás debe exponerse.

## Errores comunes

- `python no se reconoce`: instala Python marcando PATH y abre otra terminal.
- `Missing required environment variables`: crea `.env` y completa URL y clave.
- `PGRST205` o `Could not find the table`: ejecuta ambos SQL y espera unos
  segundos para que Supabase recargue el esquema.
- `Invalid API key` / HTTP 401: copiaste una clave incompleta o de otro proyecto.
- HTTP 403 / `permission denied`: para `--write-test` usa la clave secret o
  `service_role`, no la publishable/anon.
- Error de DNS, TLS o timeout: revisa Internet, la URL exacta y el estado del
  proyecto; los proyectos Free pueden pausarse por inactividad.

No avances a la Fase 2 hasta que la prueba de lectura y, preferentemente, la de
escritura terminen con `OK`.

## Fase 2: primer conector Luma

La API de administración de Luma requiere Luma Plus, por lo que el proyecto no
la utiliza. El primer conector consume el feed iCal público oficial de
[Hack0 Community](https://luma.com/hack0), un calendario activo de eventos
tecnológicos de Perú y eventos virtuales.

El feed se valida y procesa con:

- timeout de 20 segundos;
- tres reintentos con espera incremental para 429 y errores 5xx;
- User-Agent identificable;
- límite de respuesta de 5 MB;
- validación de contenido `VCALENDAR`;
- aislamiento de errores por conector;
- filtro de eventos finalizados y presenciales fuera de Perú.

Prueba sin escribir en Supabase:

```powershell
.\.venv\Scripts\python.exe -m backend.main --dry-run --preview 10
```

Ejecuta el pipeline real:

```powershell
.\.venv\Scripts\python.exe -m backend.main
```

Verifica fuente, eventos y último log:

```powershell
.\.venv\Scripts\python.exe -m backend.scripts.check_phase2
```

La ejecución es idempotente: identifica primero `(source, source_event_id)` y
después `event_hash`. Una segunda ejecución actualiza eventos existentes en vez
de insertarlos otra vez.

### Límites de los datos iCal de Luma

El feed no publica de forma consistente imagen, precio, gratuidad, categoría ni
la ubicación exacta de eventos que requieren registro. Esos campos permanecen
en `null` o `Other`; no se inventan datos. La modalidad usa señales del propio
feed (coordenadas, dirección, palabras como Zoom/online y formatos físicos con
ubicación oculta). La clasificación detallada pertenece a la Fase 5.

## Fase 3: eventos de Google Developer Groups

El segundo conector consulta el endpoint JSON público que utiliza el sitio
oficial de Google Developer Groups. La cobertura inicial incluye GDG Lima, GDG
Cloud Lima, GDG Open y GDG Callao. No necesita credenciales ni un plan de pago.

El conector procesa campos estructurados de fecha, zona horaria, modalidad,
ubicación, etiquetas, imagen y registro. También incorpora timeout, reintentos,
límite de 5 MB, validación del tipo de contenido, paginación limitada y
aislamiento de errores por comunidad.

Prueba solamente GDG sin escribir en Supabase:

```powershell
.\.venv\Scripts\python.exe -m backend.main --only gdg --dry-run --preview 10
```

Ejecuta la carga real y verifica el resultado:

```powershell
.\.venv\Scripts\python.exe -m backend.main --only gdg
.\.venv\Scripts\python.exe -m backend.scripts.check_phase3
```

Los eventos coorganizados pueden aparecer en varias comunidades. La clave
`(source, source_event_id)` conserva una sola fila por identificador GDG; por
ejemplo, el evento compartido por GDG Cloud Lima y GDG Open no se duplica.

El endpoint pertenece al sitio oficial y es de acceso público, pero no es una
API externa con garantía contractual de estabilidad. Las validaciones del
conector permiten detectar un cambio de formato y registrar el fallo sin
detener las demás fuentes.

## Fase 4: catálogo oficial de eventos AWS

El conector AWS consulta el endpoint JSON público que alimenta el
[catálogo oficial de eventos AWS](https://aws.amazon.com/events/explore-aws-events/).
No requiere cuenta, API key ni un servicio de pago. Se limita a eventos
first-party que estén marcados como virtuales o pertenezcan a América, y luego
conserva:

- eventos virtuales o híbridos disponibles remotamente;
- eventos presenciales cuya ubicación indique Perú o Lima.

Cada respuesta tiene timeout, tres reintentos, validación JSON y un límite de
5 MB y 1000 elementos. Se combinan los resultados virtuales y americanos por
el ID oficial de AWS antes de normalizarlos.

Prueba AWS sin escribir en Supabase:

```powershell
.\.venv\Scripts\python.exe -m backend.main --only aws --dry-run --preview 10
```

Ejecuta la carga real y verifica el resultado:

```powershell
.\.venv\Scripts\python.exe -m backend.main --only aws
.\.venv\Scripts\python.exe -m backend.scripts.check_phase4
```

El catálogo puede publicar la fecha sin todos los campos opcionales. El
conector aprovecha el rango horario visible cuando existe, conserva `null` para
precio, país o imagen desconocidos y no incorpora eventos presenciales de
otros países. Si AWS marca un registro como virtual y presencial a la vez, se
normaliza como `hybrid`.

## Fase 5: clasificación, deduplicación y filtros

Todos los conectores pasan ahora por un clasificador local antes de escribir en
Supabase. No usa IA ni servicios pagados: aplica reglas ordenadas sobre título,
descripción, organizador, tipo y etiquetas. Las categorías disponibles son:

- Artificial Intelligence, Cloud, Data y Cybersecurity;
- DevOps, Programming, Web Development y Mobile;
- Blockchain, Networking e IoT;
- Entrepreneurship, Technology y Other.

La categoría más específica se elige como principal y las demás señales útiles
se conservan como etiquetas, por ejemplo `AI`, `AWS`, `Python`, `Security` o
`Serverless`. Las etiquetas originales de cada proveedor no se eliminan.

La deduplicación mantiene las dos comprobaciones exactas existentes:
`(source, source_event_id)` y `event_hash`. Además compara eventos nuevos contra
las demás fuentes mediante título normalizado, palabras compartidas, una
ventana máxima de 30 minutos, ciudad y similitud del organizador. Los umbrales
son deliberadamente conservadores para no fusionar sesiones distintas.

`backend/services/event_filter.py` ofrece filtros combinables para búsqueda,
rango de fechas, categoría, organizador, modalidad, ciudad, gratuidad, tipo de
evento y etiquetas. Esta lógica es independiente de React y se reutilizará al
construir la interfaz.

Ejecuta todas las fuentes con clasificación:

```powershell
.\.venv\Scripts\python.exe -m backend.main
```

Verifica la cobertura y los duplicados almacenados:

```powershell
.\.venv\Scripts\python.exe -m backend.scripts.check_phase5
```

La comprobación analiza únicamente eventos próximos publicados, muestra su
distribución por categoría y falla si no existen categorías, etiquetas o si
detecta un duplicado probable entre proveedores.

## Fase 6: actualización automática con GitHub Actions

El workflow `.github/workflows/update-events.yml` ejecuta el pipeline cuatro
veces al día, cada seis horas, a las `00:17`, `06:17`, `12:17` y `18:17` de la
zona `America/Lima`. También permite iniciarlo manualmente desde la pestaña
Actions. El minuto 17 evita concentrar el trabajo al inicio de cada hora.

En cada ejecución GitHub:

1. descarga el repositorio con permisos de sólo lectura;
2. prepara Python 3.13 y reutiliza la caché de `pip`;
3. valida que existan los dos secretos requeridos;
4. instala las dependencias y ejecuta las pruebas;
5. recopila, clasifica, deduplica y guarda los eventos;
6. verifica categorías y duplicados en Supabase.

Configura estos **Repository secrets** en GitHub, nunca como variables públicas:

- `SUPABASE_URL`: Project URL de Supabase;
- `SUPABASE_SECRET_KEY`: clave privada `sb_secret_...` del backend.

Ruta: **GitHub → RECOPILAR_LINK → Settings → Secrets and variables → Actions →
New repository secret**. Después abre **Actions → Update technology events →
Run workflow → Run workflow**. La ejecución correcta debe finalizar en verde y
el último registro de cada fuente debe aparecer en `scraping_logs`.

El workflow usa `concurrency` para evitar dos actualizaciones simultáneas, tiene
un límite de 20 minutos y no imprime los valores de los secretos. Un fallo de un
conector queda aislado por el pipeline; si todas las fuentes fallan, el job sí
termina con error.


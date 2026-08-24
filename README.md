# TechEvents Peru — Fase 1

Base del agregador de eventos tecnológicos. Esta fase crea únicamente el entorno Python, el esquema seguro de Supabase y la prueba de conexión. Los conectores, React, Cloudflare Pages y las automatizaciones pertenecen a fases posteriores.

## Componentes

- `backend/config.py`: carga y valida variables de entorno.
- `backend/services/supabase_service.py`: crea el cliente privado.
- `backend/scripts/check_supabase.py`: comprueba lectura y escritura.
- `database/schema.sql`: tablas, relaciones, restricciones e índices.
- `database/policies.sql`: RLS y permisos públicos de solo lectura.
- `.env.example`: plantilla sin secretos.

No se crean todavía `user_preferences` ni `favorites`. Supabase Auth mantiene los usuarios en `auth.users`.

## Requisitos

- Python 3.12+
- Git
- VS Code con la extensión oficial Python
- Acceso al proyecto Supabase `RECOPILAR_LINK`

## Preparación en Windows

```powershell
git clone https://github.com/ismaelds401/RECOPILAR_LINK.git
cd RECOPILAR_LINK
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Crear las tablas

En **Supabase Dashboard → RECOPILAR_LINK → SQL Editor**:

1. Ejecuta todo `database/schema.sql`.
2. Ejecuta todo `database/policies.sql`.
3. Comprueba que existan `events`, `event_sources` y `scraping_logs`.

## Configurar credenciales

```powershell
Copy-Item .env.example .env
```

Completa `SUPABASE_URL` y `SUPABASE_SECRET_KEY`. Si el proyecto solo muestra claves legacy, usa `SUPABASE_SERVICE_ROLE_KEY`.

Nunca publiques `.env`, una clave `sb_secret_...` ni una clave `service_role`. El futuro frontend utilizará la clave publishable/anon con RLS.

## Validar Python → Supabase

Lectura:

```powershell
python -m backend.scripts.check_supabase
```

Lectura y escritura temporal:

```powershell
python -m backend.scripts.check_supabase --write-test
```

Resultado esperado:

```text
OK: connection and SELECT succeeded. Events found: 0.
OK: INSERT and DELETE succeeded; the test row was removed.
```

El número de eventos puede ser mayor que cero. No avances a la Fase 2 hasta obtener ambos mensajes `OK`.

## Errores comunes

- `python no se reconoce`: instala Python 3.12+ con la opción PATH.
- `Missing required environment variables`: crea y completa `.env`.
- `Could not find the table`: ejecuta ambos archivos SQL.
- HTTP 401: la clave está incompleta o pertenece a otro proyecto.
- HTTP 403: para escritura usa secret/service-role, nunca publishable/anon.

# Configuración de Better Auth + PostgreSQL

## Variables de Entorno Necesarias

### Frontend (Asiter/.env.local)

```env
# Better Auth
BETTER_AUTH_SECRET=tu-secret-super-seguro-aqui-minimo-32-caracteres
BETTER_AUTH_URL=http://localhost:3000
NEXT_PUBLIC_BETTER_AUTH_URL=http://localhost:3000

# Google OAuth (opcional)
GOOGLE_CLIENT_ID=tu-google-client-id
GOOGLE_CLIENT_SECRET=tu-google-client-secret

# Backend
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
```

### Backend (backend/.env)

```env
# PostgreSQL
DATABASE_URL=postgresql://usuario:password@localhost:5432/asiter

# Better Auth (mismo secret que frontend)
BETTER_AUTH_SECRET=tu-secret-super-seguro-aqui-minimo-32-caracteres

# Gemini API
GEMINI_API_KEY=tu-api-key
```

## Pasos de Configuración

### 1. Instalar Dependencias

**Frontend:**
```bash
cd Asiter
bun install
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurar PostgreSQL

1. Crear base de datos:
```sql
CREATE DATABASE asiter;
```

2. Las tablas se crearán automáticamente al iniciar el backend.

### 3. Configurar Better Auth

1. Generar un secret seguro:
```bash
openssl rand -base64 32
```

2. Agregar el secret a `.env.local` (frontend) y `.env` (backend).

### 4. Configurar Google OAuth (Opcional)

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un proyecto
3. Habilitar Google+ API
4. Crear credenciales OAuth 2.0
5. Agregar `http://localhost:3000/api/auth/callback/google` como redirect URI
6. Copiar Client ID y Client Secret a `.env.local`

### 5. Ejecutar Migraciones (si es necesario)

```bash
cd backend
alembic upgrade head
```

### 6. Iniciar Servidores

**Backend:**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend:**
```bash
cd Asiter
bun dev
```

## Funcionalidades Implementadas

✅ Autenticación con email/password
✅ Autenticación con Google OAuth
✅ Registro de usuarios
✅ Sesión persistente
✅ Guardado de TDRs por usuario en PostgreSQL
✅ Lista de TDRs generados en el dashboard
✅ Integración con ChromaDB para RAG
✅ Número real de referencias mostrado (no hardcodeado)

## Notas Importantes

- Better Auth crea sus propias tablas en PostgreSQL automáticamente
- Los usuarios se sincronizan automáticamente entre Better Auth y nuestra tabla `users`
- El backend crea usuarios automáticamente cuando recibe un token válido de Better Auth
- Los TDRs se guardan tanto en ChromaDB (para RAG) como en PostgreSQL (para historial del usuario)


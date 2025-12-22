# 🚀 Guía de Despliegue ASITER en VPS

## Pre-requisitos en tu VPS

Asegúrate de tener instalado:
```bash
# Verificar Docker
docker --version

# Si no está instalado:
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl enable docker
sudo systemctl start docker
```

## Paso 1: Subir archivos al VPS

**Opción A - Git (recomendado):**
```bash
# En tu VPS
cd /home
git clone tu-repositorio.git asiter
cd asiter
```

**Opción B - SCP (sin node_modules):**
```bash
# Desde tu PC Windows, en PowerShell
scp -r D:\Asiter-completo\Asiter root@161.132.40.223:/home/asiter/Asiter
scp -r D:\Asiter-completo\backend root@161.132.40.223:/home/asiter/backend
scp D:\Asiter-completo\docker-compose.yml root@161.132.40.223:/home/asiter/
scp D:\Asiter-completo\.env.example root@161.132.40.223:/home/asiter/.env
```

## Paso 2: Configurar variables de entorno

```bash
# En el VPS
cd /home/asiter
cp .env.example .env
nano .env
```

Edita el archivo `.env`:
```env
GEMINI_API_KEY=AIzaSyA7Lniit_f8Dq9lvxJSCZBwzNhOXdlc4BQ
BETTER_AUTH_SECRET=genera-un-secret-seguro-con-openssl-rand-base64-32
```

## Paso 3: Construir y ejecutar

```bash
# Construir imágenes (esto instala node_modules dentro de Docker)
docker-compose build

# Ejecutar en background
docker-compose up -d

# Ver logs
docker-compose logs -f
```

## Paso 4: Verificar

- **Frontend ASITER:** http://161.132.40.223:3002
- **Backend API:** http://161.132.40.223:8001/docs

## Puertos utilizados

| Servicio | Puerto | Notas |
|----------|--------|-------|
| ASITER Frontend | 3001 | Diferente al de mecánica |
| ASITER Backend | 8001 | API + RAG |
| Tu proyecto mecánica | 3000/8000 | No se toca |

## Comandos útiles

```bash
# Ver contenedores activos
docker ps

# Detener ASITER
docker-compose down

# Reiniciar
docker-compose restart

# Ver logs del backend
docker logs asiter-backend

# Reconstruir después de cambios
docker-compose build --no-cache
docker-compose up -d
```

## Solución de problemas

**Error: Puerto en uso**
```bash
# Ver qué usa el puerto
sudo lsof -i :3001
# Cambiar puerto en docker-compose.yml si es necesario
```

**Error: Gemini API**
```bash
# Verificar que la key está configurada
docker exec asiter-backend env | grep GEMINI
```

FROM node:20-alpine

WORKDIR /app

# Instalar dependencias de build para módulos nativos (better-sqlite3)
RUN apk add --no-cache python3 make g++ 

# Copiar package.json primero para aprovechar cache
COPY package.json ./

# Instalar TODAS las dependencias (incluyendo dev para build)
RUN npm install --legacy-peer-deps

# Copiar el resto del código
COPY . .

# Crear carpetas necesarias
RUN mkdir -p public
RUN mkdir -p /app/data && chmod 777 /app/data

# Variables de entorno
ENV NEXT_PUBLIC_BACKEND_URL=http://161.132.40.223:8001
ENV NEXT_PUBLIC_BETTER_AUTH_URL=http://161.132.40.223:3002
ENV NODE_ENV=production
ENV PORT=3000

# Build de Next.js
RUN npm run build

EXPOSE 3000

# Usar node para ejecutar next
CMD ["node", "node_modules/next/dist/bin/next", "start"]

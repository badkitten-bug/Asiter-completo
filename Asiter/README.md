# ASITER - Asistente Inteligente de TDR

Sistema web para crear y gestionar Términos de Referencia (TDR) en el contexto peruano.

## 🚀 Tecnologías

- **Next.js 14** (App Router)
- **React 18**
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui** (Componentes UI)
- **Bun** (Runtime y gestor de paquetes)

## 📋 Requisitos Previos

- [Bun](https://bun.sh/) instalado en tu sistema

## 🛠️ Instalación

1. Clonar el repositorio (o si ya estás en el directorio):
```bash
cd Asiter
```

2. Instalar dependencias:
```bash
bun install
```

## 🏃 Ejecutar el Proyecto

### Desarrollo
```bash
bun dev
```

El proyecto estará disponible en [http://localhost:3000](http://localhost:3000)

### Build de Producción
```bash
bun run build
bun start
```

## 🔐 Credenciales de Acceso

Por ahora, el sistema usa autenticación hardcodeada:

- **Email:** `admin@asiter.com`
- **Contraseña:** `admin123`

## 📁 Estructura del Proyecto

```
asiter/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/            # Rutas de autenticación
│   │   │   └── login/
│   │   ├── (dashboard)/       # Rutas protegidas
│   │   │   ├── crear-tdr/
│   │   │   └── consultar/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/            # Componentes reutilizables
│   │   └── ui/                # Componentes shadcn/ui
│   ├── lib/                   # Utilidades
│   │   ├── utils.ts
│   │   └── auth.ts            # Autenticación (hardcodeada)
│   └── types/                 # Definiciones TypeScript
├── PROJECT_RULES.md           # Reglas y guías del proyecto
└── README.md                  # Este archivo
```

## 🎯 Funcionalidades

### ✅ Implementadas
- Login con autenticación hardcodeada
- Dashboard principal con opciones de crear y consultar TDR
- Vista de creación de TDR con formulario
- Panel de estado del TDR con indicador de progreso
- Validación de campos obligatorios

### ⏳ Próximas
- Generación real de TDR
- Revisión de calidad
- Consulta de TDRs existentes
- Integración con backend

## 📝 Documentación

Para más detalles sobre las reglas y convenciones del proyecto, consulta [PROJECT_RULES.md](./PROJECT_RULES.md).

## 🤝 Contribución

Este proyecto sigue las convenciones establecidas en `PROJECT_RULES.md`. Por favor, consulta ese documento antes de hacer cambios significativos.

## 📄 Licencia

Este proyecto es privado.

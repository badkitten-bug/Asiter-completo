# ASITER - Reglas y Guías del Proyecto

## 📋 Descripción del Proyecto
ASITER (Asistente Inteligente de TDR) es una aplicación web para crear y gestionar Términos de Referencia (TDR) en el contexto peruano. El proyecto está construido con Next.js y React, y está diseñado para consumir un backend en el futuro.

## 🛠️ Stack Tecnológico

### Core
- **Next.js 14+** (App Router) - Framework React con SSR/SSG
- **React 18+** - Biblioteca UI
- **TypeScript** - Tipado estático
- **Bun** - Runtime y gestor de paquetes (velocidad)

### Estilos y UI
- **Tailwind CSS** - Framework de utilidades CSS
- **shadcn/ui** - Componentes UI modernos y accesibles (basados en Radix UI)
- **Lucide React** - Iconos modernos

### Estado y Formularios
- **Zustand** - Gestión de estado ligera (opcional para estado global)
- **React Hook Form** - Manejo de formularios
- **Zod** - Validación de esquemas

### Desarrollo
- **ESLint** - Linter
- **Prettier** - Formateador de código

## 📁 Estructura del Proyecto

```
asiter/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/            # Rutas de autenticación (grupo)
│   │   │   └── login/
│   │   ├── (dashboard)/       # Rutas protegidas (grupo)
│   │   │   ├── crear-tdr/
│   │   │   └── consultar/
│   │   ├── layout.tsx
│   │   └── page.tsx           # Página principal/redirección
│   ├── components/            # Componentes reutilizables
│   │   ├── ui/                # Componentes shadcn/ui
│   │   ├── auth/
│   │   └── tdr/
│   ├── lib/                   # Utilidades y helpers
│   │   ├── utils.ts
│   │   └── auth.ts            # Lógica de autenticación (hardcodeada por ahora)
│   ├── types/                 # Definiciones TypeScript
│   └── hooks/                 # Custom hooks
├── public/                    # Archivos estáticos
├── PROJECT_RULES.md          # Este archivo
└── package.json
```

## 🎨 Convenciones de Código

### Nomenclatura
- **Componentes**: PascalCase (`LoginForm.tsx`, `TdrCreator.tsx`)
- **Archivos de utilidades**: camelCase (`utils.ts`, `auth.ts`)
- **Hooks**: camelCase con prefijo `use` (`useAuth.ts`, `useTdr.ts`)
- **Tipos/Interfaces**: PascalCase (`User.ts`, `TdrData.ts`)

### Estilos
- Usar **Tailwind CSS** para todos los estilos
- Componentes UI de **shadcn/ui** como base
- Mantener consistencia en espaciado (usar valores de Tailwind)
- Colores: seguir la paleta definida en `tailwind.config.js`

### Componentes
- Componentes funcionales con TypeScript
- Props tipadas con interfaces
- Usar `export default` para componentes de página
- Usar `export` nombrado para componentes reutilizables

### Autenticación (Temporal)
- Credenciales hardcodeadas en `src/lib/auth.ts`
- Usuario de prueba: `admin@asiter.com` / `admin123`
- Implementar middleware de Next.js para proteger rutas
- Usar cookies/session storage para mantener sesión

## 📝 Funcionalidades Principales

### 1. Autenticación
- Login con email y contraseña (hardcodeado)
- Validación de formulario
- Redirección después del login
- Protección de rutas

### 2. Crear TDR
- Formulario con campos:
  - Título breve del objeto (obligatorio)
  - Descripción detallada (obligatorio)
  - Frase inicial opcional
- Botones de acción:
  - Generar TDR
  - Revisar calidad
  - Sugerir ejemplo (para descripción)
  - Limpiar campos
- Panel de estado del TDR:
  - Indicador de progreso
  - Estado (Incompleto/Completo)
  - Lista de campos faltantes
  - Botón "Ver TDR"

### 3. Consultar TDR
- Vista para consultar TDRs existentes (implementación futura)

## 🚀 Comandos del Proyecto

```bash
# Instalar dependencias
bun install

# Desarrollo
bun dev

# Build
bun run build

# Producción
bun start

# Linting
bun run lint

# Formateo
bun run format
```

## 🔒 Seguridad (Futuro)
- Cuando se integre el backend, migrar autenticación a JWT/tokens
- Validar todas las entradas del usuario
- Sanitizar datos antes de mostrar

## 📦 Dependencias Principales

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "tailwindcss": "^3.4.0",
    "@radix-ui/react-*": "versiones de shadcn/ui",
    "lucide-react": "^0.300.0",
    "react-hook-form": "^7.48.0",
    "zod": "^3.22.0",
    "@hookform/resolvers": "^3.3.0",
    "zustand": "^4.4.0"
  }
}
```

## 🎯 Próximos Pasos
1. ✅ Configurar proyecto base con Next.js + TypeScript + Tailwind
2. ✅ Instalar shadcn/ui y componentes necesarios
3. ✅ Implementar login básico
4. ✅ Implementar vista de crear TDR
5. ⏳ Integrar con backend (futuro)
6. ⏳ Implementar funcionalidad de consultar TDR

## 📌 Notas Importantes
- Este documento debe ser actualizado cuando se agreguen nuevas reglas o convenciones
- Los agentes de IA deben consultar este documento antes de hacer cambios significativos
- Mantener consistencia con las convenciones establecidas
- Priorizar código limpio y mantenible sobre velocidad de desarrollo


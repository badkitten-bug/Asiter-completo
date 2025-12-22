import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  // Rutas públicas que no requieren autenticación
  const publicPaths = ["/login", "/api/auth"];
  
  const { pathname } = request.nextUrl;
  
  // Permitir acceso a rutas públicas y API de auth
  if (
    publicPaths.some((path) => pathname.startsWith(path)) ||
    pathname === "/"
  ) {
    return NextResponse.next();
  }
  
  // Para rutas protegidas, Better Auth manejará la autenticación
  // a través de sus propios mecanismos
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};


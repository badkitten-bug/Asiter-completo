"use client";

import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_BETTER_AUTH_URL || "http://localhost:3000",
});

// Exportar funciones de conveniencia
export const { signIn, signOut, signUp, useSession } = authClient;

// Tipos para compatibilidad
export interface User {
  id: string;
  email: string;
  name: string;
  image?: string;
}

// Funciones de compatibilidad con código existente
export async function login(email: string, password: string): Promise<User | null> {
  try {
    const result = await signIn.email({
      email,
      password,
    });
    
    if (result.error) {
      return null;
    }
    
    return {
      id: result.data?.user?.id || "",
      email: result.data?.user?.email || email,
      name: result.data?.user?.name || "",
      image: result.data?.user?.image || undefined,
    };
  } catch {
    return null;
  }
}

export async function logout(): Promise<void> {
  await signOut();
}

export function getCurrentUser(): User | null {
  // Esta función ahora se debe usar con useSession hook
  // Mantenemos por compatibilidad pero es mejor usar useSession
  return null;
}

export function setCurrentUser(user: User): void {
  // Ya no es necesario, Better Auth maneja esto automáticamente
}

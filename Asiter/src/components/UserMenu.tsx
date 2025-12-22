"use client";

import { useRouter } from "next/navigation";
import { signOut, useSession } from "@/lib/auth";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { User, Settings, LogOut } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";

export function UserMenu() {
  const router = useRouter();
  const { data: session } = useSession();
  const { getThemeClasses } = useTheme();

  if (!session?.user) {
    return null;
  }

  const user = session.user;
  // Intentar obtener imagen/nombre de localStorage si están guardados
  const savedName = typeof window !== "undefined" ? localStorage.getItem("asiter-user-name") : null;
  const savedImage = typeof window !== "undefined" ? localStorage.getItem("asiter-user-image") : null;
  
  const displayName = savedName || user.name || "";
  const displayImage = savedImage || user.image || "";
  
  const initials = displayName
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || user.email?.[0].toUpperCase() || "U";

  const theme = getThemeClasses();

  const handleLogout = async () => {
    await signOut();
    router.push("/login");
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className={`flex items-center justify-center w-10 h-10 rounded-full ${theme.primary} text-white font-semibold ${theme.hover} transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2`}>
          {displayImage ? (
            <img
              src={displayImage}
              alt={displayName || "Usuario"}
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            <span className="text-sm">{initials}</span>
          )}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <div className="px-2 py-1.5">
          <p className="text-sm font-semibold text-gray-900">
            {displayName || "Usuario"}
          </p>
          <p className="text-xs text-gray-500 truncate">{user.email}</p>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => router.push("/dashboard/perfil")}
          className="cursor-pointer"
        >
          <User className="w-4 h-4 mr-2" />
          Perfil
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => router.push("/dashboard/configuracion")}
          className="cursor-pointer"
        >
          <Settings className="w-4 h-4 mr-2" />
          Configuración
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={handleLogout}
          className="cursor-pointer text-red-600 focus:text-red-600 focus:bg-red-50"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Cerrar sesión
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}


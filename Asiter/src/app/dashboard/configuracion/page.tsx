"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Palette, Loader2 } from "lucide-react";
import Link from "next/link";
import { useTheme, type ThemeColor } from "@/contexts/ThemeContext";

const colorSchemes: Record<ThemeColor, { name: string; primary: string; hover: string; preview: string }> = {
  blue: {
    name: "Azul",
    primary: "bg-blue-600",
    hover: "hover:bg-blue-700",
    preview: "bg-blue-600",
  },
  green: {
    name: "Verde",
    primary: "bg-green-600",
    hover: "hover:bg-green-700",
    preview: "bg-green-600",
  },
  purple: {
    name: "Morado",
    primary: "bg-purple-600",
    hover: "hover:bg-purple-700",
    preview: "bg-purple-600",
  },
  orange: {
    name: "Naranja",
    primary: "bg-orange-600",
    hover: "hover:bg-orange-700",
    preview: "bg-orange-600",
  },
  red: {
    name: "Rojo",
    primary: "bg-red-600",
    hover: "hover:bg-red-700",
    preview: "bg-red-600",
  },
};

export default function ConfiguracionPage() {
  const router = useRouter();
  const { data: session, isPending } = useSession();
  const { themeColor, setThemeColor, getThemeClasses } = useTheme();
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!isPending && !session) {
      router.push("/login");
      return;
    }
  }, [session, isPending, router]);

  const handleColorChange = (color: ThemeColor) => {
    setThemeColor(color);
    setMessage({ type: "success", text: "Color actualizado correctamente" });
    // Recargar después de un breve delay para aplicar cambios
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  };

  if (isPending || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Link href="/dashboard">
          <Button variant="ghost" className="mb-6">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver al Dashboard
          </Button>
        </Link>

        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-full bg-blue-600 text-white flex items-center justify-center">
              <Palette className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Configuración</h1>
              <p className="text-gray-600">Personaliza la apariencia de la aplicación</p>
            </div>
          </div>

          {message && (
            <div
              className={`mb-6 p-4 rounded-md ${
                message.type === "success"
                  ? "bg-green-50 text-green-800 border border-green-200"
                  : "bg-red-50 text-red-800 border border-red-200"
              }`}
            >
              {message.text}
            </div>
          )}

          <div className="space-y-8">
            <div>
              <Label className="text-lg font-semibold mb-4 block">
                Color del tema
              </Label>
              <div className="grid grid-cols-5 gap-4">
                {Object.entries(colorSchemes).map(([key, scheme]) => {
                  const colorKey = key as ThemeColor;
                  return (
                    <button
                      key={key}
                      onClick={() => handleColorChange(colorKey)}
                      className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all ${
                        themeColor === colorKey
                          ? "border-gray-900 shadow-md"
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                    >
                      <div
                        className={`w-12 h-12 rounded-full ${scheme.preview}`}
                      />
                      <span className="text-sm font-medium">{scheme.name}</span>
                      {themeColor === colorKey && (
                        <span className={`text-xs ${getThemeClasses().text} font-semibold`}>✓ Seleccionado</span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="pt-4 border-t">
              <p className="text-sm text-gray-500">
                Los cambios de color se aplicarán en toda la aplicación. Algunos cambios pueden requerir recargar la página.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


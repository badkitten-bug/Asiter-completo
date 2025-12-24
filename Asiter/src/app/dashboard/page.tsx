"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { FileText, Search, Loader2 } from "lucide-react";
import { TdrFilter } from "@/components/tdr/TdrFilter";
import { TdrTypeSelector } from "@/components/tdr/TdrTypeSelector";
import { UserMenu } from "@/components/UserMenu";
import { getMyTdrs, type MyTdr } from "@/lib/api";
import { useTheme } from "@/contexts/ThemeContext";
import type { TdrTipo } from "@/lib/tdr-types";
import { tdrTipoLabels } from "@/lib/tdr-types";

export default function DashboardPage() {
  const router = useRouter();
  const { data: session, isPending } = useSession();
  const { getThemeClasses } = useTheme();
  const [selectedTipo, setSelectedTipo] = useState<TdrTipo | null>(null);
  const [showTypeSelector, setShowTypeSelector] = useState(false);
  const [myTdrs, setMyTdrs] = useState<MyTdr[]>([]);
  const [loadingTdrs, setLoadingTdrs] = useState(true);
  
  const theme = useMemo(() => getThemeClasses(), [getThemeClasses]);

  useEffect(() => {
    if (!isPending && !session) {
      router.push("/login");
    }
  }, [session, isPending, router]);

  useEffect(() => {
    if (session) {
      loadMyTdrs();
    }
  }, [session]);

  const loadMyTdrs = async () => {
    if (!session?.user?.id) return;
    
    try {
      setLoadingTdrs(true);
      const response = await getMyTdrs(session.user.id, 20, 0);
      setMyTdrs(response.tdrs);
    } catch (error) {
      console.error("Error al cargar TDRs:", error);
    } finally {
      setLoadingTdrs(false);
    }
  };


  const handleCrearTdr = () => {
    setShowTypeSelector(true);
  };

  const handleSelectTipo = (tipo: TdrTipo) => {
    // Guardar el tipo en sessionStorage y redirigir
    if (typeof window !== "undefined") {
      sessionStorage.setItem("tdr_tipo_seleccionado", tipo);
    }
    router.push(`/dashboard/crear-tdr?tipo=${tipo}`);
  };

  if (isPending || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const user = session.user;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-center mb-2">
                <span className={`border-b-2 ${theme.border} pb-2`}>
                  ASISTENTE INTELIGENTE DE TDR(ASITER)
                </span>
              </h1>
            </div>
            <UserMenu />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Panel de Filtros - Izquierda */}
          <div className="lg:col-span-1">
            <TdrFilter
              selectedTipo={selectedTipo}
              onSelectTipo={setSelectedTipo}
            />
          </div>

          {/* Panel Principal - Centro/Derecha */}
          <div className="lg:col-span-3">
            <div className="flex gap-6 justify-center">
              <Button
                size="lg"
                className={`h-32 w-64 flex flex-col items-center justify-center gap-3 text-lg ${theme.primary} ${theme.hover} text-white`}
                onClick={handleCrearTdr}
              >
                <div className="flex items-center gap-2">
                  <div className={`w-8 h-8 ${theme.bg} rounded flex items-center justify-center`}>
                    <span className={`${theme.text} font-bold text-sm`}>AI</span>
                  </div>
                  <FileText className="w-6 h-6" />
                </div>
                CREAR TDR
              </Button>

              <Button
                size="lg"
                variant="outline"
                className="h-32 w-64 flex flex-col items-center justify-center gap-3 text-lg border-2 border-blue-600 text-blue-600 bg-white hover:bg-blue-600 hover:text-white transition-colors"
                onClick={() => router.push("/dashboard/consultar")}
              >
                <Search className="w-8 h-8" />
                CONSULTAR
              </Button>
            </div>

            {/* Indicador de filtro activo */}
            {selectedTipo && (
              <div className="mt-6 bg-orange-50 border-2 border-orange-500 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-orange-800">
                      Filtro activo:
                    </p>
                    <p className="text-lg font-bold text-orange-900">
                      {tdrTipoLabels[selectedTipo]}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedTipo(null)}
                    className="border-orange-500 text-orange-700 hover:bg-orange-100"
                  >
                    Limpiar
                  </Button>
                </div>
              </div>
            )}

            {/* Lista de TDRs Generados */}
            <div className="mt-12">
              <h2 className="text-2xl font-bold mb-4">Mis TDRs Generados</h2>
              
              {loadingTdrs ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                </div>
              ) : myTdrs.length === 0 ? (
                <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-2">No has generado ningún TDR aún</p>
                  <p className="text-sm text-gray-500">
                    Crea tu primer TDR usando el botón &quot;CREAR TDR&quot; arriba
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {myTdrs.map((tdr) => (
                    <div
                      key={tdr.id}
                      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded">
                              {tdrTipoLabels[tdr.tipo as TdrTipo] || tdr.tipo}
                            </span>
                            <h3 className="font-semibold text-lg">{tdr.titulo}</h3>
                          </div>
                          <p className="text-sm text-gray-500">
                            Creado: {new Date(tdr.created_at).toLocaleDateString("es-PE", {
                              year: "numeric",
                              month: "long",
                              day: "numeric",
                            })}
                          </p>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/dashboard/crear-tdr?id=${tdr.id}`)}
                        >
                          Ver/Editar
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <TdrTypeSelector
        open={showTypeSelector}
        onOpenChange={setShowTypeSelector}
        onSelect={handleSelectTipo}
      />
    </div>
  );
}


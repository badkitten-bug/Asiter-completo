"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Search } from "lucide-react";
import Link from "next/link";
import { TdrFilter } from "@/components/tdr/TdrFilter";
import type { TdrTipo } from "@/lib/tdr-types";
import { tdrTipoLabels } from "@/lib/tdr-types";

export default function ConsultarPage() {
  const router = useRouter();
  const [selectedTipo, setSelectedTipo] = useState<TdrTipo | null>(null);

  useEffect(() => {
    const currentUser = getCurrentUser();
    if (!currentUser) {
      router.push("/login");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm" className="mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Volver
            </Button>
          </Link>
          <h1 className="text-2xl font-bold">Consultar TDR</h1>
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
            {selectedTipo && (
              <div className="mb-6 bg-orange-50 border-2 border-orange-500 rounded-lg p-4">
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

            <div className="bg-white p-8 rounded-lg shadow-sm text-center">
              <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-2">
                Funcionalidad de consulta próximamente disponible.
              </p>
              {selectedTipo && (
                <p className="text-sm text-gray-500">
                  Filtrando por: <strong>{tdrTipoLabels[selectedTipo]}</strong>
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


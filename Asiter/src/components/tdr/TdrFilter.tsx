"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { TdrTipo } from "@/lib/tdr-types";
import { tdrTipoLabels } from "@/lib/tdr-types";
import { Package, Building2, Wrench, FileText } from "lucide-react";

interface TdrFilterProps {
  selectedTipo: TdrTipo | null;
  onSelectTipo: (tipo: TdrTipo | null) => void;
}

const tipoOptions: Array<{ value: TdrTipo; label: string; icon: typeof Package }> = [
  { value: "SERVICIO", label: tdrTipoLabels.SERVICIO, icon: FileText },
  { value: "CONSULTORIA_OBRA", label: tdrTipoLabels.CONSULTORIA_OBRA, icon: Wrench },
  { value: "BIEN", label: tdrTipoLabels.BIEN, icon: Package },
  { value: "OBRA", label: tdrTipoLabels.OBRA, icon: Building2 },
];

export function TdrFilter({ selectedTipo, onSelectTipo }: TdrFilterProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 border-2 border-green-500">
      <div className="mb-3">
        <p className="text-sm font-semibold text-gray-700 mb-1">
          Filtro para seleccionar
        </p>
      </div>
      <div className="space-y-2">
        {tipoOptions.map((option) => {
          const Icon = option.icon;
          const isSelected = selectedTipo === option.value;
          return (
            <Button
              key={option.value}
              variant={isSelected ? "default" : "outline"}
              className={cn(
                "w-full justify-start",
                isSelected && "bg-blue-600 hover:bg-blue-700"
              )}
              onClick={() =>
                onSelectTipo(isSelected ? null : option.value)
              }
            >
              <Icon className="w-4 h-4 mr-2" />
              {option.label}
            </Button>
          );
        })}
      </div>
      {selectedTipo && (
        <div className="mt-4 pt-4 border-t">
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-xs"
            onClick={() => onSelectTipo(null)}
          >
            Limpiar filtro
          </Button>
        </div>
      )}
    </div>
  );
}


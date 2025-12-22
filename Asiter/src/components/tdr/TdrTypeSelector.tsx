"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { FileText, Building2, Wrench, Package } from "lucide-react";
import type { TdrTipo } from "@/lib/tdr-types";
import { tdrTipoLabels, tdrTipoDescriptions } from "@/lib/tdr-types";

interface TdrTypeSelectorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (tipo: TdrTipo) => void;
}

const tipoIcons = {
  BIEN: Package,
  OBRA: Building2,
  CONSULTORIA_OBRA: Wrench,
  SERVICIO: FileText,
};

export function TdrTypeSelector({
  open,
  onOpenChange,
  onSelect,
}: TdrTypeSelectorProps) {
  const tipos: TdrTipo[] = ["BIEN", "OBRA", "CONSULTORIA_OBRA", "SERVICIO"];

  const handleSelect = (tipo: TdrTipo) => {
    onSelect(tipo);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Seleccionar Tipo de TDR</DialogTitle>
          <DialogDescription>
            Selecciona el tipo de Término de Referencia que deseas crear
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-4 py-4">
          {tipos.map((tipo) => {
            const Icon = tipoIcons[tipo];
            return (
              <Button
                key={tipo}
                variant="outline"
                className="h-32 flex flex-col items-center justify-center gap-3 hover:bg-blue-50 hover:border-blue-500"
                onClick={() => handleSelect(tipo)}
              >
                <Icon className="w-8 h-8 text-blue-600" />
                <div className="text-center">
                  <div className="font-semibold">{tdrTipoLabels[tipo]}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {tdrTipoDescriptions[tipo]}
                  </div>
                </div>
              </Button>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}


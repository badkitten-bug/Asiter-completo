"use client";

import { useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { FileText, Download, X } from "lucide-react";
import type { TdrData } from "@/types";
import type { TdrTipo } from "@/lib/tdr-types";
import { tdrTipoLabels } from "@/lib/tdr-types";
import { tdrSectionsByType } from "@/lib/tdr-sections";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

interface TdrViewerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tdrTipo: TdrTipo | null;
  tdrData: TdrData;
}

export function TdrViewer({ open, onOpenChange, tdrTipo, tdrData }: TdrViewerProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  const handleExportPDF = async () => {
    if (!contentRef.current || !tdrTipo) return;

    try {
      // Mostrar indicador de carga
      const loadingButton = document.activeElement as HTMLElement;
      const originalText = loadingButton?.textContent;
      if (loadingButton) {
        loadingButton.textContent = "Generando PDF...";
        loadingButton.setAttribute("disabled", "true");
      }

      // Capturar el contenido como imagen
      const canvas = await html2canvas(contentRef.current, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: "#ffffff",
      });

      // Crear PDF
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = canvas.width;
      const imgHeight = canvas.height;
      const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
      const imgScaledWidth = imgWidth * ratio;
      const imgScaledHeight = imgHeight * ratio;

      // Si el contenido es más alto que una página, dividirlo
      const pageHeight = imgScaledHeight;
      let heightLeft = imgScaledHeight;
      let position = 0;

      pdf.addImage(imgData, "PNG", 0, position, imgScaledWidth, imgScaledHeight);
      heightLeft -= pdfHeight;

      while (heightLeft >= 0) {
        position = heightLeft - imgScaledHeight;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, position, imgScaledWidth, imgScaledHeight);
        heightLeft -= pdfHeight;
      }

      // Descargar PDF
      const fileName = `TDR_${tdrTipo}_${new Date().toISOString().split("T")[0]}.pdf`;
      pdf.save(fileName);

      // Restaurar botón
      if (loadingButton) {
        loadingButton.textContent = originalText || "Descargar PDF";
        loadingButton.removeAttribute("disabled");
      }
    } catch (error) {
      console.error("Error al generar PDF:", error);
      alert("Error al generar el PDF. Por favor, intenta nuevamente.");
    }
  };

  if (!tdrTipo) return null;

  const sections = tdrSectionsByType[tdrTipo] || [];
  const tipoLabel = tdrTipoLabels[tdrTipo];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Visualización de TDR - {tipoLabel}
          </DialogTitle>
          <DialogDescription>
            Revisa el contenido del TDR antes de exportarlo o procesarlo.
          </DialogDescription>
        </DialogHeader>

        <div ref={contentRef} className="p-8 bg-white">
          {/* Encabezado del TDR */}
          <div className="mb-8 border-b-2 border-gray-300 pb-4">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {tdrData.tituloBreve || 
               tdrData.denominacionContratacion || 
               "Términos de Referencia"}
            </h1>
            <p className="text-sm text-gray-600">
              Tipo: <span className="font-semibold">{tipoLabel}</span>
            </p>
            {tdrData.fraseInicial && (
              <p className="text-base text-gray-700 mt-2 italic">
                {tdrData.fraseInicial}
              </p>
            )}
          </div>

          {/* Contenido por secciones */}
          {sections.map((section) => {
            // Obtener los campos de esta sección que tienen datos
            const sectionFields = section.fields
              .map((fieldKey) => {
                const fieldValue = tdrData[fieldKey as keyof TdrData];
                if (!fieldValue || (typeof fieldValue === "string" && !fieldValue.trim())) {
                  return null;
                }
                return { key: fieldKey, value: fieldValue };
              })
              .filter((f): f is { key: string; value: any } => f !== null);

            // Si no hay campos con datos en esta sección, no mostrarla
            if (sectionFields.length === 0) {
              return null;
            }

            return (
              <div key={section.id} className="mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 border-l-4 border-blue-600 pl-3">
                  {section.title}
                </h2>
                {section.description && (
                  <p className="text-sm text-gray-600 mb-4 italic">{section.description}</p>
                )}
                
                <div className="space-y-4">
                  {sectionFields.map(({ key, value }) => {
                    // Formatear el nombre del campo (convertir camelCase a título)
                    const fieldLabel = key
                      .replace(/([A-Z])/g, " $1")
                      .replace(/^./, (str) => str.toUpperCase())
                      .trim();

                    return (
                      <div key={key} className="mb-4">
                        <h3 className="text-base font-semibold text-gray-700 mb-2">
                          {fieldLabel}
                        </h3>
                        {typeof value === "string" ? (
                          <div className="text-gray-700 whitespace-pre-wrap leading-relaxed pl-4 border-l-2 border-gray-200">
                            {value}
                          </div>
                        ) : Array.isArray(value) ? (
                          <ul className="list-disc list-inside space-y-2 text-gray-700 pl-4 border-l-2 border-gray-200">
                            {value.map((item, idx) => (
                              <li key={idx}>{String(item)}</li>
                            ))}
                          </ul>
                        ) : typeof value === "object" && value !== null ? (
                          <div className="text-gray-700 pl-4 border-l-2 border-gray-200">
                            <pre className="whitespace-pre-wrap font-sans">
                              {JSON.stringify(value, null, 2)}
                            </pre>
                          </div>
                        ) : (
                          <div className="text-gray-700 pl-4 border-l-2 border-gray-200">
                            {String(value)}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* Campos adicionales que no están en ninguna sección */}
          {(() => {
            const allSectionFields = new Set(
              sections.flatMap((s) => s.fields)
            );
            const additionalFields = Object.entries(tdrData).filter(
              ([key, value]) => {
                // Excluir campos especiales o que ya están en secciones
                if (
                  key === "tipo" ||
                  key === "tituloBreve" ||
                  key === "denominacionContratacion" ||
                  key === "fraseInicial" ||
                  key === "descripcionDetallada" ||
                  allSectionFields.has(key) ||
                  !value ||
                  (typeof value === "string" && !value.trim())
                ) {
                  return false;
                }
                return true;
              }
            );

            if (additionalFields.length === 0) return null;

            return (
              <div className="mt-8 pt-6 border-t-2 border-gray-300">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">
                  Información Adicional
                </h2>
                <div className="space-y-4">
                  {additionalFields.map(([key, value]) => {
                    const fieldLabel = key
                      .replace(/([A-Z])/g, " $1")
                      .replace(/^./, (str) => str.toUpperCase())
                      .trim();

                    return (
                      <div key={key} className="mb-4">
                        <h3 className="text-base font-semibold text-gray-700 mb-2">
                          {fieldLabel}
                        </h3>
                        <div className="text-gray-700 whitespace-pre-wrap pl-4 border-l-2 border-gray-200">
                          {typeof value === "string"
                            ? value
                            : JSON.stringify(value, null, 2)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })()}

          {/* Pie de página */}
          <div className="mt-8 pt-4 border-t border-gray-300 text-xs text-gray-500 text-center">
            Generado el {new Date().toLocaleDateString("es-ES", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </div>
        </div>

        <DialogFooter className="flex gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            <X className="w-4 h-4 mr-2" />
            Cerrar
          </Button>
          <Button onClick={handleExportPDF} className="bg-blue-600 hover:bg-blue-700">
            <Download className="w-4 h-4 mr-2" />
            Descargar PDF
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}


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

      // Capturar el contenido como imagen con mayor calidad
      const canvas = await html2canvas(contentRef.current, {
        scale: 3, // Mayor resolución para mejor calidad
        useCORS: true,
        logging: false,
        backgroundColor: "#ffffff",
        windowWidth: 794, // Ancho A4 en px a 96 DPI
      });

      // Crear PDF A4
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      
      // Márgenes en mm
      const marginLeft = 15;
      const marginTop = 15;
      const contentWidth = pdfWidth - (marginLeft * 2);
      
      const imgWidth = canvas.width;
      const imgHeight = canvas.height;
      const ratio = contentWidth / imgWidth;
      const imgScaledWidth = imgWidth * ratio;
      const imgScaledHeight = imgHeight * ratio;

      // Calcular páginas
      const pageContentHeight = pdfHeight - (marginTop * 2);
      let heightLeft = imgScaledHeight;
      let position = 0;
      let pageNum = 0;

      // Primera página
      pdf.addImage(
        canvas.toDataURL("image/png"),
        "PNG",
        marginLeft,
        marginTop - position,
        imgScaledWidth,
        imgScaledHeight
      );
      heightLeft -= pageContentHeight;
      pageNum++;

      // Páginas adicionales si el contenido es largo
      while (heightLeft > 0) {
        position += pageContentHeight;
        pdf.addPage();
        pdf.addImage(
          canvas.toDataURL("image/png"),
          "PNG",
          marginLeft,
          marginTop - position,
          imgScaledWidth,
          imgScaledHeight
        );
        heightLeft -= pageContentHeight;
        pageNum++;
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

  // Contador de secciones para numeración
  let sectionNumber = 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Vista Previa del Documento - {tipoLabel}
          </DialogTitle>
          <DialogDescription>
            Revisa el contenido del TDR antes de exportarlo como PDF.
          </DialogDescription>
        </DialogHeader>

        {/* Contenedor del documento con estilo de página */}
        <div 
          ref={contentRef} 
          className="bg-white mx-auto"
          style={{
            width: "210mm",
            minHeight: "297mm",
            padding: "25mm 20mm",
            boxShadow: "0 0 10px rgba(0,0,0,0.1)",
            fontFamily: "'Times New Roman', Times, serif",
          }}
        >
          {/* Encabezado institucional */}
          <div className="text-center mb-8 pb-4 border-b-2 border-gray-400">
            <p className="text-xs text-gray-500 mb-2 tracking-widest uppercase">
              Términos de Referencia
            </p>
            <h1 
              className="text-xl font-bold text-gray-900 mb-3 leading-tight"
              style={{ fontFamily: "'Arial', sans-serif" }}
            >
              {tdrData.tituloBreve || 
               tdrData.denominacionContratacion || 
               "TÉRMINOS DE REFERENCIA"}
            </h1>
            <div className="flex justify-center items-center gap-4 text-sm text-gray-600">
              <span className="px-3 py-1 bg-blue-50 border border-blue-200 rounded">
                Tipo: <strong>{tipoLabel}</strong>
              </span>
              <span className="px-3 py-1 bg-gray-50 border border-gray-200 rounded">
                Fecha: {new Date().toLocaleDateString("es-PE", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </span>
            </div>
          </div>

          {/* Frase inicial si existe */}
          {tdrData.fraseInicial && (
            <div className="mb-6 p-4 bg-gray-50 border-l-4 border-blue-500 italic text-gray-700">
              {tdrData.fraseInicial}
            </div>
          )}

          {/* Contenido por secciones */}
          {sections.map((section) => {
            const sectionFields = section.fields
              .map((fieldKey) => {
                const fieldValue = tdrData[fieldKey as keyof TdrData];
                if (!fieldValue || (typeof fieldValue === "string" && !fieldValue.trim())) {
                  return null;
                }
                return { key: fieldKey, value: fieldValue };
              })
              .filter((f): f is { key: string; value: any } => f !== null);

            if (sectionFields.length === 0) {
              return null;
            }

            sectionNumber++;

            return (
              <div key={section.id} className="mb-6">
                {/* Título de sección numerado */}
                <div className="flex items-start gap-3 mb-4">
                  <span 
                    className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold"
                    style={{ fontFamily: "'Arial', sans-serif" }}
                  >
                    {sectionNumber}
                  </span>
                  <div>
                    <h2 
                      className="text-lg font-bold text-gray-800 uppercase tracking-wide"
                      style={{ fontFamily: "'Arial', sans-serif" }}
                    >
                      {section.title}
                    </h2>
                    {section.description && (
                      <p className="text-sm text-gray-500 mt-1">{section.description}</p>
                    )}
                  </div>
                </div>
                
                {/* Campos de la sección */}
                <div className="ml-11 space-y-4">
                  {sectionFields.map(({ key, value }, fieldIdx) => {
                    const fieldLabel = key
                      .replace(/([A-Z])/g, " $1")
                      .replace(/^./, (str) => str.toUpperCase())
                      .trim();

                    return (
                      <div key={key} className="mb-4">
                        <h3 
                          className="text-sm font-bold text-gray-700 mb-2 uppercase"
                          style={{ fontFamily: "'Arial', sans-serif" }}
                        >
                          {sectionNumber}.{fieldIdx + 1} {fieldLabel}
                        </h3>
                        {typeof value === "string" ? (
                          <div 
                            className="text-gray-800 whitespace-pre-wrap leading-relaxed text-justify pl-4 border-l-2 border-gray-300"
                            style={{ textAlign: "justify" }}
                          >
                            {value}
                          </div>
                        ) : Array.isArray(value) ? (
                          <ul className="list-disc space-y-1 text-gray-800 pl-8">
                            {value.map((item, idx) => (
                              <li key={idx} className="leading-relaxed">{String(item)}</li>
                            ))}
                          </ul>
                        ) : typeof value === "object" && value !== null ? (
                          <div className="text-gray-800 pl-4 border-l-2 border-gray-300">
                            <pre className="whitespace-pre-wrap font-sans text-sm">
                              {JSON.stringify(value, null, 2)}
                            </pre>
                          </div>
                        ) : (
                          <div className="text-gray-800 pl-4 border-l-2 border-gray-300">
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

            sectionNumber++;

            return (
              <div className="mb-6 pt-4 border-t border-gray-200">
                <div className="flex items-start gap-3 mb-4">
                  <span 
                    className="flex-shrink-0 w-8 h-8 bg-gray-600 text-white rounded-full flex items-center justify-center text-sm font-bold"
                    style={{ fontFamily: "'Arial', sans-serif" }}
                  >
                    {sectionNumber}
                  </span>
                  <h2 
                    className="text-lg font-bold text-gray-800 uppercase tracking-wide"
                    style={{ fontFamily: "'Arial', sans-serif" }}
                  >
                    Información Adicional
                  </h2>
                </div>
                <div className="ml-11 space-y-4">
                  {additionalFields.map(([key, value], fieldIdx) => {
                    const fieldLabel = key
                      .replace(/([A-Z])/g, " $1")
                      .replace(/^./, (str) => str.toUpperCase())
                      .trim();

                    return (
                      <div key={key} className="mb-4">
                        <h3 
                          className="text-sm font-bold text-gray-700 mb-2 uppercase"
                          style={{ fontFamily: "'Arial', sans-serif" }}
                        >
                          {sectionNumber}.{fieldIdx + 1} {fieldLabel}
                        </h3>
                        <div 
                          className="text-gray-800 whitespace-pre-wrap pl-4 border-l-2 border-gray-300"
                          style={{ textAlign: "justify" }}
                        >
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
          <div className="mt-12 pt-6 border-t-2 border-gray-400">
            <div className="flex justify-between items-center text-xs text-gray-500">
              <span>TDR - {tipoLabel}</span>
              <span>
                Documento generado el {new Date().toLocaleDateString("es-PE", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </span>
            </div>
            <p className="text-center text-xs text-gray-400 mt-4 italic">
              Este documento fue generado automáticamente por el Sistema ASITER
            </p>
          </div>
        </div>

        <DialogFooter className="flex gap-2 mt-4">
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


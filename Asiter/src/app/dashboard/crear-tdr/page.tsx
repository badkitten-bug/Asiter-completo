"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useSession } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  FileText,
  Sparkles,
  CheckCircle2,
  Search,
  ArrowLeft,
  Save,
  AlertCircle,
  CheckCircle,
  Info,
  Loader2,
  Zap,
  Database,
} from "lucide-react";
import Link from "next/link";
import type { TdrData, TdrStatus } from "@/types";
import type { TdrTipo } from "@/lib/tdr-types";
import { tdrFieldsByType, tdrTipoLabels } from "@/lib/tdr-types";
import { tdrSectionsByType } from "@/lib/tdr-sections";
import { TdrFormField } from "@/components/tdr/TdrFormField";
import { TdrSection } from "@/components/tdr/TdrSection";
import { TdrViewer } from "@/components/tdr/TdrViewer";
import {
  saveTdrDraft,
  loadTdrDraft,
  clearTdrDraft,
  hasTdrDraft,
  getTdrDraftInfo,
  markTdrDraftAsCompleted,
} from "@/lib/tdr-storage";
import { validateTdrData } from "@/lib/tdr-validation";
import { 
  generateFields, 
  checkHealth, 
  mapBackendFieldsToFrontend,
  addTdrToDatabase,
  type GenerateFieldsResponse 
} from "@/lib/api";

// Wrapper with Suspense for useSearchParams
export default function CrearTdrPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>}>
      <CrearTdrContent />
    </Suspense>
  );
}

function CrearTdrContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { data: session, isPending } = useSession();
  const [tdrTipo, setTdrTipo] = useState<TdrTipo | null>(null);
  const [tdrData, setTdrData] = useState<TdrData>({
    tituloBreve: "",
    descripcionDetallada: "",
    fraseInicial: "",
  });
  const [status, setStatus] = useState<TdrStatus>({
    estado: "Incompleto",
    progreso: 0,
    camposFaltantes: [],
  });
  const [validationErrors, setValidationErrors] = useState<
    Record<string, string>
  >({});
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [showSaveNotification, setShowSaveNotification] = useState(false);
  
  // Estados para RAG
  const [isGenerating, setIsGenerating] = useState(false);
  const [ragResult, setRagResult] = useState<GenerateFieldsResponse | null>(null);
  const [backendReady, setBackendReady] = useState<boolean | null>(null);
  const [ragError, setRagError] = useState<string | null>(null);
  
  // Estados para guardar TDR
  const [isSavingToDb, setIsSavingToDb] = useState(false);
  const [savedToDb, setSavedToDb] = useState(false);
  const [totalTdrsInDb, setTotalTdrsInDb] = useState<number | null>(null);
  
  // Estado para diálogo de borrador
  const [showDraftDialog, setShowDraftDialog] = useState(false);
  const [draftInfo, setDraftInfo] = useState<{ data: TdrData; timestamp: string } | null>(null);
  
  // Estado para visualización de TDR
  const [showTdrViewer, setShowTdrViewer] = useState(false);

  useEffect(() => {
    if (!isPending && !session) {
      router.push("/login");
      return;
    }

    // Obtener tipo de TDR desde URL o sessionStorage
    const tipoFromUrl = searchParams.get("tipo") as TdrTipo | null;
    const tipoFromStorage =
      typeof window !== "undefined"
        ? (sessionStorage.getItem("tdr_tipo_seleccionado") as TdrTipo | null)
        : null;

    const tipo = tipoFromUrl || tipoFromStorage;

    if (
      !tipo ||
      !["BIEN", "OBRA", "CONSULTORIA_OBRA", "SERVICIO"].includes(tipo)
    ) {
      router.push("/dashboard");
      return;
    }

    setTdrTipo(tipo);
    
    // Verificar si hay un borrador pendiente
    const draftInfo = getTdrDraftInfo(tipo);
    if (draftInfo && draftInfo.status === "draft") {
      // Mostrar diálogo para preguntar si quiere restaurar
      setDraftInfo({
        data: draftInfo.data,
        timestamp: draftInfo.timestamp,
      });
      setShowDraftDialog(true);
    } else {
      // No hay borrador o está completado, empezar limpio
      setTdrData((prev) => ({ ...prev, tipo }));
    }
    
    // Verificar si el backend RAG está disponible
    checkHealth()
      .then((health) => {
        setBackendReady(health.ready);
        if (health.ready) {
          console.log(`✅ Backend conectado - ${health.total_tdrs} TDRs disponibles`);
        } else {
          console.warn("⚠️ Backend no disponible o sin TDRs");
        }
      })
      .catch((error) => {
        console.error("Error verificando backend:", error);
        setBackendReady(false);
      });
  }, [router, searchParams]);

  // Guardar automáticamente cada 30 segundos (solo si no está guardado)
  useEffect(() => {
    if (!tdrTipo || savedToDb) return;

    const autoSaveInterval = setInterval(() => {
      // Solo guardar si hay datos y no está completado
      if (tdrData.tituloBreve || tdrData.descripcionDetallada) {
        saveTdrDraft(tdrTipo, tdrData);
        setLastSaved(new Date());
        setShowSaveNotification(true);
        setTimeout(() => setShowSaveNotification(false), 3000);
      }
    }, 30000); // 30 segundos

    return () => clearInterval(autoSaveInterval);
  }, [tdrTipo, tdrData, savedToDb]);

  // Guardar manualmente
  const handleManualSave = useCallback(() => {
    if (!tdrTipo) return;
    saveTdrDraft(tdrTipo, tdrData);
    setLastSaved(new Date());
    setShowSaveNotification(true);
    setTimeout(() => setShowSaveNotification(false), 3000);
  }, [tdrTipo, tdrData]);

  useEffect(() => {
    if (!tdrTipo) return;

    // Calcular progreso basado en campos requeridos del tipo
    const fields = tdrFieldsByType[tdrTipo];
    const camposObligatorios = fields.filter((f) => f.required);
    const camposCompletados = camposObligatorios.filter((field) => {
      const value = tdrData[field.key];
      return value !== undefined && value !== null && value !== "";
    }).length;

    const progreso =
      camposObligatorios.length > 0
        ? Math.round((camposCompletados / camposObligatorios.length) * 100)
        : 0;

    const camposFaltantes = camposObligatorios
      .filter((field) => {
        const value = tdrData[field.key];
        return !value || value === "";
      })
      .map((field) => field.label);

    setStatus({
      estado: progreso === 100 ? "Completo" : "Incompleto",
      progreso,
      camposFaltantes,
    });
  }, [tdrData, tdrTipo]);

  const handleFieldChange = (key: string, value: any) => {
    setTdrData((prev) => ({ ...prev, [key]: value }));
    // Limpiar error de validación cuando el usuario modifica el campo
    if (validationErrors[key]) {
      setValidationErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[key];
        return newErrors;
      });
    }
  };

  const handleSugerirEjemplo = async () => {
    if (!tdrTipo) return;
    
    // Verificar que hay al menos título o descripción
    if (!tdrData.tituloBreve && !tdrData.descripcionDetallada) {
      setRagError("Por favor, ingresa al menos un título o descripción para generar sugerencias.");
      return;
    }
    
    setIsGenerating(true);
    setRagError(null);
    
    try {
      // Usar un número dinámico de referencias (puede ser configurable)
      // Por defecto 5, pero el backend puede devolver menos si no hay suficientes
      const numReferencias = 5;
      
      const result = await generateFields({
        tipo: tdrTipo,
        descripcion_inicial: tdrData.descripcionDetallada || undefined,
        objeto_contratacion: tdrData.tituloBreve || undefined,
        num_referencias: numReferencias,
      }, session?.user?.id);
      
      setRagResult(result);
      
      if (result.success && result.campos_sugeridos) {
        // Mapear campos del backend al formato del frontend
        const mappedFields = mapBackendFieldsToFrontend(result.campos_sugeridos);
        
        // Actualizar todos los campos con las sugerencias
        setTdrData((prev) => ({
          ...prev,
          ...mappedFields,
          // Mantener los campos iniciales que el usuario ya llenó
          tituloBreve: prev.tituloBreve || mappedFields.denominacionContratacion || "",
          descripcionDetallada: prev.descripcionDetallada || mappedFields.descripcion || "",
        }));
      }
    } catch (error) {
      console.error("Error al generar campos:", error);
      setRagError(
        error instanceof Error 
          ? error.message 
          : "Error al conectar con el servicio de IA. Verifica que el backend esté corriendo."
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleLimpiar = () => {
    setTdrData((prev) => ({ ...prev, descripcionDetallada: "" }));
  };

  const handleGenerarTdr = async () => {
    if (!tdrTipo) return;

    // Validar datos
    const validation = validateTdrData(tdrTipo, tdrData);
    
    if (!validation.valid) {
      // Mostrar errores de validación
      const errors: Record<string, string> = {};
      validation.errors?.forEach((error) => {
        errors[error.field] = error.message;
      });
      setValidationErrors(errors);
      
      // Scroll al primer error
      const firstErrorField = Object.keys(errors)[0];
      if (firstErrorField) {
        const element = document.getElementById(firstErrorField);
        element?.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      
      alert("Por favor, complete todos los campos obligatorios correctamente.");
      return;
    }

    // Guardar TDR en la base de datos para aprendizaje continuo
    setIsSavingToDb(true);
    
    try {
      const result = await addTdrToDatabase({
        tipo: tdrTipo,
        titulo: tdrData.tituloBreve || tdrData.denominacionContratacion || "TDR Sin Título",
        campos: tdrData,
        usuario: session?.user?.email,
      }, session?.user?.id);
      
      if (result.success) {
        setSavedToDb(true);
        setTotalTdrsInDb(result.total_tdrs);
        
        // Marcar borrador como completado y luego limpiarlo
        markTdrDraftAsCompleted(tdrTipo);
        // Limpiar después de un breve delay para asegurar que se guardó
        setTimeout(() => {
          clearTdrDraft(tdrTipo);
        }, 1000);
        
        console.log("TDR guardado:", result);
        alert(`✅ TDR generado y guardado exitosamente!\n\n📚 El sistema ahora tiene ${result.total_tdrs} TDRs de referencia.\n\nCada TDR creado mejora las sugerencias futuras.`);
      }
    } catch (error) {
      console.error("Error al guardar TDR:", error);
      // Aún así permitir generar aunque no se guarde
      alert("TDR generado. (No se pudo guardar en la base de conocimiento)");
    } finally {
      setIsSavingToDb(false);
    }
  };

  const handleRevisarCalidad = () => {
    if (!tdrTipo) return;

    const validation = validateTdrData(tdrTipo, tdrData);
    
    if (!validation.valid) {
      const errors: Record<string, string> = {};
      validation.errors?.forEach((error) => {
        errors[error.field] = error.message;
      });
      setValidationErrors(errors);
      alert("Hay errores en el formulario. Por favor, corríjalos antes de revisar la calidad.");
      return;
    }

    alert("Funcionalidad de revisión de calidad próximamente");
  };

  // Manejar restauración de borrador
  const handleRestoreDraft = () => {
    if (draftInfo && tdrTipo) {
      setTdrData({ ...draftInfo.data, tipo: tdrTipo });
      setShowDraftDialog(false);
      setDraftInfo(null);
    }
  };

  // Manejar descartar borrador
  const handleDiscardDraft = () => {
    if (tdrTipo) {
      clearTdrDraft(tdrTipo);
      setShowDraftDialog(false);
      setDraftInfo(null);
      // Empezar con formulario limpio
      setTdrData({
        tituloBreve: "",
        descripcionDetallada: "",
        fraseInicial: "",
        tipo: tdrTipo,
      });
    }
  };

  if (isPending || !session || !tdrTipo) {
    return null;
  }
  
  const user = session.user;

  const fields = tdrFieldsByType[tdrTipo];
  const sections = tdrSectionsByType[tdrTipo];
  const fieldsMap = new Map(fields.map((f) => [f.key, f]));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header con notificación de guardado */}
        <div className="mb-6">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm" className="mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Volver
            </Button>
          </Link>
          
          {/* Indicador de borrador pendiente */}
          {hasTdrDraft(tdrTipo) && !savedToDb && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4 text-blue-600" />
                <span className="text-sm text-blue-800">
                  Tienes un borrador guardado automáticamente
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  clearTdrDraft(tdrTipo);
                  window.location.reload();
                }}
                className="text-blue-600 hover:text-blue-700"
              >
                Descartar borrador
              </Button>
            </div>
          )}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">
                Crear TDR - {tdrTipoLabels[tdrTipo]}
              </h1>
              {lastSaved && (
                <p className="text-sm text-gray-500 mt-1">
                  Último guardado: {lastSaved.toLocaleTimeString()}
                </p>
              )}
            </div>
            <div className="flex items-center gap-3">
              {showSaveNotification && (
                <div className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-lg text-sm">
                  <CheckCircle className="w-4 h-4" />
                  Guardado automáticamente
                </div>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={handleManualSave}
                className="flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Guardar
              </Button>
              <div className="px-4 py-2 bg-blue-100 text-blue-800 rounded-lg text-sm font-semibold">
                {tdrTipoLabels[tdrTipo]}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Panel Izquierdo - Formulario */}
          <div className="lg:col-span-2 space-y-6">
            {/* Campos básicos comunes */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="mb-4 pb-3 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">
                  Información Inicial
                </h2>
                <p className="text-sm text-gray-500 mt-1">
                  Datos básicos para comenzar el TDR
                </p>
              </div>
              
              <div className="space-y-4">
                <div>
                  <Label htmlFor="titulo" className="text-base font-semibold">
                    Título breve del objeto <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="titulo"
                    placeholder='Ej.: Servicio de difusión de spots radiales'
                    value={tdrData.tituloBreve || ""}
                    onChange={(e) => handleFieldChange("tituloBreve", e.target.value)}
                    className={`mt-2 ${validationErrors.tituloBreve ? "border-red-500" : ""}`}
                  />
                  {validationErrors.tituloBreve && (
                    <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                      <AlertCircle className="w-4 h-4" />
                      {validationErrors.tituloBreve}
                    </p>
                  )}
                  <p className="text-sm text-gray-600 mt-2">
                    Frase corta que resuma la contratación (sin "Contratación de..."
                    si no quieres repetir).
                  </p>
                </div>

                <div>
                  <Label htmlFor="descripcion" className="text-base font-semibold">
                    Descripción detallada <span className="text-red-500">*</span>
                  </Label>
                  <Textarea
                    id="descripcion"
                    placeholder="Describe con claridad qué se está contratando, qué incluye y, si corresponde, el público objetivo o alcance."
                    value={tdrData.descripcionDetallada || ""}
                    onChange={(e) =>
                      handleFieldChange("descripcionDetallada", e.target.value)
                    }
                    className={`mt-2 min-h-[120px] ${validationErrors.descripcionDetallada ? "border-red-500" : ""}`}
                  />
                  {validationErrors.descripcionDetallada && (
                    <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                      <AlertCircle className="w-4 h-4" />
                      {validationErrors.descripcionDetallada}
                    </p>
                  )}
                  <p className="text-sm text-gray-600 mt-2">
                    Evita frases vacías como "según requerimiento del área usuaria".
                    Sé concreto y medible.
                  </p>
                  <div className="flex flex-col gap-3 mt-3">
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="default"
                        size="sm"
                        onClick={handleSugerirEjemplo}
                        disabled={isGenerating || backendReady === false}
                        className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                      >
                        {isGenerating ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Generando con IA...
                          </>
                        ) : (
                          <>
                            <Zap className="w-4 h-4" />
                            Generar con IA
                          </>
                        )}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleLimpiar}
                        className="flex items-center gap-2"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        Limpiar
                      </Button>
                    </div>
                    
                    {/* Indicador de estado del backend */}
                    {backendReady !== null && (
                      <div className={`flex items-center justify-between gap-2 text-xs px-2 py-1 rounded ${
                        backendReady 
                          ? "bg-green-50 text-green-700" 
                          : "bg-yellow-50 text-yellow-700"
                      }`}>
                        <div className="flex items-center gap-2">
                          <Database className="w-3 h-3" />
                          {backendReady 
                            ? "IA conectada y lista" 
                            : "Backend no disponible - Verifica que el servidor esté corriendo en http://localhost:8001"}
                        </div>
                        {!backendReady && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-xs"
                            onClick={async () => {
                              const health = await checkHealth();
                              setBackendReady(health.ready);
                            }}
                          >
                            Reintentar
                          </Button>
                        )}
                      </div>
                    )}
                    
                    {/* Error de RAG */}
                    {ragError && (
                      <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded">
                        <AlertCircle className="w-4 h-4" />
                        {ragError}
                      </div>
                    )}
                    
                    {/* Resultado de RAG */}
                    {ragResult && ragResult.success && (
                      <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-2 rounded">
                        <Sparkles className="w-4 h-4" />
                        Campos sugeridos (confianza: {Math.round(ragResult.confidence * 100)}%)
                        {ragResult.referencias_usadas.length > 0 && (
                          <span className="text-gray-500">
                            - Basado en {ragResult.referencias_usadas.length} TDRs similares
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <Label htmlFor="fraseInicial" className="text-base font-semibold">
                    Frase inicial opcional
                  </Label>
                  <Input
                    id="fraseInicial"
                    placeholder='Ej.: La presente contratación tiene por objeto...'
                    value={tdrData.fraseInicial || ""}
                    onChange={(e) => handleFieldChange("fraseInicial", e.target.value)}
                    className="mt-2"
                  />
                  <p className="text-sm text-gray-600 mt-2">
                    Si la dejas vacía, usaré una frase estándar.
                  </p>
                </div>
              </div>
            </div>

            {/* Campos dinámicos agrupados en secciones */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <Info className="w-5 h-5 text-blue-600" />
                <h2 className="text-xl font-semibold text-gray-800">
                  Campos Específicos por Sección
                </h2>
              </div>
              
              {sections.map((section) => {
                const sectionFields = section.fields
                  .map((fieldKey) => fieldsMap.get(fieldKey))
                  .filter((field): field is NonNullable<typeof field> => field !== undefined);

                if (sectionFields.length === 0) return null;

                return (
                  <TdrSection
                    key={section.id}
                    title={section.title}
                    description={section.description}
                    defaultOpen={section.id === "basico"}
                  >
                    <div className="space-y-4">
                      {sectionFields.map((field) => {
                        const hasError = validationErrors[field.key];
                        return (
                          <div key={field.key}>
                            <TdrFormField
                              field={field}
                              value={tdrData[field.key]}
                              onChange={(value) => handleFieldChange(field.key, value)}
                            />
                            {hasError && (
                              <p className="text-sm text-red-500 mt-1 flex items-center gap-1 ml-6">
                                <AlertCircle className="w-4 h-4" />
                                {validationErrors[field.key]}
                              </p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </TdrSection>
                );
              })}
            </div>

            {/* Botones de acción */}
            <div className="flex gap-3 pt-4 sticky bottom-0 bg-gray-50 pb-4 border-t border-gray-200">
              <Button
                onClick={handleGenerarTdr}
                className="flex items-center gap-2"
                size="lg"
                disabled={isSavingToDb}
              >
                {isSavingToDb ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <FileText className="w-5 h-5" />
                    Generar TDR
                  </>
                )}
              </Button>
              <Button
                onClick={handleRevisarCalidad}
                variant="outline"
                size="lg"
                className="flex items-center gap-2"
              >
                <Search className="w-5 h-5" />
                Revisar calidad
              </Button>
              
              {/* Indicador de guardado exitoso */}
              {savedToDb && totalTdrsInDb && (
                <div className="flex items-center gap-2 px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm">
                  <CheckCircle className="w-4 h-4" />
                  Guardado en BD ({totalTdrsInDb} TDRs)
                </div>
              )}
            </div>
          </div>

          {/* Panel Derecho - Estado */}
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Estado del TDR</h2>
                <Button variant="outline" size="sm">
                  SEMÁFORO
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{status.estado}</span>
                    <span className="text-sm text-gray-600">
                      {status.progreso}%
                    </span>
                  </div>
                  <Progress
                    value={status.progreso}
                    className="h-2"
                    indicatorClassName={
                      status.progreso === 100
                        ? "bg-green-500"
                        : "bg-red-500"
                    }
                  />
                </div>

                {status.estado === "Incompleto" && (
                  <div className="text-sm text-gray-600">
                    <p className="mb-2">
                      Complete los campos obligatorios y revise la calidad.
                    </p>
                    {status.camposFaltantes.length > 0 && (
                      <ul className="list-disc list-inside space-y-1 max-h-48 overflow-y-auto">
                        {status.camposFaltantes.slice(0, 10).map((campo, index) => (
                          <li key={index}>• {campo}</li>
                        ))}
                        {status.camposFaltantes.length > 10 && (
                          <li className="text-gray-400">
                            ... y {status.camposFaltantes.length - 10} más
                          </li>
                        )}
                      </ul>
                    )}
                  </div>
                )}

                {status.estado === "Completo" && (
                  <div className="flex items-center gap-2 text-green-600 bg-green-50 p-3 rounded-lg">
                    <CheckCircle className="w-5 h-5" />
                    <span className="text-sm font-medium">
                      Todos los campos obligatorios están completos
                    </span>
                  </div>
                )}

                <Button
                  variant="outline"
                  size="sm"
                  className="w-full flex items-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  Coherencia objetivo → alcance → plazo
                </Button>
              </div>
            </div>

            <Button
              size="lg"
              className="w-full flex items-center justify-center gap-2"
              onClick={() => {
                // Validar que hay datos antes de mostrar
                if (!tdrTipo) {
                  alert("Por favor, selecciona un tipo de TDR primero.");
                  return;
                }
                setShowTdrViewer(true);
              }}
            >
              <FileText className="w-5 h-5" />
              Ver TDR
            </Button>
          </div>
        </div>
      </div>

      {/* Diálogo para restaurar borrador */}
      <Dialog open={showDraftDialog} onOpenChange={setShowDraftDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Restaurar borrador pendiente?</DialogTitle>
            <DialogDescription>
              Se encontró un borrador guardado anteriormente para este tipo de TDR.
              {draftInfo && (
                <span className="block mt-2 text-xs text-gray-500">
                  Guardado el: {new Date(draftInfo.timestamp).toLocaleString("es-ES")}
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-gray-600">
              ¿Deseas restaurar el borrador anterior o empezar con un formulario limpio?
            </p>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={handleDiscardDraft}
            >
              Descartar y empezar nuevo
            </Button>
            <Button
              onClick={handleRestoreDraft}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Restaurar borrador
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Visualizador de TDR */}
      <TdrViewer
        open={showTdrViewer}
        onOpenChange={setShowTdrViewer}
        tdrTipo={tdrTipo}
        tdrData={tdrData}
      />
    </div>
  );
}

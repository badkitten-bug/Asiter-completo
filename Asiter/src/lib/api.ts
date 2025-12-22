/**
 * Servicio API para conectar con el backend TDR Generator.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

/**
 * Crea headers con autenticación.
 * Better Auth usa cookies HTTP-only. Para el backend, necesitamos obtener
 * el user ID de la sesión y enviarlo en un header.
 */
async function getAuthHeaders(userId?: string): Promise<HeadersInit> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  
  // Si se proporciona un user ID, enviarlo en el header
  if (userId) {
    headers["X-User-Id"] = userId;
  } else {
    // Intentar obtener el user ID de la sesión de Better Auth
    try {
      const sessionResponse = await fetch("/api/auth/get-session", {
        credentials: "include",
      });
      
      if (sessionResponse.ok) {
        const sessionData = await sessionResponse.json();
        if (sessionData.data?.user?.id) {
          headers["X-User-Id"] = sessionData.data.user.id;
        }
      }
    } catch {
      // Si falla, continuar sin user ID
    }
  }
  
  return headers;
}

export interface TdrTipoAPI {
  value: string;
  label: string;
  description: string;
}

export interface TdrSearchResult {
  id: string;
  filename: string;
  tipo: string;
  similarity: number;
  fields: Record<string, any>;
}

export interface GenerateFieldsRequest {
  tipo: "BIEN" | "SERVICIO" | "OBRA" | "CONSULTORIA_OBRA";
  descripcion_inicial?: string;
  objeto_contratacion?: string;
  campos_parciales?: Record<string, string>;
  num_referencias?: number;
}

export interface GenerateFieldsResponse {
  success: boolean;
  tipo: string;
  campos_sugeridos: Record<string, any>;
  referencias_usadas: TdrSearchResult[];
  confidence: number;
}

export interface TdrStats {
  total_tdrs: number;
  por_tipo: Record<string, number>;
  por_categoria: Record<string, number>;
}

/**
 * Obtiene las estadísticas de la base de datos.
 */
export async function getStats(): Promise<TdrStats> {
  const response = await fetch(`${API_BASE_URL}/api/tdr/stats`);
  if (!response.ok) {
    throw new Error("Error al obtener estadísticas");
  }
  return response.json();
}

/**
 * Busca TDRs similares en la base de datos.
 */
export async function searchTdrs(
  query: string,
  tipo?: string,
  limit: number = 5
): Promise<TdrSearchResult[]> {
  const params = new URLSearchParams({ q: query, limit: limit.toString() });
  if (tipo) {
    params.append("tipo", tipo);
  }

  const response = await fetch(`${API_BASE_URL}/api/tdr/search?${params}`);
  if (!response.ok) {
    throw new Error("Error al buscar TDRs");
  }
  return response.json();
}

/**
 * Genera campos para un nuevo TDR usando RAG.
 */
export async function generateFields(
  request: GenerateFieldsRequest,
  userId?: string
): Promise<GenerateFieldsResponse> {
  const headers = await getAuthHeaders(userId);
  const response = await fetch(`${API_BASE_URL}/api/tdr/generate`, {
    method: "POST",
    headers,
    credentials: "include",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Error al generar campos: ${error}`);
  }

  return response.json();
}

/**
 * Obtiene los tipos de TDR disponibles.
 */
export async function getTipos(): Promise<{ tipos: TdrTipoAPI[] }> {
  const response = await fetch(`${API_BASE_URL}/api/tdr/tipos`);
  if (!response.ok) {
    throw new Error("Error al obtener tipos");
  }
  return response.json();
}

/**
 * Verifica si el backend está disponible.
 */
export async function checkHealth(): Promise<{
  status: string;
  total_tdrs: number;
  ready: boolean;
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      // No usar AbortSignal.timeout si no está disponible
      signal: typeof AbortSignal !== "undefined" && AbortSignal.timeout 
        ? AbortSignal.timeout(5000) 
        : undefined,
    });
    
    if (!response.ok) {
      console.error(`Backend health check failed: ${response.status} ${response.statusText}`);
      return { status: "offline", total_tdrs: 0, ready: false };
    }
    
    const data = await response.json();
    return {
      status: data.status || "healthy",
      total_tdrs: data.total_tdrs || 0,
      ready: data.ready !== false && data.status === "healthy",
    };
  } catch (error) {
    console.error("Error checking backend health:", error);
    return { status: "offline", total_tdrs: 0, ready: false };
  }
}

export interface AddTdrRequest {
  tipo: "BIEN" | "SERVICIO" | "OBRA" | "CONSULTORIA_OBRA";
  titulo: string;
  campos: Record<string, any>;
  usuario?: string;
}

export interface AddTdrResponse {
  success: boolean;
  message: string;
  tdr_id: string;
  total_tdrs: number;
}

/**
 * Agrega un nuevo TDR a la base de datos para aprendizaje continuo.
 * Esto permite que el sistema mejore con cada TDR creado.
 */
export async function addTdrToDatabase(
  request: AddTdrRequest,
  userId?: string
): Promise<AddTdrResponse> {
  const headers = await getAuthHeaders(userId);
  const response = await fetch(`${API_BASE_URL}/api/tdr/add`, {
    method: "POST",
    headers,
    credentials: "include",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Error al guardar TDR: ${error}`);
  }

  return response.json();
}

export interface MyTdr {
  id: string;
  tipo: string;
  titulo: string;
  created_at: string;
  updated_at: string;
  campos: Record<string, any>;
}

export interface MyTdrsResponse {
  tdrs: MyTdr[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Obtiene los TDRs generados por el usuario actual.
 */
export async function getMyTdrs(
  userId: string,
  limit: number = 50,
  offset: number = 0
): Promise<MyTdrsResponse> {
  const headers = await getAuthHeaders(userId);
  const response = await fetch(
    `${API_BASE_URL}/api/tdr/my-tdrs?limit=${limit}&offset=${offset}`,
    {
      headers,
      credentials: "include",
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("No autenticado. Por favor inicia sesión.");
    }
    const error = await response.text();
    throw new Error(`Error al obtener TDRs: ${error}`);
  }

  return response.json();
}

/**
 * Mapea campos del backend a campos del frontend.
 * El backend usa snake_case, el frontend usa camelCase.
 */
export function mapBackendFieldsToFrontend(
  campos: Record<string, any>
): Record<string, any> {
  // Mapeo completo de todos los campos posibles
  const mapping: Record<string, string> = {
    // Campos básicos - incluyendo variantes de Gemini
    titulo: "tituloBreve",
    denominacion_contratacion: "denominacionContratacion",
    objeto_contratacion: "objetivoContratacion",
    objetivo_contratacion: "objetivoContratacion",
    finalidad_publica: "finalidadPublica",
    objetivo_general: "objetivoGeneral",
    objetivos_especificos: "objetivosEspecificos",
    
    // Campos adicionales que Gemini puede generar
    version: "version",
    fecha_elaboracion: "fechaElaboracion",
    entidad_contratante: "entidadContratante",
    area_usuaria: "areaUsuaria",
    
    // Descripción y alcance
    alcance: "alcance",
    alcance_descripcion_bienes: "alcanceDescripcionBienes",
    alcance_descripcion_servicio: "alcanceDescripcionServicio",
    descripcion_servicio: "descripcion",
    descripcion: "descripcion",
    descripcion_detallada_servicio: "descripcionDetalladaServicio",
    
    // Características
    caracteristicas: "caracteristicas",
    caracteristicas_tecnicas: "caracteristicasTecnicas",
    especificaciones_tecnicas: "especificacionesTecnicas",
    
    // Cantidades
    cantidad: "cantidad",
    unidad_medida: "unidad",
    
    // Actividades y entregables
    actividades: "actividades",
    entregables: "entregables",
    entregable: "entregable",
    
    // Perfil y requisitos del proveedor
    perfil_proveedor: "perfilProveedor",
    perfil_profesional: "perfilProveedor",
    requisitos_proveedor: "requisitosProveedor",
    requisitos_tecnicos_minimos: "caracteristicasTecnicas",
    formacion_academica: "formacionAcademica",
    experiencia: "experiencia",
    acreditacion: "acreditacion",
    
    // Ejecución
    plazo: "plazo",
    plazo_ejecucion: "plazo",
    lugar: "lugar",
    lugar_prestacion: "lugar",
    lugar_plazo_ejecucion: "lugarPlazoEjecucion",
    
    // Control y supervisión
    supervision: "supervision",
    conformidad: "conformidad",
    medidas_control_ejecucion: "medidasControlEjecucion",
    areas_coordinar_contratista: "areasCoordinarContratista",
    gestion_riesgos: "gestionRiesgos",
    
    // Pago
    forma_pago: "formaPago",
    forma_condiciones_pago: "formaCondicionesPago",
    
    // Garantías
    garantia_comercial: "garantiaComercial",
    prestaciones_accesorias: "prestacionesAccesorias",
    
    // Legal
    penalidades: "penalidades",
    penalidad_mora: "penalidadMora",
    otras_penalidades: "otrasPenalidades",
    confidencialidad: "confidencialidad",
    anticorrupcion_antisoborno: "anticorrupcionAntisoborno",
    clausula_antisoborno: "clausulaAntisoborno",
    clausula_anticorrupcion_antisoborno: "clausulaAnticorrupcionAntisoborno",
    responsabilidad_vicios_ocultos: "responsabilidadViciosOcultos",
    solucion_controversias: "solucionControversias",
    
    // Adicional
    antecedentes: "antecedentes",
    actividad_poi: "actividadPoi",
    
    // Consultoría obra
    plan_trabajo: "planTrabajo",
    funciones_especificas: "funcionesEspecificas",
    funciones_generales: "funcionesGenerales",
    metodologias_procedimientos: "metodologiasProcedimientos",
    costo_total: "costoTotal",
    
    // Obra
    valor_unitario: "valorUnitario",
    importe_total: "importeTotal",
    importe_venta: "importeVenta",
  };

  const result: Record<string, any> = {};

  for (const [backendKey, value] of Object.entries(campos)) {
    if (value === null || value === undefined || value === "") continue;
    
    const frontendKey = mapping[backendKey] || toCamelCase(backendKey);
    
    // Convertir arrays y objetos a strings si es necesario
    if (Array.isArray(value)) {
      if (value.length === 0) continue;
      
      // Para entregables, formatear como texto
      if (backendKey === "entregables" || backendKey === "entregable") {
        if (typeof value[0] === "object") {
          result[frontendKey] = value
            .map((e: any, i: number) => {
              const nombre = e.nombre || e.descripcion || e.ENTREGABLE || "";
              const plazo = e.plazo || e.PLAZO || "";
              const contenido = e.contenido || e.CONTENIDO || "";
              return `Entregable ${i + 1}: ${nombre}${plazo ? `\nPlazo: ${plazo}` : ""}${contenido ? `\n${contenido}` : ""}`;
            })
            .join("\n\n");
        } else {
          result[frontendKey] = value.map((v, i) => `${i + 1}. ${v}`).join("\n");
        }
      } else if (backendKey === "actividades") {
        result[frontendKey] = value.map((v, i) => `${i + 1}. ${v}`).join("\n");
      } else if (backendKey.includes("requisitos") || backendKey.includes("objetivos")) {
        result[frontendKey] = value.map((v, i) => `• ${v}`).join("\n");
      } else {
        result[frontendKey] = value.join("\n");
      }
    } else if (typeof value === "object" && value !== null) {
      // Convertir objetos a texto formateado
      if (backendKey === "perfil_profesional" || backendKey === "perfil_proveedor") {
        const parts = [];
        if (value.formacion) parts.push(`Formación: ${value.formacion}`);
        if (value.experiencia) parts.push(`Experiencia: ${value.experiencia}`);
        if (value.conocimientos) {
          const conocimientos = Array.isArray(value.conocimientos) 
            ? value.conocimientos.join(", ") 
            : value.conocimientos;
          parts.push(`Conocimientos: ${conocimientos}`);
        }
        // Incluir cualquier otro campo del objeto
        for (const [k, v] of Object.entries(value)) {
          if (!["formacion", "experiencia", "conocimientos"].includes(k) && v) {
            parts.push(`${capitalizeFirst(k)}: ${v}`);
          }
        }
        result[frontendKey] = parts.join("\n");
      } else {
        // Para otros objetos, formatear cada propiedad
        const parts = Object.entries(value)
          .filter(([_, v]) => v)
          .map(([k, v]) => `${capitalizeFirst(k.replace(/_/g, " "))}: ${v}`);
        result[frontendKey] = parts.join("\n");
      }
    } else {
      result[frontendKey] = String(value);
    }
  }

  return result;
}

// Helpers
function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

function capitalizeFirst(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}


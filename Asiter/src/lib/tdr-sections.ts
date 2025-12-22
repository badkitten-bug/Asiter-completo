import type { TdrTipo } from "./tdr-types";

// Agrupación de campos por secciones lógicas
export interface TdrSection {
  id: string;
  title: string;
  description: string;
  fields: string[];
  icon?: string;
}

export const tdrSectionsByType: Record<TdrTipo, TdrSection[]> = {
  BIEN: [
    {
      id: "basico",
      title: "Información Básica",
      description: "Datos generales de la contratación",
      fields: [
        "denominacionContratacion",
        "finalidadPublica",
        "objetivoContratacion",
        "objetivoGeneral",
        "objetivosEspecificos",
        "actividadPoi",
        "dependenciaSolicitante",
        "metaPoiVinculado",
      ],
    },
    {
      id: "descripcion",
      title: "Descripción y Alcance",
      description: "Detalles del bien a contratar",
      fields: [
        "descripcion",
        "alcanceDescripcionBienes",
        "caracteristicas",
        "caracteristicasTecnicas",
        "especificacionesTecnicas",
        "material",
        "color",
        "medida",
        "cantidad",
        "muestras",
      ],
    },
    {
      id: "proveedor",
      title: "Requisitos del Proveedor",
      description: "Condiciones y perfil del proveedor",
      fields: [
        "perfilProveedor",
        "requisitosProveedor",
        "acreditacion",
        "capacidad",
      ],
    },
    {
      id: "ejecucion",
      title: "Ejecución y Control",
      description: "Medidas de control y coordinación",
      fields: [
        "plazo",
        "lugar",
        "medidasControlEjecucion",
        "areasCoordinarContratista",
        "areasResponsablesControl",
        "gestionRiesgos",
      ],
    },
    {
      id: "pago",
      title: "Pago y Garantías",
      description: "Condiciones de pago y garantías",
      fields: [
        "formaPago",
        "formaCondicionesPago",
        "garantiaComercial",
        "prestacionesAccesorias",
      ],
    },
    {
      id: "legal",
      title: "Aspectos Legales",
      description: "Cláusulas legales y penalidades",
      fields: [
        "anticorrupcionAntisoborno",
        "clausulaAntisoborno",
        "responsabilidadViciosOcultos",
        "penalidades",
        "penalidadMora",
        "otrasPenalidades",
        "solucionControversias",
        "conformidad",
      ],
    },
    {
      id: "adicional",
      title: "Información Adicional",
      description: "Otros datos relevantes",
      fields: [
        "antecedentes",
        "imagenReferencial",
        "decenioIgualdad",
        "contratoMenor",
        "otras",
        "total",
      ],
    },
  ],

  CONSULTORIA_OBRA: [
    {
      id: "basico",
      title: "Información Básica",
      description: "Datos generales de la contratación",
      fields: [
        "denominacionContratacion",
        "finalidadPublica",
        "objetivoContratacion",
        "objetivoGeneral",
        "objetivosEspecificos",
        "actividadPoi",
        "areaUsuaria",
        "objetoContratacion",
        "planOperativoInstitucional",
      ],
    },
    {
      id: "alcance",
      title: "Alcance del Servicio",
      description: "Descripción del servicio de consultoría",
      fields: [
        "alcancesDescripcionProyecto",
        "alcanceServicio",
        "descripcionDetalladaServicio",
        "descripcion",
      ],
    },
    {
      id: "supervision",
      title: "Supervisión y Funciones",
      description: "Funciones y responsabilidades",
      fields: [
        "supervision",
        "funcionesGenerales",
        "funcionesEspecificas",
      ],
    },
    {
      id: "metodologia",
      title: "Metodología y Plan de Trabajo",
      description: "Procedimientos y metodologías",
      fields: [
        "metodologiasProcedimientos",
        "planTrabajo",
        "actividades",
        "procedimiento",
      ],
    },
    {
      id: "ejecucion",
      title: "Ejecución",
      description: "Plazos y condiciones de ejecución",
      fields: [
        "plazo",
        "conformidad",
        "garantia",
        "sujetoObligado",
      ],
    },
    {
      id: "estructura",
      title: "Estructura y Costos",
      description: "Componentes y costos",
      fields: [
        "estructuraComponentes",
        "codigo",
        "item",
        "unidad",
        "cantidad",
        "participacion",
        "dias",
        "costoParcial",
        "costoTotal",
      ],
    },
    {
      id: "legal",
      title: "Aspectos Legales",
      description: "Cláusulas legales",
      fields: [
        "prestacionesAccesorias",
        "otrasPenalidades",
        "anexoN",
        "antecedentes",
      ],
    },
  ],

  OBRA: [
    {
      id: "basico",
      title: "Información Básica",
      description: "Datos generales de la obra",
      fields: [
        "ruc",
        "municipalidadDistrital",
        "boletaVentaElectronica",
      ],
    },
    {
      id: "descripcion",
      title: "Descripción de la Obra",
      description: "Detalles de la obra a ejecutar",
      fields: [
        "descripcion",
        "cantidad",
        "unidad",
        "medida",
      ],
    },
    {
      id: "valores",
      title: "Valores y Costos",
      description: "Valores unitarios y totales",
      fields: [
        "valorUnitario",
        "descuento",
        "importeVenta",
        "importeTotal",
        "soles",
      ],
    },
  ],

  SERVICIO: [
    {
      id: "basico",
      title: "Información Básica",
      description: "Datos generales de la contratación",
      fields: [
        "denominacionContratacion",
        "finalidadPublica",
        "objetivoContratacion",
        "objetivoGeneral",
        "objetivosContratacion",
        "actividadPoi",
        "areaUsuariaRequiereServicio",
        "metaPresupuestaria",
        "contratacion",
      ],
    },
    {
      id: "descripcion",
      title: "Descripción del Servicio",
      description: "Alcance y descripción del servicio",
      fields: [
        "alcanceDescripcionServicio",
        "descripcion",
        "lugarPlazoEjecucion",
        "actividades",
      ],
    },
    {
      id: "entregables",
      title: "Entregables",
      description: "Productos y entregables del servicio",
      fields: [
        "entregable",
        "entregables",
      ],
    },
    {
      id: "proveedor",
      title: "Requisitos del Proveedor",
      description: "Perfil y requisitos",
      fields: [
        "perfilProveedor",
        "requisitosProveedor",
        "requisitosProveedorPersonal",
        "formacionAcademica",
        "experiencia",
        "acreditacion",
        "requisitosContratacion",
      ],
    },
    {
      id: "ejecucion",
      title: "Ejecución y Control",
      description: "Plazos, lugar y control",
      fields: [
        "plazo",
        "lugar",
        "medidasControlEjecucion",
        "gestionRiesgos",
        "conformidad",
      ],
    },
    {
      id: "pago",
      title: "Pago",
      description: "Condiciones de pago",
      fields: [
        "formaPago",
        "formaCondicionesPago",
      ],
    },
    {
      id: "legal",
      title: "Aspectos Legales",
      description: "Cláusulas legales y penalidades",
      fields: [
        "anticorrupcionAntisoborno",
        "clausulaAnticorrupcionAntisoborno",
        "clausulaAntisoborno",
        "clausulaCumplimiento",
        "responsabilidadViciosOcultos",
        "penalidades",
        "penalidadMora",
        "otrasPenalidades",
        "resolucionContrato",
        "solucionControversias",
      ],
    },
    {
      id: "adicional",
      title: "Información Adicional",
      description: "Otros aspectos del servicio",
      fields: [
        "antecedentes",
        "confidencialidad",
        "propiedadIntelectual",
        "otrasObligacionesContratista",
        "terminosReferencia",
        "condicionesGenerales",
        "unidadOrganizacion",
        "mesaPartesDigital",
        "mesaPartesPresencial",
      ],
    },
  ],
};


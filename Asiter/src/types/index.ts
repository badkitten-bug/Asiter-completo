import type { TdrTipo } from "@/lib/tdr-types";

export interface TdrData {
  tipo?: TdrTipo;
  tituloBreve: string;
  descripcionDetallada: string;
  fraseInicial?: string;
  entidad?: string;
  areaUsuaria?: string;
  objetivoGeneral?: string;
  plazo?: string;
  lugar?: string;
  [key: string]: any; // Para campos dinámicos
}

export interface TdrStatus {
  estado: "Incompleto" | "Completo";
  progreso: number;
  camposFaltantes: string[];
}


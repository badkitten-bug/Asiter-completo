// Utilidades para guardar y cargar TDRs temporalmente en localStorage

const STORAGE_KEY_PREFIX = "asiter_tdr_draft_";

export function saveTdrDraft(tipo: string, data: any) {
  if (typeof window === "undefined") return;

  try {
    const key = `${STORAGE_KEY_PREFIX}${tipo}`;
    const draftData = {
      tipo,
      data,
      timestamp: new Date().toISOString(),
      status: "draft", // Estado del borrador: "draft" (pendiente) o "completed" (completado)
    };
    localStorage.setItem(key, JSON.stringify(draftData));
  } catch (error) {
    console.error("Error guardando borrador:", error);
  }
}

export function markTdrDraftAsCompleted(tipo: string) {
  if (typeof window === "undefined") return;

  try {
    const key = `${STORAGE_KEY_PREFIX}${tipo}`;
    const stored = localStorage.getItem(key);
    if (!stored) return;

    const draftData = JSON.parse(stored);
    draftData.status = "completed";
    draftData.completedAt = new Date().toISOString();
    localStorage.setItem(key, JSON.stringify(draftData));
  } catch (error) {
    console.error("Error marcando borrador como completado:", error);
  }
}

export function loadTdrDraft(tipo: string) {
  if (typeof window === "undefined") return null;

  try {
    const key = `${STORAGE_KEY_PREFIX}${tipo}`;
    const stored = localStorage.getItem(key);
    if (!stored) return null;

    const draftData = JSON.parse(stored);
    // Solo retornar si es un borrador pendiente, no si está completado
    if (draftData.status === "completed") {
      return null;
    }
    return draftData.data;
  } catch (error) {
    console.error("Error cargando borrador:", error);
    return null;
  }
}

export function getTdrDraftInfo(tipo: string): { data: any; timestamp: string; status: string } | null {
  if (typeof window === "undefined") return null;

  try {
    const key = `${STORAGE_KEY_PREFIX}${tipo}`;
    const stored = localStorage.getItem(key);
    if (!stored) return null;

    const draftData = JSON.parse(stored);
    return {
      data: draftData.data,
      timestamp: draftData.timestamp,
      status: draftData.status || "draft",
    };
  } catch (error) {
    console.error("Error obteniendo info del borrador:", error);
    return null;
  }
}

export function clearTdrDraft(tipo: string) {
  if (typeof window === "undefined") return;

  try {
    const key = `${STORAGE_KEY_PREFIX}${tipo}`;
    localStorage.removeItem(key);
  } catch (error) {
    console.error("Error eliminando borrador:", error);
  }
}

export function clearAllTdrDrafts() {
  if (typeof window === "undefined") return;

  try {
    const keys = Object.keys(localStorage);
    keys.forEach((key) => {
      if (key.startsWith(STORAGE_KEY_PREFIX)) {
        localStorage.removeItem(key);
      }
    });
  } catch (error) {
    console.error("Error eliminando borradores:", error);
  }
}

export function hasTdrDraft(tipo: string): boolean {
  if (typeof window === "undefined") return false;

  try {
    const key = `${STORAGE_KEY_PREFIX}${tipo}`;
    return localStorage.getItem(key) !== null;
  } catch {
    return false;
  }
}


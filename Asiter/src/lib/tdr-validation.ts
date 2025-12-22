import { z } from "zod";
import type { TdrTipo } from "./tdr-types";
import { tdrFieldsByType } from "./tdr-types";

// Crear esquema de validación dinámico basado en el tipo de TDR
export function createTdrSchema(tipo: TdrTipo) {
  const fields = tdrFieldsByType[tipo];
  const schemaObject: Record<string, any> = {
    tipo: z.literal(tipo),
    tituloBreve: z.string().min(1, "El título breve es obligatorio"),
    descripcionDetallada: z
      .string()
      .min(10, "La descripción debe tener al menos 10 caracteres"),
    fraseInicial: z.string().optional(),
  };

  // Agregar validaciones para cada campo según su tipo
  fields.forEach((field) => {
    if (field.required) {
      switch (field.type) {
        case "text":
          schemaObject[field.key] = z
            .string()
            .min(1, `${field.label} es obligatorio`);
          break;
        case "textarea":
          schemaObject[field.key] = z
            .string()
            .min(1, `${field.label} es obligatorio`);
          break;
        case "number":
          schemaObject[field.key] = z
            .union([
              z.number().min(0, `${field.label} debe ser un número válido`),
              z.string().transform((val) => {
                if (val === "") return undefined;
                const num = Number(val);
                return isNaN(num) ? undefined : num;
              }),
            ])
            .refine((val) => val !== undefined, {
              message: `${field.label} es obligatorio`,
            })
            .pipe(z.number().min(0));
          break;
        case "date":
          schemaObject[field.key] = z.string().min(1, `${field.label} es obligatorio`);
          break;
        case "select":
          schemaObject[field.key] = z.string().min(1, `${field.label} es obligatorio`);
          break;
      }
    } else {
      // Campos opcionales
      switch (field.type) {
        case "text":
        case "textarea":
        case "date":
        case "select":
          schemaObject[field.key] = z.string().optional();
          break;
        case "number":
          schemaObject[field.key] = z
            .union([
              z.number().optional(),
              z.string().transform((val) => {
                if (val === "") return undefined;
                const num = Number(val);
                return isNaN(num) ? undefined : num;
              }),
            ])
            .pipe(z.number().optional());
          break;
      }
    }
  });

  return z.object(schemaObject);
}

// Función para validar datos de TDR
export function validateTdrData(tipo: TdrTipo, data: any) {
  const schema = createTdrSchema(tipo);
  const result = schema.safeParse(data);

  if (!result.success) {
    return {
      valid: false,
      errors: result.error.errors.map((err) => ({
        field: err.path.join("."),
        message: err.message,
      })),
    };
  }

  return {
    valid: true,
    data: result.data,
  };
}


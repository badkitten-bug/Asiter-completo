"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { TdrField } from "@/lib/tdr-types";

interface TdrFormFieldProps {
  field: TdrField;
  value: any;
  onChange: (value: any) => void;
}

export function TdrFormField({ field, value, onChange }: TdrFormFieldProps) {
  const renderField = () => {
    switch (field.type) {
      case "textarea":
        return (
          <Textarea
            id={field.key}
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            className="mt-2 min-h-[100px]"
            required={field.required}
          />
        );
      case "number":
        return (
          <Input
            id={field.key}
            type="number"
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : "")}
            className="mt-2"
            required={field.required}
          />
        );
      case "date":
        return (
          <Input
            id={field.key}
            type="date"
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            className="mt-2"
            required={field.required}
          />
        );
      case "select":
        return (
          <select
            id={field.key}
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            className="mt-2 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            required={field.required}
          >
            <option value="">Seleccionar...</option>
            {field.options?.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );
      default:
        return (
          <Input
            id={field.key}
            type="text"
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            className="mt-2"
            required={field.required}
          />
        );
    }
  };

  return (
    <div>
      <Label htmlFor={field.key} className="text-base font-semibold">
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </Label>
      {renderField()}
    </div>
  );
}


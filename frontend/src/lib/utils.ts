/**
 * Utilitários genéricos de UI.
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combina classes CSS condicionalmente (`clsx`) e resolve conflitos entre
 * utilitários Tailwind (`tailwind-merge`), ex.: `cn("px-2", "px-4")` → `"px-4"`.
 * Padrão adotado pelos componentes no estilo shadcn/ui (ver components/ui).
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

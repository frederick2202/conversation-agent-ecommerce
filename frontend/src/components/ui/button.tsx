/**
 * Componente de botão reutilizável no padrão shadcn/ui (ver components.json).
 * As variações visuais são definidas com `class-variance-authority` (cva).
 * Observação: atualmente as telas usam majoritariamente <button> com classes
 * Tailwind diretas; este componente está disponível para novos desenvolvimentos.
 */
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * Mapa de classes por variante:
 * - `variant`: default (azul Lumen), success (verde), destructive (vermelho),
 *   outline (borda translúcida) e ghost (sem fundo);
 * - `size`: default, sm e lg.
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-lg text-sm font-bold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-[#0099D6] text-white hover:bg-[#0082B8]",
        success: "bg-emerald-600 text-white hover:bg-emerald-500",
        destructive: "bg-[#F04E5E] text-white hover:bg-rose-600",
        outline: "border border-white/20 bg-transparent text-white hover:bg-white/10",
        ghost: "text-slate-200 hover:bg-white/10",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-6 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

/** Props nativas de <button> + `variant` e `size` derivados de `buttonVariants`. */
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

/**
 * Botão estilizado. Usa `forwardRef` para permitir acesso ao elemento DOM
 * (foco, integração com bibliotecas) e `cn` para mesclar `className` extra
 * sem conflitos de classes Tailwind.
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size, className }))} {...props} />
  )
);
Button.displayName = "Button";

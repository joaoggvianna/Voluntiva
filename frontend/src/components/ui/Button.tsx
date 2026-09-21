import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variante = 'primary' | 'accent' | 'ghost' | 'danger'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: Variante
  children: ReactNode
}

// Coral (accent) é reservado a CTA, conforme a diretriz 70/20/10 do README.
const ESTILOS: Record<Variante, string> = {
  primary: 'bg-primary text-white hover:bg-primary/90',
  accent: 'bg-accent text-white hover:bg-accent/90',
  ghost: 'bg-transparent text-primary border border-edge hover:bg-primary-light',
  danger: 'bg-danger text-white hover:bg-danger/90',
}

export function Button({ variante = 'primary', className = '', children, ...props }: Props) {
  return (
    <button
      className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors
        disabled:cursor-not-allowed disabled:opacity-50 ${ESTILOS[variante]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

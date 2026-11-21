import { AlertTriangle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { EstadoVazio } from "@/components/EstadoVazio"

export function Carregando({ texto = "Carregando..." }) {
  return (
    <div
      className="flex items-center justify-center gap-2 py-16 text-sm text-muted-foreground"
      role="status"
      aria-live="polite"
    >
      <Loader2 className="h-4 w-4 animate-spin" /> {texto}
    </div>
  )
}

export function ErroCarga({ erro, aoTentarDeNovo }) {
  return (
    <EstadoVazio
      icone={AlertTriangle}
      titulo="Não foi possível carregar"
      descricao={erro?.message ?? "Tente novamente em instantes."}
    >
      {aoTentarDeNovo && (
        <Button variant="outline" onClick={aoTentarDeNovo}>
          Tentar de novo
        </Button>
      )}
    </EstadoVazio>
  )
}

import { Link } from "react-router-dom"
import { SearchX } from "lucide-react"
import { Button } from "@/components/ui/button"
import { EstadoVazio } from "@/components/EstadoVazio"

export function NaoEncontrada() {
  return (
    <div className="container mx-auto max-w-2xl px-4 py-16">
      <EstadoVazio
        icone={SearchX}
        titulo="Página não encontrada"
        descricao="O endereço que você tentou acessar não existe ou foi removido."
      >
        <Button asChild>
          <Link to="/">Voltar para o início</Link>
        </Button>
      </EstadoVazio>
    </div>
  )
}

import { Link, useSearchParams } from "react-router-dom"
import { SearchX } from "lucide-react"
import { Button } from "@/components/ui/button"
import { CartaoAcao } from "@/components/CartaoAcao"
import { EstadoVazio } from "@/components/EstadoVazio"
import { FiltrosAcoes } from "@/components/FiltrosAcoes"
import { useApp } from "@/contexto/AppContexto"
import { listarAcoes } from "@/lib/servico"

const CAMPOS = ["busca", "causa", "uf", "de", "ate", "vagas", "compativeis"]

export function Acoes() {
  const { usuario } = useApp()
  const [params, setParams] = useSearchParams()
  const ehVoluntario = usuario?.tipo === "voluntario"

  const filtros = Object.fromEntries(CAMPOS.map((campo) => [campo, params.get(campo) ?? ""]))

  function alterar(parcial) {
    const proximo = new URLSearchParams(params)
    Object.entries(parcial).forEach(([campo, valor]) => {
      if (valor) proximo.set(campo, valor)
      else proximo.delete(campo)
    })
    setParams(proximo, { replace: true })
  }

  const acoes = listarAcoes({
    busca: filtros.busca,
    causa: filtros.causa,
    uf: filtros.uf,
    de: filtros.de,
    ate: filtros.ate,
    somenteComVagas: Boolean(filtros.vagas),
    compativeisCom: ehVoluntario && filtros.compativeis ? usuario : null,
  })

  const perfilVazio =
    ehVoluntario &&
    usuario.habilidades.length === 0 &&
    usuario.disponibilidade.dias.length === 0

  return (
    <div className="container mx-auto space-y-6 px-4 py-10">
      <div>
        <h1 className="text-3xl font-bold">Ações sociais</h1>
        <p className="mt-2 text-muted-foreground">
          Consulte as oportunidades de voluntariado cadastradas pelas ONGs.
        </p>
      </div>

      <FiltrosAcoes
        filtros={filtros}
        aoAlterar={alterar}
        aoLimpar={() => setParams({}, { replace: true })}
        mostrarCompativeis={ehVoluntario}
      />

      {perfilVazio && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-accent/40 p-4 text-sm">
          <p>
            Preencha suas habilidades e disponibilidade para ver quais ações combinam com você.
          </p>
          <Button asChild size="sm">
            <Link to="/painel?aba=perfil">Completar perfil</Link>
          </Button>
        </div>
      )}

      <p className="text-sm text-muted-foreground" aria-live="polite">
        {acoes.length === 1 ? "1 ação encontrada" : `${acoes.length} ações encontradas`}
      </p>

      {acoes.length === 0 ? (
        <EstadoVazio
          icone={SearchX}
          titulo="Nenhuma ação encontrada"
          descricao="Tente remover alguns filtros ou buscar por outro termo."
        >
          <Button variant="outline" onClick={() => setParams({}, { replace: true })}>
            Limpar filtros
          </Button>
        </EstadoVazio>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {acoes.map((acao) => (
            <CartaoAcao key={acao.id} acao={acao} />
          ))}
        </div>
      )}
    </div>
  )
}

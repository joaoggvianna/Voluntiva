import { useEffect, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { SearchX } from "lucide-react"
import { Button } from "@/components/ui/button"
import { CartaoAcao } from "@/components/CartaoAcao"
import { Carregando, ErroCarga } from "@/components/Carregando"
import { EstadoVazio } from "@/components/EstadoVazio"
import { FiltrosAcoes } from "@/components/FiltrosAcoes"
import { useApp } from "@/contexto/AppContexto"
import { paraAcao } from "@/lib/adaptadores"
import { api } from "@/lib/api"
import { useCarregar } from "@/lib/useCarregar"

const CAMPOS = ["busca", "causa", "uf", "de", "ate", "vagas", "compativeis"]
const POR_PAGINA = 24

/** Espera o usuário parar de digitar antes de consultar o servidor. */
function useAtrasado(valor, ms = 350) {
  const [atrasado, setAtrasado] = useState(valor)
  useEffect(() => {
    const id = setTimeout(() => setAtrasado(valor), ms)
    return () => clearTimeout(id)
  }, [valor, ms])
  return atrasado
}

export function Acoes() {
  const { usuario, versao } = useApp()
  const [params, setParams] = useSearchParams()
  const [pagina, setPagina] = useState(0)
  const ehVoluntario = usuario?.tipo === "voluntario"

  const filtros = Object.fromEntries(CAMPOS.map((campo) => [campo, params.get(campo) ?? ""]))
  const busca = useAtrasado(filtros.busca)
  const compativeis = ehVoluntario && Boolean(filtros.compativeis)

  function alterar(parcial) {
    const proximo = new URLSearchParams(params)
    Object.entries(parcial).forEach(([campo, valor]) => {
      if (valor) proximo.set(campo, valor)
      else proximo.delete(campo)
    })
    setPagina(0)
    setParams(proximo, { replace: true })
  }

  function limpar() {
    setPagina(0)
    setParams({}, { replace: true })
  }

  const { dados, carregando, erro, recarregar } = useCarregar(async () => {
    // "Compatíveis comigo" usa o filtro RF004 do servidor; os demais
    // filtros são aplicados por cima, no próprio navegador.
    if (compativeis) {
      const resposta = await api.acoesCompativeis(100)
      let itens = resposta.itens.map(paraAcao)
      const termo = busca.trim().toLowerCase()
      if (termo) {
        itens = itens.filter((a) =>
          [a.titulo, a.descricao, a.ong.nome, a.unidade?.cidade]
            .join(" ")
            .toLowerCase()
            .includes(termo)
        )
      }
      if (filtros.causa) itens = itens.filter((a) => a.causaValor === filtros.causa)
      if (filtros.uf) itens = itens.filter((a) => a.unidade?.uf === filtros.uf)
      if (filtros.de) itens = itens.filter((a) => a.data >= filtros.de)
      if (filtros.ate) itens = itens.filter((a) => a.data <= filtros.ate)
      if (filtros.vagas) itens = itens.filter((a) => a.vagasRestantes > 0)
      return { itens, total: itens.length }
    }
    const resposta = await api.listarAcoes({
      busca,
      causa: filtros.causa || undefined,
      uf: filtros.uf || undefined,
      de: filtros.de || undefined,
      ate: filtros.ate || undefined,
      com_vagas: Boolean(filtros.vagas),
      futuras: true,
      limite: POR_PAGINA,
      offset: pagina * POR_PAGINA,
    })
    return { itens: resposta.itens.map(paraAcao), total: resposta.total }
  }, [busca, filtros.causa, filtros.uf, filtros.de, filtros.ate, filtros.vagas, compativeis, pagina, versao])

  const acoes = dados?.itens ?? []
  const total = dados?.total ?? 0
  const paginas = compativeis ? 1 : Math.max(Math.ceil(total / POR_PAGINA), 1)

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
        aoLimpar={limpar}
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

      {erro && !dados ? (
        <ErroCarga erro={erro} aoTentarDeNovo={recarregar} />
      ) : carregando && !dados ? (
        <Carregando texto="Buscando ações..." />
      ) : (
        <>
          <p className="text-sm text-muted-foreground" aria-live="polite">
            {total === 1 ? "1 ação encontrada" : `${total} ações encontradas`}
          </p>

          {acoes.length === 0 ? (
            <EstadoVazio
              icone={SearchX}
              titulo="Nenhuma ação encontrada"
              descricao="Tente remover alguns filtros ou buscar por outro termo."
            >
              <Button variant="outline" onClick={limpar}>
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

          {paginas > 1 && (
            <nav className="flex items-center justify-center gap-3" aria-label="Paginação">
              <Button
                variant="outline"
                size="sm"
                disabled={pagina === 0}
                onClick={() => setPagina((p) => p - 1)}
              >
                Anterior
              </Button>
              <span className="text-sm text-muted-foreground">
                Página {pagina + 1} de {paginas}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={pagina + 1 >= paginas}
                onClick={() => setPagina((p) => p + 1)}
              >
                Próxima
              </Button>
            </nav>
          )}
        </>
      )}
    </div>
  )
}

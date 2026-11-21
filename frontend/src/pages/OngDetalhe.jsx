import { Link, useParams } from "react-router-dom"
import { ArrowLeft, CalendarDays, Globe, Mail, MapPin, Phone, SearchX } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { CartaoAcao } from "@/components/CartaoAcao"
import { Carregando, ErroCarga } from "@/components/Carregando"
import { EstadoVazio } from "@/components/EstadoVazio"
import { SeloCausa } from "@/components/SeloCausa"
import { useApp } from "@/contexto/AppContexto"
import { paraAcao, paraOng } from "@/lib/adaptadores"
import { api } from "@/lib/api"
import { useCarregar } from "@/lib/useCarregar"

export function OngDetalhe() {
  const { id } = useParams()
  const { versao } = useApp()
  const { dados, carregando, erro, recarregar } = useCarregar(async () => {
    const [ong, abertas, encerradas] = await Promise.all([
      api.obterOng(id),
      api.listarAcoes({ ong_id: id, futuras: true, limite: 100 }),
      api.listarAcoes({ ong_id: id, status: "concluida", limite: 30 }),
    ])
    return {
      ong: paraOng(ong),
      acoes: [...abertas.itens, ...encerradas.itens].map(paraAcao),
    }
  }, [id, versao])

  const naoEncontrada = erro && (erro.status === 404 || erro.status === 422)
  if (carregando && !dados) return <Carregando />
  if (erro && !naoEncontrada && !dados) {
    return (
      <div className="container mx-auto max-w-2xl px-4 py-16">
        <ErroCarga erro={erro} aoTentarDeNovo={recarregar} />
      </div>
    )
  }

  if (naoEncontrada || !dados) {
    return (
      <div className="container mx-auto max-w-2xl px-4 py-16">
        <EstadoVazio
          icone={SearchX}
          titulo="ONG não encontrada"
          descricao="Ela pode ter sido removida ou o endereço está incorreto."
        >
          <Button asChild>
            <Link to="/ongs">Ver todas as ONGs</Link>
          </Button>
        </EstadoVazio>
      </div>
    )
  }

  const { ong, acoes } = dados
  const abertas = acoes.filter((a) => a.situacao === "ativa")
  const anteriores = acoes.filter((a) => a.situacao !== "ativa")

  return (
    <div className="container mx-auto space-y-10 px-4 py-10">
      <div className="space-y-6">
        <Button asChild variant="ghost" size="sm" className="-ml-3">
          <Link to="/ongs">
            <ArrowLeft /> Voltar para as ONGs
          </Link>
        </Button>

        <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
          <div className="space-y-4">
            <SeloCausa causa={ong.causa} />
            <h1 className="text-3xl font-bold md:text-4xl">{ong.nome}</h1>
            <p className="whitespace-pre-line leading-relaxed text-muted-foreground">
              {ong.descricao || "Esta ONG ainda não escreveu uma descrição."}
            </p>
          </div>

          <Card>
            <CardContent className="space-y-3 pt-6 text-sm">
              <h2 className="font-semibold">Contato</h2>
              {ong.email && (
                <p className="flex items-center gap-2 text-muted-foreground">
                  <Mail className="h-4 w-4 text-primary" /> {ong.email}
                </p>
              )}
              {ong.telefone && (
                <p className="flex items-center gap-2 text-muted-foreground">
                  <Phone className="h-4 w-4 text-primary" /> {ong.telefone}
                </p>
              )}
              {ong.site && (
                <p className="flex items-center gap-2 text-muted-foreground">
                  <Globe className="h-4 w-4 text-primary" />
                  <a href={ong.site} target="_blank" rel="noopener noreferrer" className="hover:underline">
                    {ong.site}
                  </a>
                </p>
              )}
              {!ong.email && !ong.telefone && !ong.site && (
                <p className="text-muted-foreground">Contato não informado.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <section className="space-y-4">
        <h2 className="text-2xl font-bold">Unidades</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {ong.unidades.map((unidade) => (
            <Card key={unidade.id}>
              <CardContent className="space-y-1 pt-6 text-sm">
                <h3 className="font-semibold">{unidade.nome}</h3>
                <p className="flex items-start gap-2 text-muted-foreground">
                  <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  <span>
                    {unidade.endereco && (
                      <>
                        {unidade.endereco}
                        <br />
                      </>
                    )}
                    {unidade.cidade}/{unidade.uf}
                    {unidade.cep && ` — CEP ${unidade.cep}`}
                  </span>
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-bold">Ações abertas</h2>
        {abertas.length === 0 ? (
          <EstadoVazio
            icone={CalendarDays}
            titulo="Nenhuma ação aberta no momento"
            descricao="Volte em breve para conferir novas oportunidades."
          />
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {abertas.map((acao) => (
              <CartaoAcao key={acao.id} acao={acao} />
            ))}
          </div>
        )}
      </section>

      {anteriores.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-2xl font-bold">Ações anteriores</h2>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {anteriores.map((acao) => (
              <CartaoAcao key={acao.id} acao={acao} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

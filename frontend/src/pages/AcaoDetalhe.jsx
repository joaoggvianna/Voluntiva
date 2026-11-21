import { useState } from "react"
import { Link, useLocation, useParams } from "react-router-dom"
import {
  ArrowLeft,
  CalendarDays,
  Check,
  Clock,
  Mail,
  MapPin,
  Minus,
  Phone,
  SearchX,
  Users,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Carregando, ErroCarga } from "@/components/Carregando"
import { ConfirmarDialogo } from "@/components/ConfirmarDialogo"
import { EstadoVazio } from "@/components/EstadoVazio"
import { SeloCausa } from "@/components/SeloCausa"
import { useApp } from "@/contexto/AppContexto"
import { localResumo, paraAcao, paraOng } from "@/lib/adaptadores"
import { api } from "@/lib/api"
import { calcularCompatibilidade } from "@/lib/compatibilidade"
import { useCarregar } from "@/lib/useCarregar"
import { cn, diaDaSemana, formatarData, turnoDoHorario } from "@/lib/utils"

function ItemCompatibilidade({ ok, children }) {
  return (
    <li className="flex items-center gap-2 text-sm">
      <span
        className={cn(
          "flex h-5 w-5 shrink-0 items-center justify-center rounded-full",
          ok ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
        )}
      >
        {ok ? <Check className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
      </span>
      <span className={ok ? "" : "text-muted-foreground"}>{children}</span>
    </li>
  )
}

export function AcaoDetalhe() {
  const { id } = useParams()
  const local = useLocation()
  const { usuario, executar, versao } = useApp()
  const [confirmando, setConfirmando] = useState(false)
  const ehVoluntario = usuario?.tipo === "voluntario"

  const { dados, carregando, erro, recarregar } = useCarregar(async () => {
    const acaoApi = await api.obterAcao(id)
    const [ong, inscricoes] = await Promise.all([
      api.obterOng(acaoApi.ong_id).then(paraOng).catch(() => null),
      ehVoluntario ? api.minhasInscricoes() : Promise.resolve([]),
    ])
    return {
      acao: paraAcao(acaoApi),
      ong,
      inscricao: inscricoes.find((i) => i.acao_id === acaoApi.acao_id) ?? null,
    }
  }, [id, ehVoluntario, versao])

  // 404 (não existe ou é rascunho de outra ONG) e 422 (id malformado).
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
          titulo="Ação não encontrada"
          descricao="Ela pode ter sido removida ou o endereço está incorreto."
        >
          <Button asChild>
            <Link to="/acoes">Ver todas as ações</Link>
          </Button>
        </EstadoVazio>
      </div>
    )
  }

  const { acao, ong, inscricao } = dados
  const ehDonaDaAcao =
    usuario?.tipo === "admin" || Boolean(usuario?.ongs?.some((o) => o.id === acao.ongId))
  const compatibilidade = ehVoluntario ? calcularCompatibilidade(acao, usuario) : null
  const ativa = acao.situacao === "ativa"

  return (
    <div className="container mx-auto space-y-6 px-4 py-10">
      <Button asChild variant="ghost" size="sm" className="-ml-3">
        <Link to="/acoes">
          <ArrowLeft /> Voltar para as ações
        </Link>
      </Button>

      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <div className="space-y-8">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <SeloCausa causa={acao.causa} />
              {acao.situacao === "cancelada" && <Badge variant="destructive">Cancelada</Badge>}
              {acao.situacao === "concluida" && <Badge variant="secondary">Encerrada</Badge>}
              {ativa && acao.vagasRestantes === 0 && <Badge variant="outline">Lotada</Badge>}
            </div>
            <h1 className="text-3xl font-bold leading-tight md:text-4xl">{acao.titulo}</h1>
            <p className="text-muted-foreground">
              Organizada por{" "}
              <Link to={`/ongs/${acao.ongId}`} className="font-medium text-primary hover:underline">
                {acao.ong.nome}
              </Link>
            </p>
          </div>

          <section className="space-y-2">
            <h2 className="text-lg font-semibold">Sobre a ação</h2>
            <p className="whitespace-pre-line leading-relaxed text-muted-foreground">
              {acao.descricao || "A ONG ainda não descreveu esta ação."}
            </p>
          </section>

          {acao.habilidades.length > 0 && (
            <section className="space-y-2">
              <h2 className="text-lg font-semibold">Habilidades desejadas</h2>
              <div className="flex flex-wrap gap-2">
                {acao.habilidades.map((habilidade) => (
                  <Badge key={habilidade} variant="outline">
                    {habilidade}
                  </Badge>
                ))}
              </div>
            </section>
          )}

          <section className="space-y-3">
            <h2 className="text-lg font-semibold">Local</h2>
            <Card>
              <CardContent className="space-y-3 pt-6 text-sm">
                <p className="flex items-start gap-2">
                  <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  <span>
                    {acao.unidade && (
                      <>
                        <span className="font-medium">{acao.unidade.nome}</span>
                        <br />
                      </>
                    )}
                    <span className="text-muted-foreground">
                      {[acao.localTexto, localResumo(acao)]
                        .filter((parte, i, lista) => parte && lista.indexOf(parte) === i)
                        .join(" — ")}
                    </span>
                  </span>
                </p>
                {ong?.email && (
                  <p className="flex items-center gap-2 text-muted-foreground">
                    <Mail className="h-4 w-4 shrink-0 text-primary" /> {ong.email}
                  </p>
                )}
                {ong?.telefone && (
                  <p className="flex items-center gap-2 text-muted-foreground">
                    <Phone className="h-4 w-4 shrink-0 text-primary" /> {ong.telefone}
                  </p>
                )}
              </CardContent>
            </Card>
          </section>
        </div>

        <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Detalhes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="space-y-3 text-sm">
                <li className="flex items-center gap-2">
                  <CalendarDays className="h-4 w-4 text-primary" />
                  {formatarData(acao.data)}{" "}
                  <span className="text-muted-foreground">({diaDaSemana(acao.data)})</span>
                </li>
                <li className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-primary" /> {acao.horario}
                  <span className="text-muted-foreground">({turnoDoHorario(acao.horario)})</span>
                </li>
                <li className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-primary" />
                  {ativa
                    ? `${acao.vagasRestantes} de ${acao.vagas} vagas restantes`
                    : `${acao.inscritos} participantes`}
                </li>
              </ul>

              {ehVoluntario && ativa && !inscricao && acao.vagasRestantes > 0 && (
                <Button
                  className="w-full"
                  onClick={() => executar(() => api.inscrever(acao.id), "Inscrição confirmada!")}
                >
                  Quero participar
                </Button>
              )}

              {ehVoluntario && ativa && !inscricao && acao.vagasRestantes === 0 && (
                <div className="space-y-2">
                  <Button
                    className="w-full"
                    variant="outline"
                    onClick={() =>
                      executar(
                        () => api.inscrever(acao.id, true),
                        "Você entrou na lista de espera. Avisaremos se abrir uma vaga."
                      )
                    }
                  >
                    Entrar na lista de espera
                  </Button>
                  <p className="text-center text-xs text-muted-foreground">
                    Vagas esgotadas
                    {acao.emListaEspera > 0 && ` · ${acao.emListaEspera} na fila`}. Se alguém
                    desistir, a vaga vai para o primeiro da fila.
                  </p>
                </div>
              )}

              {ehVoluntario && inscricao && (
                <div className="space-y-3">
                  {inscricao.status === "lista_espera" ? (
                    <div className="rounded-md border border-dashed p-3 text-sm">
                      <p className="font-medium">Você está na lista de espera</p>
                      <p className="text-muted-foreground">
                        Avisaremos se abrir uma vaga para você.
                      </p>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 rounded-md bg-accent p-3 text-sm font-medium text-accent-foreground">
                      <Check className="h-4 w-4" /> Você está inscrito nesta ação
                    </div>
                  )}
                  {ativa && (
                    <Button variant="outline" className="w-full" onClick={() => setConfirmando(true)}>
                      {inscricao.status === "lista_espera" ? "Sair da lista de espera" : "Cancelar participação"}
                    </Button>
                  )}
                </div>
              )}

              {ehVoluntario && !ativa && !inscricao && (
                <p className="text-sm text-muted-foreground">
                  Esta ação não aceita mais inscrições.
                </p>
              )}

              {!usuario && ativa && (
                <div className="space-y-2">
                  <Button asChild className="w-full">
                    <Link to="/entrar" state={{ de: local.pathname }}>
                      Entrar para se inscrever
                    </Link>
                  </Button>
                  <p className="text-center text-xs text-muted-foreground">
                    Ainda não tem conta?{" "}
                    <Link to="/cadastro" className="text-primary hover:underline">
                      Cadastre-se
                    </Link>
                  </p>
                </div>
              )}

              {ehDonaDaAcao && (
                <Button asChild variant="outline" className="w-full">
                  <Link to="/painel?aba=acoes">Gerenciar no painel</Link>
                </Button>
              )}

              {acao.situacao === "rascunho" && ehDonaDaAcao && (
                <p className="text-sm text-muted-foreground">
                  Rascunho: só a sua ONG vê esta ação até ela ser publicada.
                </p>
              )}

              {usuario?.tipo === "ong" && !ehDonaDaAcao && (
                <p className="text-sm text-muted-foreground">
                  Contas de ONG não se inscrevem em ações.
                </p>
              )}
            </CardContent>
          </Card>

          {compatibilidade && ativa && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Combina com você?</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <ItemCompatibilidade ok={compatibilidade.diaOk}>
                    {compatibilidade.diaOk
                      ? `Você está disponível em ${diaDaSemana(acao.data).toLowerCase()}`
                      : `Você não marcou ${diaDaSemana(acao.data).toLowerCase()} como disponível`}
                  </ItemCompatibilidade>
                  <ItemCompatibilidade ok={compatibilidade.turnoOk}>
                    {compatibilidade.turnoOk
                      ? `Você está disponível no turno da ${turnoDoHorario(acao.horario).toLowerCase()}`
                      : `Você não marcou o turno da ${turnoDoHorario(acao.horario).toLowerCase()}`}
                  </ItemCompatibilidade>
                  <ItemCompatibilidade ok={compatibilidade.habilidadeOk}>
                    {acao.habilidades.length === 0
                      ? "Nenhuma habilidade específica exigida"
                      : compatibilidade.habilidadeOk
                        ? `Habilidades em comum: ${compatibilidade.habilidadesEmComum.join(", ")}`
                        : "Nenhuma habilidade em comum"}
                  </ItemCompatibilidade>
                </ul>
                <Button asChild variant="link" className="mt-2 h-auto p-0">
                  <Link to="/painel?aba=perfil">Editar meu perfil</Link>
                </Button>
              </CardContent>
            </Card>
          )}
        </aside>
      </div>

      <ConfirmarDialogo
        aberto={confirmando}
        aoFechar={() => setConfirmando(false)}
        titulo="Cancelar participação?"
        descricao={`Você deixará de participar de "${acao.titulo}" e a vaga ficará disponível para outros voluntários.`}
        rotuloConfirmar="Cancelar participação"
        destrutivo
        aoConfirmar={() => executar(() => api.cancelarInscricao(acao.id), "Participação cancelada.")}
      />
    </div>
  )
}

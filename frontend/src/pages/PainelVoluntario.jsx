import { useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { CalendarCheck, CalendarDays, CheckCircle2, ClipboardList, History, MapPin } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Carregando, ErroCarga } from "@/components/Carregando"
import { ConfirmarDialogo } from "@/components/ConfirmarDialogo"
import { EstadoVazio } from "@/components/EstadoVazio"
import { ListaNotificacoes } from "@/components/ListaNotificacoes"
import { SeletorChips } from "@/components/SeletorChips"
import { SeloCausa } from "@/components/SeloCausa"
import { useApp } from "@/contexto/AppContexto"
import {
  disponibilidadeParaJanelas,
  localResumo,
  paraHistorico,
  paraMinhaInscricao,
  somenteDigitos,
} from "@/lib/adaptadores"
import { api } from "@/lib/api"
import { DIAS_SEMANA, TURNOS } from "@/lib/dominio"
import { useCarregar } from "@/lib/useCarregar"
import { formatarData, formatarTelefone } from "@/lib/utils"

function BlocoNumero({ icone: Icone, valor, rotulo }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 pt-6">
        <div className="rounded-full bg-primary/10 p-3">
          <Icone className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-2xl font-bold leading-none">{valor}</p>
          <p className="mt-1 text-sm text-muted-foreground">{rotulo}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function AbaInscricoes({ inscricoes }) {
  const { executar } = useApp()
  const [cancelando, setCancelando] = useState(null)
  const vigentes = inscricoes.filter((i) => i.acao.situacao !== "concluida")

  if (vigentes.length === 0) {
    return (
      <EstadoVazio
        icone={ClipboardList}
        titulo="Você ainda não tem inscrições"
        descricao="Encontre uma ação que combine com você e garanta a sua vaga."
      >
        <Button asChild>
          <Link to="/acoes">Explorar ações</Link>
        </Button>
      </EstadoVazio>
    )
  }

  return (
    <>
      <ul className="space-y-3">
        {vigentes.map(({ id, acao }) => (
          <li key={id}>
            <Card>
              <CardContent className="flex flex-wrap items-center justify-between gap-4 pt-6">
                <div className="min-w-0 space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <SeloCausa causa={acao.causa} />
                    {acao.situacao === "cancelada" && (
                      <Badge variant="destructive">Cancelada pela ONG</Badge>
                    )}
                  </div>
                  <Link to={`/acoes/${acao.id}`} className="block font-semibold hover:text-primary">
                    {acao.titulo}
                  </Link>
                  <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1.5">
                      <CalendarDays className="h-4 w-4" /> {formatarData(acao.data)} · {acao.horario}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <MapPin className="h-4 w-4" /> {localResumo(acao)}
                    </span>
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button asChild variant="outline" size="sm">
                    <Link to={`/acoes/${acao.id}`}>Detalhes</Link>
                  </Button>
                  {acao.situacao === "ativa" && (
                    <Button variant="outline" size="sm" onClick={() => setCancelando(acao)}>
                      Cancelar participação
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </li>
        ))}
      </ul>
      <ConfirmarDialogo
        aberto={Boolean(cancelando)}
        aoFechar={() => setCancelando(null)}
        titulo="Cancelar participação?"
        descricao={
          cancelando
            ? `Você deixará de participar de "${cancelando.titulo}" e a vaga ficará disponível para outros voluntários.`
            : ""
        }
        rotuloConfirmar="Cancelar participação"
        destrutivo
        aoConfirmar={() =>
          executar(() => api.cancelarInscricao(cancelando.id), "Participação cancelada.")
        }
      />
    </>
  )
}

function AbaHistorico({ resumo }) {
  if (resumo.total === 0) {
    return (
      <EstadoVazio
        icone={History}
        titulo="Nenhuma participação registrada"
        descricao="Depois que as ações em que você se inscreveu forem realizadas, o histórico aparecerá aqui."
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 text-sm">
        <Badge variant="secondary">{resumo.total} ações realizadas</Badge>
        <Badge>{resumo.presentes} presenças</Badge>
        {resumo.ausentes > 0 && <Badge variant="outline">{resumo.ausentes} sem presença</Badge>}
        <Badge variant="outline">
          {resumo.totalHoras.toLocaleString("pt-BR", { maximumFractionDigits: 2 })} horas de voluntariado
        </Badge>
      </div>
      <ul className="divide-y rounded-lg border">
        {resumo.itens.map(({ id, acao, presenca, horas }) => (
          <li key={id} className="flex flex-wrap items-center justify-between gap-3 p-4">
            <div className="min-w-0">
              <Link to={`/acoes/${acao.id}`} className="font-medium hover:text-primary">
                {acao.titulo}
              </Link>
              <p className="text-sm text-muted-foreground">
                {acao.ong.nome} · {formatarData(acao.data)}
              </p>
            </div>
            {presenca === "presente" && (
              <Badge className="gap-1">
                <CheckCircle2 className="h-3 w-3" /> Presente
                {horas != null && ` · ${horas.toLocaleString("pt-BR")} h`}
              </Badge>
            )}
            {presenca === "ausente" && <Badge variant="outline">Sem presença registrada</Badge>}
          </li>
        ))}
      </ul>
    </div>
  )
}

function AbaPerfil() {
  const { usuario, executar, catalogoHabilidades, atualizarUsuario } = useApp()
  const [nome, setNome] = useState(usuario.nome)
  const [telefone, setTelefone] = useState(usuario.telefone)
  const [habilidades, setHabilidades] = useState(usuario.habilidades)
  const [dias, setDias] = useState(usuario.disponibilidade.dias)
  const [turnos, setTurnos] = useState(usuario.disponibilidade.turnos)

  const [salvando, setSalvando] = useState(false)
  const idPorNome = Object.fromEntries(catalogoHabilidades.map((h) => [h.nome, h.id]))

  async function salvar(evento) {
    evento.preventDefault()
    setSalvando(true)
    const resposta = await executar(
      () =>
        api.atualizarPerfil({
          nome: nome.trim(),
          telefone: somenteDigitos(telefone) || null,
          habilidades: habilidades
            .filter((h) => idPorNome[h])
            .map((h) => ({ habilidade_id: idPorNome[h] })),
          disponibilidade: disponibilidadeParaJanelas({ dias, turnos }),
        }),
      "Perfil atualizado."
    )
    if (resposta.ok) await atualizarUsuario().catch(() => {})
    setSalvando(false)
  }

  return (
    <form onSubmit={salvar} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Dados pessoais</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="perfil-nome">Nome</Label>
            <Input id="perfil-nome" value={nome} onChange={(e) => setNome(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="perfil-email">E-mail</Label>
            <Input id="perfil-email" value={usuario.email} disabled />
          </div>
          <div className="space-y-2">
            <Label htmlFor="perfil-telefone">Telefone</Label>
            <Input
              id="perfil-telefone"
              value={telefone}
              onChange={(e) => setTelefone(formatarTelefone(e.target.value))}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Habilidades</CardTitle>
          <CardDescription>Selecione tudo o que você pode oferecer como voluntário.</CardDescription>
        </CardHeader>
        <CardContent>
          <SeletorChips
            rotulo="Habilidades"
            opcoes={catalogoHabilidades.map((h) => h.nome)}
            valor={habilidades}
            aoAlterar={setHabilidades}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Disponibilidade</CardTitle>
          <CardDescription>
            Usamos os dias e turnos para indicar as ações que combinam com você.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Dias da semana</Label>
            <SeletorChips rotulo="Dias da semana" opcoes={DIAS_SEMANA} valor={dias} aoAlterar={setDias} />
          </div>
          <div className="space-y-2">
            <Label>Turnos</Label>
            <SeletorChips rotulo="Turnos" opcoes={TURNOS} valor={turnos} aoAlterar={setTurnos} />
          </div>
        </CardContent>
      </Card>

      <Button type="submit" disabled={salvando}>
        {salvando ? "Salvando..." : "Salvar perfil"}
      </Button>
    </form>
  )
}

export function PainelVoluntario() {
  const { usuario, notificacoesNaoLidas, versao } = useApp()
  const [params, setParams] = useSearchParams()
  const aba = params.get("aba") ?? "inscricoes"
  const { dados, carregando, erro, recarregar } = useCarregar(async () => {
    const [inscricoes, historico] = await Promise.all([api.minhasInscricoes(), api.historico()])
    return { inscricoes: inscricoes.map(paraMinhaInscricao), resumo: paraHistorico(historico) }
  }, [versao])
  const inscricoes = dados?.inscricoes ?? []
  const resumo = dados?.resumo ?? { itens: [], total: 0, presentes: 0, ausentes: 0, totalHoras: 0 }
  const proximas = inscricoes.filter((i) => i.acao.situacao === "ativa")

  return (
    <div className="container mx-auto space-y-8 px-4 py-10">
      <div>
        <h1 className="text-3xl font-bold">Olá, {usuario.nome.split(" ")[0]}!</h1>
        <p className="mt-2 text-muted-foreground">
          Acompanhe suas inscrições, seu histórico e mantenha seu perfil atualizado.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <BlocoNumero icone={ClipboardList} valor={proximas.length} rotulo="Próximas participações" />
        <BlocoNumero icone={CalendarCheck} valor={resumo.presentes} rotulo="Presenças registradas" />
        <BlocoNumero icone={History} valor={resumo.total} rotulo="Ações realizadas" />
      </div>

      <Tabs value={aba} onValueChange={(valor) => setParams({ aba: valor }, { replace: true })}>
        <TabsList className="h-auto flex-wrap">
          <TabsTrigger value="inscricoes">Minhas inscrições</TabsTrigger>
          <TabsTrigger value="historico">Histórico</TabsTrigger>
          <TabsTrigger value="perfil">Perfil</TabsTrigger>
          <TabsTrigger value="notificacoes" className="gap-2">
            Notificações
            {notificacoesNaoLidas > 0 && (
              <span className="rounded-full bg-destructive px-1.5 text-[10px] font-bold text-destructive-foreground">
                {notificacoesNaoLidas}
              </span>
            )}
          </TabsTrigger>
        </TabsList>
        <TabsContent value="inscricoes" className="mt-6">
          {erro && !dados ? (
            <ErroCarga erro={erro} aoTentarDeNovo={recarregar} />
          ) : carregando && !dados ? (
            <Carregando />
          ) : (
            <AbaInscricoes inscricoes={inscricoes} />
          )}
        </TabsContent>
        <TabsContent value="historico" className="mt-6">
          {carregando && !dados ? <Carregando /> : <AbaHistorico resumo={resumo} />}
        </TabsContent>
        <TabsContent value="perfil" className="mt-6">
          <AbaPerfil key={usuario.id} />
        </TabsContent>
        <TabsContent value="notificacoes" className="mt-6">
          <ListaNotificacoes />
        </TabsContent>
      </Tabs>
    </div>
  )
}

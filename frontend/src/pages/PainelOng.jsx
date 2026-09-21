import { useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { Building2, CalendarDays, MapPin, Pencil, Plus, Trash2, Users } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ConfirmarDialogo } from "@/components/ConfirmarDialogo"
import { EstadoVazio } from "@/components/EstadoVazio"
import { FormularioAcao } from "@/components/FormularioAcao"
import { FormularioUnidade } from "@/components/FormularioUnidade"
import { ListaNotificacoes } from "@/components/ListaNotificacoes"
import { ListaPresenca } from "@/components/ListaPresenca"
import { useApp } from "@/contexto/AppContexto"
import {
  cancelarAcao,
  listarAcoes,
  listarUnidades,
  obterOng,
  removerUnidade,
} from "@/lib/servico"
import { formatarData, hojeIso } from "@/lib/utils"

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

function SituacaoBadge({ situacao }) {
  if (situacao === "ativa") return <Badge>Ativa</Badge>
  if (situacao === "cancelada") return <Badge variant="destructive">Cancelada</Badge>
  return <Badge variant="secondary">Encerrada</Badge>
}

function AbaAcoes({ ong, acoes, unidades }) {
  const { executar } = useApp()
  const [formulario, setFormulario] = useState(null)
  const [cancelando, setCancelando] = useState(null)

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          {acoes.length === 1 ? "1 ação cadastrada" : `${acoes.length} ações cadastradas`}
        </p>
        <Button disabled={unidades.length === 0} onClick={() => setFormulario({ acao: null })}>
          <Plus /> Nova ação
        </Button>
      </div>

      {unidades.length === 0 && (
        <p className="rounded-lg border bg-accent/40 p-4 text-sm">
          Cadastre pelo menos uma unidade na aba <strong>Unidades</strong> antes de criar ações.
        </p>
      )}

      {acoes.length === 0 ? (
        <EstadoVazio
          icone={CalendarDays}
          titulo="Nenhuma ação cadastrada"
          descricao="Crie a primeira ação social da sua ONG para começar a receber voluntários."
        />
      ) : (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ação</TableHead>
                <TableHead>Data</TableHead>
                <TableHead>Unidade</TableHead>
                <TableHead>Vagas</TableHead>
                <TableHead>Situação</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {acoes.map((acao) => (
                <TableRow key={acao.id}>
                  <TableCell className="max-w-64 font-medium">
                    <Link to={`/acoes/${acao.id}`} className="hover:text-primary">
                      {acao.titulo}
                    </Link>
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    {formatarData(acao.data)}
                    <span className="block text-xs text-muted-foreground">{acao.horario}</span>
                  </TableCell>
                  <TableCell className="whitespace-nowrap">{acao.unidade?.nome}</TableCell>
                  <TableCell className="whitespace-nowrap">
                    {acao.inscritos}/{acao.vagas}
                  </TableCell>
                  <TableCell>
                    <SituacaoBadge situacao={acao.situacao} />
                  </TableCell>
                  <TableCell className="text-right">
                    {acao.situacao === "ativa" && (
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={`Editar ${acao.titulo}`}
                          onClick={() => setFormulario({ acao })}
                        >
                          <Pencil />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={`Cancelar ${acao.titulo}`}
                          onClick={() => setCancelando(acao)}
                        >
                          <Trash2 className="text-destructive" />
                        </Button>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {formulario && (
        <FormularioAcao
          key={formulario.acao?.id ?? "nova"}
          aberto
          aoFechar={() => setFormulario(null)}
          acao={formulario.acao}
          ong={ong}
          unidades={unidades}
        />
      )}

      <ConfirmarDialogo
        aberto={Boolean(cancelando)}
        aoFechar={() => setCancelando(null)}
        titulo="Cancelar esta ação?"
        descricao={
          cancelando
            ? `"${cancelando.titulo}" será cancelada e os ${cancelando.inscritos} voluntários inscritos serão notificados.`
            : ""
        }
        rotuloConfirmar="Cancelar ação"
        destrutivo
        aoConfirmar={() =>
          executar(() => cancelarAcao(cancelando.id, ong.id), "Ação cancelada e inscritos notificados.")
        }
      />
    </div>
  )
}

function AbaUnidades({ ong, unidades }) {
  const { executar } = useApp()
  const [formulario, setFormulario] = useState(null)
  const [removendo, setRemovendo] = useState(null)

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          {unidades.length === 1 ? "1 unidade cadastrada" : `${unidades.length} unidades cadastradas`}
        </p>
        <Button onClick={() => setFormulario({ unidade: null })}>
          <Plus /> Nova unidade
        </Button>
      </div>

      {unidades.length === 0 ? (
        <EstadoVazio
          icone={Building2}
          titulo="Nenhuma unidade cadastrada"
          descricao="As ações sociais são realizadas em unidades da ONG."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {unidades.map((unidade) => (
            <Card key={unidade.id}>
              <CardContent className="flex items-start justify-between gap-3 pt-6">
                <div className="min-w-0 space-y-1 text-sm">
                  <h3 className="font-semibold">{unidade.nome}</h3>
                  <p className="flex items-start gap-2 text-muted-foreground">
                    <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <span>
                      {unidade.endereco}
                      <br />
                      {unidade.cidade}/{unidade.uf}
                      {unidade.cep && ` — CEP ${unidade.cep}`}
                    </span>
                  </p>
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Editar ${unidade.nome}`}
                    onClick={() => setFormulario({ unidade })}
                  >
                    <Pencil />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Remover ${unidade.nome}`}
                    onClick={() => setRemovendo(unidade)}
                  >
                    <Trash2 className="text-destructive" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {formulario && (
        <FormularioUnidade
          key={formulario.unidade?.id ?? "nova"}
          aberto
          aoFechar={() => setFormulario(null)}
          unidade={formulario.unidade}
          ongId={ong.id}
        />
      )}

      <ConfirmarDialogo
        aberto={Boolean(removendo)}
        aoFechar={() => setRemovendo(null)}
        titulo="Remover unidade?"
        descricao={
          removendo
            ? `A unidade "${removendo.nome}" será removida. Unidades com ações vinculadas não podem ser removidas.`
            : ""
        }
        rotuloConfirmar="Remover"
        destrutivo
        aoConfirmar={() => executar(() => removerUnidade(removendo.id, ong.id), "Unidade removida.")}
      />
    </div>
  )
}

function AbaPresenca({ ong, acoes }) {
  const [selecionada, setSelecionada] = useState(null)
  const candidatas = acoes.filter((a) => a.situacao !== "cancelada")

  if (candidatas.length === 0) {
    return (
      <EstadoVazio
        icone={Users}
        titulo="Nenhuma ação para controlar"
        descricao="Crie uma ação para acompanhar inscritos e registrar presença."
      />
    )
  }

  const padrao =
    candidatas.filter((a) => a.data <= hojeIso()).sort((a, b) => b.data.localeCompare(a.data))[0] ??
    candidatas[0]
  const acao = candidatas.find((a) => a.id === selecionada) ?? padrao

  return (
    <div className="space-y-4">
      <div className="max-w-md space-y-2">
        <Label>Ação</Label>
        <Select value={String(acao.id)} onValueChange={(valor) => setSelecionada(Number(valor))}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {candidatas.map((item) => (
              <SelectItem key={item.id} value={String(item.id)}>
                {item.titulo} — {formatarData(item.data)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <ListaPresenca key={acao.id} acao={acao} ongId={ong.id} />
    </div>
  )
}

export function PainelOng() {
  const { usuario, notificacoesNaoLidas } = useApp()
  const [params, setParams] = useSearchParams()
  const aba = params.get("aba") ?? "acoes"
  const ong = obterOng(usuario.ongId)
  const acoes = listarAcoes({ ongId: usuario.ongId, incluirEncerradas: true })
  const unidades = listarUnidades(usuario.ongId)
  const abertas = acoes.filter((a) => a.situacao === "ativa")
  const inscritosTotal = abertas.reduce((soma, a) => soma + a.inscritos, 0)

  return (
    <div className="container mx-auto space-y-8 px-4 py-10">
      <div>
        <h1 className="text-3xl font-bold">{ong.nome}</h1>
        <p className="mt-2 text-muted-foreground">
          Gerencie unidades, ações sociais, inscritos e presença.{" "}
          <Link to={`/ongs/${ong.id}`} className="text-primary hover:underline">
            Ver página pública
          </Link>
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <BlocoNumero icone={CalendarDays} valor={abertas.length} rotulo="Ações ativas" />
        <BlocoNumero icone={Users} valor={inscritosTotal} rotulo="Inscritos nas ações ativas" />
        <BlocoNumero icone={Building2} valor={unidades.length} rotulo="Unidades" />
      </div>

      <Tabs value={aba} onValueChange={(valor) => setParams({ aba: valor }, { replace: true })}>
        <TabsList className="h-auto flex-wrap">
          <TabsTrigger value="acoes">Ações</TabsTrigger>
          <TabsTrigger value="unidades">Unidades</TabsTrigger>
          <TabsTrigger value="presenca">Presença</TabsTrigger>
          <TabsTrigger value="notificacoes" className="gap-2">
            Notificações
            {notificacoesNaoLidas > 0 && (
              <span className="rounded-full bg-destructive px-1.5 text-[10px] font-bold text-destructive-foreground">
                {notificacoesNaoLidas}
              </span>
            )}
          </TabsTrigger>
        </TabsList>
        <TabsContent value="acoes" className="mt-6">
          <AbaAcoes ong={ong} acoes={acoes} unidades={unidades} />
        </TabsContent>
        <TabsContent value="unidades" className="mt-6">
          <AbaUnidades ong={ong} unidades={unidades} />
        </TabsContent>
        <TabsContent value="presenca" className="mt-6">
          <AbaPresenca ong={ong} acoes={acoes} />
        </TabsContent>
        <TabsContent value="notificacoes" className="mt-6">
          <ListaNotificacoes />
        </TabsContent>
      </Tabs>
    </div>
  )
}

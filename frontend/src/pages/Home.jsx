import { Link } from "react-router-dom"
import {
  ArrowRight,
  BellRing,
  Building2,
  CalendarCheck,
  ClipboardList,
  Search,
  UserPlus,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { CartaoAcao } from "@/components/CartaoAcao"
import { useApp } from "@/contexto/AppContexto"
import { CAUSAS } from "@/data/ongs"
import { causaIcones } from "@/lib/causas"
import { estatisticas, listarAcoes } from "@/lib/servico"

const passos = [
  {
    icone: UserPlus,
    titulo: "1. Crie seu perfil",
    descricao:
      "Cadastre suas habilidades e a sua disponibilidade de dias e turnos.",
  },
  {
    icone: Search,
    titulo: "2. Encontre uma ação",
    descricao:
      "Consulte as oportunidades e veja quais combinam com o seu perfil.",
  },
  {
    icone: ClipboardList,
    titulo: "3. Inscreva-se",
    descricao:
      "Garanta sua vaga e cancele a participação sempre que precisar.",
  },
  {
    icone: CalendarCheck,
    titulo: "4. Acompanhe",
    descricao:
      "Receba avisos de mudanças e consulte o histórico de presenças.",
  },
]

export function Home() {
  const { usuario } = useApp()
  const numeros = estatisticas()
  const destaques = listarAcoes({ somenteComVagas: true }).slice(0, 6)

  const totais = [
    { valor: numeros.ongs, rotulo: "ONGs cadastradas" },
    { valor: numeros.acoesAbertas, rotulo: "Ações abertas" },
    { valor: numeros.voluntarios, rotulo: "Voluntários ativos" },
    { valor: numeros.participacoes, rotulo: "Inscrições confirmadas" },
  ]

  return (
    <div>
      <section className="bg-gradient-to-b from-accent to-background">
        <div className="container mx-auto space-y-6 px-4 py-20 text-center md:py-28">
          <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight md:text-6xl">
            Encontre a ação social <span className="text-primary">certa para você.</span>
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-muted-foreground md:text-xl">
            A Voluntiva conecta voluntários e ONGs: cadastre suas habilidades e
            disponibilidade, descubra oportunidades compatíveis e acompanhe toda
            a sua participação.
          </p>
          <div className="flex flex-col justify-center gap-3 pt-4 sm:flex-row">
            <Button asChild size="lg">
              <Link to="/acoes">
                Ver ações sociais <ArrowRight className="ml-1" />
              </Link>
            </Button>
            {usuario ? (
              <Button asChild size="lg" variant="outline">
                <Link to="/painel">Ir para o meu painel</Link>
              </Button>
            ) : (
              <Button asChild size="lg" variant="outline">
                <Link to="/cadastro">Criar minha conta</Link>
              </Button>
            )}
          </div>
        </div>
      </section>

      <section className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {totais.map((total) => (
            <Card key={total.rotulo}>
              <CardContent className="pt-6 text-center">
                <p className="text-4xl font-bold text-primary">{total.valor}</p>
                <p className="mt-1 text-sm text-muted-foreground">{total.rotulo}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="container mx-auto px-4 py-12">
        <h2 className="text-center text-2xl font-bold md:text-3xl">Explore por causa</h2>
        <p className="mb-8 mt-2 text-center text-muted-foreground">
          Escolha a área em que você quer atuar
        </p>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {CAUSAS.map((causa) => {
            const Icone = causaIcones[causa]
            return (
              <Link key={causa} to={`/acoes?causa=${encodeURIComponent(causa)}`}>
                <Card className="h-full transition-colors hover:border-primary hover:bg-accent/50">
                  <CardContent className="flex flex-col items-center gap-3 pt-6 text-center">
                    <div className="rounded-full bg-primary/10 p-3">
                      <Icone className="h-6 w-6 text-primary" />
                    </div>
                    <span className="text-sm font-medium">{causa}</span>
                  </CardContent>
                </Card>
              </Link>
            )
          })}
        </div>
      </section>

      <section className="container mx-auto px-4 py-12">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold md:text-3xl">Próximas ações</h2>
            <p className="mt-2 text-muted-foreground">
              Oportunidades com vagas abertas nas próximas semanas
            </p>
          </div>
          <Button asChild variant="outline" className="hidden sm:inline-flex">
            <Link to="/acoes">Ver todas</Link>
          </Button>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {destaques.map((acao) => (
            <CartaoAcao key={acao.id} acao={acao} />
          ))}
        </div>
        <div className="mt-6 text-center sm:hidden">
          <Button asChild variant="outline">
            <Link to="/acoes">Ver todas as ações</Link>
          </Button>
        </div>
      </section>

      <section className="bg-muted/40 py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-center text-2xl font-bold md:text-3xl">Como funciona</h2>
          <p className="mb-10 mt-2 text-center text-muted-foreground">
            Da inscrição ao histórico de participação
          </p>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {passos.map((passo) => (
              <Card key={passo.titulo}>
                <CardContent className="space-y-3 pt-6 text-center">
                  <div className="mx-auto w-fit rounded-full bg-primary/10 p-4">
                    <passo.icone className="h-8 w-8 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold">{passo.titulo}</h3>
                  <p className="text-sm text-muted-foreground">{passo.descricao}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="container mx-auto px-4 py-16">
        <div className="grid gap-6 rounded-2xl bg-primary p-8 text-primary-foreground md:grid-cols-[1fr_auto] md:items-center md:p-12">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium opacity-90">
              <Building2 className="h-4 w-4" /> Para ONGs
            </div>
            <h2 className="text-2xl font-bold md:text-3xl">
              Gerencie voluntários e ações em um só lugar
            </h2>
            <p className="max-w-2xl opacity-90">
              Cadastre unidades e ações, acompanhe as inscrições, registre a
              presença e avise os voluntários automaticamente sobre qualquer
              mudança.
            </p>
            <p className="flex items-center gap-2 text-sm opacity-90">
              <BellRing className="h-4 w-4" /> Notificações de criação,
              atualização e cancelamento
            </p>
          </div>
          <Button asChild size="lg" variant="secondary">
            <Link to="/cadastro?tipo=ong">Cadastrar minha ONG</Link>
          </Button>
        </div>
      </section>
    </div>
  )
}

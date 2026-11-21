import { useState } from "react"
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom"
import { Building2, HeartHandshake, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"
import { useApp } from "@/contexto/AppContexto"

// Contas criadas pelo seed de desenvolvimento (db/seed/seed_dev.sql).
// O cartão só aparece em `npm run dev`, nunca no build de produção.
const SENHA_DE_TESTE = "voluntiva123"
const CONTAS_DE_TESTE = import.meta.env.DEV

export function Entrar() {
  const { usuario, entrar } = useApp()
  const navegar = useNavigate()
  const local = useLocation()
  const [email, setEmail] = useState("")
  const [senha, setSenha] = useState("")
  const [erros, setErros] = useState({})
  const [enviando, setEnviando] = useState(false)

  if (usuario) return <Navigate to={local.state?.de ?? "/painel"} replace />

  async function enviar(evento) {
    evento.preventDefault()
    const novosErros = {}
    if (!email.trim()) novosErros.email = "Informe o seu e-mail."
    if (!senha) novosErros.senha = "Informe a sua senha."
    setErros(novosErros)
    if (Object.keys(novosErros).length > 0) return
    setEnviando(true)
    try {
      await entrar(email.trim(), senha)
      toast.success("Bem-vindo de volta!")
      navegar(local.state?.de ?? "/painel", { replace: true })
    } catch (erro) {
      toast.error(erro.message)
    } finally {
      setEnviando(false)
    }
  }

  function usarConta(emailConta) {
    setEmail(emailConta)
    setSenha(SENHA_DE_TESTE)
    setErros({})
  }

  return (
    <div className="container mx-auto flex max-w-md flex-col gap-6 px-4 py-12">
      <Card>
        <CardHeader className="items-center text-center">
          <HeartHandshake className="h-10 w-10 text-primary" />
          <CardTitle className="text-2xl">Entrar na Voluntiva</CardTitle>
          <CardDescription>Acesse sua conta de voluntário ou de ONG.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={enviar} className="space-y-4" noValidate>
            <div className="space-y-2">
              <Label htmlFor="email">E-mail</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-invalid={Boolean(erros.email)}
              />
              {erros.email && <p className="text-sm text-destructive">{erros.email}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="senha">Senha</Label>
              <Input
                id="senha"
                type="password"
                autoComplete="current-password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                aria-invalid={Boolean(erros.senha)}
              />
              {erros.senha && <p className="text-sm text-destructive">{erros.senha}</p>}
            </div>
            <Button type="submit" className="w-full" disabled={enviando}>
              {enviando ? "Entrando..." : "Entrar"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Ainda não tem conta?{" "}
            <Link to="/cadastro" className="font-medium text-primary hover:underline">
              Cadastre-se
            </Link>
          </p>
        </CardContent>
      </Card>

      {CONTAS_DE_TESTE && (
      <Card className="border-dashed">
        <CardContent className="space-y-3 pt-6">
          <p className="text-sm font-medium">Contas de teste</p>
          <p className="text-xs text-muted-foreground">
            Contas do seed de desenvolvimento (senha {SENHA_DE_TESTE}). Só aparecem em modo dev.
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            <Button variant="outline" size="sm" onClick={() => usarConta("voluntario@voluntiva.dev")}>
              <User /> Voluntário
            </Button>
            <Button variant="outline" size="sm" onClick={() => usarConta("ong@voluntiva.dev")}>
              <Building2 /> ONG
            </Button>
          </div>
        </CardContent>
      </Card>
      )}
    </div>
  )
}

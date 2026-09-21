import { useState } from "react"
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom"
import { Building2, HeartHandshake, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useApp } from "@/contexto/AppContexto"
import { entrar } from "@/lib/servico"

export function Entrar() {
  const { usuario, executar } = useApp()
  const navegar = useNavigate()
  const local = useLocation()
  const [email, setEmail] = useState("")
  const [senha, setSenha] = useState("")
  const [erros, setErros] = useState({})

  if (usuario) return <Navigate to="/painel" replace />

  function enviar(evento) {
    evento.preventDefault()
    const novosErros = {}
    if (!email.trim()) novosErros.email = "Informe o seu e-mail."
    if (!senha) novosErros.senha = "Informe a sua senha."
    setErros(novosErros)
    if (Object.keys(novosErros).length > 0) return
    const resposta = executar(() => entrar(email, senha), "Bem-vindo de volta!")
    if (resposta.ok) navegar(local.state?.de ?? "/painel", { replace: true })
  }

  function usarConta(emailConta) {
    setEmail(emailConta)
    setSenha("123456")
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
            <Button type="submit" className="w-full">
              Entrar
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

      <Card className="border-dashed">
        <CardContent className="space-y-3 pt-6">
          <p className="text-sm font-medium">Contas de teste</p>
          <p className="text-xs text-muted-foreground">
            Preencha o formulário com uma conta de exemplo (senha 123456).
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            <Button variant="outline" size="sm" onClick={() => usarConta("voluntario@teste.com")}>
              <User /> Voluntário
            </Button>
            <Button variant="outline" size="sm" onClick={() => usarConta("ong@teste.com")}>
              <Building2 /> ONG
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

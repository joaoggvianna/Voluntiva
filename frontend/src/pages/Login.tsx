import { useState } from 'react'
import type { FormEvent } from 'react'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/Button'

export function Login() {
  const { entrar } = useAuth()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento: FormEvent) {
    evento.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      await entrar(email, senha)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao entrar')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="mx-auto mt-16 max-w-sm rounded-card border border-edge bg-surface p-6">
      <h1 className="mb-1 text-xl font-bold text-primary">Entrar</h1>
      <p className="mb-5 text-sm text-ink-muted">Acesse sua conta Voluntiva</p>

      <form onSubmit={aoEnviar} className="space-y-4">
        <div>
          <label htmlFor="email" className="mb-1 block text-sm font-medium">E-mail</label>
          <input
            id="email" type="email" required autoComplete="email"
            value={email} onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-edge px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="senha" className="mb-1 block text-sm font-medium">Senha</label>
          <input
            id="senha" type="password" required autoComplete="current-password"
            value={senha} onChange={(e) => setSenha(e.target.value)}
            className="w-full rounded-lg border border-edge px-3 py-2 text-sm"
          />
        </div>

        {erro && (
          <p role="alert" className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">
            {erro}
          </p>
        )}

        <Button type="submit" variante="accent" className="w-full" disabled={enviando}>
          {enviando ? 'Entrando...' : 'Entrar'}
        </Button>
      </form>
    </div>
  )
}

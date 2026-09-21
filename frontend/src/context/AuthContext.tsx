import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api, tokenStore } from '@/lib/api'
import type { Usuario } from '@/types'

interface AuthContextValue {
  usuario: Usuario | null
  carregando: boolean
  entrar: (email: string, senha: string) => Promise<void>
  sair: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [carregando, setCarregando] = useState(true)

  // Revalida o token guardado ao abrir a aplicação: ele pode ter expirado
  // enquanto a aba estava fechada.
  useEffect(() => {
    if (!tokenStore.get()) {
      setCarregando(false)
      return
    }
    api.eu()
      .then(setUsuario)
      .catch(() => tokenStore.clear())
      .finally(() => setCarregando(false))
  }, [])

  const entrar = useCallback(async (email: string, senha: string) => {
    const resposta = await api.login(email, senha)
    tokenStore.set(resposta.access_token)
    setUsuario(resposta.usuario)
  }, [])

  const sair = useCallback(() => {
    tokenStore.clear()
    setUsuario(null)
  }, [])

  return (
    <AuthContext.Provider value={{ usuario, carregando, entrar, sair }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth precisa estar dentro de <AuthProvider>')
  return ctx
}

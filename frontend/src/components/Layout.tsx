import type { ReactNode } from 'react'
import { useAuth } from '@/context/AuthContext'
import { Button } from './ui/Button'

export function Layout({ children }: { children: ReactNode }) {
  const { usuario, sair } = useAuth()

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-edge bg-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <span className="text-lg font-bold text-primary">Voluntiva</span>
          {usuario && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-ink-muted">{usuario.nome}</span>
              <Button variante="ghost" onClick={sair}>Sair</Button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { AcaoComVagas } from '@/types'
import { Button } from '@/components/ui/Button'

export function Acoes() {
  const [acoes, setAcoes] = useState<AcaoComVagas[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    api.listarAcoes({ status: 'publicada' })
      .then(setAcoes)
      .catch((e) => setErro(e instanceof Error ? e.message : 'Erro ao carregar'))
      .finally(() => setCarregando(false))
  }, [])

  async function inscrever(acaoId: string) {
    try {
      await api.inscrever(acaoId)
      setAcoes(await api.listarAcoes({ status: 'publicada' }))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao inscrever')
    }
  }

  if (carregando) return <p className="text-ink-muted">Carregando ações...</p>

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold text-primary">Oportunidades</h1>

      {erro && (
        <p role="alert" className="mb-4 rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">
          {erro}
        </p>
      )}

      {acoes.length === 0 ? (
        <p className="text-ink-muted">Nenhuma ação publicada no momento.</p>
      ) : (
        <ul className="space-y-3">
          {acoes.map((acao) => (
            <li key={acao.acao_id}
                className="rounded-card border border-edge bg-surface p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-semibold">{acao.titulo}</h2>
                  <p className="text-sm text-ink-muted">{acao.ong_nome}</p>
                  <p className="mt-1 text-sm">
                    {new Date(acao.inicio).toLocaleString('pt-BR')}
                    {' · '}
                    <span className={acao.vagas_disponiveis > 0 ? 'text-success' : 'text-danger'}>
                      {acao.vagas_disponiveis > 0
                        ? `${acao.vagas_disponiveis} de ${acao.vagas} vagas`
                        : 'Lotada'}
                    </span>
                  </p>
                </div>
                <Button
                  variante="accent"
                  disabled={acao.vagas_disponiveis <= 0}
                  onClick={() => inscrever(acao.acao_id)}
                >
                  Inscrever-se
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

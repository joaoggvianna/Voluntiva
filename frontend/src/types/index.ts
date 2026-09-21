// Espelha os schemas Pydantic do backend. Se um schema mudar lá,
// ajuste aqui — não há geração automática de tipos.

export type TipoUsuario = 'voluntario' | 'ong' | 'admin'

export type StatusAcao =
  | 'rascunho' | 'publicada' | 'em_andamento' | 'concluida' | 'cancelada'

export type StatusInscricao =
  | 'pendente' | 'confirmada' | 'lista_espera' | 'cancelada'

export interface Usuario {
  id: string
  nome: string
  email: string
  tipo: TipoUsuario
  ativo: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  usuario: Usuario
}

/** Projeção da view vw_acao_vagas. */
export interface AcaoComVagas {
  acao_id: string
  ong_id: string
  ong_nome: string
  unidade_id: string | null
  titulo: string
  inicio: string
  fim: string
  status: StatusAcao
  vagas: number
  vagas_ocupadas: number
  vagas_disponiveis: number
  em_lista_espera: number
}

export interface Inscricao {
  id: string
  acao_id: string
  voluntario_id: string
  status: StatusInscricao
  inscrito_em: string
  cancelado_em: string | null
}

export interface Notificacao {
  id: string
  tipo: string
  titulo: string
  mensagem: string
  lida: boolean
  criada_em: string
}

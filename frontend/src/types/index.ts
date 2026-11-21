// Espelha os schemas Pydantic do backend (backend/app/schemas). Se um
// schema mudar lá, ajuste aqui — não há geração automática de tipos.

export type TipoUsuario = 'voluntario' | 'ong' | 'admin'

export type StatusAcao =
  | 'rascunho' | 'publicada' | 'em_andamento' | 'concluida' | 'cancelada'

export type StatusInscricao =
  | 'pendente' | 'confirmada' | 'lista_espera' | 'cancelada'

export type Causa =
  | 'meio_ambiente' | 'educacao' | 'animais' | 'saude'
  | 'assistencia_social' | 'cultura' | 'esporte' | 'direitos_humanos'

export type TipoNotificacao =
  | 'acao_criada' | 'acao_atualizada' | 'acao_cancelada'
  | 'inscricao_confirmada' | 'inscricao_cancelada' | 'lembrete'

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

export interface HabilidadeDaAcao {
  id: string
  nome: string
  obrigatoria: boolean
}

/** GET /acoes (itens) e GET /acoes/{id}. */
export interface AcaoComVagas {
  acao_id: string
  codigo: number
  ong_id: string
  ong_nome: string
  unidade_id: string | null
  unidade_nome: string | null
  unidade_cidade: string | null
  unidade_uf: string | null
  titulo: string
  descricao: string | null
  local_texto: string | null
  inicio: string
  fim: string
  status: StatusAcao
  causa: Causa | null
  vagas: number
  vagas_ocupadas: number
  vagas_disponiveis: number
  em_lista_espera: number
  habilidades: HabilidadeDaAcao[]
}

export interface AcaoGravada {
  id: string
  ong_id: string
  unidade_id: string | null
  titulo: string
  descricao: string | null
  local_texto: string | null
  inicio: string
  fim: string
  vagas: number
  status: StatusAcao
  causa: Causa | null
}

export interface AcaoDados {
  titulo?: string
  descricao?: string | null
  local_texto?: string | null
  inicio?: string
  fim?: string
  vagas?: number
  causa?: Causa | null
  unidade_id?: string | null
  status?: StatusAcao
}

export interface AcaoNova extends AcaoDados {
  ong_id: string
  titulo: string
  inicio: string
  fim: string
  vagas: number
  habilidades: string[]
  habilidades_obrigatorias?: string[]
  status?: 'rascunho' | 'publicada'
}

export interface Inscricao {
  id: string
  acao_id: string
  voluntario_id: string
  status: StatusInscricao
  inscrito_em: string
  cancelado_em: string | null
}

export interface AcaoResumo {
  id: string
  codigo: number
  titulo: string
  inicio: string
  fim: string
  status: StatusAcao
  causa: Causa | null
  local_texto: string | null
  ong_id: string
  ong_nome: string
  unidade_cidade: string | null
  unidade_uf: string | null
}

/** GET /inscricoes/minhas */
export interface InscricaoComAcao extends Inscricao {
  acao: AcaoResumo
  check_in: string | null
  check_out: string | null
  horas_computadas: string | null
}

/** GET /acoes/{id}/inscricoes */
export interface Inscrito {
  inscricao_id: string
  status: StatusInscricao
  inscrito_em: string
  voluntario_id: string
  nome: string
  email: string
  telefone: string | null
  check_in: string | null
  check_out: string | null
  horas_computadas: string | null
}

export interface Presenca {
  inscricao_id: string
  check_in: string
  check_out: string | null
  horas_computadas: string | null
}

export interface Unidade {
  id: string
  ong_id: string
  nome: string
  cep: string | null
  logradouro: string | null
  numero: string | null
  complemento: string | null
  bairro: string | null
  cidade: string
  uf: string
}

export type UnidadeDados = Partial<Omit<Unidade, 'id' | 'ong_id'>>

export interface OngPublica {
  id: string
  nome: string
  descricao: string | null
  site: string | null
  email_contato: string | null
  telefone: string | null
  causa: Causa | null
  unidades: Unidade[]
  acoes_abertas: number
}

export interface MinhaOng {
  id: string
  nome: string
  acesso_total: boolean
  papel: 'proprietario' | 'gestor' | 'operador' | null
  unidades: Array<{ id: string; nome: string; cidade: string; uf: string }>
}

export interface OngCadastro {
  nome: string
  email: string
  senha: string
  nome_responsavel?: string | null
  telefone?: string | null
  descricao?: string | null
  causa?: Causa | null
  sede?: UnidadeDados & { nome: string; cidade: string; uf: string }
}

export interface Habilidade {
  id: string
  nome: string
  categoria: string | null
}

export interface JanelaDisponibilidade {
  dia_semana: number
  hora_inicio: string
  hora_fim: string
}

export interface PerfilVoluntario {
  usuario_id: string
  voluntario_id: string
  nome: string
  email: string
  telefone: string | null
  data_nascimento: string | null
  cidade: string | null
  uf: string | null
  biografia: string | null
  habilidades: Array<{ habilidade_id: string; nivel: string; nome: string; categoria: string | null }>
  disponibilidade: JanelaDisponibilidade[]
}

export interface PerfilAtualizacao {
  nome?: string
  telefone?: string | null
  cidade?: string | null
  uf?: string | null
  biografia?: string | null
  habilidades?: Array<{ habilidade_id: string; nivel?: string }>
  disponibilidade?: JanelaDisponibilidade[]
}

export interface ItemHistorico {
  acao_id: string
  acao_titulo: string
  ong_nome: string
  inicio: string
  fim: string
  status_acao: StatusAcao
  status_inscricao: StatusInscricao
  check_in: string | null
  check_out: string | null
  horas_computadas: string | null
}

export interface Historico {
  itens: ItemHistorico[]
  total_acoes: number
  presencas: number
  ausencias: number
  total_horas: string
}

export interface Notificacao {
  id: string
  acao_id: string | null
  tipo: TipoNotificacao
  titulo: string
  mensagem: string
  lida: boolean
  criada_em: string
}

export interface Estatisticas {
  ongs: number
  acoes_abertas: number
  voluntarios: number
  participacoes: number
}

export interface FiltrosAcoes {
  status?: StatusAcao
  todos_status?: boolean
  ong_id?: string
  busca?: string
  uf?: string
  causa?: Causa
  de?: string
  ate?: string
  com_vagas?: boolean
  futuras?: boolean
  limite?: number
  offset?: number
}

export interface Pagina<T> {
  itens: T[]
  total: number
}

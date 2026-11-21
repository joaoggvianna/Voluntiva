/* Vocabulário fixo da interface: causas, estados, dias e turnos.
 * Substitui as constantes que viviam nos dados-semente do mock. */

/** Causas na ordem de exibição. `valor` é o enum do banco (migration 0004). */
export const CAUSAS = [
  { valor: "meio_ambiente", rotulo: "Meio Ambiente" },
  { valor: "educacao", rotulo: "Educação" },
  { valor: "animais", rotulo: "Animais" },
  { valor: "saude", rotulo: "Saúde" },
  { valor: "assistencia_social", rotulo: "Assistência Social" },
  { valor: "cultura", rotulo: "Cultura" },
  { valor: "esporte", rotulo: "Esporte" },
  { valor: "direitos_humanos", rotulo: "Direitos Humanos" },
]

const ROTULO_POR_CAUSA = Object.fromEntries(CAUSAS.map((c) => [c.valor, c.rotulo]))

export function rotuloCausa(valor) {
  return ROTULO_POR_CAUSA[valor] ?? null
}

export const UFS = [
  "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
  "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]

/** Dias na ordem de exibição (segunda primeiro). `indice` segue
 *  EXTRACT(DOW) do Postgres: 0 = domingo ... 6 = sábado. */
export const DIAS = [
  { indice: 1, nome: "Segunda-feira" },
  { indice: 2, nome: "Terça-feira" },
  { indice: 3, nome: "Quarta-feira" },
  { indice: 4, nome: "Quinta-feira" },
  { indice: 5, nome: "Sexta-feira" },
  { indice: 6, nome: "Sábado" },
  { indice: 0, nome: "Domingo" },
]

export const DIAS_SEMANA = DIAS.map((d) => d.nome)

/** Turnos e a janela de horário que cada um representa no backend. */
export const TURNOS_HORARIOS = [
  { nome: "Manhã", inicio: "06:00", fim: "12:00" },
  { nome: "Tarde", inicio: "12:00", fim: "18:00" },
  { nome: "Noite", inicio: "18:00", fim: "23:59" },
]

export const TURNOS = TURNOS_HORARIOS.map((t) => t.nome)

import { diaDaSemana, turnoDoHorario } from "@/lib/utils"

export function calcularCompatibilidade(acao, voluntario) {
  if (!voluntario || voluntario.tipo !== "voluntario") return null
  const disponibilidade = voluntario.disponibilidade ?? { dias: [], turnos: [] }
  const habilidades = voluntario.habilidades ?? []
  const dia = diaDaSemana(acao.data)
  const turno = turnoDoHorario(acao.horario)
  const diaOk = disponibilidade.dias.includes(dia)
  const turnoOk = disponibilidade.turnos.includes(turno)
  const habilidadesEmComum = acao.habilidades.filter((h) => habilidades.includes(h))
  const habilidadeOk = acao.habilidades.length === 0 || habilidadesEmComum.length > 0
  const pontos = (diaOk ? 1 : 0) + (turnoOk ? 1 : 0) + (habilidadeOk ? 1 : 0)
  return {
    diaOk,
    turnoOk,
    habilidadeOk,
    habilidadesEmComum,
    pontos,
    compativel: diaOk && turnoOk && habilidadeOk,
  }
}

export function rotuloCompatibilidade(compatibilidade) {
  if (!compatibilidade) return null
  if (compatibilidade.compativel) return "Combina com você"
  if (compatibilidade.pontos === 2) return "Combina em parte"
  return null
}

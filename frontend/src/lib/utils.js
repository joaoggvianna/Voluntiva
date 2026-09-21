import { clsx } from "clsx";
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

export const DIAS_DA_SEMANA_INDICE = [
  "Domingo",
  "Segunda-feira",
  "Terça-feira",
  "Quarta-feira",
  "Quinta-feira",
  "Sexta-feira",
  "Sábado",
]

export function analisarData(iso) {
  const [ano, mes, dia] = iso.split("-").map(Number)
  return new Date(ano, mes - 1, dia)
}

export function hojeIso() {
  const agora = new Date()
  const mes = String(agora.getMonth() + 1).padStart(2, "0")
  const dia = String(agora.getDate()).padStart(2, "0")
  return `${agora.getFullYear()}-${mes}-${dia}`
}

export function formatarData(iso) {
  const data = analisarData(iso)
  return `${data.getDate()} de ${MESES[data.getMonth()]} de ${data.getFullYear()}`
}

export function formatarDataCurta(iso) {
  const data = analisarData(iso)
  return {
    dia: String(data.getDate()).padStart(2, "0"),
    mes: MESES[data.getMonth()].toUpperCase(),
  }
}

export function diaDaSemana(iso) {
  return DIAS_DA_SEMANA_INDICE[analisarData(iso).getDay()]
}

export function formatarDataHora(iso) {
  const data = new Date(iso)
  const dia = String(data.getDate()).padStart(2, "0")
  const mes = String(data.getMonth() + 1).padStart(2, "0")
  const hora = String(data.getHours()).padStart(2, "0")
  const minuto = String(data.getMinutes()).padStart(2, "0")
  return `${dia}/${mes}/${data.getFullYear()} às ${hora}:${minuto}`
}

export function formatarTelefone(valor) {
  const numeros = valor.replace(/\D/g, "").slice(0, 11)
  if (numeros.length <= 2) return numeros
  if (numeros.length <= 6) return `(${numeros.slice(0, 2)}) ${numeros.slice(2)}`
  if (numeros.length <= 10) {
    return `(${numeros.slice(0, 2)}) ${numeros.slice(2, 6)}-${numeros.slice(6)}`
  }
  return `(${numeros.slice(0, 2)}) ${numeros.slice(2, 7)}-${numeros.slice(7)}`
}

export function turnoDoHorario(horario) {
  const hora = parseInt(horario.slice(0, 2), 10)
  if (hora < 12) return "Manhã"
  if (hora < 18) return "Tarde"
  return "Noite"
}

export function emailValido(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export function normalizarTexto(texto) {
  return texto
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
}

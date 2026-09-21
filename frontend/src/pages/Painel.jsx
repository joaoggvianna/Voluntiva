import { useApp } from "@/contexto/AppContexto"
import { PainelOng } from "@/pages/PainelOng"
import { PainelVoluntario } from "@/pages/PainelVoluntario"

export function Painel() {
  const { usuario } = useApp()
  return usuario.tipo === "ong" ? <PainelOng /> : <PainelVoluntario />
}

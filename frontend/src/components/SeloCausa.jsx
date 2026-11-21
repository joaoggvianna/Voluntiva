import { Badge } from "@/components/ui/badge"
import { causaIcones } from "@/lib/causas"

/** `causa` é o rótulo ("Educação"); sem causa cadastrada, não mostra nada. */
export function SeloCausa({ causa }) {
  if (!causa) return null
  const Icone = causaIcones[causa]
  return (
    <Badge variant="secondary" className="gap-1 font-medium">
      {Icone && <Icone className="h-3 w-3" />}
      {causa}
    </Badge>
  )
}

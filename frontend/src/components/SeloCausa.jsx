import { Badge } from "@/components/ui/badge"
import { causaIcones } from "@/lib/causas"

export function SeloCausa({ causa }) {
  const Icone = causaIcones[causa]
  return (
    <Badge variant="secondary" className="gap-1 font-medium">
      {Icone && <Icone className="h-3 w-3" />}
      {causa}
    </Badge>
  )
}

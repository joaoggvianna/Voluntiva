import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

export function ConfirmarDialogo({
  aberto,
  aoFechar,
  titulo,
  descricao,
  rotuloConfirmar = "Confirmar",
  destrutivo = false,
  aoConfirmar,
}) {
  return (
    <Dialog open={aberto} onOpenChange={(valor) => !valor && aoFechar()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{titulo}</DialogTitle>
          <DialogDescription>{descricao}</DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={aoFechar}>
            Voltar
          </Button>
          <Button
            variant={destrutivo ? "destructive" : "default"}
            onClick={() => {
              aoConfirmar()
              aoFechar()
            }}
          >
            {rotuloConfirmar}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

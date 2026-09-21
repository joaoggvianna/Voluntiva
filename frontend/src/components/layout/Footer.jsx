import { Link } from "react-router-dom"
import { HeartHandshake } from "lucide-react"
import { Separator } from "@/components/ui/separator"

export function Footer() {
  return (
    <footer className="mt-auto border-t bg-muted/40">
      <div className="container mx-auto px-4 py-10">
        <div className="grid gap-8 md:grid-cols-3">
          <div className="space-y-3">
            <div className="flex items-center gap-2 font-bold">
              <HeartHandshake className="h-6 w-6 text-primary" />
              <span>
                Volunti<span className="text-primary">va</span>
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Sistema de gestão de voluntários para ONGs: ações sociais,
              inscrições, presença e histórico de participação em um só lugar.
            </p>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Navegação</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <Link to="/" className="transition-colors hover:text-primary">
                  Início
                </Link>
              </li>
              <li>
                <Link to="/acoes" className="transition-colors hover:text-primary">
                  Ações sociais
                </Link>
              </li>
              <li>
                <Link to="/ongs" className="transition-colors hover:text-primary">
                  ONGs
                </Link>
              </li>
              <li>
                <Link to="/cadastro" className="transition-colors hover:text-primary">
                  Criar conta
                </Link>
              </li>
            </ul>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Projeto acadêmico</h3>
            <p className="text-sm text-muted-foreground">
              Laboratório de Projeto de Software, Projeto de Protocolo de Redes
              e Laboratório de Banco de Dados.
            </p>
          </div>
        </div>

        <Separator className="my-6" />

        <p className="text-center text-xs text-muted-foreground">
          © {new Date().getFullYear()} Voluntiva. Protótipo de front-end com dados
          simulados, armazenados apenas neste navegador.
        </p>
      </div>
    </footer>
  )
}

import { cn } from "@/lib/utils"

export function SeletorChips({ opcoes, valor, aoAlterar, rotulo }) {
  function alternar(opcao) {
    if (valor.includes(opcao)) aoAlterar(valor.filter((item) => item !== opcao))
    else aoAlterar([...valor, opcao])
  }

  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label={rotulo}>
      {opcoes.map((opcao) => {
        const ativo = valor.includes(opcao)
        return (
          <button
            key={opcao}
            type="button"
            aria-pressed={ativo}
            onClick={() => alternar(opcao)}
            className={cn(
              "rounded-full border px-3 py-1 text-sm transition-colors",
              ativo
                ? "border-primary bg-primary text-primary-foreground"
                : "bg-background text-muted-foreground hover:border-primary hover:text-foreground"
            )}
          >
            {opcao}
          </button>
        )
      })}
    </div>
  )
}

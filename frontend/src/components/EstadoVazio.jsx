export function EstadoVazio({ icone: Icone, titulo, descricao, children }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed px-6 py-12 text-center">
      {Icone && (
        <div className="rounded-full bg-muted p-3">
          <Icone className="h-6 w-6 text-muted-foreground" />
        </div>
      )}
      <h3 className="font-semibold">{titulo}</h3>
      {descricao && (
        <p className="max-w-md text-sm text-muted-foreground">{descricao}</p>
      )}
      {children}
    </div>
  )
}

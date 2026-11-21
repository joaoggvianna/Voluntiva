import { useCallback, useEffect, useRef, useState } from "react"

/** Carrega dados assíncronos e refaz a carga quando `dependencias` mudam.
 *
 *  Respostas que chegam fora de ordem (o usuário mudou o filtro antes da
 *  anterior voltar) são descartadas: só a última requisição atualiza o
 *  estado. Durante uma recarga, `dados` mantém o valor anterior para a
 *  tela não piscar. */
export function useCarregar(carregar, dependencias) {
  const [estado, setEstado] = useState({ dados: undefined, erro: null, carregando: true })
  const ultima = useRef(0)
  const [rodada, setRodada] = useState(0)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const funcao = useCallback(carregar, dependencias)

  useEffect(() => {
    const numero = ++ultima.current
    setEstado((atual) => ({ ...atual, carregando: true, erro: null }))
    funcao()
      .then((dados) => {
        if (numero === ultima.current) setEstado({ dados, erro: null, carregando: false })
      })
      .catch((erro) => {
        if (numero === ultima.current) {
          setEstado((atual) => ({ ...atual, erro, carregando: false }))
        }
      })
  }, [funcao, rodada])

  const recarregar = useCallback(() => setRodada((r) => r + 1), [])

  return { ...estado, recarregar }
}

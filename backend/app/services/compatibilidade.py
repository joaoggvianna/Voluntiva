"""Regra de compatibilidade voluntário x ação (RF004), em SQL.

Fica num lugar só porque é usada em dois sentidos:
  * listar as ações compatíveis com UM voluntário (acao_service);
  * achar os voluntários compatíveis com UMA ação para notificá-los
    quando ela é publicada (notificacao_service).

Compatível quando:
  * habilidades: a ação não pede nenhuma, ou o voluntário tem ao menos uma
    das pedidas; e tem todas as marcadas como obrigatórias;
  * disponibilidade: o voluntário tem uma janela no dia da semana da ação
    que cobre do horário de início ao de fim, no fuso da aplicação
    (parâmetro :fuso). Ação que vira a noite não casa com nenhuma janela.
"""


def condicao_compativel(*, acao_id: str, inicio: str, fim: str, voluntario_id: str) -> str:
    """Devolve a condição SQL (para um WHERE) com as expressões dadas.

    Os argumentos são EXPRESSÕES SQL fixas escritas no código (nomes de
    coluna ou CAST de bind param), nunca dados vindos do usuário.
    """
    return f"""(
        (NOT EXISTS (SELECT 1 FROM public.acao_habilidade ah
                      WHERE ah.acao_id = {acao_id})
         OR EXISTS (SELECT 1
                      FROM public.acao_habilidade ah
                      JOIN public.voluntario_habilidade vh
                        ON vh.habilidade_id = ah.habilidade_id
                     WHERE ah.acao_id = {acao_id}
                       AND vh.voluntario_id = {voluntario_id}))
        AND NOT EXISTS (
            SELECT 1 FROM public.acao_habilidade ah
             WHERE ah.acao_id = {acao_id} AND ah.obrigatoria
               AND NOT EXISTS (
                   SELECT 1 FROM public.voluntario_habilidade vh
                    WHERE vh.voluntario_id = {voluntario_id}
                      AND vh.habilidade_id = ah.habilidade_id))
        AND EXISTS (
            SELECT 1 FROM public.voluntario_disponibilidade vd
             WHERE vd.voluntario_id = {voluntario_id}
               AND vd.dia_semana = EXTRACT(DOW FROM {inicio} AT TIME ZONE :fuso)::int
               AND ({inicio} AT TIME ZONE :fuso)::date = ({fim} AT TIME ZONE :fuso)::date
               AND vd.hora_inicio <= ({inicio} AT TIME ZONE :fuso)::time
               AND vd.hora_fim >= ({fim} AT TIME ZONE :fuso)::time)
    )"""

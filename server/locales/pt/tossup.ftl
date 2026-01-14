# Mensagens do jogo Toss Up (Português)
# Nota: Mensagens comuns como round-start, turn-start, target-score estão em games.ftl

# Informações do jogo
game-name-tossup = Toss Up
tossup-category = Jogos de Dados

# Ações
tossup-roll-first = Jogar { $count } dados
tossup-roll-remaining = Jogar { $count } dados restantes
tossup-bank = Guardar { $points } pontos

# Eventos do jogo
tossup-turn-start = Vez de { $player }. Pontuação: { $score }
tossup-you-roll = Você jogou: { $results }.
tossup-player-rolls = { $player } jogou: { $results }.

# Status da rodada
tossup-you-have-points = Pontos da rodada: { $turn_points }. Dados restantes: { $dice_count }.
tossup-player-has-points = { $player } tem { $turn_points } pontos da rodada. { $dice_count } dados restantes.

# Dados novos
tossup-you-get-fresh = Sem dados! Recebendo { $count } dados novos.
tossup-player-gets-fresh = { $player } recebe { $count } dados novos.

# Perda (bust)
tossup-you-bust = Perdeu! Você perde { $points } pontos desta rodada.
tossup-player-busts = { $player } perde e perde { $points } pontos!

# Guardar
tossup-you-bank = Você guarda { $points } pontos. Pontuação total: { $total }.
tossup-player-banks = { $player } guarda { $points } pontos. Pontuação total: { $total }.

# Vencedor
tossup-winner = { $player } vence com { $score } pontos!
tossup-tie-tiebreaker = É um empate entre { $players }! Rodada de desempate!

# Opções
tossup-set-rules-variant = Variante de regras: { $variant }
tossup-select-rules-variant = Selecione a variante de regras:
tossup-option-changed-rules = Variante de regras alterada para { $variant }

tossup-set-starting-dice = Dados iniciais: { $count }
tossup-enter-starting-dice = Digite o número de dados iniciais:
tossup-option-changed-dice = Dados iniciais alterados para { $count }

# Variantes de regras
tossup-rules-standard = Padrão
tossup-rules-playpalace = PlayPalace

# Explicações das regras
tossup-rules-standard-desc = 3 verdes, 2 amarelos, 1 vermelho por dado. Perde se não houver verdes e houver pelo menos um vermelho.
tossup-rules-playpalace-desc = Distribuição igual. Perde se todos os dados forem vermelhos.

# Razões de desabilitação
tossup-need-points = Você precisa de pontos para guardar.

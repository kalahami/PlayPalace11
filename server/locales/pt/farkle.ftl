# Mensagens do jogo Farkle (Português)

# Informações do jogo
game-name-farkle = Farkle

# Ações - Rolar e Bancar
farkle-roll = Rolar { $count } { $count ->
    [one] dado
   *[other] dados
}
farkle-bank = Bancar { $points } pontos

# Ações de combinação de pontuação (igual ao v10)
farkle-take-single-one = Um 1 por { $points } pontos
farkle-take-single-five = Um 5 por { $points } pontos
farkle-take-three-kind = Três { $number }s por { $points } pontos
farkle-take-four-kind = Quatro { $number }s por { $points } pontos
farkle-take-five-kind = Cinco { $number }s por { $points } pontos
farkle-take-six-kind = Seis { $number }s por { $points } pontos
farkle-take-straight = Sequência por { $points } pontos
farkle-take-three-pairs = Três pares por { $points } pontos
farkle-take-double-triplets = Dupla trinca por { $points } pontos
farkle-take-four-kind-pair = Quatro iguais mais um par por { $points } pontos

# Eventos do jogo (igual ao v10)
farkle-rolls = { $player } rola { $count } { $count ->
    [one] dado
   *[other] dados
}...
farkle-roll-result = { $dice }
farkle-start-roll = { $player } rola { $roll } para decidir quem começa.
farkle-start-roll-tie = Empate na maior rolagem. Rolando novamente.
farkle-start-first-player = { $player } começa.
farkle-farkle = FARKLE! { $player } perde { $points } pontos
farkle-takes-combo = { $player } pega { $combo } por { $points } pontos
farkle-you-take-combo = Você pega { $combo } por { $points } pontos
farkle-hot-dice = Dados quentes!
farkle-banks = { $player } banca { $points } pontos para um total de { $total }
farkle-winner = { $player } vence com { $score } pontos!
farkle-winners-tie = Temos um empate! Vencedores: { $players }

# Ação de verificar pontuação do turno
farkle-turn-score = { $player } tem { $points } pontos neste turno.
farkle-no-turn = Ninguém está jogando no momento.

# Opções específicas do Farkle
farkle-set-target-score = Pontuação alvo: { $score }
farkle-enter-target-score = Digite a pontuação alvo (1000-50000):
farkle-option-changed-target = Pontuação alvo definida para { $score }.
farkle-set-min-bank = Mínimo para abrir: { $points }
farkle-enter-min-bank = Digite o mínimo para abrir (0-5000):
farkle-option-changed-min-bank = Mínimo para abrir definido para { $points }.

# Razões para ações desabilitadas
farkle-must-take-combo = Você deve pegar uma combinação primeiro.
farkle-cannot-bank = Você não pode bancar agora.
farkle-need-min-bank = Você precisa de mais pontos para bancar pela primeira vez.

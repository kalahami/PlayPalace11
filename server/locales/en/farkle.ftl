# Farkle game messages

# Game info
game-name-farkle = Farkle

# Actions - Roll and Bank
farkle-roll = Roll { $count } { $count ->
    [one] die
   *[other] dice
}
farkle-bank = Bank { $points } points

# Scoring combination actions
farkle-take-single-one = Single 1 for { $points } points
farkle-take-single-five = Single 5 for { $points } points
farkle-take-three-kind = Three { $number }s for { $points } points
farkle-take-four-kind = Four { $number }s for { $points } points
farkle-take-five-kind = Five { $number }s for { $points } points
farkle-take-six-kind = Six { $number }s for { $points } points
farkle-take-straight = Straight for { $points } points
farkle-take-three-pairs = Three pairs for { $points } points
farkle-take-double-triplets = Double triplets for { $points } points
farkle-take-four-kind-pair = Four of a kind plus a pair for { $points } points

# Game events (matching v10 exactly)
farkle-rolls = { $player } rolls { $count } { $count ->
    [one] die
   *[other] dice
}...
farkle-roll-result = { $dice }
farkle-start-roll = { $player } rolls { $roll } to decide who goes first.
farkle-start-roll-tie = Tie for highest roll. Rolling again.
farkle-start-first-player = { $player } goes first.
farkle-farkle = FARKLE! { $player } loses { $points } points
farkle-takes-combo = { $player } takes { $combo } for { $points } points
farkle-you-take-combo = You take { $combo } for { $points } points
farkle-hot-dice = Hot dice!
farkle-banks = { $player } banks { $points } points for a total of { $total }
farkle-winner = { $player } wins with { $score } points!
farkle-winners-tie = We have a tie! Winners: { $players }

# Check turn score action
farkle-turn-score = { $player } has { $points } points this turn.
farkle-no-turn = No one is currently taking a turn.

# Farkle-specific options
farkle-set-target-score = Target score: { $score }
farkle-enter-target-score = Enter target score (1000-50000):
farkle-option-changed-target = Target score set to { $score }.
farkle-set-min-bank = Minimum opening bank: { $points }
farkle-enter-min-bank = Enter minimum opening bank (0-5000):
farkle-option-changed-min-bank = Minimum opening bank set to { $points }.

# Disabled action reasons
farkle-must-take-combo = You must take a scoring combination first.
farkle-cannot-bank = You cannot bank right now.
farkle-need-min-bank = You need more points to bank for the first time.

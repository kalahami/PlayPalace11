"""
Farkle Game Implementation for PlayPalace v11.

Classic dice game: score combinations and don't Farkle!
Push your luck by rolling again or bank your points.
"""

from dataclasses import dataclass, field
from datetime import datetime
import random

from ..base import Game, Player, GameOptions
from ..registry import register_game
from ...game_utils.actions import Action, ActionSet, Visibility
from ...game_utils.bot_helper import BotHelper
from ...game_utils.game_result import GameResult, PlayerResult
from ...game_utils.options import IntOption, option_field
from ...messages.localization import Localization
from ...ui.keybinds import KeybindState


@dataclass
class FarklePlayer(Player):
    """Player state for Farkle game."""

    score: int = 0  # Permanent score (banked points)
    turn_score: int = 0  # Points accumulated this turn (lost on farkle)
    current_roll: list[int] = field(default_factory=list)  # Dice available to take
    banked_dice: list[int] = field(default_factory=list)  # Dice taken this turn
    has_taken_combo: bool = False  # True after taking a combo (enables roll)
    has_banked: bool = False  # True after banking for the first time
    # Stats tracking
    turns_taken: int = 0  # Number of turns completed (for avg points per turn)
    best_turn: int = 0  # Highest points banked in a single turn


@dataclass
class FarkleOptions(GameOptions):
    """Options for Farkle game."""

    target_score: int = option_field(
        IntOption(
            default=10000,
            min_val=1000,
            max_val=50000,
            value_key="score",
            label="farkle-set-target-score",
            prompt="farkle-enter-target-score",
            change_msg="farkle-option-changed-target",
        )
    )
    min_bank_points: int = option_field(
        IntOption(
            default=500,
            min_val=0,
            max_val=5000,
            value_key="points",
            label="farkle-set-min-bank",
            prompt="farkle-enter-min-bank",
            change_msg="farkle-option-changed-min-bank",
        )
    )


# Scoring combination types
COMBO_SINGLE_1 = "single_1"
COMBO_SINGLE_5 = "single_5"
COMBO_THREE_OF_KIND = "three_of_kind"
COMBO_FOUR_OF_KIND = "four_of_kind"
COMBO_FIVE_OF_KIND = "five_of_kind"
COMBO_SIX_OF_KIND = "six_of_kind"
COMBO_STRAIGHT = "straight"
COMBO_THREE_PAIRS = "three_pairs"
COMBO_DOUBLE_TRIPLETS = "double_triplets"
COMBO_FOUR_KIND_PLUS_PAIR = "four_kind_pair"

# Combo sounds
COMBO_SOUNDS = {
    COMBO_SINGLE_1: "game_farkle/point10.ogg",
    COMBO_SINGLE_5: "game_farkle/singles5.ogg",
    COMBO_THREE_OF_KIND: "game_farkle/3kind.ogg",
    COMBO_FOUR_OF_KIND: "game_farkle/4kind.ogg",
    COMBO_FIVE_OF_KIND: "game_farkle/5kind.ogg",
    COMBO_SIX_OF_KIND: "game_farkle/6kind.ogg",
    COMBO_STRAIGHT: "game_farkle/largestraight.ogg",
    COMBO_THREE_PAIRS: "game_farkle/3pairs.ogg",
    COMBO_DOUBLE_TRIPLETS: "game_farkle/doubletriplets.ogg",
    COMBO_FOUR_KIND_PLUS_PAIR: "game_farkle/fullhouse.ogg",
}


def count_dice(dice: list[int]) -> dict[int, int]:
    """Count occurrences of each die value (1-6)."""
    counts = {i: 0 for i in range(1, 7)}
    for die in dice:
        counts[die] += 1
    return counts


def has_combination(dice: list[int], combo_type: str, number: int = 0) -> bool:
    """Check if dice contain a specific combination."""
    counts = count_dice(dice)

    if combo_type == COMBO_SINGLE_1:
        return counts[1] >= 1
    elif combo_type == COMBO_SINGLE_5:
        return counts[5] >= 1
    elif combo_type == COMBO_THREE_OF_KIND:
        return counts[number] >= 3
    elif combo_type == COMBO_FOUR_OF_KIND:
        return counts[number] >= 4
    elif combo_type == COMBO_FIVE_OF_KIND:
        return counts[number] >= 5
    elif combo_type == COMBO_SIX_OF_KIND:
        return counts[number] == 6
    elif combo_type == COMBO_STRAIGHT:
        if len(dice) != 6:
            return False
        return all(counts[i] == 1 for i in range(1, 7))
    elif combo_type == COMBO_THREE_PAIRS:
        if len(dice) != 6:
            return False
        pairs = sum(1 for i in range(1, 7) if counts[i] == 2)
        return pairs == 3
    elif combo_type == COMBO_DOUBLE_TRIPLETS:
        if len(dice) != 6:
            return False
        triplets = sum(1 for i in range(1, 7) if counts[i] == 3)
        return triplets == 2
    elif combo_type == COMBO_FOUR_KIND_PLUS_PAIR:
        if len(dice) != 6:
            return False
        has_quad = any(counts[i] == 4 for i in range(1, 7))
        has_pair = any(counts[i] == 2 for i in range(1, 7))
        return has_quad and has_pair

    return False


def get_combination_points(combo_type: str, number: int = 0) -> int:
    """Get point value for a combination."""
    if combo_type == COMBO_SINGLE_1:
        return 100
    elif combo_type == COMBO_SINGLE_5:
        return 50
    elif combo_type == COMBO_THREE_OF_KIND:
        return 300 if number == 1 else number * 100
    elif combo_type == COMBO_FOUR_OF_KIND:
        return 1000
    elif combo_type == COMBO_FIVE_OF_KIND:
        return 2000
    elif combo_type == COMBO_SIX_OF_KIND:
        return 3000
    elif combo_type == COMBO_STRAIGHT:
        return 1500
    elif combo_type == COMBO_THREE_PAIRS:
        return 1500
    elif combo_type == COMBO_DOUBLE_TRIPLETS:
        return 2500
    elif combo_type == COMBO_FOUR_KIND_PLUS_PAIR:
        return 1500
    return 0


def has_scoring_dice(dice: list[int]) -> bool:
    """Check if dice contain any scoring combinations (for farkle detection)."""
    if not dice:
        return False

    counts = count_dice(dice)

    # Single 1s or 5s
    if counts[1] > 0 or counts[5] > 0:
        return True

    # Three or more of a kind
    if any(counts[i] >= 3 for i in range(1, 7)):
        return True

    # Straight (1-2-3-4-5-6)
    if len(dice) == 6 and all(counts[i] == 1 for i in range(1, 7)):
        return True

    # Three pairs
    if len(dice) == 6:
        pairs = sum(1 for i in range(1, 7) if counts[i] == 2)
        if pairs == 3:
            return True

    # Double triplets
    if len(dice) == 6:
        triplets = sum(1 for i in range(1, 7) if counts[i] == 3)
        if triplets == 2:
            return True

    return False


def get_available_combinations(dice: list[int]) -> list[tuple[str, int, int]]:
    """Get all available scoring combinations as (combo_type, number, points) tuples."""
    combinations = []

    if not dice:
        return combinations

    counts = count_dice(dice)

    # Six of a kind (check first, highest points)
    for num in range(1, 7):
        if has_combination(dice, COMBO_SIX_OF_KIND, num):
            points = get_combination_points(COMBO_SIX_OF_KIND, num)
            combinations.append((COMBO_SIX_OF_KIND, num, points))

    # Five of a kind
    for num in range(1, 7):
        if has_combination(dice, COMBO_FIVE_OF_KIND, num):
            points = get_combination_points(COMBO_FIVE_OF_KIND, num)
            combinations.append((COMBO_FIVE_OF_KIND, num, points))

    # Four of a kind
    for num in range(1, 7):
        if has_combination(dice, COMBO_FOUR_OF_KIND, num):
            points = get_combination_points(COMBO_FOUR_OF_KIND, num)
            combinations.append((COMBO_FOUR_OF_KIND, num, points))

    # Double triplets (higher priority than three pairs)
    if has_combination(dice, COMBO_DOUBLE_TRIPLETS):
        points = get_combination_points(COMBO_DOUBLE_TRIPLETS)
        combinations.append((COMBO_DOUBLE_TRIPLETS, 0, points))

    # Straight (1-2-3-4-5-6)
    if has_combination(dice, COMBO_STRAIGHT):
        points = get_combination_points(COMBO_STRAIGHT)
        combinations.append((COMBO_STRAIGHT, 0, points))

    # Four of a kind plus a pair
    if has_combination(dice, COMBO_FOUR_KIND_PLUS_PAIR):
        points = get_combination_points(COMBO_FOUR_KIND_PLUS_PAIR)
        combinations.append((COMBO_FOUR_KIND_PLUS_PAIR, 0, points))

    # Three pairs
    if has_combination(dice, COMBO_THREE_PAIRS):
        points = get_combination_points(COMBO_THREE_PAIRS)
        combinations.append((COMBO_THREE_PAIRS, 0, points))

    # Three of a kind
    for num in range(1, 7):
        if has_combination(dice, COMBO_THREE_OF_KIND, num):
            points = get_combination_points(COMBO_THREE_OF_KIND, num)
            combinations.append((COMBO_THREE_OF_KIND, num, points))

    # Single 1s (always available if there's at least one 1)
    if counts[1] > 0:
        points = get_combination_points(COMBO_SINGLE_1)
        combinations.append((COMBO_SINGLE_1, 1, points))

    # Single 5s
    if counts[5] > 0:
        points = get_combination_points(COMBO_SINGLE_5)
        combinations.append((COMBO_SINGLE_5, 5, points))

    # Sort by points descending
    combinations.sort(key=lambda x: x[2], reverse=True)

    return combinations


@dataclass
@register_game
class FarkleGame(Game):
    """
    Farkle dice game.

    Players take turns rolling 6 dice and selecting scoring combinations.
    After each selection, they can roll remaining dice or bank their points.
    Rolling dice with no scoring combinations (Farkle!) loses all turn points.
    First player to reach the target score wins.
    """

    players: list[FarklePlayer] = field(default_factory=list)
    options: FarkleOptions = field(default_factory=FarkleOptions)
    final_round_score: int | None = None
    final_round_leader_id: str | None = None
    final_round_pending: set[str] = field(default_factory=set)

    @classmethod
    def get_name(cls) -> str:
        return "Farkle"

    @classmethod
    def get_type(cls) -> str:
        return "farkle"

    @classmethod
    def get_category(cls) -> str:
        return "category-dice-games"

    @classmethod
    def get_min_players(cls) -> int:
        return 2

    @classmethod
    def get_max_players(cls) -> int:
        return 4

    @classmethod
    def get_leaderboard_types(cls) -> list[dict]:
        return [
            {
                "id": "avg_points_per_turn",
                "numerator": "player_stats.{player_name}.total_score",
                "denominator": "player_stats.{player_name}.turns_taken",
                "aggregate": "sum",  # sum num/sum denom across games
                "format": "avg",
                "decimals": 1,
            },
            {
                "id": "best_single_turn",
                "path": "player_stats.{player_name}.best_turn",
                "aggregate": "max",
                "format": "score",
            },
        ]

    def create_player(
        self, player_id: str, name: str, is_bot: bool = False
    ) -> FarklePlayer:
        """Create a new player with Farkle-specific state."""
        return FarklePlayer(
            id=player_id,
            name=name,
            is_bot=is_bot,
            score=0,
            turn_score=0,
            current_roll=[],
            banked_dice=[],
            has_taken_combo=False,
            has_banked=False,
        )

    def create_turn_action_set(self, player: FarklePlayer) -> ActionSet:
        """Create the turn action set for a player."""
        user = self.get_user(player)
        locale = user.locale if user else "en"

        action_set = ActionSet(name="turn")

        # Roll action
        action_set.add(
            Action(
                id="roll",
                label=Localization.get(locale, "farkle-roll", count=6),
                handler="_action_roll",
                is_enabled="_is_roll_enabled",
                is_hidden="_is_roll_hidden",
                get_label="_get_roll_label",
            )
        )

        # Bank action
        action_set.add(
            Action(
                id="bank",
                label=Localization.get(locale, "farkle-bank", points=0),
                handler="_action_bank",
                is_enabled="_is_bank_enabled",
                is_hidden="_is_bank_hidden",
                get_label="_get_bank_label",
            )
        )

        # Check turn score (F5 menu only)
        action_set.add(
            Action(
                id="check_turn_score",
                label="Check turn score",
                handler="_action_check_turn_score",
                is_enabled="_is_check_turn_score_enabled",
                is_hidden="_is_check_turn_score_hidden",
            )
        )

        return action_set

    def setup_keybinds(self) -> None:
        """Define all keybinds for the game."""
        super().setup_keybinds()

        # Turn action keybinds
        self.define_keybind("r", "Roll dice", ["roll"], state=KeybindState.ACTIVE)
        self.define_keybind("b", "Bank points", ["bank"], state=KeybindState.ACTIVE)
        self.define_keybind(
            "c", "Check turn score", ["check_turn_score"], state=KeybindState.ACTIVE
        )

    def _get_combo_label(
        self, locale: str, combo_type: str, number: int, points: int
    ) -> str:
        """Get the localized label for a scoring combination."""
        if combo_type == COMBO_SINGLE_1:
            return Localization.get(locale, "farkle-take-single-one", points=points)
        elif combo_type == COMBO_SINGLE_5:
            return Localization.get(locale, "farkle-take-single-five", points=points)
        elif combo_type == COMBO_THREE_OF_KIND:
            return Localization.get(
                locale, "farkle-take-three-kind", number=number, points=points
            )
        elif combo_type == COMBO_FOUR_OF_KIND:
            return Localization.get(
                locale, "farkle-take-four-kind", number=number, points=points
            )
        elif combo_type == COMBO_FIVE_OF_KIND:
            return Localization.get(
                locale, "farkle-take-five-kind", number=number, points=points
            )
        elif combo_type == COMBO_SIX_OF_KIND:
            return Localization.get(
                locale, "farkle-take-six-kind", number=number, points=points
            )
        elif combo_type == COMBO_STRAIGHT:
            return Localization.get(locale, "farkle-take-straight", points=points)
        elif combo_type == COMBO_THREE_PAIRS:
            return Localization.get(locale, "farkle-take-three-pairs", points=points)
        elif combo_type == COMBO_DOUBLE_TRIPLETS:
            return Localization.get(
                locale, "farkle-take-double-triplets", points=points
            )
        elif combo_type == COMBO_FOUR_KIND_PLUS_PAIR:
            return Localization.get(
                locale, "farkle-take-four-kind-pair", points=points
            )
        return f"{combo_type} for {points} points"

    def _get_combo_name(self, combo_type: str, number: int) -> str:
        """Get the English name for a combo (for announcements)."""
        if combo_type == COMBO_SINGLE_1:
            return "Single 1"
        elif combo_type == COMBO_SINGLE_5:
            return "Single 5"
        elif combo_type == COMBO_THREE_OF_KIND:
            return f"Three {number}s"
        elif combo_type == COMBO_FOUR_OF_KIND:
            return f"Four {number}s"
        elif combo_type == COMBO_FIVE_OF_KIND:
            return f"Five {number}s"
        elif combo_type == COMBO_SIX_OF_KIND:
            return f"Six {number}s"
        elif combo_type == COMBO_STRAIGHT:
            return "Straight"
        elif combo_type == COMBO_THREE_PAIRS:
            return "Three pairs"
        elif combo_type == COMBO_DOUBLE_TRIPLETS:
            return "Double triplets"
        elif combo_type == COMBO_FOUR_KIND_PLUS_PAIR:
            return "Four of a kind plus a pair"
        return combo_type

    def update_scoring_actions(self, player: FarklePlayer) -> None:
        """Update scoring actions based on current roll.

        Scoring actions are placed BEFORE roll/bank in the menu.
        """
        turn_set = self.get_action_set(player, "turn")
        if not turn_set:
            return

        user = self.get_user(player)
        locale = user.locale if user else "en"

        # Remove old scoring actions from _actions dict
        old_actions = [
            action_id
            for action_id in turn_set._actions.keys()
            if action_id.startswith("score_")
        ]
        for action_id in old_actions:
            del turn_set._actions[action_id]

        # Get available combinations
        combos = get_available_combinations(player.current_roll)

        # Rebuild the order: scoring actions first, then roll, bank, check_turn_score
        turn_set._order.clear()

        # Add scoring actions first (sorted by points, highest first)
        for combo_type, number, points in combos:
            action_id = f"score_{combo_type}_{number}"
            label = self._get_combo_label(locale, combo_type, number, points)

            turn_set._actions[action_id] = Action(
                id=action_id,
                label=label,
                handler="_action_take_combo",
                is_enabled="_is_scoring_action_enabled",
                is_hidden="_is_scoring_action_hidden",
            )
            turn_set._order.append(action_id)

        # Add roll, bank, check_turn_score after scoring actions
        for action_id in ["roll", "bank", "check_turn_score"]:
            if action_id in turn_set._actions:
                turn_set._order.append(action_id)

    # ==========================================================================
    # Declarative Action Callbacks
    # ==========================================================================

    def _is_roll_enabled(self, player: Player) -> str | None:
        """Check if roll action is enabled."""
        if self.status != "playing":
            return "action-not-playing"
        if self.current_player != player:
            return "action-not-your-turn"
        if player.is_spectator:
            return "action-spectator"
        farkle_player: FarklePlayer = player  # type: ignore
        can_roll = len(farkle_player.current_roll) == 0 or farkle_player.has_taken_combo
        if not can_roll:
            return "farkle-must-take-combo"
        return None

    def _is_roll_hidden(self, player: Player) -> Visibility:
        """Check if roll action is hidden."""
        if self.status != "playing":
            return Visibility.HIDDEN
        if self.current_player != player:
            return Visibility.HIDDEN
        farkle_player: FarklePlayer = player  # type: ignore
        can_roll = len(farkle_player.current_roll) == 0 or farkle_player.has_taken_combo
        if not can_roll:
            return Visibility.HIDDEN
        return Visibility.VISIBLE

    def _get_roll_label(self, player: Player, action_id: str) -> str:
        """Get dynamic label for roll action."""
        user = self.get_user(player)
        locale = user.locale if user else "en"
        farkle_player: FarklePlayer = player  # type: ignore
        num_dice = self._get_roll_dice_count(farkle_player)
        return Localization.get(locale, "farkle-roll", count=num_dice)

    def _is_bank_enabled(self, player: Player) -> str | None:
        """Check if bank action is enabled."""
        if self.status != "playing":
            return "action-not-playing"
        if self.current_player != player:
            return "action-not-your-turn"
        if player.is_spectator:
            return "action-spectator"
        farkle_player: FarklePlayer = player  # type: ignore
        if len(farkle_player.current_roll) > 0 and not farkle_player.has_taken_combo:
            return "farkle-must-take-combo"
        if farkle_player.turn_score <= 0:
            return "farkle-cannot-bank"
        min_required = max(1, self.options.min_bank_points)
        if not farkle_player.has_banked and farkle_player.turn_score < min_required:
            return "farkle-need-min-bank"
        return None

    def _is_bank_hidden(self, player: Player) -> Visibility:
        """Check if bank action is hidden."""
        return (
            Visibility.VISIBLE
            if self._is_bank_enabled(player) is None
            else Visibility.HIDDEN
        )

    def _get_bank_label(self, player: Player, action_id: str) -> str:
        """Get dynamic label for bank action."""
        user = self.get_user(player)
        locale = user.locale if user else "en"
        farkle_player: FarklePlayer = player  # type: ignore
        return Localization.get(locale, "farkle-bank", points=farkle_player.turn_score)

    def _is_check_turn_score_enabled(self, player: Player) -> str | None:
        """Check if check turn score action is enabled."""
        if self.status != "playing":
            return "action-not-playing"
        return None

    def _is_check_turn_score_hidden(self, player: Player) -> Visibility:
        """Check turn score is always hidden from menu (keybind only)."""
        return Visibility.HIDDEN

    def _is_scoring_action_enabled(self, player: Player) -> str | None:
        """Check if a scoring action is enabled (scoring actions are only created when available)."""
        if self.status != "playing":
            return "action-not-playing"
        if self.current_player != player:
            return "action-not-your-turn"
        if player.is_spectator:
            return "action-spectator"
        return None

    def _is_scoring_action_hidden(self, player: Player) -> Visibility:
        """Check if a scoring action is hidden."""
        if self.status != "playing":
            return Visibility.HIDDEN
        if self.current_player != player:
            return Visibility.HIDDEN
        return Visibility.VISIBLE

    def _get_roll_dice_count(self, player: FarklePlayer) -> int:
        """Get the number of dice that will be rolled."""
        if len(player.current_roll) > 0:
            return len(player.current_roll)
        else:
            num_dice = 6 - len(player.banked_dice)
            if num_dice == 0:
                num_dice = 6  # Hot dice
            return num_dice

    def _action_roll(self, player: Player, action_id: str) -> None:
        """Handle roll action."""
        farkle_player: FarklePlayer = player  # type: ignore

        # Check for hot dice (all 6 banked) and reset
        if len(farkle_player.current_roll) == 0:
            num_dice = 6 - len(farkle_player.banked_dice)
            if num_dice == 0:
                # Hot dice! Reset banked dice and roll all 6
                farkle_player.banked_dice = []
                num_dice = 6
        else:
            num_dice = len(farkle_player.current_roll)

        self.broadcast_l("farkle-rolls", player=player.name, count=num_dice)
        self.play_sound("game_pig/roll.ogg")

        # Jolt bot to pause before next action
        BotHelper.jolt_bot(player, ticks=random.randint(10, 20))

        # Roll the dice
        farkle_player.current_roll = sorted(
            [random.randint(1, 6) for _ in range(num_dice)]
        )

        # Announce the roll
        dice_str = ", ".join(str(d) for d in farkle_player.current_roll)
        self.broadcast_l("farkle-roll-result", dice=dice_str)

        # Check for farkle
        if not has_scoring_dice(farkle_player.current_roll):
            self.play_sound("game_farkle/farkle.ogg")
            self.broadcast_l(
                "farkle-farkle", player=player.name, points=farkle_player.turn_score
            )
            # Track turn (farkle = 0 points banked)
            farkle_player.turns_taken += 1
            farkle_player.turn_score = 0
            farkle_player.current_roll = []
            farkle_player.banked_dice = []
            self.end_turn()
            return

        # Reset combo flag after roll
        farkle_player.has_taken_combo = False

        # Update scoring actions based on new roll
        self.update_scoring_actions(farkle_player)
        self.rebuild_player_menu(farkle_player)

    def _action_take_combo(self, player: Player, action_id: str) -> None:
        """Handle taking a scoring combination."""
        farkle_player: FarklePlayer = player  # type: ignore

        # Jolt bot to pause before next action
        BotHelper.jolt_bot(player, ticks=random.randint(8, 12))

        # Parse combo type and number from action_id (e.g., "score_three_of_kind_4")
        parts = action_id.split("_", 1)[1]  # Remove "score_" prefix

        # Extract combo type and number
        if parts.startswith("single_1"):
            combo_type = COMBO_SINGLE_1
            number = 1
        elif parts.startswith("single_5"):
            combo_type = COMBO_SINGLE_5
            number = 5
        elif parts.startswith("three_of_kind"):
            combo_type = COMBO_THREE_OF_KIND
            number = int(parts.split("_")[-1])
        elif parts.startswith("four_of_kind"):
            combo_type = COMBO_FOUR_OF_KIND
            number = int(parts.split("_")[-1])
        elif parts.startswith("five_of_kind"):
            combo_type = COMBO_FIVE_OF_KIND
            number = int(parts.split("_")[-1])
        elif parts.startswith("six_of_kind"):
            combo_type = COMBO_SIX_OF_KIND
            number = int(parts.split("_")[-1])
        elif parts.startswith("straight"):
            combo_type = COMBO_STRAIGHT
            number = 0
        elif parts.startswith("three_pairs"):
            combo_type = COMBO_THREE_PAIRS
            number = 0
        elif parts.startswith("double_triplets"):
            combo_type = COMBO_DOUBLE_TRIPLETS
            number = 0
        elif parts.startswith("four_kind_pair"):
            combo_type = COMBO_FOUR_KIND_PLUS_PAIR
            number = 0
        else:
            return  # Unknown combo

        points = get_combination_points(combo_type, number)
        combo_name = self._get_combo_name(combo_type, number)

        # Remove dice from current_roll and add to banked_dice
        self._remove_combo_dice(farkle_player, combo_type, number)

        # Add points
        farkle_player.turn_score += points

        # Play sounds
        self.play_sound("game_farkle/takepoint.ogg")
        if combo_type in COMBO_SOUNDS:
            self.schedule_sound(COMBO_SOUNDS[combo_type], delay_ticks=2)

        # Announce what was taken
        self.broadcast_personal_l(
            player, "farkle-you-take-combo", "farkle-takes-combo",
            combo=combo_name, points=points
        )

        # Check for hot dice
        if len(farkle_player.banked_dice) == 6 and len(farkle_player.current_roll) == 0:
            self.broadcast_l("farkle-hot-dice")
            self.play_sound("game_farkle/hotdice.ogg")

        # Mark that we've taken a combo
        farkle_player.has_taken_combo = True

        # Update actions
        self.update_scoring_actions(farkle_player)
        self.rebuild_player_menu(farkle_player)

    def _remove_combo_dice(
        self, player: FarklePlayer, combo_type: str, number: int
    ) -> None:
        """Remove dice from current_roll for the given combination."""
        dice_to_remove = self._collect_combo_dice(
            player.current_roll, combo_type, number
        )
        if not dice_to_remove:
            return

        for die in dice_to_remove:
            if die in player.current_roll:
                player.current_roll.remove(die)
                player.banked_dice.append(die)

    def _collect_combo_dice(
        self, dice: list[int], combo_type: str, number: int
    ) -> list[int]:
        """Return dice for the combo so they can be removed."""
        counts = count_dice(dice)
        if combo_type == COMBO_SINGLE_1 and counts[1] >= 1:
            return [1]
        if combo_type == COMBO_SINGLE_5 and counts[5] >= 1:
            return [5]
        if combo_type == COMBO_THREE_OF_KIND and counts[number] >= 3:
            return [number] * 3
        if combo_type == COMBO_FOUR_OF_KIND and counts[number] >= 4:
            return [number] * 4
        if combo_type == COMBO_FIVE_OF_KIND and counts[number] >= 5:
            return [number] * 5
        if combo_type == COMBO_SIX_OF_KIND and counts[number] >= 6:
            return [number] * 6
        if combo_type in (
            COMBO_STRAIGHT,
            COMBO_THREE_PAIRS,
            COMBO_DOUBLE_TRIPLETS,
            COMBO_FOUR_KIND_PLUS_PAIR,
        ):
            return list(dice)
        return []

    def _action_bank(self, player: Player, action_id: str) -> None:
        """Handle bank action."""
        farkle_player: FarklePlayer = player  # type: ignore

        # Track stats before resetting
        farkle_player.turns_taken += 1
        if farkle_player.turn_score > farkle_player.best_turn:
            farkle_player.best_turn = farkle_player.turn_score

        # Add turn score to permanent score
        farkle_player.score += farkle_player.turn_score
        farkle_player.has_banked = True

        # Sync to TeamManager for score actions
        self._team_manager.add_to_team_score(player.name, farkle_player.turn_score)

        self.play_sound(f"game_farkle/bank{random.randint(1, 3)}.ogg")

        self.broadcast_l(
            "farkle-banks",
            player=player.name,
            points=farkle_player.turn_score,
            total=farkle_player.score,
        )

        self._maybe_start_or_update_final_round(farkle_player)

        # Reset turn state
        farkle_player.turn_score = 0
        farkle_player.current_roll = []
        farkle_player.banked_dice = []
        farkle_player.has_taken_combo = False

        self.end_turn()

    def _action_check_turn_score(self, player: Player, action_id: str) -> None:
        """Handle check turn score action."""
        current = self.current_player
        if current:
            farkle_current: FarklePlayer = current  # type: ignore
            self.status_box(
                player,
                [
                    Localization.get(
                        "en",
                        "farkle-turn-score",
                        player=current.name,
                        points=farkle_current.turn_score,
                    )
                ],
            )
        else:
            self.status_box(
                player, [Localization.get("en", "farkle-no-turn")]
            )

    def _maybe_start_or_update_final_round(self, player: FarklePlayer) -> None:
        """Track the current score to beat once someone reaches the target."""
        if player.score < self.options.target_score:
            return

        if self.final_round_score is None or player.score > self.final_round_score:
            self.final_round_score = player.score
            self.final_round_leader_id = player.id
            active_ids = {p.id for p in self.get_active_players()}
            self.final_round_pending = active_ids - {player.id}

    def _try_finish_final_round(self) -> bool:
        """Return True if the game ends due to final-round completion."""
        if self.final_round_score is None or self.final_round_leader_id is None:
            return False
        if self.final_round_pending:
            return False

        winner = next(
            (
                p
                for p in self.get_active_players()
                if p.id == self.final_round_leader_id
            ),
            None,
        )
        if not winner:
            self.finish_game()
            return True

        self.play_sound("game_pig/win.ogg")
        winner_farkle: FarklePlayer = winner  # type: ignore
        self.broadcast_l(
            "farkle-winner", player=winner.name, score=winner_farkle.score
        )
        self.finish_game()
        return True

    def on_start(self) -> None:
        """Called when the game starts."""
        self.status = "playing"
        self.game_active = True
        self.round = 0
        self.final_round_score = None
        self.final_round_leader_id = None
        self.final_round_pending = set()

        # Initialize turn order
        active_players = self.get_active_players()
        starting_player = self._determine_starting_player(active_players)
        start_index = active_players.index(starting_player)
        turn_order = active_players[start_index:] + active_players[:start_index]
        self.set_turn_players(turn_order)
        self.broadcast_l("farkle-start-first-player", player=starting_player.name)

        # Set up TeamManager for score tracking (individual mode)
        self._team_manager.team_mode = "individual"
        self._team_manager.setup_teams([p.name for p in active_players])

        # Reset all player state
        for p in active_players:
            farkle_p: FarklePlayer = p  # type: ignore
            farkle_p.score = 0
            farkle_p.turn_score = 0
            farkle_p.current_roll = []
            farkle_p.banked_dice = []
            farkle_p.has_taken_combo = False
            farkle_p.has_banked = False

        # Play intro music (using pig music as placeholder)
        self.play_music("game_pig/mus.ogg")

        # Start first round
        self._start_round()

    def _start_round(self) -> None:
        """Start a new round."""
        self.round += 1

        # Refresh turn order
        active_players = self.get_active_players()
        if self.turn_players:
            ordered = [p for p in self.turn_players if p in active_players]
            for p in active_players:
                if p not in ordered:
                    ordered.append(p)
            self.set_turn_players(ordered)
        else:
            self.set_turn_players(active_players)

        self.broadcast_l("game-round-start", round=self.round)

        self._start_turn()

    def _start_turn(self) -> None:
        """Start a player's turn."""
        player = self.current_player
        if not player:
            return

        farkle_player: FarklePlayer = player  # type: ignore

        # Reset turn state
        farkle_player.turn_score = 0
        farkle_player.current_roll = []
        farkle_player.banked_dice = []
        farkle_player.has_taken_combo = False

        # Announce turn
        self.announce_turn()

        # Set up bot if needed
        if player.is_bot:
            BotHelper.set_target(player, 0)  # Bot will calculate during think

        # Rebuild menus
        self.rebuild_all_menus()

    def _determine_starting_player(
        self, players: list[FarklePlayer]
    ) -> FarklePlayer:
        """Roll to determine the first player, with tie rerolls."""
        contenders = list(players)
        while True:
            rolls = {}
            for player in contenders:
                roll = random.randint(1, 6)
                rolls[player.id] = roll
                self.broadcast_l("farkle-start-roll", player=player.name, roll=roll)

            high_roll = max(rolls.values())
            top_players = [p for p in contenders if rolls[p.id] == high_roll]
            if len(top_players) == 1:
                return top_players[0]

            self.broadcast_l("farkle-start-roll-tie")
            contenders = top_players

    def on_tick(self) -> None:
        """Called every tick. Handle bot AI and scheduled sounds."""
        super().on_tick()
        self.process_scheduled_sounds()

        if not self.game_active:
            return

        BotHelper.on_tick(self)

    def bot_think(self, player: FarklePlayer) -> str | None:
        """Bot AI decision making."""
        turn_set = self.get_action_set(player, "turn")
        if not turn_set:
            return None

        # Resolve actions to get enabled state
        resolved = turn_set.resolve_actions(self, player)

        # Take highest-value scoring combo first
        for ra in resolved:
            if ra.enabled and ra.action.id.startswith("score_"):
                return ra.action.id

        # Check roll/bank enabled state
        roll_enabled = self._is_roll_enabled(player) is None
        bank_enabled = self._is_bank_enabled(player) is None

        if roll_enabled:
            # Banking decision based on dice remaining and points
            dice_remaining = 6 - len(player.banked_dice)
            if dice_remaining == 0:
                dice_remaining = 6  # Hot dice

            score_to_beat = self.final_round_score
            potential_total = player.score + player.turn_score

            # If a final round is active, must beat the current leader
            if score_to_beat is not None and potential_total <= score_to_beat:
                return "roll"

            # Banking decision based on turn score and dice remaining
            bank_threshold = max(350, self.options.min_bank_points)
            if player.turn_score >= bank_threshold:
                # Bank probability increases as fewer dice remain
                bank_probabilities = {
                    6: 0.40,
                    5: 0.50,
                    4: 0.55,
                    3: 0.65,
                    2: 0.70,
                    1: 0.75,
                }
                bank_prob = bank_probabilities.get(dice_remaining, 0.50)

                if random.random() < bank_prob:
                    if bank_enabled:
                        return "bank"

            return "roll"

        if bank_enabled:
            return "bank"

        return None

    def _on_turn_end(self) -> None:
        """Handle end of a player's turn."""
        current = self.current_player
        if self.final_round_score is not None:
            active_ids = {p.id for p in self.get_active_players()}
            self.final_round_pending.intersection_update(active_ids)
            if current and current.id in self.final_round_pending:
                self.final_round_pending.remove(current.id)
        if self._try_finish_final_round():
            return

        # Check if round is over
        if self.turn_index >= len(self.turn_players) - 1:
            self._on_round_end()
        else:
            self.advance_turn(announce=False)
            self._start_turn()

    def _on_round_end(self) -> None:
        """Handle end of a round."""
        self._start_round()

    def build_game_result(self) -> GameResult:
        """Build the game result with Farkle-specific data."""
        sorted_players = sorted(
            self.get_active_players(),
            key=lambda p: p.score,  # type: ignore
            reverse=True,
        )

        # Build final scores and per-player stats
        final_scores = {}
        player_stats = {}
        for p in sorted_players:
            farkle_p: FarklePlayer = p  # type: ignore
            final_scores[p.name] = farkle_p.score
            player_stats[p.name] = {
                "turns_taken": farkle_p.turns_taken,
                "best_turn": farkle_p.best_turn,
                "total_score": farkle_p.score,
            }

        winner = sorted_players[0] if sorted_players else None
        winner_farkle: FarklePlayer = winner  # type: ignore

        return GameResult(
            game_type=self.get_type(),
            timestamp=datetime.now().isoformat(),
            duration_ticks=self.sound_scheduler_tick,
            player_results=[
                PlayerResult(
                    player_id=p.id,
                    player_name=p.name,
                    is_bot=p.is_bot,
                )
                for p in self.get_active_players()
            ],
            custom_data={
                "winner_name": winner.name if winner else None,
                "winner_score": winner_farkle.score if winner_farkle else 0,
                "final_scores": final_scores,
                "player_stats": player_stats,
                "rounds_played": self.round,
                "target_score": self.options.target_score,
                "min_bank_points": self.options.min_bank_points,
            },
        )

    def format_end_screen(self, result: GameResult, locale: str) -> list[str]:
        """Format the end screen for Farkle game."""
        lines = [Localization.get(locale, "game-final-scores")]

        final_scores = result.custom_data.get("final_scores", {})
        for i, (name, score) in enumerate(final_scores.items(), 1):
            points_str = Localization.get(locale, "game-points", count=score)
            lines.append(f"{i}. {name}: {points_str}")

        return lines

    def end_turn(self, jolt_min: int = 20, jolt_max: int = 30) -> None:
        """End the current player's turn."""
        BotHelper.jolt_bots(self, ticks=random.randint(jolt_min, jolt_max))
        self._on_turn_end()

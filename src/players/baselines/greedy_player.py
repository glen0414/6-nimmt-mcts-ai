def _card_score(card):
    if card % 55 == 0:
        return 7
    if card % 11 == 0:
        return 5
    if card % 10 == 0:
        return 3
    if card % 5 == 0:
        return 2
    return 1


class GreedyPlayer:
    """One-step greedy baseline: plays the card with the lowest immediate
    penalty, assuming no other player's card lands before it. Ties are broken
    by preferring the card that fits most tightly onto a row end."""

    def __init__(self, player_idx):
        self.player_idx = player_idx

    def action(self, hand, history):
        board = history["board"]
        best_key, best_card = None, hand[0]
        for card in hand:
            target, gap = -1, 999
            for i, row in enumerate(board):
                if row[-1] < card and card - row[-1] < gap:
                    target, gap = i, card - row[-1]
            if target == -1:
                penalty = min(sum(_card_score(c) for c in row) for row in board)
            elif len(board[target]) >= 5:
                penalty = sum(_card_score(c) for c in board[target])
            else:
                penalty = 0
            key = (penalty, gap)
            if best_key is None or key < best_key:
                best_key, best_card = key, card
        return best_card

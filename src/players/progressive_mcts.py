import time
import random
import math
import bisect

_BULLHEADS = [0] * 105
for i in range(1, 105):
    if i == 55: _BULLHEADS[i] = 7
    elif i % 11 == 0: _BULLHEADS[i] = 5
    elif i % 10 == 0: _BULLHEADS[i] = 3
    elif i % 10 == 5: _BULLHEADS[i] = 2
    else: _BULLHEADS[i] = 1
_BULLHEADS = tuple(_BULLHEADS)

def fast_process_placement(board_state, card):
    best_row_idx = -1
    max_val_under_card = -1
    
    for r_idx, row in enumerate(board_state):
        last = row[-1]
        if last < card and last > max_val_under_card:
            best_row_idx = r_idx
            max_val_under_card = last
            
    if best_row_idx != -1:
        chosen_row = board_state[best_row_idx]
        if len(chosen_row) >= 5:
            score = sum(_BULLHEADS[c] for c in chosen_row)
            new_row = [card]
        else:
            score = 0
            new_row = chosen_row + [card]
            
        new_board = list(board_state)
        new_board[best_row_idx] = new_row
        return new_board, score
    else:
        chosen_r_idx = 0
        min_score = 999
        min_len = 999
        for i, row in enumerate(board_state):
            rs = sum(_BULLHEADS[c] for c in row)
            rl = len(row)
            if rs < min_score or (rs == min_score and rl < min_len):
                min_score = rs
                min_len = rl
                chosen_r_idx = i
                
        score = min_score
        new_board = list(board_state)
        new_board[chosen_r_idx] = [card]
        return new_board, score

def fast_engine(board_state, cards_played):
    cur_board = board_state
    indexed_cards = sorted(enumerate(cards_played), key=lambda x: x[1])
    scores = [0] * len(cards_played)
    for original_idx, card in indexed_cards:
        cur_board, s = fast_process_placement(cur_board, card)
        scores[original_idx] = s
    return cur_board, scores

def get_robust_rollout_card(board, hand, row_ends, row_scores):
    """
    Unbiased Robust Rollout:
    - 10% Epsilon-Greedy to model high-entropy chaos/mistakes.
    - Random safe choice to eliminate the bias of always playing the smallest safe card.
    """
    if len(hand) == 1: return hand[0]
    
    if random.random() < 0.10:
        return hand[random.randint(0, len(hand) - 1)]
        
    safe_count = 0
    safe_choices = [0] * len(hand)
    
    best_card = hand[0]
    best_score = 999999
    min_score = min(row_scores)
    
    for c in hand:
        best_r = -1
        max_val = -1
        
        r_end = row_ends[0]
        if r_end < c and r_end > max_val: max_val = r_end; best_r = 0
        r_end = row_ends[1]
        if r_end < c and r_end > max_val: max_val = r_end; best_r = 1
        r_end = row_ends[2]
        if r_end < c and r_end > max_val: max_val = r_end; best_r = 2
        r_end = row_ends[3]
        if r_end < c and r_end > max_val: max_val = r_end; best_r = 3
        
        if best_r != -1:
            if len(board[best_r]) < 5:
                safe_choices[safe_count] = c
                safe_count += 1
            else:
                score = row_scores[best_r]
                if score < best_score:
                    best_score = score
                    best_card = c
        else:
            score = min_score
            if score < best_score:
                best_score = score
                best_card = c
                
    if safe_count > 0:
        return safe_choices[random.randint(0, safe_count - 1)]
        
    return best_card

_COMB_CACHE = {}
def fast_comb(n, k):
    if k < 0 or k > n: return 0
    if k == 0 or k == n: return 1
    if k > n - k: k = n - k
    key = (n, k)
    if key in _COMB_CACHE: return _COMB_CACHE[key]
    _COMB_CACHE[key] = math.comb(n, k)
    return _COMB_CACHE[key]

_PROB_CACHE = {}
def get_hypergeometric_tail(capacity, K, U, O):
    if K < capacity: return 0.0
    if O <= 0 or U <= 0: return 0.0
    if O < capacity: return 0.0
    
    key = (capacity, K, U, O)
    if key in _PROB_CACHE: return _PROB_CACHE[key]
    
    prob = 0.0
    for i in range(capacity, min(K, O) + 1):
        ways = fast_comb(K, i) * fast_comb(U - K, O - i)
        prob += ways
        
    total_ways = fast_comb(U, O)
    if total_ways > 0:
        prob /= total_ways
    else:
        prob = 0.0
        
    _PROB_CACHE[key] = prob
    return prob

def evaluate_card_danger_fast(board, card, sorted_unknowns, opponents_hand_size, row_ends, row_scores):
    best_row_idx = -1
    max_val_under_card = -1
    
    r_end = row_ends[0]
    if r_end < card and r_end > max_val_under_card: max_val_under_card = r_end; best_row_idx = 0
    r_end = row_ends[1]
    if r_end < card and r_end > max_val_under_card: max_val_under_card = r_end; best_row_idx = 1
    r_end = row_ends[2]
    if r_end < card and r_end > max_val_under_card: max_val_under_card = r_end; best_row_idx = 2
    r_end = row_ends[3]
    if r_end < card and r_end > max_val_under_card: max_val_under_card = r_end; best_row_idx = 3
            
    if best_row_idx == -1:
        min_score = 999
        min_len = 999
        for i in range(4):
            rs = row_scores[i]
            rl = len(board[i])
            if rs < min_score or (rs == min_score and rl < min_len):
                min_score = rs
                min_len = rl
        return float(min_score) * 0.9 if min_score <= 2 else float(min_score)
        
    capacity = 5 - len(board[best_row_idx])
    
    idx_high = bisect.bisect_left(sorted_unknowns, card)
    idx_low = bisect.bisect_right(sorted_unknowns, max_val_under_card)
    gap_count = max(0, idx_high - idx_low)
    
    prob = get_hypergeometric_tail(capacity, gap_count, len(sorted_unknowns), opponents_hand_size)
    row_penalty = row_scores[best_row_idx]
    return prob * row_penalty

def get_analytical_card_fast(board, hand, sorted_unknowns, opponents_hand_size):
    if len(hand) == 1: return hand[0]
    
    best_card = hand[0]
    min_danger = 999999.0
    best_gap = 999
    
    row_ends = [r[-1] for r in board]
    row_scores = [sum(_BULLHEADS[x] for x in r) for r in board]
    
    for c in hand:
        max_val_under_card = -1
        target_r = -1
        r_end = row_ends[0]
        if r_end < c and r_end > max_val_under_card: max_val_under_card = r_end; target_r = 0
        r_end = row_ends[1]
        if r_end < c and r_end > max_val_under_card: max_val_under_card = r_end; target_r = 1
        r_end = row_ends[2]
        if r_end < c and r_end > max_val_under_card: max_val_under_card = r_end; target_r = 2
        r_end = row_ends[3]
        if r_end < c and r_end > max_val_under_card: max_val_under_card = r_end; target_r = 3
                
        gap = c - max_val_under_card if max_val_under_card != -1 else 999
        row_len = len(board[target_r]) + 1 if target_r != -1 else 0
        
        danger = evaluate_card_danger_fast(board, c, sorted_unknowns, opponents_hand_size, row_ends, row_scores)
        
        if row_len == 5 and danger < 0.2:
            row_bullheads = row_scores[target_r]
            reward = 0.1 + (row_bullheads * 0.05)
            danger -= reward
        
        if danger < min_danger - 0.001:
            min_danger = danger
            best_card = c
            best_gap = gap
        elif abs(danger - min_danger) <= 0.001:
            if gap < best_gap:
                best_gap = gap
                best_card = c
                    
    return best_card

def calculate_unknown_cards(my_hand, history_state, n_cards=104):
    seen = set(my_hand)
    if history_state.get('board_history'):
        for row in history_state['board_history'][0]:
            for c in row: seen.add(c)
    for round_actions in history_state.get('history_matrix', []):
        for c in round_actions:
            if c != 0: seen.add(c)
    return [c for c in range(1, n_cards + 1) if c not in seen]

class ISMCTS_Node:
    def __init__(self, actions):
        self.visits = 0
        self.stats = {a: [0.0, 0] for a in actions}
        self.children = {}

class ProgressiveMCTSPlayer:
    """
    Dynamic Deep ISMCTS.
    Replaces the hardcoded Depth-2 truncation with a seamless 'Progressive Expansion' tree.
    In the early game, it probes promising paths deeply. In the endgame (<= 5 cards), 
    the tree dynamically grows to the bottom, completely solving the remaining game 
    without relying on chaotic rollout noise.
    """
    def __init__(self, player_idx):
        self.player_idx = player_idx

    def deduce_impossible_mask(self, history, unknown_cards, num_others):
        mask = [[False] * 105 for _ in range(num_others)]
        cur_round = history["round"]
        if cur_round > 1 and history.get('history_matrix'):
            for r_idx in range(cur_round - 1):
                if history.get('board_history') and len(history['board_history']) > r_idx:
                    prev_board = history['board_history'][r_idx]
                    prev_actions = history['history_matrix'][r_idx]
                    row_ends = [r[-1] for r in prev_board]
                    
                    for p_idx, played_card in enumerate(prev_actions):
                        if p_idx == self.player_idx or played_card == 0:
                            continue
                        opp_rel_idx = p_idx if p_idx < self.player_idx else p_idx - 1
                        
                        if played_card < min(row_ends):
                            played_target_r = -1
                        else:
                            max_val = -1
                            played_target_r = -1
                            for i, r_end in enumerate(row_ends):
                                if r_end < played_card and r_end > max_val:
                                    max_val = r_end
                                    played_target_r = i
                                    
                        if played_target_r == -1 or len(prev_board[played_target_r]) >= 4:
                            for uc in unknown_cards:
                                if uc > min(row_ends):
                                    max_val = -1
                                    target_r = -1
                                    for i, r_end in enumerate(row_ends):
                                        if r_end < uc and r_end > max_val:
                                            max_val = r_end
                                            target_r = i
                                    
                                    if target_r != -1 and target_r != played_target_r:
                                        capacity = 5 - len(prev_board[target_r])
                                        gap = uc - max_val
                                        if capacity >= 2 and gap <= 3:
                                            mask[opp_rel_idx][uc] = True
        return mask

    def action(self, hand, history):
        start_time = time.time()
        time_limit = 0.85
        board = history["board"]
        
        unknown_cards = calculate_unknown_cards(hand, history)
        num_others = len(history['scores']) - 1
        cur_hand_size = len(hand)
        
        if cur_hand_size == 1:
            return hand[0]
            
        impossible_mask = self.deduce_impossible_mask(history, unknown_cards, num_others)
        sorted_unknowns = sorted(unknown_cards)
        
        root = ISMCTS_Node(hand)
        simulations = 0
        
        while time.time() - start_time < time_limit:
            if len(unknown_cards) < num_others * cur_hand_size:
                break
                
            can_simulate = False
            for _ in range(10):
                random.shuffle(unknown_cards)
                other_hands = []
                used = [False] * len(unknown_cards)
                valid = True
                
                for p in range(num_others):
                    hand_p = []
                    for idx, c in enumerate(unknown_cards):
                        if not used[idx] and not impossible_mask[p][c]:
                            hand_p.append(c)
                            used[idx] = True
                            if len(hand_p) == cur_hand_size:
                                break
                    if len(hand_p) < cur_hand_size:
                        valid = False
                        break
                    other_hands.append(hand_p)
                
                if valid:
                    can_simulate = True
                    break
                    
            if not can_simulate:
                random.shuffle(unknown_cards)
                other_hands = []
                ptr = 0
                for _ in range(num_others):
                    other_hands.append(unknown_cards[ptr:ptr+cur_hand_size])
                    ptr += cur_hand_size
            
            node = root
            path = []
            
            sim_board = board
            sim_my_hand = hand[:]
            total_penalty = 0.0
            
            in_tree = True
            
            for trick in range(cur_hand_size):
                # 1. Pre-calculate trick features (skipping Trick 1 since analytical evaluates directly)
                if trick > 0:
                    row_ends = [r[-1] for r in sim_board]
                    row_scores = [sum(_BULLHEADS[x] for x in r) for r in sim_board]
                else:
                    row_ends = None
                    row_scores = None
                    
                # 2. My Action Selection
                if in_tree:
                    best_ucb = 999999.0
                    a = sim_my_hand[0]
                    expanded = False
                    
                    for c in sim_my_hand:
                        stats = node.stats[c]
                        if stats[1] == 0:
                            a = c
                            expanded = True
                            break
                        avg = stats[0] / stats[1]
                        explore = 15.0 * math.sqrt(math.log(node.visits) / stats[1])
                        if avg - explore < best_ucb:
                            best_ucb = avg - explore
                            a = c
                            
                    path.append((node, a))
                    sim_my_hand.remove(a)
                    
                    if expanded:
                        in_tree = False
                    else:
                        if a not in node.children:
                            node.children[a] = ISMCTS_Node(sim_my_hand)
                        node = node.children[a]
                else:
                    a = get_robust_rollout_card(sim_board, sim_my_hand, row_ends, row_scores)
                    sim_my_hand.remove(a)
                    
                # 3. Opponents' Actions
                opp_cards = []
                if trick == 0:
                    opp_hand_size = num_others * (cur_hand_size - 1)
                    for oh in other_hands:
                        c = get_analytical_card_fast(sim_board, oh, sorted_unknowns, opp_hand_size)
                        opp_cards.append(c)
                        oh.remove(c)
                else:
                    for oh in other_hands:
                        c = get_robust_rollout_card(sim_board, oh, row_ends, row_scores)
                        opp_cards.append(c)
                        oh.remove(c)
                        
                # 4. Engine Transition
                cs_played = opp_cards + [a]
                sim_board, slist = fast_engine(sim_board, cs_played)
                total_penalty += slist[-1]
                
            # --- Backpropagation ---
            for n, a in path:
                n.visits += 1
                n.stats[a][0] += total_penalty
                n.stats[a][1] += 1
                
            simulations += 1
            
        # Select best action based on lowest average penalty at root
        best_card = hand[0]
        min_avg = 999999.0
        for c in hand:
            if root.stats[c][1] > 0:
                avg = root.stats[c][0] / root.stats[c][1]
                if avg < min_avg:
                    min_avg = avg
                    best_card = c
        
        if root.stats[best_card][1] == 0:
            opponents_hand_size = num_others * len(hand)
            return get_analytical_card_fast(board, hand, sorted_unknowns, opponents_hand_size)
            
        return best_card

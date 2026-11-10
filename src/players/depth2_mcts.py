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

def sum_bullheads(row):
    l = len(row)
    if l == 1: return _BULLHEADS[row[0]]
    if l == 2: return _BULLHEADS[row[0]] + _BULLHEADS[row[1]]
    if l == 3: return _BULLHEADS[row[0]] + _BULLHEADS[row[1]] + _BULLHEADS[row[2]]
    if l == 4: return _BULLHEADS[row[0]] + _BULLHEADS[row[1]] + _BULLHEADS[row[2]] + _BULLHEADS[row[3]]
    return _BULLHEADS[row[0]] + _BULLHEADS[row[1]] + _BULLHEADS[row[2]] + _BULLHEADS[row[3]] + _BULLHEADS[row[4]]

def new_process_placement(board_state, card):
    best_row_idx = -1
    max_val_under_card = -1
    for r_idx in range(4):
        row = board_state[r_idx]
        last = row[-1]
        if last < card and last > max_val_under_card:
            best_row_idx = r_idx
            max_val_under_card = last
            
    if best_row_idx != -1:
        chosen_row = board_state[best_row_idx]
        l_row = len(chosen_row)
        if l_row >= 5:
            score = _BULLHEADS[chosen_row[0]] + _BULLHEADS[chosen_row[1]] + _BULLHEADS[chosen_row[2]] + _BULLHEADS[chosen_row[3]] + _BULLHEADS[chosen_row[4]]
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
        for i in range(4):
            row = board_state[i]
            l = len(row)
            if l == 1: rs = _BULLHEADS[row[0]]
            elif l == 2: rs = _BULLHEADS[row[0]] + _BULLHEADS[row[1]]
            elif l == 3: rs = _BULLHEADS[row[0]] + _BULLHEADS[row[1]] + _BULLHEADS[row[2]]
            elif l == 4: rs = _BULLHEADS[row[0]] + _BULLHEADS[row[1]] + _BULLHEADS[row[2]] + _BULLHEADS[row[3]]
            else: rs = _BULLHEADS[row[0]] + _BULLHEADS[row[1]] + _BULLHEADS[row[2]] + _BULLHEADS[row[3]] + _BULLHEADS[row[4]]
            
            if rs < min_score or (rs == min_score and l < min_len):
                min_score = rs
                min_len = l
                chosen_r_idx = i
                
        score = min_score
        new_board = list(board_state)
        new_board[chosen_r_idx] = [card]
        return new_board, score

def fast_engine_my_score(board_state, opp_cards, my_card):
    cards_played = opp_cards.copy()
    cards_played.append(my_card)
    sorted_cards = sorted(cards_played)
    
    cur_board = board_state
    my_score = 0
    for card in sorted_cards:
        cur_board, s = new_process_placement(cur_board, card)
        if card == my_card:
            my_score = s
    return cur_board, my_score

def get_robust_rollout_card(board, hand, row_ends, row_scores):
    """
    Unbiased Robust Rollout:
    - 10% Epsilon-Greedy to model high-entropy chaos/mistakes.
    - Random safe choice to eliminate the bias of always playing the smallest safe card.
    - Zero list allocations using pre-allocated arrays.
    """
    if len(hand) == 1: return hand[0]
    
    if random.random() < 0.10:
        return hand[int(random.random() * len(hand))]
        
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
        return safe_choices[int(random.random() * safe_count)]
        
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
    row_scores = [sum_bullheads(r) for r in board]
    
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
    def __init__(self, actions=None):
        self.visits = 0
        self.stats = {}  # Lazy instantiation: {action: [total_score, visits]}
        self.children = {}

class Depth2MCTSPlayer:
    """
    Unbiased Robust Depth-2 ISMCTS - Combined Ultimate Agent.
    - Uses an unbiased rollout strategy to model the full 
      stochastic range of competitive opponents.
      (Random safe choice + Epsilon-Greedy, matching UCB exploration constant 15.0).
    - Incorporates all low-level Python speedups:
      * Lazy node statistics instantiation.
      * Non-intrusive pre-check bypass for impossible rules.
      * Rate-limited time checking (every 20 simulations).
      * Zero-allocation pre-allocated arrays in get_robust_rollout_card.
    - Runs up to 3500 simulations under 0.75s time limit safely.
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
        time_limit = 0.75
        board = history["board"]
        
        unknown_cards = calculate_unknown_cards(hand, history)
        num_others = len(history['scores']) - 1
        cur_hand_size = len(hand)
        
        if cur_hand_size == 1:
            return hand[0]
            
        impossible_mask = self.deduce_impossible_mask(history, unknown_cards, num_others)
        has_impossible_rules = False
        for row in impossible_mask:
            if any(row):
                has_impossible_rules = True
                break
                
        sorted_unknowns = sorted(unknown_cards)
        
        root = ISMCTS_Node()
        simulations = 0
        
        while simulations < 3500:
            if simulations % 20 == 0:
                if time.time() - start_time > time_limit:
                    break
            if len(unknown_cards) < num_others * cur_hand_size:
                break
                
            other_hands = []
            if has_impossible_rules:
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
            else:
                random.shuffle(unknown_cards)
                ptr = 0
                for _ in range(num_others):
                    other_hands.append(unknown_cards[ptr:ptr+cur_hand_size])
                    ptr += cur_hand_size
            
            node = root
            path = []
            
            sim_board = board
            sim_my_hand = hand[:]
            
            # --- Depth 1 Selection (Zero Allocation) ---
            best_ucb = 999999.0
            a1 = sim_my_hand[0]
            for c in sim_my_hand:
                stats = node.stats.get(c)
                if stats is None:
                    a1 = c
                    break
                avg = stats[0] / stats[1]
                explore = 15.0 * math.sqrt(math.log(node.visits) / stats[1])
                if avg - explore < best_ucb:
                    best_ucb = avg - explore
                    a1 = c
            
            path.append((node, a1))
            sim_my_hand.remove(a1)
            
            # --- Depth 1 Transition ---
            opp_cards = [0] * num_others
            opp_hand_size = num_others * len(sim_my_hand)
            for idx in range(num_others):
                oh = other_hands[idx]
                c = get_analytical_card_fast(sim_board, oh, sorted_unknowns, opp_hand_size)
                opp_cards[idx] = c
                oh.remove(c)
                
            sim_board, total_penalty = fast_engine_my_score(sim_board, opp_cards, a1)
            
            # --- Depth 2 Selection (Zero Allocation) ---
            if len(sim_my_hand) > 0:
                if a1 not in node.children:
                    node.children[a1] = ISMCTS_Node()
                child_node = node.children[a1]
                
                best_ucb2 = 999999.0
                a2 = sim_my_hand[0]
                for c in sim_my_hand:
                    stats = child_node.stats.get(c)
                    if stats is None:
                        a2 = c
                        break
                    avg = stats[0] / stats[1]
                    explore = 15.0 * math.sqrt(math.log(child_node.visits) / stats[1])
                    if avg - explore < best_ucb2:
                        best_ucb2 = avg - explore
                        a2 = c
                            
                path.append((child_node, a2))
                sim_my_hand.remove(a2)
                
                # --- Depth 2 Transition ---
                row_ends = [sim_board[0][-1], sim_board[1][-1], sim_board[2][-1], sim_board[3][-1]]
                row_scores = [
                    sum_bullheads(sim_board[0]),
                    sum_bullheads(sim_board[1]),
                    sum_bullheads(sim_board[2]),
                    sum_bullheads(sim_board[3])
                ]
                
                opp_cards2 = [0] * num_others
                for idx in range(num_others):
                    oh = other_hands[idx]
                    c = get_robust_rollout_card(sim_board, oh, row_ends, row_scores)
                    opp_cards2[idx] = c
                    oh.remove(c)
                    
                sim_board, my_score2 = fast_engine_my_score(sim_board, opp_cards2, a2)
                total_penalty += my_score2
                
                # --- Deep Rollout (Depth 3+) ---
                while len(sim_my_hand) > 0:
                    r_ends = [sim_board[0][-1], sim_board[1][-1], sim_board[2][-1], sim_board[3][-1]]
                    r_scores = [
                        sum_bullheads(sim_board[0]),
                        sum_bullheads(sim_board[1]),
                        sum_bullheads(sim_board[2]),
                        sum_bullheads(sim_board[3])
                    ]
                    
                    my_c = get_robust_rollout_card(sim_board, sim_my_hand, r_ends, r_scores)
                    sim_my_hand.remove(my_c)
                    
                    opp_cs = [0] * num_others
                    for idx in range(num_others):
                        oh = other_hands[idx]
                        c = get_robust_rollout_card(sim_board, oh, r_ends, r_scores)
                        opp_cs[idx] = c
                        oh.remove(c)
                        
                    sim_board, my_score3 = fast_engine_my_score(sim_board, opp_cs, my_c)
                    total_penalty += my_score3
                
            # --- Backpropagation ---
            for n, a in path:
                n.visits += 1
                if a not in n.stats:
                    n.stats[a] = [total_penalty, 1]
                else:
                    n.stats[a][0] += total_penalty
                    n.stats[a][1] += 1
                
            simulations += 1
            
        # Select best action based on lowest average penalty at root
        best_card = hand[0]
        min_avg = 999999.0
        for c in hand:
            stats = root.stats.get(c)
            if stats is not None and stats[1] > 0:
                avg = stats[0] / stats[1]
                if avg < min_avg:
                    min_avg = avg
                    best_card = c
        
        stats = root.stats.get(best_card)
        if stats is None or stats[1] == 0:
            opponents_hand_size = num_others * len(hand)
            return get_analytical_card_fast(board, hand, sorted_unknowns, opponents_hand_size)
            
        return best_card

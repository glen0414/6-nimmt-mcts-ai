# 6 Nimmt! AI — Information Set MCTS under a 1-Second Budget

![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![Dependencies](https://img.shields.io/badge/agent%20deps-stdlib%20only-brightgreen.svg)

Two game-playing agents for **6 Nimmt!** (*Take 6!*), a simultaneous-move, imperfect-information card game. Built for the final project of NTU *Foundations of Artificial Intelligence* (2026), where every student's agent competed in a shared tournament under a strict per-move time limit.

Both agents use **Information Set Monte Carlo Tree Search (ISMCTS)**. They differ in how deep they search:

| Agent | File | Idea | Role |
| --- | --- | --- | --- |
| **Depth-2 MCTS** | [`src/players/depth2_mcts.py`](src/players/depth2_mcts.py) | Tree cut at depth 2 to spend the budget on breadth, then unbiased rollouts | Robust "floor": hard to exploit in chaotic tables |
| **Progressive MCTS** | [`src/players/progressive_mcts.py`](src/players/progressive_mcts.py) | Tree grows freely and reaches the leaves in the late game (exact endgame solving) | Higher "ceiling" against rational opponents |

## Results

Official course tournament, run by the TAs with every submitted agent: **56 agents, 8,000 games**.

| Rank | Agent | Strategy | Avg. Rank ↓ | ELO | Timeout Rate |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **1** | `depth2_mcts` | Depth-2 robust ISMCTS | **2.05** | **1609** | **0.00%** |
| **2** | `progressive_mcts` | Progressive ISMCTS | **2.09** | **1598** | **0.00%** |
| 7 | `Baseline10` | TA analytical baseline | 2.18 | 1577 | 0.00% |

*Average rank is within 4-player games (1 = best, 4 = worst).*

## The Game (tournament setup)

- 104 cards, each worth 1–7 "bullheads" (penalty points). 4 rows on the board, **4 players**, **10 rounds**.
- Every round, all players pick a card **simultaneously**. Cards are then placed in ascending order, each onto the row whose last card is the highest one still below it.
- **6th card rule:** placing the 6th card in a row means you take the 5 cards already there as penalty.
- **Low card rule:** a card lower than every row's last card takes the row with the lowest score (ties: fewest cards, then lowest index).
- **Lowest total penalty wins.** Each move must return within **1 second**, single-threaded. Timing out or raising an exception means the engine plays your smallest card for you.

What makes it hard: the opponents' hands are hidden, everyone moves at once, and a Python agent gets only about 0.8 s per move.

## How the Agents Work

### Determinized search (ISMCTS)
In each simulation, the unseen cards are dealt at random to the opponents. Opponents are played by a cheap policy, our candidate cards are scored by UCB, and after the search the agent plays the card with the best average outcome.

### Opponent modeling
- **Rollout policy:** with 90% probability an opponent plays a random *safe* card (one that doesn't fill a row); otherwise it plays a random card. This keeps the rollouts unbiased instead of assuming perfect play.
- **Impossible-card mask:** if an opponent took a dangerous row when an obviously safe card was available, they almost certainly don't hold that kind of card. The mask removes those cards from future deals, so the sampled hands match what the opponent has shown.
- **Closed-form first ply:** at the root, the agent doesn't roll out opponents. It estimates how likely each row is to overflow with a hypergeometric tail, computed in O(1):

$$P(\text{explode}) = \sum_{i=\text{capacity}}^{\min(K, O)} \frac{\binom{K}{i}\binom{U-K}{O-i}}{\binom{U}{O}}$$

  where *capacity* is the room left in the row, *K* the number of unknown cards between the row's end and our card, *U* the total number of unknown cards, and *O* the opponents' hand size.

### Making Python fast enough
- **Zero-allocation rollouts:** fixed-size arrays are allocated once and reused, so the hot loop never creates lists for the garbage collector.
- **Rate-limited clock checks:** Depth-2 MCTS reads the clock only once every 20 simulations. It gets up to 3,500 simulations in a 0.75 s budget, with no timeouts in the official tournament.
- Lazily created node statistics, a cached `math.comb`, and a stripped-down engine used only for simulation.

### Trade-off between the two agents
**Depth-2 MCTS** makes no long-horizon rationality assumptions, so it stays robust in noisy, mixed tables. The cost is that it can be outplayed in multi-step endgame traps.

**Progressive MCTS** solves the late game exactly, which works well against rational, risk-averse opponents. It degrades when random players make its deep predictions wrong.

Full write-up, in Traditional Chinese: [docs/report.md](docs/report.md) ([PDF](docs/report.pdf)). In the report, *BestPlayer1* = Depth-2 MCTS and *BestPlayer2* = Progressive MCTS.

## Getting Started

```bash
git clone https://github.com/glen0414/6-nimmt-mcts-ai.git
cd 6-nimmt-mcts-ai
pip install -r requirements.txt   # Python 3.13; only the tournament runner needs packages
```

**Watch one game** (the two MCTS agents vs. greedy and random, with turn-by-turn logs):
```bash
python run_single_game.py --config configs/game/demo.json
```

**Play against the AI** (you type your card each round):
```bash
python run_single_game.py --config configs/game/play_vs_ai.json
```

**Run a small tournament** (every seating permutation, so the deal doesn't decide the result):
```bash
python run_tournament.py --config configs/tournament/benchmark.json
```

Results are saved as JSON under `results/`.

## Project Structure

```
6-nimmt-mcts-ai/
├── src/
│   ├── engine.py               # Game engine (course-provided)
│   ├── game_utils.py           # Player loading / config helpers (course-provided)
│   ├── tournament_runner.py    # Parallel tournament runner (course-provided)
│   └── players/
│       ├── depth2_mcts.py      # ★ Depth-2 robust ISMCTS
│       ├── progressive_mcts.py # ★ Progressive ISMCTS
│       └── baselines/          # random, greedy, and human (CLI) players
├── configs/                    # Game and tournament configs (JSON)
├── docs/                       # Project report (md + pdf)
├── run_single_game.py
└── run_tournament.py
```

### Writing your own agent
Any class with this interface can be added to a config:

```python
class MyPlayer:
    def __init__(self, player_idx): ...
    def action(self, hand, history) -> int:   # return a card from `hand`
        ...
```

`history` contains the current `board`, the `scores`, the `round`, and the past moves (`history_matrix`, `board_history`).

## Acknowledgements
- The game engine and tournament framework were provided by the NTU FAI 2026 course staff. The TA baseline agents are compiled binaries that belong to the course, so they are not included here.
- [johannbrehmer/rl-6-nimmt](https://github.com/johannbrehmer/rl-6-nimmt) helped guide the early design.

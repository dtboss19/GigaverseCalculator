# Gigaverse Combat Calculator

A strategic combat optimizer for [Gigaverse](https://gigaverse.io), a web browser-based dungeon crawler game. This tool fetches real-time game data via the Gigaverse API and calculates optimal move selections to maximize your chances of victory in dungeon encounters.

## About Gigaverse

Gigaverse is a browser-based RPG where players explore dungeons and engage in turn-based combat against enemies. The combat system follows a **rock-paper-scissors** style mechanic with three move types:

| Move | Beats | Loses To |
|------|-------|----------|
| ⚔️ Sword | Spell | Shield |
| 🛡️ Shield | Sword | Spell |
| ✨ Spell | Shield | Sword |

Each move has associated **attack** and **defense** stats, limited **charges**, and potential **cooldowns**. Players must strategically manage their resources while predicting enemy behavior to survive dungeon runs.

## Features

- **Real-time API Integration**: Fetches live game state including player/enemy health, shield, and stats
- **Move Value Calculation**: Computes expected value for each move based on:
  - Player and enemy attack/defense stats
  - Available move charges
  - Cooldown states
  - Current health/shield values
  - Enemy move patterns
- **Continuous Monitoring**: Auto-refreshes every 2 seconds to track combat progression
- **Game History Logging**: Records fight states and outcomes to `game_history.json`

## Prerequisites

- Python 3.7+
- A Gigaverse account with an active dungeon run
- Your Bearer token from the Gigaverse website

## Installation

1. Clone or download this repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```env
   GIGAVERSE_BEARER=your_bearer_token_here
   ```

## Getting Your Bearer Token

1. Open [gigaverse.io](https://gigaverse.io) in your browser and log in
2. Open **Developer Tools** (F12 or Right-click → Inspect)
3. Navigate to the **Network** tab
4. Perform any action in the game (or refresh the page)
5. Click on any API request to `gigaverse.io/api/`
6. In the **Headers** section, find the `Authorization` header
7. Copy the token value (everything after `Bearer `)

> ⚠️ **Security Note**: Keep your Bearer token private. Never share it or commit it to version control.

## Usage

Start an active dungeon run in Gigaverse, then run:

```bash
python gigaverse_calculator.py
```

The calculator will display:

```
Current Game State (Round 5):
Player Stats:
  Health: 14
  Shield: 6
  Sword ATK: 9, DEF: 0, Charges: 2/3
  Shield ATK: 0, DEF: 4, Charges: 3/3
  Spell ATK: 2, DEF: 2, Charges: 1/3

Enemy Stats:
  Name: Goblin_Warrior
  Health: 8
  Shield: 0
  Sword ATK: 5, DEF: 2
  Shield ATK: 3, DEF: 3
  Spell ATK: 4, DEF: 1

Expected value for each move:
  Sword: 12.50 (Charges left: 2)
  Shield: 8.33 (Charges left: 3)
  Spell: ON COOLDOWN (no charges left)

Best move: Sword
Expected value: 12.50

Press Ctrl+C to exit
```

## How It Works

### Move Value Calculation

The calculator evaluates each available move by computing its **expected value**:

1. **Counter Bonus**: If your move counters the enemy's likely move, you deal damage and may repair shield
2. **Counter Penalty**: If the enemy's move counters yours, you take damage
3. **Low HP Bonus**: Sword gets a bonus when enemy health is critically low
4. **Charge Scaling**: Move value scales based on remaining charges

### API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `/api/game/dungeon/state` | Current dungeon run state (players, enemies, combat stats) |
| `/api/user/me` | Player profile and base stats |

## Project Structure

```
gigaverse/
├── gigaverse_calculator.py   # Main calculator application
├── requirements.txt          # Python dependencies
├── .env                      # Bearer token (create this)
├── game_history.json         # Auto-generated combat log
└── gigaversedocs/            # Reference documentation (MHTML)
```

## Game History

Combat data is automatically saved to `game_history.json`, recording:
- Player and enemy stats per round
- Move history and outcomes
- Timestamps for analysis

This data can be used to analyze patterns and improve strategy over time.

## Disclaimer

This tool is for educational and personal use. Use responsibly and in accordance with Gigaverse's terms of service.

## License

MIT License - Feel free to modify and distribute.


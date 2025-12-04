import requests
import json
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import os
import time

load_dotenv()
BEARER_TOKEN = os.getenv("GIGAVERSE_BEARER")
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"} if BEARER_TOKEN else {}

class PlayerSkills:
    def __init__(self, 
                 sword_atk: int = 1,
                 sword_def: int = 1,
                 shield_atk: int = 1,
                 shield_def: int = 1,
                 spell_atk: int = 1,
                 spell_def: int = 1,
                 base_hp: int = 100,
                 base_armor: int = 50):
        self.sword_atk = sword_atk
        self.sword_def = sword_def
        self.shield_atk = shield_atk
        self.shield_def = shield_def
        self.spell_atk = spell_atk
        self.spell_def = spell_def
        self.base_hp = base_hp
        self.base_armor = base_armor

class EnemyStats:
    def __init__(self,
                 name: str,
                 move_pattern: List[int],
                 equipment_head_cid: int,
                 equipment_body_cid: int):
        self.name = name
        self.move_pattern = move_pattern
        self.equipment_head_cid = equipment_head_cid
        self.equipment_body_cid = equipment_body_cid
        
        # Calculate enemy's base stats from move pattern
        # The move pattern array represents [Sword ATK, Sword DEF, Shield ATK, Shield DEF, Spell ATK, Spell DEF]
        self.sword_atk = move_pattern[0]
        self.sword_def = move_pattern[1]
        self.shield_atk = move_pattern[2]
        self.shield_def = move_pattern[3]
        self.spell_atk = move_pattern[4]
        self.spell_def = move_pattern[5]

class FightState:
    def __init__(self,
                 enemy_id: int,
                 enemy_health: int,
                 player_health: int,
                 player_shield: int,
                 player_skills: PlayerSkills,
                 enemy_stats: Optional[EnemyStats] = None,
                 last_player_move: Optional[str] = None,
                 last_enemy_move: Optional[str] = None,
                 player_move_charges: Optional[Dict[str, int]] = None,
                 player_move_cooldowns: Optional[Dict[str, int]] = None,
                 enemy_move_charges: Optional[Dict[str, int]] = None,
                 enemy_move_cooldowns: Optional[Dict[str, int]] = None,
                 round_number: int = 0,
                 move_history: Optional[List[Dict[str, str]]] = None,  # Track sequence of moves
                 move_outcomes: Optional[List[Dict[str, int]]] = None,  # Track damage/healing outcomes
                 timestamp: Optional[float] = None):  # Track when move was made
        self.enemy_id = enemy_id
        self.enemy_health = enemy_health
        self.player_health = player_health
        self.player_shield = player_shield
        self.player_skills = player_skills
        self.enemy_stats = enemy_stats
        self.last_player_move = last_player_move
        self.last_enemy_move = last_enemy_move
        self.player_move_charges = player_move_charges or {"Sword": 3, "Shield": 3, "Spell": 3}
        self.player_move_cooldowns = player_move_cooldowns or {"Sword": 0, "Shield": 0, "Spell": 0}
        self.enemy_move_charges = enemy_move_charges or {"Sword": 3, "Shield": 3, "Spell": 3}
        self.enemy_move_cooldowns = enemy_move_cooldowns or {"Sword": 0, "Shield": 0, "Spell": 0}
        self.round_number = round_number
        self.move_history = move_history or []  # Initialize empty list for move history
        self.move_outcomes = move_outcomes or []  # Initialize empty list for move outcomes
        self.timestamp = timestamp or time.time()  # Current timestamp if not provided

    def to_dict(self) -> Dict:
        """Convert fight state to dictionary for saving"""
        return {
            "enemy_id": self.enemy_id,
            "enemy_health": self.enemy_health,
            "player_health": self.player_health,
            "player_shield": self.player_shield,
            "player_skills": {
                "sword_atk": self.player_skills.sword_atk,
                "sword_def": self.player_skills.sword_def,
                "shield_atk": self.player_skills.shield_atk,
                "shield_def": self.player_skills.shield_def,
                "spell_atk": self.player_skills.spell_atk,
                "spell_def": self.player_skills.spell_def,
                "base_hp": self.player_skills.base_hp,
                "base_armor": self.player_skills.base_armor
            },
            "enemy_stats": {
                "name": self.enemy_stats.name if self.enemy_stats else None,
                "move_pattern": self.enemy_stats.move_pattern if self.enemy_stats else None,
                "sword_atk": self.enemy_stats.sword_atk if self.enemy_stats else None,
                "sword_def": self.enemy_stats.sword_def if self.enemy_stats else None,
                "shield_atk": self.enemy_stats.shield_atk if self.enemy_stats else None,
                "shield_def": self.enemy_stats.shield_def if self.enemy_stats else None,
                "spell_atk": self.enemy_stats.spell_atk if self.enemy_stats else None,
                "spell_def": self.enemy_stats.spell_def if self.enemy_stats else None
            },
            "last_player_move": self.last_player_move,
            "last_enemy_move": self.last_enemy_move,
            "player_move_charges": self.player_move_charges,
            "player_move_cooldowns": self.player_move_cooldowns,
            "enemy_move_charges": self.enemy_move_charges,
            "enemy_move_cooldowns": self.enemy_move_cooldowns,
            "round_number": self.round_number,
            "move_history": self.move_history,
            "move_outcomes": self.move_outcomes,
            "timestamp": self.timestamp
        }

class GigaverseCalculator:
    def __init__(self):
        self.enemies = self._fetch_enemies()
        self.move_counter = {
            "Sword": "Spell",
            "Spell": "Shield",
            "Shield": "Sword"
        }
        self.move_counter_reverse = {v: k for k, v in self.move_counter.items()}

    def _fetch_enemies(self) -> Dict:
        """Fetch enemy data from the API"""
        response = requests.get("https://gigaverse.io/api/game/dungeon/state", headers=HEADERS)
        if response.status_code == 200:
            game_state = response.json()
            if not game_state or not game_state.get("data", {}).get("run"):
                return {"entities": []}
            
            run_data = game_state["data"]["run"]
            players = run_data["players"]
            enemy_data = next((p for p in players if not p["id"].startswith("0x")), None)
            
            if not enemy_data:
                return {"entities": []}
                
            return {
                "entities": [{
                    "ID_CID": run_data["_id"],
                    "NAME_CID": enemy_data["id"],
                    "MOVE_STATS_CID_array": [
                        enemy_data["rock"]["currentATK"], enemy_data["rock"]["currentDEF"],
                        enemy_data["paper"]["currentATK"], enemy_data["paper"]["currentDEF"],
                        enemy_data["scissor"]["currentATK"], enemy_data["scissor"]["currentDEF"]
                    ],
                    "EQUIPMENT_HEAD_CID": 0,
                    "EQUIPMENT_BODY_CID": 0
                }]
            }
        else:
            raise Exception(f"Failed to fetch enemy data: {response.status_code}")

    def fetch_player_state(self) -> PlayerSkills:
        response = requests.get("https://gigaverse.io/api/user/me", headers=HEADERS)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch player data: {response.status_code}")
        player_data = response.json()
        # Adjust these keys based on actual API response structure
        hp = player_data.get('hp', 16)
        arm = player_data.get('arm', 6)
        skills = player_data.get('skills', {})
        sword_atk = skills.get('sword_atk', 9)
        sword_def = skills.get('sword_def', 0)
        shield_atk = skills.get('shield_atk', 0)
        shield_def = skills.get('shield_def', 4)
        spell_atk = skills.get('spell_atk', 2)
        spell_def = skills.get('spell_def', 2)
        
        print(f"Player Skills from API:")
        print(f"Sword ATK: {sword_atk}, DEF: {sword_def}")
        print(f"Shield ATK: {shield_atk}, DEF: {shield_def}")
        print(f"Spell ATK: {spell_atk}, DEF: {spell_def}")
        
        return PlayerSkills(
            sword_atk=sword_atk,
            sword_def=sword_def,
            shield_atk=shield_atk,
            shield_def=shield_def,
            spell_atk=spell_atk,
            spell_def=spell_def,
            base_hp=hp,
            base_armor=arm
        )

    def fetch_enemy_state(self, enemy_id: int, enemy_hp: int = None, enemy_arm: int = None) -> EnemyStats:
        enemy = next(e for e in self.enemies['entities'] if e['ID_CID'] == str(enemy_id))
        # If you have a live endpoint for enemy HP/ARM, use it here
        enemy_stats = EnemyStats(
            name=enemy["NAME_CID"],
            move_pattern=enemy["MOVE_STATS_CID_array"],
            equipment_head_cid=enemy["EQUIPMENT_HEAD_CID"],
            equipment_body_cid=enemy["EQUIPMENT_BODY_CID"]
        )
        
        print(f"\nEnemy Stats from API:")
        print(f"Name: {enemy_stats.name}")
        print(f"Sword ATK: {enemy_stats.sword_atk}, DEF: {enemy_stats.sword_def}")
        print(f"Shield ATK: {enemy_stats.shield_atk}, DEF: {enemy_stats.shield_def}")
        print(f"Spell ATK: {enemy_stats.spell_atk}, DEF: {enemy_stats.spell_def}")
        
        return enemy_stats

    def get_enemy_stats(self, enemy_id: int) -> Optional[EnemyStats]:
        """Get the stats for a specific enemy"""
        enemy = next((e for e in self.enemies["entities"] if e["ID_CID"] == str(enemy_id)), None)
        if enemy:
            return EnemyStats(
                name=enemy["NAME_CID"],
                move_pattern=enemy["MOVE_STATS_CID_array"],
                equipment_head_cid=enemy["EQUIPMENT_HEAD_CID"],
                equipment_body_cid=enemy["EQUIPMENT_BODY_CID"]
            )
        return None

    def calculate_best_move(self, fight_state: FightState) -> Tuple[str, float]:
        """
        Calculate the best move based on current game state
        
        Returns:
            Tuple[str, float]: (Best move, Expected value)
        """
        if not fight_state.enemy_stats:
            fight_state.enemy_stats = self.get_enemy_stats(fight_state.enemy_id)
            if not fight_state.enemy_stats:
                return "Unknown", 0.0

        # Calculate expected value for each move
        move_values = {
            "Sword": self._calculate_move_value("Sword", fight_state),
            "Shield": self._calculate_move_value("Shield", fight_state),
            "Spell": self._calculate_move_value("Spell", fight_state)
        }
        
        print(f"\nMove Values:")
        for move, value in move_values.items():
            print(f"{move}: {value:.2f}")

        # Find the move with highest expected value
        best_move = max(move_values.items(), key=lambda x: x[1])
        return best_move

    def _calculate_move_value(self, 
                            move: str, 
                            fight_state: FightState) -> float:
        """Calculate the expected value of a move"""
        value = 0.0
        
        # Check if move is on cooldown
        if fight_state.player_move_cooldowns[move] > 0:
            return float('-inf')  # Move is on cooldown
        
        # Check if move has charges left
        if fight_state.player_move_charges[move] <= 0:
            return float('-inf')  # No charges left
        
        # Get player's attack and defense stats for this move
        player_atk = getattr(fight_state.player_skills, f"{move.lower()}_atk")
        player_def = getattr(fight_state.player_skills, f"{move.lower()}_def")
        
        # Calculate probability of each enemy move based on pattern and cooldowns
        move_pattern = fight_state.enemy_stats.move_pattern
        total_moves = sum(move_pattern)
        move_probabilities = [m/total_moves for m in move_pattern]
        
        # For each possible enemy move
        move_types = ["Sword", "Shield", "Spell"]
        for i, prob in enumerate(move_probabilities):
            if i >= len(move_types):
                break
            enemy_move = move_types[i]
            
            # Skip if enemy move is on cooldown
            if fight_state.enemy_move_cooldowns[enemy_move] > 0:
                continue
            
            # Skip if enemy has no charges left
            if fight_state.enemy_move_charges[enemy_move] <= 0:
                continue
            
            # Get enemy's power for this move
            enemy_power = getattr(fight_state.enemy_stats, f"{enemy_move.lower()}_atk")
            
            # If our move counters enemy move
            if self.move_counter[move] == enemy_move:
                # Calculate damage dealt with attack stat and enemy defense
                base_damage = enemy_power
                damage_dealt = min(
                    fight_state.enemy_health,
                    base_damage * max(1, player_atk)
                )
                
                # Calculate shield repair with defense stat
                base_repair = enemy_power // 2
                shield_repair = min(
                    100 - fight_state.player_shield,
                    base_repair * max(1, player_def)
                )
                
                # Add value based on damage dealt and shield repair
                value += prob * (damage_dealt * 2 + shield_repair)  # Weight damage more heavily
            
            # If enemy move counters our move
            elif self.move_counter[enemy_move] == move:
                # Calculate damage taken with defense stat and enemy attack
                base_damage = enemy_power
                damage_taken = min(
                    fight_state.player_health,
                    base_damage // max(1, player_def)
                )
                value -= prob * damage_taken * 2  # Weight damage taken more heavily
        
        # Consider enemy's current HP in the calculation
        if fight_state.enemy_health <= 4:  # If enemy is low on HP
            # Prioritize moves that can finish off the enemy
            if move == "Sword" and player_atk > 0:
                value += 5  # Bonus for Sword when enemy is low HP
        
        # Consider remaining charges in the calculation
        value *= (fight_state.player_move_charges[move] / 3)  # Scale value based on remaining charges
        
        return value

    def update_fight_state(self, 
                          fight_state: FightState,
                          player_move: str,
                          enemy_move: str) -> FightState:
        """Update the fight state with new moves and calculate outcomes"""
        # Create new fight state with updated moves
        new_state = FightState(
            enemy_id=fight_state.enemy_id,
            enemy_health=fight_state.enemy_health,
            player_health=fight_state.player_health,
            player_shield=fight_state.player_shield,
            player_skills=fight_state.player_skills,
            enemy_stats=fight_state.enemy_stats,
            last_player_move=player_move,
            last_enemy_move=enemy_move,
            player_move_charges=fight_state.player_move_charges,
            player_move_cooldowns=fight_state.player_move_cooldowns,
            enemy_move_charges=fight_state.enemy_move_charges,
            enemy_move_cooldowns=fight_state.enemy_move_cooldowns,
            round_number=fight_state.round_number + 1,
            move_history=fight_state.move_history.copy() if fight_state.move_history else [],
            move_outcomes=fight_state.move_outcomes.copy() if fight_state.move_outcomes else [],
            timestamp=time.time()
        )

        # Calculate move outcomes
        player_damage = self._calculate_damage(player_move, enemy_move, fight_state)
        enemy_damage = self._calculate_damage(enemy_move, player_move, fight_state)

        # Update health based on outcomes
        new_state.enemy_health -= player_damage
        new_state.player_health -= enemy_damage

        # Record move history and outcomes
        new_state.move_history.append({
            "player_move": player_move,
            "enemy_move": enemy_move,
            "round": new_state.round_number
        })
        
        new_state.move_outcomes.append({
            "player_damage": player_damage,
            "enemy_damage": enemy_damage,
            "round": new_state.round_number
        })

        return new_state

    def _calculate_damage(self, attack_move: str, defense_move: str, state: FightState) -> int:
        """Calculate damage based on moves and stats"""
        # This is a simplified damage calculation - adjust based on your game's rules
        if attack_move == "Sword":
            attack_power = state.player_skills.sword_atk if state.last_player_move == attack_move else state.enemy_stats.sword_atk
            defense_power = state.player_skills.sword_def if state.last_enemy_move == defense_move else state.enemy_stats.sword_def
        elif attack_move == "Shield":
            attack_power = state.player_skills.shield_atk if state.last_player_move == attack_move else state.enemy_stats.shield_atk
            defense_power = state.player_skills.shield_def if state.last_enemy_move == defense_move else state.enemy_stats.shield_def
        else:  # Spell
            attack_power = state.player_skills.spell_atk if state.last_player_move == attack_move else state.enemy_stats.spell_atk
            defense_power = state.player_skills.spell_def if state.last_enemy_move == defense_move else state.enemy_stats.spell_def

        # Calculate final damage (simplified)
        damage = max(0, attack_power - defense_power)
        return damage

    def fetch_game_state(self):
        """Fetch the current dungeon state from the API and extract player and enemy info."""
        response = requests.get("https://gigaverse.io/api/game/dungeon/state", headers=HEADERS)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch game state: {response.status_code}")
        game_state = response.json()
        print("\nRaw game state response:")
        print(json.dumps(game_state, indent=2))
        return game_state

def main():
    calculator = GigaverseCalculator()
    
    # Load existing game history if it exists
    try:
        with open("game_history.json", "r") as f:
            game_history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        game_history = []
    
    def update_and_show_best_move():
        try:
            # Fetch current game state from API
            game_state = calculator.fetch_game_state()
            
            # Check if game is over (null state)
            if not game_state or not game_state.get("data", {}).get("run"):
                print("\nGame Over - Player has died or game has ended")
                # Append game history to file
                with open("game_history.json", "w") as f:
                    json.dump(game_history, f, indent=2)
                return False
            
            run_data = game_state["data"]["run"]
            players = run_data["players"]

            # Identify player and enemy
            player_data = next(p for p in players if p["id"].startswith("0x"))
            enemy_data = next(p for p in players if not p["id"].startswith("0x"))

            # Parse player stats
            player_hp = player_data["health"]["current"]
            player_shield = player_data["shield"]["current"]
            player_skills = PlayerSkills(
                sword_atk=player_data["rock"]["currentATK"],
                sword_def=player_data["rock"]["currentDEF"],
                shield_atk=player_data["paper"]["currentATK"],
                shield_def=player_data["paper"]["currentDEF"],
                spell_atk=player_data["scissor"]["currentATK"],
                spell_def=player_data["scissor"]["currentDEF"],
                base_hp=player_hp,
                base_armor=player_shield
            )

            # Parse move charges
            move_charges = {
                "Sword": player_data["rock"]["currentCharges"],
                "Shield": player_data["paper"]["currentCharges"],
                "Spell": player_data["scissor"]["currentCharges"]
            }
            move_max_charges = {
                "Sword": player_data["rock"]["maxCharges"],
                "Shield": player_data["paper"]["maxCharges"],
                "Spell": player_data["scissor"]["maxCharges"]
            }

            # Parse enemy stats
            enemy_hp = enemy_data["health"]["current"]
            enemy_shield = enemy_data["shield"]["current"]
            enemy_id = run_data["_id"]
            enemy_move_pattern = [
                enemy_data["rock"]["currentATK"], enemy_data["rock"]["currentDEF"],
                enemy_data["paper"]["currentATK"], enemy_data["paper"]["currentDEF"],
                enemy_data["scissor"]["currentATK"], enemy_data["scissor"]["currentDEF"]
            ]
            enemy_stats = EnemyStats(
                name=enemy_data["id"],
                move_pattern=enemy_move_pattern,
                equipment_head_cid=0,
                equipment_body_cid=0
            )

            last_move = player_data.get("lastMove", "")
            move_history = [last_move] * 3 if last_move else []

            fight_state = FightState(
                enemy_id=enemy_id,
                enemy_health=enemy_hp,
                player_health=player_hp,
                player_shield=player_shield,
                player_skills=player_skills,
                enemy_stats=enemy_stats,
                last_player_move=last_move,
                player_move_charges=move_charges,
                round_number=len(game_history)
            )

            # Save current state to history
            game_history.append(fight_state.to_dict())

            move_names = ["Sword", "Shield", "Spell"]
            move_values = {}
            for move in move_names:
                move_values[move] = calculator._calculate_move_value(move, fight_state)

            best_move = max(move_values.items(), key=lambda x: x[1])

            # Clear screen and print current state
            print("\033[H\033[J")  # Clear screen
            print(f"\nCurrent Game State (Round {fight_state.round_number}):")
            print(f"Player Stats:")
            print(f"  Health: {player_hp}")
            print(f"  Shield: {player_shield}")
            print(f"  Sword ATK: {player_skills.sword_atk}, DEF: {player_skills.sword_def}, Charges: {move_charges['Sword']}/{move_max_charges['Sword']}")
            print(f"  Shield ATK: {player_skills.shield_atk}, DEF: {player_skills.shield_def}, Charges: {move_charges['Shield']}/{move_max_charges['Shield']}")
            print(f"  Spell ATK: {player_skills.spell_atk}, DEF: {player_skills.spell_def}, Charges: {move_charges['Spell']}/{move_max_charges['Spell']}")
            print(f"\nEnemy Stats:")
            print(f"  Name: {enemy_stats.name}")
            print(f"  Health: {enemy_hp}")
            print(f"  Shield: {enemy_shield}")
            print(f"  Sword ATK: {enemy_stats.sword_atk}, DEF: {enemy_stats.sword_def}")
            print(f"  Shield ATK: {enemy_stats.shield_atk}, DEF: {enemy_stats.shield_def}")
            print(f"  Spell ATK: {enemy_stats.spell_atk}, DEF: {enemy_stats.spell_def}")
            print(f"\nExpected value for each move:")
            for move, value in move_values.items():
                if value == float('-inf'):
                    print(f"  {move}: ON COOLDOWN (no charges left)")
                else:
                    print(f"  {move}: {value:.2f} (Charges left: {move_charges[move]})")
            print(f"\nBest move: {best_move[0]}")
            print(f"Expected value: {best_move[1]:.2f}")
            print("\nPress Ctrl+C to exit")
            
            return True
            
        except Exception as e:
            print(f"Error updating game state: {e}")
            time.sleep(5)  # Wait before retrying
            return True

    try:
        while True:
            if not update_and_show_best_move():
                break
            time.sleep(2)  # Update every 2 seconds
    except KeyboardInterrupt:
        print("\nExiting...")
        # Append game history to file
        with open("game_history.json", "w") as f:
            json.dump(game_history, f, indent=2)

if __name__ == "__main__":
    main() 
"""Game process detection module."""
import psutil
from typing import List, Optional
import re


class GameDetector:
    """Detects and identifies running game processes."""
    
    def __init__(self):
        """Initialize game detector."""
        self.known_games = self._load_game_patterns()
    
    def _load_game_patterns(self) -> dict:
        """Load game title patterns for identification."""
        return {
            "valorant": ["valorant", "vanguard"],
            "league_of_legends": ["league", "lol", "leagueoflegends"],
            "cs2": ["cs2", "csgo", "counter-strike"],
            "dota2": ["dota 2", "dota2"],
            "overwatch": ["overwatch", "ow2"],
            "fortnite": ["fortnite"],
            "apex": ["apex", "apex legends"],
            "minecraft": ["minecraft"],
            "valorant": ["valorant"],
        }
    
    def get_running_games(self) -> List[str]:
        """
        Get list of likely game process names.
        
        Returns:
            List of game process names currently running
        """
        games = []
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                name = proc.info['name']
                if name:
                    name_lower = name.lower()
                    for game_name, patterns in self.known_games.items():
                        if any(p in name_lower for p in patterns):
                            if game_name not in games:
                                games.append(game_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return games
    
    def get_game_pid(self, game_name: str) -> Optional[int]:
        """
        Get PID of a specific game.
        
        Args:
            game_name: Name of the game to find
            
        Returns:
            Process ID if found, None otherwise
        """
        game_lower = game_name.lower()
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                proc_name = proc.info['name'].lower() if proc.info['name'] else ''
                if game_lower in proc_name:
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None
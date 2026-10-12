"""Deterministic generator for synthetic football player and match datasets.
Generates plausible, high-variance football data adhering to real tactical distributions.
"""

from pathlib import Path
import random
import csv
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Fixed seed for reproducibility
random.seed(42)

CLUBS = {
    "Premier League": [
        "Arsenal",
        "Manchester City",
        "Liverpool",
        "Chelsea",
        "Tottenham",
        "Aston Villa",
        "Newcastle United",
        "Brighton",
    ],
    "La Liga": [
        "Real Madrid",
        "Barcelona",
        "Atletico Madrid",
        "Real Sociedad",
        "Athletic Bilbao",
        "Girona",
        "Real Betis",
        "Villarreal",
    ],
}

NATIONALITIES = [
    "England", "Spain", "France", "Germany", "Brazil", "Argentina", "Portugal",
    "Netherlands", "Italy", "Belgium", "Norway", "Uruguay", "Croatia", "Japan",
    "Nigeria", "Senegal", "Denmark", "Scotland", "Poland", "Colombia"
]

FIRST_NAMES = [
    "Marcus", "Bukayo", "Declan", "Erling", "Kevin", "Phil", "Mohamed", "Virgil",
    "Cole", "Enzo", "Son", "James", "Ollie", "Douglas", "Alexander", "Bruno",
    "Jude", "Vinicius", "Rodrygo", "Lamine", "Pedri", "Gavi", "Robert", "Antoine",
    "Alvaro", "Mikel", "Martin", "Nico", "Inaki", "Savinho", "Artem", "Takefusa",
    "Lucas", "Mateo", "Gabriel", "William", "Alisson", "Ederson", "David", "Thibaut",
    "Jan", "Marc", "Unai", "Emiliano", "Guglielmo", "Jordan", "Federico", "Eduardo"
]

LAST_NAMES = [
    "Saka", "Rice", "Haaland", "De Bruyne", "Foden", "Salah", "Van Dijk", "Palmer",
    "Fernandez", "Heung-min", "Maddison", "Watkins", "Luiz", "Isak", "Guimaraes",
    "Bellingham", "Junior", "Goes", "Yamal", "Gonzalez", "Gavi", "Lewandowski",
    "Griezmann", "Morata", "Merino", "Zubimendi", "Williams", "Oyarzabal", "Dovbyk",
    "Kubo", "Paqueta", "Kovacic", "Magalhaes", "Saliba", "Becker", "Santana",
    "Raya", "Courtois", "Oblak", "Ter Stegen", "Simon", "Martinez", "Vicario",
    "Pickford", "Valverde", "Camavinga", "Tchouameni", "Alvarez"
]

POSITIONS = ["Goalkeeper", "Defender", "Midfielder", "Forward"]


def generate_players(count: int = 140):
    players = []
    used_names = set()

    player_id = 1
    # Distribute positions logically: ~15% GK, ~30% DF, ~35% MF, ~20% FW
    pos_targets = {
        "Goalkeeper": int(count * 0.15),
        "Defender": int(count * 0.30),
        "Midfielder": int(count * 0.35),
        "Forward": count - int(count * 0.15) - int(count * 0.30) - int(count * 0.35)
    }

    current_counts = {p: 0 for p in POSITIONS}

    for league, clubs in CLUBS.items():
        for club in clubs:
            # Generate 8-9 players per club across all 4 positions
            club_player_count = random.randint(8, 10)
            for _ in range(club_player_count):
                if player_id > count:
                    break

                # Pick position with remaining capacity
                avail_pos = [p for p in POSITIONS if current_counts[p] < pos_targets[p]]
                if not avail_pos:
                    avail_pos = POSITIONS
                pos = random.choice(avail_pos)
                current_counts[pos] += 1

                # Generate distinct name
                while True:
                    fn = random.choice(FIRST_NAMES)
                    ln = random.choice(LAST_NAMES)
                    name = f"{fn} {ln}"
                    if name not in used_names:
                        used_names.add(name)
                        break

                age = random.randint(18, 36)
                nat = random.choice(NATIONALITIES)
                season = "2023-2024"

                # Appearances and minutes
                apps = random.randint(12, 38)
                # Average 65-90 minutes per appearance
                avg_mins = random.uniform(60, 89)
                mins = int(min(apps * avg_mins, 3420))

                # Position-specific metric modeling
                if pos == "Goalkeeper":
                    goals = 0
                    assists = random.choice([0, 0, 0, 1])
                    shots = random.choice([0, 0, 1])
                    sot = 0
                    xg = 0.0
                    xa = round(random.uniform(0.0, 0.4), 2)
                    key_passes = random.randint(1, 8)
                    passes_att = random.randint(int(apps * 18), int(apps * 35))
                    passes_comp = int(passes_att * random.uniform(0.68, 0.88))
                    tackles = random.randint(0, 4)
                    interceptions = random.randint(0, 5)
                    yellow = random.randint(0, 3)
                    red = random.choice([0, 0, 0, 1]) if random.random() < 0.08 else 0
                    rating = round(random.uniform(6.4, 7.8), 2)

                elif pos == "Defender":
                    goals = random.randint(0, 4)
                    assists = random.randint(0, 6)
                    shots = random.randint(goals, goals + random.randint(8, 25))
                    sot = random.randint(goals, min(shots, goals + 12))
                    xg = round(goals * random.uniform(0.7, 1.25) + random.uniform(0.2, 1.5), 2)
                    xa = round(assists * random.uniform(0.6, 1.3) + random.uniform(0.3, 2.0), 2)
                    key_passes = random.randint(assists, assists + random.randint(5, 25))
                    passes_att = random.randint(int(apps * 45), int(apps * 75))
                    passes_comp = int(passes_att * random.uniform(0.80, 0.93))
                    tackles = random.randint(int(apps * 1.4), int(apps * 3.2))
                    interceptions = random.randint(int(apps * 1.1), int(apps * 2.8))
                    yellow = random.randint(1, 8)
                    red = 1 if random.random() < 0.15 else 0
                    rating = round(random.uniform(6.5, 8.1), 2)

                elif pos == "Midfielder":
                    goals = random.randint(1, 12)
                    assists = random.randint(2, 14)
                    shots = random.randint(goals + 10, goals + 45)
                    sot = random.randint(goals, min(shots, goals + 24))
                    xg = round(goals * random.uniform(0.8, 1.2) + random.uniform(0.5, 2.5), 2)
                    xa = round(assists * random.uniform(0.8, 1.3) + random.uniform(1.0, 3.5), 2)
                    key_passes = random.randint(assists + 10, assists + random.randint(25, 60))
                    passes_att = random.randint(int(apps * 50), int(apps * 85))
                    passes_comp = int(passes_att * random.uniform(0.82, 0.92))
                    tackles = random.randint(int(apps * 1.2), int(apps * 2.8))
                    interceptions = random.randint(int(apps * 0.8), int(apps * 2.1))
                    yellow = random.randint(1, 7)
                    red = 1 if random.random() < 0.10 else 0
                    rating = round(random.uniform(6.6, 8.5), 2)

                else:  # Forward
                    goals = random.randint(5, 29)
                    assists = random.randint(1, 12)
                    shots = random.randint(goals + 25, goals + 90)
                    sot = random.randint(goals + 5, min(shots, goals + 50))
                    xg = round(goals * random.uniform(0.85, 1.25) + random.uniform(0.8, 4.0), 2)
                    xa = round(assists * random.uniform(0.7, 1.3) + random.uniform(0.5, 3.0), 2)
                    key_passes = random.randint(assists + 5, assists + random.randint(15, 45))
                    passes_att = random.randint(int(apps * 18), int(apps * 42))
                    passes_comp = int(passes_att * random.uniform(0.68, 0.82))
                    tackles = random.randint(int(apps * 0.3), int(apps * 1.2))
                    interceptions = random.randint(int(apps * 0.2), int(apps * 0.8))
                    yellow = random.randint(0, 5)
                    red = 1 if random.random() < 0.05 else 0
                    rating = round(random.uniform(6.7, 8.7), 2)

                # Ensure strict mathematical sanity constraints
                sot = min(sot, shots)
                passes_comp = min(passes_comp, passes_att)

                players.append({
                    "player_id": player_id,
                    "player_name": name,
                    "club": club,
                    "league": league,
                    "nationality": nat,
                    "position": pos,
                    "age": age,
                    "season": season,
                    "appearances": apps,
                    "minutes_played": mins,
                    "goals": goals,
                    "assists": assists,
                    "shots": shots,
                    "shots_on_target": sot,
                    "xg": xg,
                    "xa": xa,
                    "key_passes": key_passes,
                    "passes_completed": passes_comp,
                    "passes_attempted": passes_att,
                    "tackles": tackles,
                    "interceptions": interceptions,
                    "yellow_cards": yellow,
                    "red_cards": red,
                    "rating": rating,
                })
                player_id += 1

    return players


def generate_matches(count: int = 160):
    matches = []
    start_date = datetime(2023, 8, 12)
    match_id = 1

    # Generate roughly half in Premier League, half in La Liga
    for league, clubs in CLUBS.items():
        league_matches = count // len(CLUBS)
        for i in range(league_matches):
            home_team, away_team = random.sample(clubs, 2)
            # Realistic scoring: mostly 0-4 goals
            home_goals = random.choices([0, 1, 2, 3, 4, 5], weights=[20, 35, 25, 12, 6, 2])[0]
            away_goals = random.choices([0, 1, 2, 3, 4], weights=[28, 38, 22, 9, 3])[0]

            # Sequential match dates across the 9-month season
            match_date = start_date + timedelta(days=int((i / league_matches) * 270) + random.randint(0, 3))
            date_str = match_date.strftime("%Y-%m-%d")

            matches.append({
                "match_id": match_id,
                "match_date": date_str,
                "season": "2023-2024",
                "league": league,
                "home_team": home_team,
                "away_team": away_team,
                "home_goals": home_goals,
                "away_goals": away_goals,
            })
            match_id += 1

    # Sort matches chronologically
    matches.sort(key=lambda m: m["match_date"])
    for idx, m in enumerate(matches, 1):
        m["match_id"] = idx
    return matches


def main():
    players = generate_players(140)
    matches = generate_matches(160)

    # Write players.csv
    players_csv = DATA_DIR / "players.csv"
    with open(players_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(players[0].keys()))
        writer.writeheader()
        writer.writerows(players)
    print(f"Generated {len(players)} players in {players_csv}")

    # Write matches.csv
    matches_csv = DATA_DIR / "matches.csv"
    with open(matches_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(matches[0].keys()))
        writer.writeheader()
        writer.writerows(matches)
    print(f"Generated {len(matches)} matches in {matches_csv}")


if __name__ == "__main__":
    main()

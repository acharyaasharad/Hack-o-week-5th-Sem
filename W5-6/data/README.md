# Touchline Analytics — Dataset Documentation

## Demo Dataset · Synthetic Sample Statistics

> **Notice**: The datasets bundled in this directory (`players.csv` and `matches.csv`) contain synthetic sample statistics generated deterministically for demonstration, testing, and portfolio evaluation purposes. They do not represent real-world official club or league records.

---

## 1. `players.csv` Schema

Contains 140 synthetic football player records across 16 clubs in the Premier League and La Liga for the 2023-2024 season.

| Column | Data Type | Description | Constraints / Validation |
|---|---|---|---|
| `player_id` | Integer | Unique identifier for each player | Primary key, strictly unique |
| `player_name` | String | Full name of the player | Non-empty |
| `club` | String | Current club name | Valid competition club |
| `league` | String | League (Premier League / La Liga) | Supported league |
| `nationality` | String | Player nationality | Standard country name |
| `position` | String | Goalkeeper, Defender, Midfielder, Forward | Exact position category |
| `age` | Integer | Player age | Range: 17–45 |
| `season` | String | Season identifier e.g. `2023-2024` | Formatted `YYYY-YYYY` |
| `appearances` | Integer | Total matches appeared in | Non-negative integer |
| `minutes_played` | Integer | Total minutes played on pitch | 0 to 3,420 |
| `goals` | Integer | Total goals scored | Non-negative integer |
| `assists` | Integer | Total assists recorded | Non-negative integer |
| `shots` | Integer | Total shots attempted | Must be >= `shots_on_target` |
| `shots_on_target`| Integer | Shots directed on target | Must be <= `shots` |
| `xg` | Float | Expected goals metric | Non-negative float |
| `xa` | Float | Expected assists metric | Non-negative float |
| `key_passes` | Integer | Passes directly leading to a shot | Non-negative integer |
| `passes_completed` | Integer | Completed passes | Must be <= `passes_attempted` |
| `passes_attempted` | Integer | Attempted passes | Must be >= `passes_completed` |
| `tackles` | Integer | Successful tackles executed | Non-negative integer |
| `interceptions` | Integer | Passes intercepted | Non-negative integer |
| `yellow_cards` | Integer | Cautions received | Non-negative integer |
| `red_cards` | Integer | Dismissals received | Non-negative integer |
| `rating` | Float | Performance rating | Scale: 0.0 to 10.0 |

---

## 2. `matches.csv` Schema

Contains 160 synthetic league fixture records spanning August 2023 through May 2024.

| Column | Data Type | Description | Constraints / Validation |
|---|---|---|---|
| `match_id` | Integer | Unique fixture identifier | Primary key |
| `match_date` | Date | Fixture date formatted `YYYY-MM-DD` | Valid ISO calendar date |
| `season` | String | Season identifier e.g. `2023-2024` | Valid season |
| `league` | String | League competition | Premier League / La Liga |
| `home_team` | String | Name of the hosting club | Different from away_team |
| `away_team` | String | Name of the visiting club | Different from home_team |
| `home_goals` | Integer | Goals scored by hosting club | Non-negative integer |
| `away_goals` | Integer | Goals scored by visiting club | Non-negative integer |

---

## 3. Custom Dataset Upload Format

Users can upload custom CSV files via the Touchline Analytics web dashboard. Custom datasets must include all required column headers listed above and conform to standard UTF-8 encoding.

# Habitica Party Podium

Generate a readable podium summary for your Habitica party, including top damage dealers, top damage taken, and most team skills cast, formatted for mobile compatibility.

## Features

- Fetches party chat and group info from Habitica API
- Aggregates boss damage and team skill usage for the last 7 days
- Updates your party/group description with a readable podium (no markdown tables)
- Shows top users for:
  - Damage dealt
  - Damage taken
  - Team skills cast

## Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd habitica-party-podium
   ```

2. **Configure API credentials:**
   - Create a `.env` file with your Habitica API credentials:
     ```python
     API_USER_ID = "<your-user-id>"
     API_TOKEN = "<your-api-token>"
     API_CLIENT = "<your-client-id>"
     ```

3. **Create and activate the environment:**
   ```bash
   conda env create -f environment.yml
   conda activate HABITICA
   ```

## Usage

Run the script:

```bash
python src/main.py
```

- The script will print a summary to the console and update your Habitica group description with the latest podium.

## Output Example

```
**Period:** 2024-06-01 → 2024-06-08

### 💪 Top Damage Dealers
1. Alice   Damage Dealt: 123.4
2. Bob     Damage Dealt: 98.7

### 💀 Top Damage Taken
1. Bob     Damage Taken: 45.6
2. Alice   Damage Taken: 12.3

### ✨ Most Team Skills Cast
1. Alice   Skills Cast: 5 times
2. Bob     Skills Cast: 2 times

_Last updated: 2024-06-08 12:34 UTC_
---
```

## Notes

- The podium is formatted for best readability on Habitica mobile.
- Only the last 7 days of activity are considered.


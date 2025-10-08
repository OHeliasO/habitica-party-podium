import requests
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from config import API_USER_ID, API_TOKEN, API_CLIENT

# =======================
# 🔧 Configuration
# =======================
BASE_GROUP_URL = "https://habitica.com/api/v4/groups"
PARTY_URL = f"{BASE_GROUP_URL}/party"

HEADERS = {
    "x-api-user": API_USER_ID,
    "x-api-key": API_TOKEN,
    "x-client": API_CLIENT,
    "Content-Type": "application/json",
}


# =======================
# 🧩 Utility Functions
# =======================


def fetch_group_info() -> Dict[str, Any]:
    """Fetches the Habitica party chat messages."""
    try:
        response = requests.get(PARTY_URL, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"⚠️ Failed to fetch party chat: {e}")
        return []


def fetch_party_chat() -> List[Dict[str, Any]]:
    """Fetches the Habitica party chat messages."""
    try:
        response = requests.get(PARTY_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json().get("data", {})
        return data.get("chat", [])
    except requests.RequestException as e:
        print(f"⚠️ Failed to fetch party chat: {e}")
        return []


def filter_recent_boss_messages(
    chat: List[Dict[str, Any]], days: int = 7
) -> List[Dict[str, Any]]:
    """Filters boss damage messages from the last given number of days."""
    now = datetime.now()
    since = now - timedelta(days=days)

    return [
        msg
        for msg in chat
        if msg.get("info", {}).get("type") == "boss_damage"
        and datetime.fromtimestamp(msg["timestamp"] / 1000) >= since
    ]


def aggregate_user_damage(
    messages: List[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """Aggregates user and boss damage per player."""
    stats: Dict[str, Dict[str, float]] = {}

    for msg in messages:
        info = msg.get("info", {})
        user = info.get("user")
        if not user:
            continue

        user_damage = info.get("userDamage")
        boss_damage = info.get("bossDamage")

        if user not in stats:
            stats[user] = {"userDamage": 0.0, "bossDamage": 0.0}

        try:
            if user_damage is not None:
                stats[user]["userDamage"] += float(user_damage)
            if boss_damage is not None:
                stats[user]["bossDamage"] += float(boss_damage)
        except (ValueError, TypeError):
            # Skip malformed numeric values
            continue

    return stats


def aggregate_team_skills(
    messages: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Aggregates the total number of team skills cast by each user.
    Returns: {user: total_count}
    """
    skills: Dict[str, int] = {}
    for msg in messages:
        info = msg.get("info", {})
        if info.get("type") != "spell_cast_party":
            continue
        user = info.get("user")
        times = info.get("times", 1)
        if not user:
            continue
        if user not in skills:
            skills[user] = 0
        skills[user] += int(times)
    return skills


def generate_markdown_report(
    user_stats: Dict[str, Dict[str, float]],
    period_start: datetime,
    period_end: datetime,
    top_n: int = 5,
    team_skills: Dict[str, int] = None,
) -> str:
    """Generates a user-friendly podium report for mobile Habitica."""
    top_user_damage = sorted(
        user_stats.items(), key=lambda x: x[1]["userDamage"], reverse=True
    )[:top_n]
    top_boss_damage = sorted(
        user_stats.items(), key=lambda x: x[1]["bossDamage"], reverse=True
    )[:top_n]

    md = [
        "",
        f"**Period:** {period_start.strftime('%Y-%m-%d')} → {period_end.strftime('%Y-%m-%d')}",
        "",
        "### 💪 Top Damage Dealers",
    ]

    for i, (user, stats) in enumerate(top_user_damage, 1):
        md.append(f"{i}. {user}\tDamage Dealt: {stats['userDamage']:.1f}")

    md += [
        "",
        "### 💀 Top Damage Taken",
    ]

    for i, (user, stats) in enumerate(top_boss_damage, 1):
        md.append(f"{i}. {user}\tDamage Taken: {stats['bossDamage']:.1f}")

    # Add team skills section (total per user)
    if team_skills:
        sorted_skills = sorted(team_skills.items(), key=lambda x: x[1], reverse=True)
        md += [
            "",
            "### ✨ Most Team Skills Cast",
        ]
        for i, (user, count) in enumerate(sorted_skills[:top_n], 1):
            md.append(f"{i}. {user}\tSkills Cast: {count} times")

    return "\n".join(md)


def print_console_report(user_stats: Dict[str, Dict[str, float]]):
    """Prints a clean, formatted table to console."""
    print("\n=== 🧾 Damage Report (Last 7 Days) ===\n")
    print(f"{'Player':<25}{'Damage Dealt':>15}{'Damage Taken':>15}")
    print("-" * 55)
    for user, stats in sorted(
        user_stats.items(), key=lambda x: x[1]["userDamage"], reverse=True
    ):
        print(f"{user:<25}{stats['userDamage']:>15.1f}{stats['bossDamage']:>15.1f}")
    print("\n========================================\n")


def update_group_description(group_id: str, new_description: str):
    """Updates the Habitica group description."""
    try:
        resp = requests.put(
            f"{BASE_GROUP_URL}/{group_id}",
            headers=HEADERS,
            json={"description": new_description},
        )
        resp.raise_for_status()
        print("✅ Successfully updated group description on Habitica.")
    except requests.RequestException as e:
        print(f"⚠️ Failed to update group description: {e}")


def replace_podium_section(description: str, podium_md: str) -> str:
    """
    Replaces ONLY the section between '## 🏆 Podium' and the next '## ' header.
    This makes it robust even if the section contains tables with '---'.
    If the section doesn't exist, the podium will be appended at the end.
    """
    description = description.strip()
    podium_header = "## 🏆 Podium"

    # Regex: match from podium header to next '## ' or end of text
    pattern = r"(## 🏆 Podium[\s\S]*?)(?=\n## |\Z)"

    # Ensure the markdown section starts properly formatted
    new_podium_section = f"{podium_header}\n\n{podium_md.strip()}\n"

    if re.search(pattern, description):
        updated_description = re.sub(pattern, new_podium_section, description)
        print("ℹ️ Replaced existing '## 🏆 Podium' section.")
    else:
        # Append it neatly before the end
        updated_description = description.rstrip() + "\n\n" + new_podium_section + "\n"
        print("ℹ️ Added new '## 🏆 Podium' section.")

    return updated_description


# =======================
# 🚀 Main Execution
# =======================


def main():
    chat = fetch_party_chat()
    if not chat:
        print("⚠️ No chat messages found.")
        return

    recent_messages = filter_recent_boss_messages(chat, days=7)
    if not recent_messages:
        print("⚠️ No boss damage messages found in the last 7 days.")
        return

    user_stats = aggregate_user_damage(recent_messages)

    # Aggregate team skills from all chat messages in the period
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)
    # Filter spell_cast_party messages in the last 7 days
    recent_skill_msgs = [
        msg for msg in chat
        if msg.get("info", {}).get("type") == "spell_cast_party"
        and datetime.fromtimestamp(msg["timestamp"] / 1000) >= seven_days_ago
    ]
    team_skills = aggregate_team_skills(recent_skill_msgs)

    # Console report
    # print_console_report(user_stats)

    # Generate Markdown podium
    markdown_report = generate_markdown_report(
        user_stats, seven_days_ago, now, team_skills=team_skills
    )

    # Add a "last updated" line for visibility
    last_updated = f"_Last updated: {now.strftime('%Y-%m-%d %H:%M')} UTC_"
    full_podium_md = f"{markdown_report}\n\n{last_updated}\n\n---"

    # Fetch group info
    group_info = fetch_group_info()
    group_data = group_info.get("data", {})
    group_id = group_data.get("_id")
    description = group_data.get("description", "")

    if not group_id or not description:
        print("⚠️ Could not find group ID or description.")
        return

    # Replace only the podium section (safe)
    new_description = replace_podium_section(description, full_podium_md)

    # Update only if needed
    if new_description.strip() != description.strip():
        print("✅ Podium section needs updating. Updating...")
        # print("New description:\n", new_description)
        # new_group_info = group_info["data"]["description"] = new_description
        update_group_description(group_id, new_description)
    else:
        print("✅ Podium section already up-to-date. No changes made.")

if __name__ == "__main__":
    main()

def compute_total_stats(parts):
    total_mod = {}
    for part in parts:
        for stat, val in part.get("statModifiers", {}).items():
            total_mod[stat] = total_mod.get(stat, 0) + val
        for cond, bonus_stats in part.get("compatibilityBonus", {}).items():
            for ref in parts:
                if cond in ref.get("manufacturer", "") or cond in ref.get("id", ""):
                    for stat, val in bonus_stats.items():
                        total_mod[stat] = total_mod.get(stat, 0) + val
    weapon_class = parts[0].get("class", "")

    base = {
        "Pistol":  {"reloadTime": 2.10, "magSize": 12, "accuracy": 100, "fireRate": 5.0},
        "SMG":     {"reloadTime": 2.25, "magSize": 30, "accuracy": 100, "fireRate": 12.0},
        "Shotgun": {"reloadTime": 2.75, "magSize":  8, "accuracy": 100, "fireRate": 1.0},
        "Sniper":  {"reloadTime": 2.75, "magSize":  8, "accuracy": 100, "fireRate": 1.0},
        "Rifle":   {"reloadTime": 2.25, "magSize": 30, "accuracy": 100, "fireRate": 8.0},
    }.get(weapon_class, {"reloadTime":0, "magSize":0, "accuracy":100, "fireRate":1})

    final = {}

    final["weaponDamage"] = total_mod.get("weaponDamage", 0)
    final["magSize"] = max(0, int(base["magSize"] + total_mod.get("magSize", 0)))
    reload = total_mod.get("reloadTime", 0)
    final["reloadTime"] = base["reloadTime"] / (1 + reload / 100.0)
    interval = total_mod.get("fireInterval", 0)
    final["fireRate"] = base["fireRate"] / (1 + interval / 100.0)
    acc_drop = total_mod.get("minAccuracy", 0)
    final["accuracy"] = max(0, min(100, base["accuracy"] - acc_drop))
    return final

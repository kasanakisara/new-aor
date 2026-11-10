# -*- coding: utf-8 -*-
"""Generate AOR 1919 land doctrine set (4 grand doctrines, 3 tracks)."""
import os, re, sys

ROOT = r"D:\new-aor"
DOC = os.path.join(ROOT, "common", "doctrines")

GRAND = [
    ("superior_firepower", "GRAND_DOCTRINE_SUPERIOR_FIREPOWER", "GFX_doctrine_superior_firepower_medium",
     [("enable_tactic = tactic_overwhelming_fire", None),
      ("category_line_artillery", {"soft_attack": 0.10}),
      ("category_support_artillery", {"soft_attack": 0.05})],
     [("enable_tactic = tactic_elastic_defense\n            supply_consumption_factor = -0.10", None),
      ("additional_brigade_column_size = 1\n            category_support_battalions = { max_organisation = 10 }", None),
      ("enable_tactic = tactic_barrage\n            category_line_artillery = { soft_attack = 0.10 }", None)]),
    ("grand_battleplan", "GRAND_DOCTRINE_GRAND_BATTLEPLAN", "GFX_doctrine_grand_battleplan_medium",
     [("enable_tactic = tactic_planned_attack", None),
      ("max_planning = 0.10", None),
      ("command_power_gain = 0.25", None)],
     [("additional_brigade_column_size = 1\n            enable_tactic = tactic_elastic_defense", None),
      ("max_planning = 0.10\n            planning_speed = 0.10", None),
      ("enable_tactic = tactic_breakthrough\n            category_all_infantry = { breakthrough = 0.10 }", None)]),
    ("mass_assault", "GRAND_DOCTRINE_MASS_ASSAULT", "GFX_doctrine_mass_assault_medium",
     [("no_supply_grace = 48", None),
      ("out_of_supply_factor = -0.10", None),
      ("enable_tactic = tactic_relentless_assault", None)],
     [("enable_tactic = tactic_human_wave_tactics\n            additional_brigade_column_size = 1", None),
      ("category_all_infantry = { max_organisation = 8 }", None),
      ("category_all_infantry = { combat_width = -0.20 }", None)]),
    ("industrial_warfare", "GRAND_DOCTRINE_INDUSTRIAL_WARFARE", "GFX_doctrine_superior_firepower_medium",
     [("army_speed_factor = 0.10", None),
      ("category_all_infantry", {"max_organisation": -8, "combat_width": -0.30}),
      ("additional_brigade_column_size = 1", None),
      ("enable_tactic = tactic_human_wave_tactics", None)],
     [("army_speed_factor = -0.10", None),
      ("category_all_infantry = { max_organisation = 4\n            combat_width = 0.15 }", None),
      ("category_all_infantry = { max_organisation = 4\n            combat_width = 0.15 }", None)]),
]

TRACKS = [
    ("infantry", "DOCTRINE_TRACK_INFANTRY", ["category_all_infantry", "category_light_infantry"], 1.0),
    ("combat_support", "DOCTRINE_TRACK_COMBAT_SUPPORT",
     ["category_line_artillery", "category_artillery", "category_support_battalions", "category_divisional_support_battalions"], 2.0),
    ("operations", "DOCTRINE_TRACK_OPERATIONS",
     ["category_all_infantry", "category_line_artillery", "category_army"], 1.5),
]

# (id, name_key, icon, effect, rewards, grand_only)
INF = [
    ("great_war_infantry", "SUBDOCTRINE_GREAT_WAR_INFANTRY", "GFX_doctrine_great_war_infantry_medium",
     {"category_all_infantry": {"defense": 0.10}},
     [("trench_discipline", {"category_all_infantry": {"defense": 0.05, "max_organisation": 5}}),
      ("mass_rifle_fire", {"category_all_infantry": {"soft_attack": 0.05}}),
      ("bayonet_drill", {"category_all_infantry": {"soft_attack": 0.05, "breakthrough": 0.03}}),
      ("regimental_pride", {"category_all_infantry": {"default_morale": 0.05, "max_organisation": 5}})], None),
    ("defensive_postures", "SUBDOCTRINE_DEFENSIVE_POSTURES", "GFX_doctrine_defensive_postures_medium",
     {"category_all_infantry": {"defense": 0.15}},
     [("dug_in_positions", {"category_all_infantry": {"defense": 0.10}}),
      ("machine_gun_nests", {"Machine_gun": {"defense": 0.10, "soft_attack": 0.05}}),
      ("elastic_defense", {"category_all_infantry": {"max_organisation": 5}}),
      ("local_counterattack", {"category_all_infantry": {"soft_attack": 0.05, "defense": 0.05}})], None),
    ("large_unit_tactics", "SUBDOCTRINE_LARGE_UNIT_TACTICS", "GFX_doctrine_offensive_formations_medium",
     {"category_all_infantry": {"max_organisation": 5}},
     [("corps_command", {"max_planning": 0.05}),
      ("staff_work", {"max_planning": 0.10}),
      ("coordinated_advance", {"category_all_infantry": {"soft_attack": 0.03}}),
      ("reserve_echelons", {"category_all_infantry": {"max_organisation": 5}})], None),
    ("assault_infantry", "SUBDOCTRINE_ASSAULT_INFANTRY", "GFX_doctrine_assault_infantry_medium",
     {"category_light_infantry": {"breakthrough": 0.05, "soft_attack": 0.05}},
     [("storm_detachments", {"assault_team": {"breakthrough": 0.05, "soft_attack": 0.05}}),
      ("flame_support", {"aor_flame_support": {"soft_attack": 0.10}}),
      ("hand_grenades", {"category_light_infantry": {"soft_attack": 0.05}}),
      ("close_combat", {"category_light_infantry": {"soft_attack": 0.05, "defense": 0.05}})], None),
    ("commandos", "SUBDOCTRINE_COMMANDOS", "GFX_doctrine_commandos_medium",
     {"commando_units": {"breakthrough": 0.05, "defense": 0.05}},
     [("patrol_doctrine", {"recon": {"recon": 0.10}, "aor_sniper_observer": {"soft_attack": 0.05}}),
      ("sniper_teams", {"aor_sniper_observer": {"soft_attack": 0.10, "defense": 0.05}}),
      ("sabotage_raids", {"commando_units": {"breakthrough": 0.05}}),
      ("night_raids", {"commando_units": {"soft_attack": 0.10}})], None),
    ("irregulars", "SUBDOCTRINE_IRREGULARS", "GFX_doctrine_irregulars_medium",
     {"irregular_infantry": {"defense": 0.10}, "militia": {"defense": 0.05}},
     [("partisan_bands", {"irregular_infantry": {"max_organisation": 5}}),
      ("local_knowledge", {"irregular_infantry": {"defense": 0.10}}),
      ("ambush_tactics", {"irregular_infantry": {"soft_attack": 0.05, "breakthrough": 0.03}}),
      ("popular_support", {"militia": {"max_organisation": 5}})], None),
    ("peoples_war", "SUBDOCTRINE_PEOPLES_WAR", "GFX_doctrine_peoples_war_medium",
     {"militia": {"max_organisation": 10}},
     [("mass_mobilisation", {"militia": {"max_organisation": 10}}),
      ("defence_of_homeland", {"militia": {"defense": 0.10}}),
      ("guerrilla_cadres", {"irregular_infantry": {"soft_attack": 0.05}}),
      ("inexhaustible_reserves", {"militia": {"max_organisation": 5, "default_morale": 0.05}})], "mass_assault"),
    ("bite_and_hold", "SUBDOCTRINE_BITE_AND_HOLD", "GFX_doctrine_defensive_postures_medium",
     {"category_all_infantry": {"defense": 0.10, "max_organisation": 4}},
     [("limited_objective_attacks", {"category_all_infantry": {"soft_attack": 0.05}}),
      ("trench_consolidation", {"engineer": {"defense": 0.10}}),
      ("counter_attack_plan", {"category_all_infantry": {"breakthrough": 0.05}}),
      ("sapping_operations", {"engineer": {"breakthrough": 0.05, "defense": 0.05}})], "industrial_warfare"),
    ("defense_in_depth", "SUBDOCTRINE_DEFENSE_IN_DEPTH", "GFX_doctrine_defensive_postures_medium",
     {"category_all_infantry": {"defense": 0.15}},
     [("reserve_trenches", {"category_all_infantry": {"defense": 0.05}}),
      ("machine_gun_nests", {"Machine_gun": {"defense": 0.10}}),
      ("elastic_defense", {"category_all_infantry": {"max_organisation": 5}}),
      ("gegenstoss", {"category_all_infantry": {"soft_attack": 0.05, "breakthrough": 0.05}})], "industrial_warfare"),
]

SUP = [
    ("fire_concentration", "SUBDOCTRINE_FIRE_CONCENTRATION", "GFX_doctrine_fire_concentration_medium",
     {"category_line_artillery": {"soft_attack": 0.10}},
     [("centralized_artillery_command", {"category_line_artillery": {"soft_attack": 0.05}}),
      ("preliminary_bombardment", {"artillery_brigade": {"soft_attack": 0.05}}),
      ("standing_barrage", {"artillery_brigade": {"soft_attack": 0.05, "defense": 0.05}}),
      ("rolling_barrage", {"category_line_artillery": {"soft_attack": 0.05, "breakthrough": 0.05}})], None),
    ("siege_artillery", "SUBDOCTRINE_SIEGE_ARTILLERY", "GFX_doctrine_siege_artillery_medium",
     {"howitzer_brigade": {"soft_attack": 0.10}, "artillery": {"soft_attack": 0.05}},
     [("heavy_shells", {"howitzer_brigade": {"soft_attack": 0.05}}),
      ("fortress_busting", {"howitzer_brigade": {"soft_attack": 0.05, "hard_attack": 0.05}}),
      ("superheavy_guns", {"howitzer_brigade": {"soft_attack": 0.10}}),
      ("counter_battery", {"artillery": {"soft_attack": 0.05}})], None),
    ("field_engineering", "SUBDOCTRINE_FIELD_ENGINEERING", "GFX_doctrine_field_engineering_medium",
     {"engineer": {"defense": 0.05}},
     [("field_works", {"engineer": {"defense": 0.10}}),
      ("bridging", {"engineer": {"maximum_speed": 0.05}}),
      ("mine_warfare", {"engineer": {"soft_attack": 0.05, "defense": 0.05}}),
      ("assault_pioneers", {"assault_engineer": {"breakthrough": 0.05}})], None),
    ("chemical_warfare", "SUBDOCTRINE_CHEMICAL_WARFARE", "GFX_doctrine_assault_infantry_medium",
     {"aor_chemical_support": {"soft_attack": 0.10}},
     [("gas_shells", {"aor_chemical_support": {"soft_attack": 0.10}}),
      ("gas_masks", {"category_all_infantry": {"defense": 0.05}}),
      ("gas_discipline", {"aor_chemical_support": {"defense": 0.05}}),
      ("chemical_barrage", {"artillery_brigade": {"soft_attack": 0.05}})], None),
    ("armored_support", "SUBDOCTRINE_ARMORED_SUPPORT", "GFX_doctrine_armored_infantry_support_medium",
     {"aor_tank_support": {"breakthrough": 0.05}, "aor_car_support": {"recon": 0.05}},
     [("tank_escort", {"aor_tank_support": {"soft_attack": 0.05, "breakthrough": 0.05}}),
      ("armored_cars", {"aor_car_support": {"recon": 0.10}}),
      ("armored_assault", {"aor_armored_assault": {"breakthrough": 0.05}}),
      ("combined_arms", {"aor_tank_support": {"defense": 0.05}})], None),
    ("logistics_support", "SUBDOCTRINE_LOGISTICS_SUPPORT", "GFX_doctrine_field_engineering_medium",
     {"field_hospital": {"max_organisation": 5}},
     [("field_hospitals", {"field_hospital": {"max_organisation": 5}}),
      ("maintenance_crews", {"engineer": {"defense": 0.05}}),
      ("supply_columns", {"aor_integrated_support": {"supply_consumption": -0.05}}),
      ("signal_corps", {"aor_integrated_support": {"initiative": 0.05}})], None),
    ("methodical_fire", "SUBDOCTRINE_METHODICAL_FIRE", "GFX_doctrine_fire_concentration_medium",
     {"category_line_artillery": {"soft_attack": 0.10}},
     [("centralized_fire_command", {"category_line_artillery": {"soft_attack": 0.05}}),
      ("preliminary_bombardment", {"artillery_brigade": {"soft_attack": 0.05}}),
      ("standing_barrage", {"artillery_brigade": {"defense": 0.05, "soft_attack": 0.05}}),
      ("counter_battery_fire", {"howitzer_brigade": {"soft_attack": 0.05}})], "industrial_warfare"),
    ("integrated_firepower", "SUBDOCTRINE_INTEGRATED_FIREPOWER", "GFX_doctrine_fire_concentration_medium",
     {"category_line_artillery": {"soft_attack": 0.05}, "category_all_infantry": {"soft_attack": 0.03}},
     [("creeping_barrage", {"category_line_artillery": {"soft_attack": 0.05, "breakthrough": 0.05}}),
      ("predicted_fire", {"artillery_brigade": {"soft_attack": 0.05}}),
      ("box_barrage", {"howitzer_brigade": {"soft_attack": 0.05}}),
      ("sos_barrage", {"category_line_artillery": {"defense": 0.05}})], "industrial_warfare"),
    ("hurricane_bombardment", "SUBDOCTRINE_HURRICANE_BOMBARDMENT", "GFX_doctrine_siege_artillery_medium",
     {"howitzer_brigade": {"soft_attack": 0.10}},
     [("short_intense_bombardment", {"howitzer_brigade": {"soft_attack": 0.10}}),
      ("mission_command", {"category_line_artillery": {"soft_attack": 0.05}}),
      ("counter_battery_fire", {"artillery": {"soft_attack": 0.05}}),
      ("pulkowski_method", {"category_line_artillery": {"breakthrough": 0.05}})], "industrial_warfare"),
]

OPS = [
    ("mission_type_tactics", "SUBDOCTRINE_MISSION_TYPE_TACTICS", "GFX_doctrine_mission_type_tactics_medium",
     {"max_planning": 0.05},
     [("mission_orders", {"max_planning": 0.05}),
      ("initiative", {"category_all_infantry": {"initiative": 0.05}}),
      ("combined_planning", {"max_planning": 0.05, "command_power_gain": 0.10}),
      ("flexible_response", {"category_all_infantry": {"maximum_speed": 0.05}})], None),
    ("last_stand", "SUBDOCTRINE_LAST_STAND", "GFX_doctrine_last_stand_medium",
     {"category_all_infantry": {"defense": 0.10}},
     [("fortified_positions", {"category_all_infantry": {"defense": 0.10, "entrenchment": 0.10}}),
      ("no_retreat", {"category_all_infantry": {"default_morale": 0.05}}),
      ("scorched_earth", {"category_all_infantry": {"defense": 0.05}}),
      ("counter_battery", {"artillery_brigade": {"defense": 0.05}})], None),
    ("infiltration_tactics", "SUBDOCTRINE_INFILTRATION_TACTICS", "GFX_doctrine_infiltration_assault_medium",
     {"category_light_infantry": {"breakthrough": 0.05}},
     [("storm_troops", {"assault_team": {"breakthrough": 0.05, "soft_attack": 0.05}}),
      ("weak_point_probing", {"category_all_infantry": {"soft_attack": 0.05}}),
      ("night_infiltration", {"land_night_attack": 0.05}),
      ("command_decentralisation", {"category_all_infantry": {"initiative": 0.05}})], None),
    ("grand_assault", "SUBDOCTRINE_GRAND_ASSAULT", "GFX_doctrine_grand_assault_medium",
     {"category_army": {"breakthrough": 0.05}},
     [("massed_attack", {"category_all_infantry": {"soft_attack": 0.05, "breakthrough": 0.05}}),
      ("artillery_preparation", {"category_line_artillery": {"soft_attack": 0.05}}),
      ("shock_groups", {"assault_team": {"breakthrough": 0.05}}),
      ("relentless_pressure", {"category_all_infantry": {"max_organisation": 5}})], None),
    ("guerilla_war", "SUBDOCTRINE_GUERILLA_WAR", "GFX_doctrine_guerilla_warfare_medium",
     {"irregular_infantry": {"defense": 0.10, "soft_attack": 0.05}},
     [("hit_and_run", {"irregular_infantry": {"soft_attack": 0.05}}),
      ("hidden_bases", {"irregular_infantry": {"defense": 0.10}}),
      ("local_levies", {"militia": {"max_organisation": 5}}),
      ("night_operations", {"land_night_attack": 0.05})], None),
    ("rapid_domination", "SUBDOCTRINE_RAPID_DOMINATION", "GFX_doctrine_offensive_formations_medium",
     {"category_all_infantry": {"soft_attack": 0.05}},
     [("concentrated_push", {"category_all_infantry": {"breakthrough": 0.05}}),
      ("artillery_support", {"category_line_artillery": {"soft_attack": 0.05}}),
      ("reserve_exploitation", {"category_all_infantry": {"maximum_speed": 0.05}}),
      ("sustained_offensive", {"category_all_infantry": {"max_organisation": 5}})], None),
    ("expeditionary_warfare", "SUBDOCTRINE_EXPEDITIONARY_WARFARE", "GFX_doctrine_expeditionary_warfare_medium",
     {"supply_consumption_factor": -0.10},
     [("overseas_supply", {"out_of_supply_factor": -0.10}),
      ("colonial_warfare", {"category_all_infantry": {"maximum_speed": 0.05}}),
      ("port_seizure", {"category_all_infantry": {"soft_attack": 0.05}}),
      ("expeditionary_logistics", {"aor_integrated_support": {"supply_consumption": -0.05}})], None),
    ("methodical_battle", "SUBDOCTRINE_METHODICAL_BATTLE", "GFX_doctrine_mission_type_tactics_medium",
     {"max_planning": 0.05},
     [("command_by_directive", {"max_planning": 0.10}),
      ("centralized_fire_planning", {"category_line_artillery": {"soft_attack": 0.05}}),
      ("scientific_conduct", {"category_all_infantry": {"initiative": 0.05}}),
      ("relentless_offensive", {"category_all_infantry": {"max_organisation": 5, "soft_attack": 0.03}})], "industrial_warfare"),
    ("attack_in_position_warfare", "SUBDOCTRINE_ATTACK_IN_POSITION_WARFARE", "GFX_doctrine_infiltration_assault_medium",
     {"assault_team": {"breakthrough": 0.05}},
     [("auftragstaktik", {"category_all_infantry": {"initiative": 0.05}}),
      ("weak_point_study", {"category_all_infantry": {"soft_attack": 0.05}}),
      ("stormtrooper_assault", {"assault_team": {"breakthrough": 0.10, "soft_attack": 0.05}}),
      ("strongpoint_isolation", {"category_all_infantry": {"soft_attack": 0.05}})], "industrial_warfare"),
]


def fmt_mods(mods, indent):
    out = []
    for target, vals in mods.items():
        if not isinstance(vals, dict):
            out.append("%s%s = %s" % (indent, target, vals))
            continue
        out.append("%s%s = {" % (indent, target))
        for k, v in vals.items():
            out.append("%s    %s = %s" % (indent, k, v))
        out.append("%s}" % indent)
    return out


def emit_sub(sd):
    sid, key, icon, effect, rewards, grand_only = sd
    L = []
    L.append("%s = {" % sid)
    L.append("    track = %s" % effect.pop("__track__"))
    L.append("    name = %s" % key)
    L.append("    description = %s_DESC" % key)
    L.append("    icon = %s" % icon)
    L.append("")
    L.append("    xp_cost = 100")
    L.append("    xp_type = army")
    L.append("")
    if grand_only:
        L.append("    available = {")
        L.append("        has_doctrine = %s" % grand_only)
        L.append("    }")
    else:
        L.append("    available = {")
        L.append("        always = yes")
        L.append("    }")
    L.append("")
    L.append("    ai_will_do = { base = 1 }")
    L.append("")
    L.append("    # EFFECTS")
    L.extend(fmt_mods(effect, "    "))
    L.append("")
    L.append("    rewards = {")
    for rid, mods in rewards:
        L.append("        %s = {" % rid)
        L.extend(fmt_mods(mods, "            "))
        L.append("        }")
    L.append("    }")
    L.append("}")
    return "\n".join(L)


def main():
    apply = "--apply" in sys.argv
    out = {}

    # --- grand doctrines ---
    L = []
    for gid, key, icon, effects, milestones in GRAND:
        L.append("%s = {" % gid)
        L.append("    folder = land")
        L.append("")
        L.append("    name = %s" % key)
        L.append("    description = %s_DESC" % key)
        L.append("    icon = %s" % icon)
        L.append("    available = { always = yes }")
        L.append("")
        L.append("    xp_cost = 100")
        L.append("    xp_type = army")
        L.append("")
        L.append("    ai_will_do = { base = 1 }")
        L.append("")
        L.append("    tracks = {")
        L.append("        infantry")
        L.append("        combat_support")
        L.append("        operations")
        L.append("    }")
        L.append("")
        L.append("    max_track_columns = 3")
        L.append("")
        L.append("    # EFFECTS")
        for line, mods in effects:
            if mods:
                L.append("    %s = {" % line)
                for k, v in mods.items():
                    L.append("        %s = %s" % (k, v))
                L.append("    }")
            else:
                L.append("    " + line)
        L.append("")
        L.append("    milestones = {")
        variables = ["infantry_milestone_var", "support_milestone_var", "operations_milestone_var"]
        for i, (line, mods) in enumerate(milestones):
            L.append("        {")
            for ln in line.split("\n"):
                L.append("            " + ln.strip())
            L.append("            effect = {")
            L.append("                if = {")
            L.append("                    limit = { NOT = { has_variable = %s } }" % variables[i])
            L.append("                    set_variable = { %s = 1 }" % variables[i])
            L.append("                }")
            L.append("                else = { add_to_variable = { %s = 1 } }" % variables[i])
            L.append("            }")
            L.append("        }")
        L.append("    }")
        L.append("}")
        L.append("")
    out["grand_doctrines/land_grand_doctrines.txt"] = "\n".join(L)

    # --- tracks ---
    L = []
    for tid, key, cats, mult in TRACKS:
        L.append("%s = {" % tid)
        L.append("    name = %s" % key)
        L.append("    mastery = {")
        L.append("        multiplier = %s" % mult)
        L.append("        categories = {")
        for c in cats:
            L.append("            %s" % c)
        L.append("        }")
        L.append("    }")
        L.append("}")
        L.append("")
    # keep the original track definitions (armor/future tracks must stay defined)

    # --- subdoctrines ---
    for track, data, fname in [("infantry", INF, "infantry_subdoctrines.txt"),
                               ("combat_support", SUP, "combat_support_subdoctrines.txt"),
                               ("operations", OPS, "operations_subdoctrines.txt")]:
        L = []
        for sd in data:
            eff = dict(sd[3])
            eff["__track__"] = track
            L.append(emit_sub((sd[0], sd[1], sd[2], eff, sd[4], sd[5])))
            L.append("")
        out["subdoctrines/land/" + fname] = "\n".join(L)

    # validation: effect targets exist
    units = set()
    for fn in os.listdir(os.path.join(ROOT, "common", "units")):
        if not fn.endswith(".txt"):
            continue
        s = open(os.path.join(ROOT, "common", "units", fn), "rb").read().decode("utf-8-sig", errors="replace")
        units |= set(re.findall(r"^\t(\w+)\s*=\s*\{", s, re.M))
    known_targets = units | {
        "category_all_infantry", "category_light_infantry", "category_line_artillery", "category_artillery",
        "category_support_battalions", "category_divisional_support_battalions", "category_army",
        "category_vehicle_infantry", "category_cavalry", "category_support_artillery"}
    bad = []
    for track, data, _ in [("infantry", INF, ""), ("combat_support", SUP, ""), ("operations", OPS, "")]:
        for sd in data:
            if sd[3]:
                for t in sd[3]:
                    if t not in known_targets:
                        bad.append((sd[0], t))
            for rid, mods in sd[4]:
                for t in mods:
                    if t not in known_targets:
                        bad.append((sd[0] + "/" + rid, t))
    print("unknown effect targets:", bad[:10], "count", len(bad))
    print("subdoctrines:", len(INF), len(SUP), len(OPS))

    if apply:
        for rel, text in out.items():
            p = os.path.join(DOC, rel)
            open(p, "wb").write(b"\xef\xbb\xbf" + text.encode("utf-8"))
            print("wrote", p)
        # delete armor + future land files
        for fn in ["future_armor_subdoctrines.txt", "future_combat_support_subdoctrines.txt",
                   "future_infantry_subdoctrines.txt", "future_operations_subdoctrines.txt"]:
            p = os.path.join(DOC, "subdoctrines", "land", fn)
            if os.path.exists(p):
                os.remove(p)
                print("removed", p)
        # 覆盖原版装甲子学说：留空文件，避免 1919 出现装甲学说
        open(os.path.join(DOC, "subdoctrines", "land", "armor_subdoctrines.txt"), "wb").write(
            b"\xef\xbb\xbf# 1919: armor doctrine disabled\n")
        for fn in ["future_land_doctrine_tracks.txt"]:
            p = os.path.join(DOC, "tracks", fn)
            if os.path.exists(p):
                os.remove(p)
                print("removed", p)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Generate AOR 1919 naval + air doctrines (sea: 2 doctrines x 2 tracks, air: 3 x 4 tracks)."""
import os, re, sys

ROOT = r"D:\new-aor"
DOC = os.path.join(ROOT, "common", "doctrines")

SEA_GRAND = [
    ("new_fleet_in_being", "GRAND_DOCTRINE_FLEET_IN_BEING", "GFX_doctrine_fleet_in_being_medium",
     [("navy_fuel_consumption_factor = -0.05", None),
      ("naval_has_potf_in_combat_attack = 0.10", None)],
     [{"battleship": {"max_organisation": 5}},
      {"light_cruiser": {"max_organisation": 5}, "destroyer": {"max_organisation": 5}}]),
    ("new_convoy_raiding", "GRAND_DOCTRINE_CONVOY_RAIDING", "GFX_doctrine_trade_interdiction_medium",
     [("convoy_raiding_efficiency_factor = 0.10", None),
      ("navy_fuel_consumption_factor = -0.05", None)],
     [{"heavy_cruiser": {"max_organisation": 5}},
      {"destroyer": {"max_organisation": 5}, "light_cruiser": {"max_organisation": 5}}]),
]

SEA_CAPITAL = [
    ("line_of_battle", "SUBDOCTRINE_LINE_OF_BATTLE", "GFX_doctrine_grand_battlefleet_medium",
     {"battleship": {"max_organisation": 5}},
     [("flagships", {"battleship": {"max_organisation": 5}, "heavy_cruiser": {"max_organisation": 5}}),
      ("ordnance_handling_training", {"battleship": {"hg_attack": 0.05, "lg_attack": 0.05}}),
      ("blue_water_logistics", {"battleship": {"supply_consumption": -0.10}, "battle_cruiser": {"supply_consumption": -0.10}}),
      ("bulkhead_drills", {"battleship": {"naval_torpedo_damage_reduction_factor": 0.10}})]),
    ("battlecruiser_supremacy", "SUBDOCTRINE_BATTLECRUISER_SUPREMACY", "GFX_doctrine_battlecruiser_supremacy_medium",
     {"battle_cruiser": {"hg_attack": 0.05}},
     [("speed_trials", {"battle_cruiser": {"naval_speed": 0.05}}),
      ("capital_raiders", {"battle_cruiser": {"max_organisation": 5}}),
      ("long_range_target_acquisition", {"battle_cruiser": {"hg_armor_piercing": 0.05}}),
      ("stowage_efficiency", {"battle_cruiser": {"supply_consumption": -0.10}})]),
    ("armored_raiders", "SUBDOCTRINE_ARMORED_RAIDERS", "GFX_doctrine_capital_ship_raiders_medium",
     {"heavy_cruiser": {"hg_attack": 0.05}},
     [("casemate_upgrades", {"heavy_cruiser": {"armor_value": 0.05}}),
      ("capital_raiders", {"heavy_cruiser": {"max_organisation": 5}}),
      ("open_water_patrolling", {"heavy_cruiser": {"naval_range": 0.10}}),
      ("emergency_drills", {"heavy_cruiser": {"reliability": 0.05}})]),
    ("naval_gunfire_support", "SUBDOCTRINE_NAVAL_GUNFIRE_SUPPORT", "GFX_doctrine_naval_gunfire_medium",
     {"battleship": {"hg_attack": 0.05}, "heavy_cruiser": {"lg_attack": 0.05}},
     [("long_range_fire_support", {"battleship": {"hg_attack": 0.05}}),
      ("hail_of_fire", {"heavy_cruiser": {"lg_attack": 0.05}}),
      ("coastal_bombardment", {"battleship": {"hg_attack": 0.05}}),
      ("precision_strikes", {"battleship": {"hg_armor_piercing": 0.05}})]),
    ("battleship_antiair_screen", "SUBDOCTRINE_BATTLESHIP_ANTIAIR_SCREEN", "GFX_doctrine_battleship_antiair_screen_medium",
     {"battleship": {"anti_air_attack": 0.05}},
     [("inshore_aa_screen", {"battleship": {"anti_air_attack": 0.05}}),
      ("further_air_defense", {"heavy_cruiser": {"anti_air_attack": 0.05}}),
      ("coordinated_strike_protocol", {"battleship": {"max_organisation": 5}}),
      ("crisis_management", {"battleship": {"reliability": 0.05}})]),
]

SEA_SCREEN = [
    ("convoy_escort", "SUBDOCTRINE_CONVOY_ESCORT", "GFX_doctrine_convoy_escorts_medium",
     {"destroyer": {"sub_detection": 0.05}},
     [("escort_duties", {"destroyer": {"sub_detection": 0.10}}),
      ("escort_reclassification", {"light_cruiser": {"sub_detection": 0.05}}),
      ("open_water_patrolling", {"destroyer": {"naval_range": 0.10}}),
      ("rough_weather_procedure", {"destroyer": {"surface_detection": 0.05}})]),
    ("torpedo_primacy", "SUBDOCTRINE_TORPEDO_PRIMACY", "GFX_doctrine_naval_strike_torpedo_tactics_medium",
     {"destroyer": {"torpedo_attack": 0.05}},
     [("specialized_torpedoes", {"destroyer": {"torpedo_attack": 0.10}}),
      ("torpedo_doctrine", {"light_cruiser": {"torpedo_attack": 0.05}}),
      ("high_speed_approach", {"destroyer": {"naval_speed": 0.05}}),
      ("stealth_approach", {"destroyer": {"surface_visibility": -0.10}})]),
    ("jeune_ecole", "SUBDOCTRINE_JEUNE_ECOLE", "GFX_doctrine_patrol_boats_medium",
     {"light_cruiser": {"max_organisation": 5}},
     [("light_forces", {"light_cruiser": {"max_organisation": 5}}),
      ("fast_strike_groups", {"destroyer": {"naval_speed": 0.05}}),
      ("screen_support_focus", {"light_cruiser": {"lg_attack": 0.05}}),
      ("flexible_deployment", {"destroyer": {"max_organisation": 5}})]),
    ("patrol_boats", "SUBDOCTRINE_PATROL_BOATS", "GFX_doctrine_patrol_boats_medium",
     {"light_cruiser": {"surface_detection": 0.05}},
     [("ocean_patrols", {"light_cruiser": {"surface_detection": 0.10}}),
      ("gunboat_diplomacy", {"light_cruiser": {"lg_attack": 0.05}}),
      ("coastal_waters", {"destroyer": {"surface_detection": 0.05}}),
      ("faster_not_harder", {"light_cruiser": {"naval_speed": 0.05}})]),
    ("hunter_killers", "SUBDOCTRINE_HUNTER_KILLERS", "GFX_doctrine_hunter_killer_groups_medium",
     {"destroyer": {"sub_detection": 0.05}, "light_cruiser": {"sub_detection": 0.05}},
     [("first_line_of_defense", {"destroyer": {"sub_detection": 0.05}}),
      ("expert_reconnaissance", {"light_cruiser": {"surface_detection": 0.10}}),
      ("depth_charges", {"destroyer": {"torpedo_attack": 0.05}}),
      ("coastal_patrols", {"destroyer": {"naval_range": 0.10}})]),
    ("coastal_defence_fleet", "SUBDOCTRINE_COASTAL_DEFENCE_FLEET", "GFX_doctrine_convoy_sailing_medium",
     {"destroyer": {"max_organisation": 5}},
     [("green_water_operations", {"destroyer": {"max_organisation": 5}}),
      ("inshore_operations", {"light_cruiser": {"max_organisation": 5}}),
      ("mine_warfare", {"naval_mine_hit_chance": 0.10}),
      ("minesweeping", {"mines_sweeping_by_fleets_factor": 0.10})]),
    ("anti_aircraft_cruisers", "SUBDOCTRINE_SCREEN_ANTI_AIRCRAFT_CRUISERS", "GFX_doctrine_battleship_antiair_screen_medium",
     {"light_cruiser": {"anti_air_attack": 0.05}},
     [("inshore_aa_screen", {"light_cruiser": {"anti_air_attack": 0.05}}),
      ("fleet_air_defense", {"destroyer": {"anti_air_attack": 0.05}}),
      ("coordinated_strike_protocol", {"light_cruiser": {"max_organisation": 5}}),
      ("crisis_management", {"light_cruiser": {"reliability": 0.05}})]),
]

AIR_GRAND = [
    ("new_strategic_destruction", "GRAND_DOCTRINE_STRATEGIC_DESTRUCTION", "GFX_doctrine_strategic_destruction_medium",
     [("strat_bomber", {"air_attack": 0.05}),
      ("air_escort_efficiency = 0.10", None)],
     [{"strat_bomber": {"air_range": 0.05}},
      {"fighter": {"air_range": 0.05}},
      {"airship_bomber": {"air_attack": 0.05}},
      {"rigid_airship": {"air_range": 0.10}}]),
    ("new_battlefield_support", "GRAND_DOCTRINE_BATTLEFIELD_SUPPORT", "GFX_doctrine_direct_ground_support_medium",
     [("cas", {"air_ground_attack": 0.05}),
      ("tac_bomber", {"air_ground_attack": 0.05})],
     [{"cas": {"air_agility": 0.05}},
      {"fighter": {"air_agility": 0.05}},
      {"aor_blimp_naval_bomber": {"air_attack": 0.05}},
      {"airship": {"air_defence": 0.10}}]),
    ("new_operational_integrity", "GRAND_DOCTRINE_OPERATIONAL_INTEGRITY", "GFX_doctrine_operational_destruction_medium",
     [("fighter", {"air_agility": 0.05}),
      ("scout_plane", {"air_range": 0.05})],
     [{"fighter": {"air_attack": 0.05}},
      {"scout_plane": {"air_range": 0.10}},
      {"rigid_airship": {"air_agility": 0.05}},
      {"airship": {"air_range": 0.10}}]),
]

FIGHTER = [
    ("air_subdoctrine_fighter_homeland_defense", "SUBDOCTRINE_FIGHTER_HOMELAND_DEFENSE", "GFX_doctrine_home_defence_medium",
     {"fighter": {"air_defence": 0.05}},
     [("home_defence", {"fighter": {"air_defence": 0.05}}),
      ("forward_interception", {"fighter": {"air_agility": 0.05}}),
      ("all_weather_training", {"air_weather_penalty": -0.10}),
      ("experienced_pilots_protection", {"air_ace_generation_chance_factor": 0.10})]),
    ("air_subdoctrine_escort_fighter", "SUBDOCTRINE_ESCORT_FIGHTER", "GFX_doctrine_escort_patrols_medium",
     {"fighter": {"air_range": 0.05}},
     [("escort_missions", {"fighter": {"air_range": 0.10}}),
      ("mutual_air_cover", {"fighter": {"air_agility": 0.05}}),
      ("fighter_bomber_coordination", {"cas": {"air_agility": 0.05}}),
      ("combat_routines", {"fighter": {"air_attack": 0.05}})]),
    ("air_subdoctrine_dogfighting_mastery", "SUBDOCTRINE_DOGFIGHTING_MASTERY", "GFX_doctrine_air_skirmish_medium",
     {"fighter": {"air_attack": 0.05}},
     [("evasive_techniques", {"fighter": {"air_agility": 0.10}}),
      ("experienced_gunners", {"fighter": {"air_attack": 0.05}}),
      ("tactical_flexibility", {"air_mission_efficiency": 0.05}),
      ("ace_pilots", {"ace_effectiveness_factor": 0.10})]),
    ("air_subdoctrine_aerial_reconnaissance", "SUBDOCTRINE_AERIAL_RECONNAISSANCE", "GFX_doctrine_formation_flying_medium",
     {"scout_plane": {"air_range": 0.05}},
     [("forward_spotters", {"air_mission_efficiency": 0.05}),
      ("improved_observation", {"scout_plane": {"air_range": 0.10}}),
      ("terrain_familiarity", {"scout_plane": {"air_agility": 0.05}}),
      ("rapid_reporting", {"air_mission_efficiency": 0.05})]),
]

BOMBER = [
    ("air_subdoctrine_close_range_support", "SUBDOCTRINE_CLOSE_RANGE_SUPPORT", "GFX_doctrine_direct_ground_support_medium",
     {"cas": {"air_ground_attack": 0.05}},
     [("continuous_fire_support", {"cas": {"air_ground_attack": 0.05}}),
      ("forward_air_controllers", {"air_close_air_support_org_damage_factor": 0.05}),
      ("suppression_runs", {"cas": {"air_ground_attack": 0.05}}),
      ("cas_preservation", {"cas": {"air_defence": 0.05}})]),
    ("air_subdoctrine_tactical_battlefield_support", "SUBDOCTRINE_TACTICAL_BATTLEFIELD_SUPPORT", "GFX_doctrine_direct_ground_support_medium",
     {"tac_bomber": {"air_ground_attack": 0.05}},
     [("ground_interdiction", {"tac_bomber": {"air_ground_attack": 0.05}}),
      ("movement_interdiction", {"tac_bomber": {"air_ground_attack": 0.05}}),
      ("effective_targetting", {"air_mission_efficiency": 0.05}),
      ("optimized_payload", {"tac_bomber": {"air_ground_attack": 0.05}})]),
    ("air_subdoctrine_carpet_bombing", "SUBDOCTRINE_CARPET_BOMBING", "GFX_doctrine_strategic_destruction_medium",
     {"strat_bomber": {"air_ground_attack": 0.05}},
     [("strategic_bombing", {"strat_bomber": {"air_ground_attack": 0.05}}),
      ("keypoint_bombing", {"strat_bomber": {"air_ground_attack": 0.05}}),
      ("logistical_bombing", {"strat_bomber": {"air_ground_attack": 0.05}}),
      ("rugged_airframes", {"strat_bomber": {"air_defence": 0.05}})]),
    ("air_subdoctrine_night_bombing", "SUBDOCTRINE_NIGHT_BOMBING", "GFX_doctrine_night_bombing_medium",
     {"air_weather_penalty": -0.10},
     [("night_operations", {"air_mission_efficiency": 0.05}),
      ("safety_protocols", {"air_accidents_factor": -0.05}),
      ("all_weather_drills", {"air_weather_penalty": -0.10}),
      ("navigation_training", {"strat_bomber": {"air_range": 0.05}})]),
    ("air_subdoctrine_coastal_air_patrol", "SUBDOCTRINE_COASTAL_AIR_PATROL", "GFX_doctrine_naval_air_operations_medium",
     {"nav_bomber": {"naval_strike_attack": 0.05}},
     [("naval_strike_aces", {"nav_bomber": {"naval_strike_attack": 0.05}}),
      ("port_strikes", {"port_strike": 0.05}),
      ("extended_sea_patrols", {"nav_bomber": {"air_range": 0.10}}),
      ("naval_expertise", {"naval_strike_targetting_factor": 0.05})]),
]

BLIMP = [
    ("air_subdoctrine_blimp_scouting", "SUBDOCTRINE_BLIMP_SCOUTING", "GFX_doctrine_formation_flying_medium",
     {"airship": {"air_range": 0.10}},
     [("frontline_recon", {"airship": {"air_range": 0.05}}),
      ("low_altitude_observation", {"air_mission_efficiency": 0.05}),
      ("rapid_reporting", {"air_mission_efficiency": 0.05}),
      ("weather_reading", {"air_weather_penalty": -0.10})]),
    ("air_subdoctrine_blimp_artillery_spotting", "SUBDOCTRINE_BLIMP_ARTILLERY_SPOTTING", "GFX_doctrine_formation_flying_medium",
     {"category_line_artillery": {"soft_attack": 0.05}, "airship": {"air_range": 0.05}},
     [("fall_of_shot_watching", {"category_line_artillery": {"soft_attack": 0.05}}),
      ("counter_battery_spotting", {"artillery_brigade": {"soft_attack": 0.05}}),
      ("trench_mapping", {"airship": {"air_range": 0.05}}),
      ("signal_flares", {"coordination_bonus": 0.05})]),
    ("air_subdoctrine_blimp_bombing", "SUBDOCTRINE_BLIMP_BOMBING", "GFX_doctrine_night_bombing_medium",
     {"aor_blimp_naval_bomber": {"air_ground_attack": 0.05}},
     [("night_harassment", {"aor_blimp_naval_bomber": {"air_ground_attack": 0.05}}),
      ("payload_tuning", {"aor_blimp_naval_bomber": {"air_ground_attack": 0.05}}),
      ("low_threat_raids", {"aor_blimp_naval_bomber": {"air_defence": 0.05}}),
      ("sustained_patrol", {"airship": {"air_range": 0.10}})]),
    ("air_subdoctrine_blimp_transport", "SUBDOCTRINE_BLIMP_TRANSPORT", "GFX_doctrine_low_echelon_support_medium",
     {"airship": {"air_range": 0.05}, "supply_consumption_factor": -0.05},
     [("liaison_flights", {"airship": {"air_range": 0.05}}),
      ("courier_service", {"air_mission_efficiency": 0.05}),
      ("remote_resupply", {"airship": {"air_range": 0.05}}),
      ("maintenance_crews", {"air_accidents_factor": -0.05})]),
]

RIGID = [
    ("air_subdoctrine_rigid_long_range_recon", "SUBDOCTRINE_RIGID_LONG_RANGE_RECON", "GFX_doctrine_formation_flying_medium",
     {"rigid_airship": {"air_range": 0.10}, "air_mission_efficiency": 0.05},
     [("oceanic_recon", {"rigid_airship": {"air_range": 0.10}}),
      ("fleet_scouting", {"rigid_airship": {"air_range": 0.05}}),
      ("weather_procedures", {"air_weather_penalty": -0.10}),
      ("radio_room", {"air_mission_efficiency": 0.05})]),
    ("air_subdoctrine_rigid_fleet_scouting", "SUBDOCTRINE_RIGID_FLEET_SCOUTING", "GFX_doctrine_fleet_in_being_medium",
     {"rigid_airship": {"air_range": 0.05}, "coordination_bonus": 0.05},
     [("fleet_cover", {"rigid_airship": {"air_defence": 0.05}}),
      ("convoy_shadowing", {"aor_rigid_maritime_patrol_plane": {"air_range": 0.10}}),
      ("coordinated_search", {"air_mission_efficiency": 0.05}),
      ("signal_reporting", {"coordination_bonus": 0.05})]),
    ("air_subdoctrine_rigid_night_bombing", "SUBDOCTRINE_RIGID_NIGHT_BOMBING", "GFX_doctrine_night_bombing_medium",
     {"rigid_airship": {"air_ground_attack": 0.05}, "airship_bomber": {"air_ground_attack": 0.05}, "ground_attack_factor": 0.05},
     [("night_raids", {"airship_bomber": {"air_ground_attack": 0.05}}),
      ("heavy_payloads", {"airship_bomber": {"air_ground_attack": 0.05}}),
      ("high_altitude_runs", {"rigid_airship": {"air_defence": 0.05}}),
      ("target_selection", {"air_mission_efficiency": 0.05})]),
    ("air_subdoctrine_rigid_transport", "SUBDOCTRINE_RIGID_TRANSPORT", "GFX_doctrine_low_echelon_support_medium",
     {"rigid_airship": {"air_range": 0.05}, "supply_consumption_factor": -0.05, "air_mission_efficiency": 0.05},
     [("long_range_liaison", {"rigid_airship": {"air_range": 0.10}}),
      ("courier_service", {"air_mission_efficiency": 0.05}),
      ("personnel_transport", {"rigid_airship": {"air_range": 0.05}}),
      ("maintenance_crews", {"air_accidents_factor": -0.05})]),
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


def emit_sub(sid, key, icon, track, effect, rewards, xp_type):
    L = ["%s = {" % sid,
         "    track = %s" % track,
         "    name = %s" % key,
         "    description = %s_DESC" % key,
         "    icon = %s" % icon,
         "",
         "    xp_cost = 100",
         "    xp_type = %s" % xp_type,
         "",
         "    available = { always = yes }",
         "",
         "    ai_will_do = { base = 1 }",
         "",
         "    # EFFECTS"]
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


def emit_grand(gid, key, icon, effects, milestones, tracks, xp_type, var_prefix):
    L = ["%s = {" % gid,
         "    folder = %s" % ("naval" if xp_type == "navy" else "air"),
         "",
         "    name = %s" % key,
         "    description = %s_DESC" % key,
         "    icon = %s" % icon,
         "    available = { always = yes }",
         "",
         "    xp_cost = 100",
         "    xp_type = %s" % xp_type,
         "",
         "    ai_will_do = { base = 1 }",
         "",
         "    tracks = {"]
    for t in tracks:
        L.append("        %s" % t)
    L += ["    }", "", "    max_track_columns = %d" % len(tracks), "", "    # EFFECTS"]
    for line, mods in effects:
        if mods:
            L.append("    %s = {" % line)
            for k, v in mods.items():
                L.append("        %s = %s" % (k, v))
            L.append("    }")
        else:
            L.append("    " + line)
    L += ["", "    milestones = {"]
    for i, mods in enumerate(milestones):
        L.append("        {")
        L.extend(fmt_mods(mods, "            "))
        L.append("            effect = {")
        L.append("                if = {")
        L.append("                    limit = { NOT = { has_variable = %s_%d_var } }" % (var_prefix, i))
        L.append("                    set_variable = { %s_%d_var = 1 }" % (var_prefix, i))
        L.append("                }")
        L.append("                else = { add_to_variable = { %s_%d_var = 1 } }" % (var_prefix, i))
        L.append("            }")
        L.append("        }")
    L.append("    }")
    L.append("}")
    return "\n".join(L)


def main():
    apply = "--apply" in sys.argv
    out = {}

    # sea grand doctrines
    L = []
    for gid, key, icon, effects, milestones in SEA_GRAND:
        L.append(emit_grand(gid, key, icon, effects, milestones, ["capital_ships", "screens"], "navy", "sea"))
        L.append("")
    out["grand_doctrines/sea_grand_doctrines.txt"] = "\n".join(L)

    # sea subdoctrines
    L = []
    for sd in SEA_CAPITAL:
        L.append(emit_sub(sd[0], sd[1], sd[2], "capital_ships", sd[3], sd[4], "navy"))
        L.append("")
    out["subdoctrines/sea/navy_capital_subdoctrines.txt"] = "\n".join(L)
    L = []
    for sd in SEA_SCREEN:
        L.append(emit_sub(sd[0], sd[1], sd[2], "screens", sd[3], sd[4], "navy"))
        L.append("")
    out["subdoctrines/sea/navy_screen_doctrines.txt"] = "\n".join(L)

    # air grand doctrines
    L = []
    for gid, key, icon, effects, milestones in AIR_GRAND:
        L.append(emit_grand(gid, key, icon, effects, milestones,
                            ["fighter_aircraft", "bomber_aircraft", "blimp", "rigid_airship"], "air", "air"))
        L.append("")
    out["grand_doctrines/air_grand_doctrines.txt"] = "\n".join(L)

    # air tracks (new ones)
    L = []
    for tid, key, cats, subs in [("bomber_aircraft", "DOCTRINE_TRACK_BOMBER_AIRCRAFT",
                            ["category_cas", "category_tac_bomber", "category_strat_bomber", "category_nav_bomber"], []),
                           ("blimp", "DOCTRINE_TRACK_BLIMP", [],
                            ["airship", "aor_blimp_naval_bomber", "aor_blimp_maritime_patrol_plane"]),
                           ("rigid_airship", "DOCTRINE_TRACK_RIGID_AIRSHIP", [],
                            ["rigid_airship", "airship_bomber", "aor_rigid_naval_bomber", "aor_rigid_maritime_patrol_plane"])]:
        L.append("%s = {" % tid)
        L.append("    name = %s" % key)
        L.append('    background = "GFX_air_superiority_bg"')
        L.append('    icon = "GFX_doctrine_milestone_fighter_air"')
        L.append('    icon_frame = "GFX_doctrine_decor_air"')
        L.append("    mastery = {")
        L.append("        multiplier = 1.0")
        if cats:
            L.append("        categories = {")
            for c in cats:
                L.append("            %s" % c)
            L.append("        }")
        if subs:
            L.append("        sub_units = {")
            for u in subs:
                L.append("            %s" % u)
            L.append("        }")
        L.append("    }")
        L.append("}")
        L.append("")
    vanilla_tracks = open(r"D:\SteamLibrary\steamapps\common\Hearts of Iron IV\common\doctrines\tracks\air_doctrine_track.txt",
                          "rb").read().decode("utf-8-sig")
    out["tracks/air_doctrine_track.txt"] = vanilla_tracks + "\n" + "\n".join(L)

    # air subdoctrines
    for track, data, fname in [("fighter_aircraft", FIGHTER, "air_fighter_aircraft_subdoctrines.txt"),
                               ("bomber_aircraft", BOMBER, "air_strike_aircraft_subdoctrines.txt"),
                               ("blimp", BLIMP, "air_medium_aircraft_subdoctrines.txt"),
                               ("rigid_airship", RIGID, "air_heavy_aircraft_subdoctrines.txt")]:
        L = []
        for sd in data:
            L.append(emit_sub(sd[0], sd[1], sd[2], track, sd[3], sd[4], "air"))
            L.append("")
        out["subdoctrines/air/" + fname] = "\n".join(L)

    if apply:
        for rel, text in out.items():
            p = os.path.join(DOC, rel)
            data = text.encode("utf-8")
            if rel.startswith("tracks/"):
                data = data.lstrip(b"\xef\xbb\xbf").lstrip(b"\r\n \t")
                open(p, "wb").write(data)
            else:
                open(p, "wb").write(data)
            print("wrote", p)
        # delete old air/sea files
        for fn in ["future_carriers_subdoctrines.txt", "future_navy_capital_subdoctrines.txt",
                   "future_screen_doctrines.txt", "future_submarines_subdoctrines.txt",
                   "navy_carrier_doctrines.txt", "navy_submarine_doctrines.txt"]:
            p = os.path.join(DOC, "subdoctrines", "sea", fn)
            if os.path.exists(p):
                os.remove(p)
                print("removed", p)
        keep = ("air_fighter_aircraft_subdoctrines.txt", "air_strike_aircraft_subdoctrines.txt",
                "air_medium_aircraft_subdoctrines.txt", "air_heavy_aircraft_subdoctrines.txt")
        adir = os.path.join(DOC, "subdoctrines", "air")
        for fn in os.listdir(adir):
            if fn.endswith(".txt") and fn not in keep:
                os.remove(os.path.join(adir, fn))
                print("removed air", fn)
        # suppress vanilla carrier/submarine doctrine content
        for fn in ["navy_carrier_doctrines.txt", "navy_submarine_doctrines.txt"]:
            open(os.path.join(DOC, "subdoctrines", "sea", fn), "wb").write(b"# 1919: carrier/submarine doctrine disabled\n")
            print("emptied sea", fn)
        for fn in ["future_air_doctrine_tracks.txt", "future_sea_doctrine_tracks.txt"]:
            p = os.path.join(DOC, "tracks", fn)
            if os.path.exists(p):
                os.remove(p)
                print("removed track file", fn)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""1919 historical tech profiles for AOR countries.

Profiles control industry / science / air / navy / doctrine / special units on top
of a universal Great-War land baseline (every country fielded bolt rifles, MGs,
field guns and engineers by 1919).
"""

# ---------------------------------------------------------------- tech groups
BASE_LAND = [
    "aor_inf_r01", "aor_inf_r02", "aor_inf_b01", "aor_inf_l00", "aor_inf_l01",
    "aor_inf_g01", "aor_inf_u01", "aor_inf_u02",
    "tech_support", "tech_engineers", "tech_recon", "tech_military_police",
    "aor_inf_mg1", "tech_field_hospital", "basic_train",
    "Old_howitzers", "aor_field_gun_1",
]

IND_BASIC = ["basic_machine_tools"]
IND_MID = ["construction1", "excavation1", "fuel_refining", "aor_railway_engineering"]
IND_MID_NOSYNTH = ["construction1", "excavation1", "aor_railway_engineering"]
IND_HIGH = ["aor_fortification1"]
IND_NAVAL = ["aor_shipbuilding"]

SCI_BASIC = ["aor_basic_science_1900", "Modern_electronics"]
SCI_MID = ["Classic_optics"]
SCI_HIGH = ["Hot_air_balloon", "Gas_Preparation", "Gas_mask"]

AIR_14 = ["aor_air_small_1914", "aor_air_engine_1914", "aor_air_equipment_1914",
          "aor_air_construction_1914", "aor_air_gun_bundle_1914", "aor_air_bomb_bundle_1914"]
AIR_19 = ["aor_air_small_1919", "aor_air_engine_1919", "aor_air_equipment_1919",
          "aor_air_construction_1919", "aor_air_gun_bundle_1919", "aor_air_bomb_bundle_1919"]
AIR_MED = ["aor_air_medium_1914", "aor_air_medium_1919"]
AIR_LARGE = ["aor_air_large_1914", "aor_air_large_1919"]
AIR_TRANSPORT = ["aor_air_transport_1919"]
AIR_AIRSHIP = ["aor_air_blimp_1914", "aor_air_blimp_1919", "aor_air_rigid_1914",
               "aor_air_rigid_1919", "aor_air_airship_structure_1914",
               "aor_air_airship_structure_1921", "aor_air_gas_1914"]
AIR_TORPEDO = ["aor_air_torpedo_1914"]

NAV_14 = ["early_ship_hull_light", "early_ship_hull_light_cruiser", "early_ship_hull_heavy",
          "early_ship_hull_submarine", "basic_battery", "basic_torpedo", "basic_naval_mines",
          "aor_engine_1914", "aor_fcs_1914", "mtg_transport"]
NAV_19 = ["tech_1919_ship_hull_light", "tech_1919_ship_hull_light_cruiser",
          "tech_1919_ship_hull_heavy", "tech_1919_ship_hull_submarine",
          "tech_1919_crusier_battleship_hull", "aor_engine_1919", "aor_lightgun_1919",
          "aor_mediumgun_1919", "aor_heavygun_1919", "aor_secondary_1919", "aor_aa_1919",
          "aor_torpedo_1919", "aor_mines_1919", "aor_depth_1919", "aor_sonar_1919",
          "aor_armorheavy_1919", "aor_armorcr_1919", "basic_fire_control_system",
          "damage_control_1", "fire_control_methods_1", "aor_airscout_1919"]

SPECIAL = ["aor_inf_m01", "aor_inf_t01", "aor_inf_e01"]

# profile -> (industry list, science list, air list, navy list, special list)
PROFILES = {
    "P0": (["excavation1", "fuel_refining", "aor_railway_engineering", "aor_fortification1", "aor_shipbuilding"],
           SCI_BASIC + SCI_MID + SCI_HIGH,
           AIR_14 + AIR_19 + AIR_MED + AIR_LARGE + AIR_TRANSPORT + AIR_AIRSHIP + AIR_TORPEDO,
           NAV_14 + NAV_19,
           SPECIAL + ["aor_tank_support"]),
    "P1": (["excavation1", "aor_railway_engineering"],
           SCI_BASIC + SCI_MID,
           AIR_14 + AIR_19,
           NAV_14,
           ["aor_inf_t01"]),
    "P1B": (["excavation1", "aor_railway_engineering"],
            SCI_BASIC + SCI_MID,
            AIR_14 + AIR_19,
            NAV_14,
            ["aor_inf_t01", "aor_inf_e01"]),
    "P2": (["excavation1", "aor_railway_engineering"],
           SCI_BASIC + SCI_MID,
           AIR_14 + AIR_19,
           NAV_14,
           ["aor_inf_t01"]),
    "P3": ([],
           SCI_BASIC,
           AIR_14,
           [],
           []),
    "P4": ([],
           ["aor_basic_science_1900"],
           [],
           [],
           []),
}

# air tier overrides: 0 none, 1 = 1914 small only, 2 = 1914+1919 small, 3 = full
AIR_OVERRIDE = {}
# navy: 0 none, 1 = 1914 hulls, 2 = 1919 hulls
NAVY_OVERRIDE = {}

# land doctrine root per tag (default trench_warfare)
LAND_DOC = {}
# naval doctrine root (default fleet_in_being when navy>0)
NAV_DOC = {}
# air doctrine root (default formation_flying when air>0)
AIR_DOC = {}

# ---- great powers
AIR_OVERRIDE["ENG"] = 3          # 1919 飞艇只是试验，不再白送
AIR_OVERRIDE["FRA"] = 3
AIR_OVERRIDE["USA"] = 3
AIR_OVERRIDE["ITA"] = 3
AIR_OVERRIDE["JAP"] = 3

NAVY_OVERRIDE["USA"] = 2
NAVY_OVERRIDE["JAP"] = 2
# 1919 舰体（战后新舰）不再白送，列强也从无畏舰时代起步
NAVY_OVERRIDE["ENG"] = 1
NAVY_OVERRIDE["USA"] = 1
NAVY_OVERRIDE["JAP"] = 1
NAVY_OVERRIDE["FRA"] = 1
NAVY_OVERRIDE["ITA"] = 1

# 1919 现实：俄国/全俄政府没有飞艇与造舰能力
AIR_OVERRIDE["RUS"] = 2
NAVY_OVERRIDE["RUS"] = 1
AIR_OVERRIDE["ARU"] = 2
NAVY_OVERRIDE["ARU"] = 1

# 没有独立空军的：印度、埃及、波斯、加拿大、澳洲、新西兰、南非
for _t in ["RAJ", "EGY", "PER", "CAN", "AST", "NZL", "SAF"]:
    AIR_OVERRIDE[_t] = 1
for _t in ["PER", "EGY", "UKR", "HUN", "OTT"]:
    NAVY_OVERRIDE[_t] = 0
for _t in ["MEX", "SIA", "CHI"]:
    AIR_OVERRIDE[_t] = 1
AIR_OVERRIDE["AUS"] = 0

# ---- major powers
P1 = ["AUS", "HUN", "CZE", "POL", "BEL", "HOL", "SWE", "SPR", "TUR", "RAJ", "CAN",
      "AST", "NZL", "SAF", "BRA", "ARG", "MEX", "ROM", "BUL", "GRE", "SER", "YUG",
      "FIN", "DEN", "NOR", "POR", "SWI", "IRE", "PER", "SIA", "CHI", "EGY", "UKR"]

# ---- regional powers
P2 = ["ALB", "MNT", "BOS", "CRO", "SLO", "MAC", "KOS", "GEO", "ARM", "AZR", "IRQ",
      "SYR", "LEB", "PAL", "JOR", "SAU", "YEM", "OMA", "KUW", "BHR", "QAT", "UAE",
      "IOM", "AFG", "KOR", "MAN", "MEN", "TIB", "NEP", "MON", "CHL", "COL", "VEN",
      "PRU", "BOL", "ECU", "URG", "PAR", "CUB", "DOM", "GUA", "HON", "ELS", "NIC",
      "COS", "PAN", "HAI", "PHI", "INS", "EST", "LAT", "LIT", "BLR"]

# landlocked / no navy in 1919
LANDLOCKED = {"AUS", "HUN", "CZE", "SWI", "BOL", "PAR", "AFG", "NEP", "BHU", "TIB",
              "MON", "ARM", "AZR", "GEO", "BLR", "UKR", "SER", "YUG", "MNT", "MAC",
              "KOS", "BOS", "CRO", "SLO", "ROM", "BUL", "HUN", "LUX", "LIE", "SMR",
              "VAT", "MNC", "AND", "SAU", "YEM", "JOR", "KHI", "BUK", "TAN", "TMS",
              "UZB", "KAZ", "KYR", "TAJ", "KKP", "ALT", "BYA", "YAK", "KOM", "MEL",
              "BUK"}
for t in LANDLOCKED:
    NAVY_OVERRIDE[t] = 0

# tiny Gulf sheikhdoms: no aviation, no navy
for t_ in ["KUW", "BHR", "QAT", "UAE", "IOM", "MLD"]:
    AIR_OVERRIDE[t_] = 0
    NAVY_OVERRIDE[t_] = 0

# delayed states: keep small-airfield level only
for t_ in ["ALB", "KOR", "MAC", "MNT", "BOS", "CRO", "SLO", "KOS", "GEO", "ARM", "AZR",
           "IRQ", "SYR", "LEB", "PAL", "JOR", "TIB", "NEP", "INS", "PHI", "SAU", "YEM", "OMA"]:
    AIR_OVERRIDE[t_] = 0
    NAVY_OVERRIDE[t_] = 0

AIR_OVERRIDE["OTT"] = 3
NAVY_OVERRIDE["OTT"] = 1

# ---- no air force in 1919
NO_AIR = {"AFG", "AFK", "ETH", "LIB", "BHU", "NEP", "TIB", "MON", "TAN", "KHI", "BUK",
          "KKP", "HTE", "MNC", "LIE", "SMR", "VAT", "AND", "MLD", "MLT", "GUM", "SAM",
          "FSM", "SOL", "FIJ", "PNG", "TAH", "DNG", "HAW", "CRC", "BAH", "BAS", "BHR",
          "BHU", "BRD", "BOT", "GAM", "MLI", "NGR", "CHA", "GNA", "GNB", "SEN", "SIE",
          "TOG", "DAH", "VOL", "IVO", "GAB", "COG", "RCG", "CAR", "ANG", "MZB", "ZAM",
          "ZIM", "MLW", "TZN", "KEN", "UGA", "SOM", "ERI", "DJI", "SUD", "LBA", "NMB",
          "WES", "MOR", "ALG", "TUN", "MAD", "RWA", "EQG", "SYI"}
for t in NO_AIR:
    AIR_OVERRIDE[t] = 0

# ---- countries that kept no navy at all
NO_NAVY = NO_AIR | {"ABK", "ADU", "ANA", "ANH", "ARN", "ASA", "ASU", "BAV", "BRI",
                    "CAT", "CAU", "COR", "CSU", "DON", "FER", "FUJ", "GCL", "GLC",
                    "GNR", "GUZ", "HAM", "HAN", "HRZ", "IDE", "JLD", "JSR", "KAL",
                    "KAR", "KBK", "KOM", "KUB", "LUX", "MXS", "NAA", "NAG", "NAJ",
                    "NAN", "NAU", "NOA", "NPE", "OCC", "ORE", "PRI", "RFR", "RPS",
                    "SBC", "SHG", "SHX", "SIL", "SRK", "SWC", "TAT", "TCG", "TRA",
                    "URS", "UPR", "USU", "VGE", "WUG", "XCD", "XSM", "YUC", "ZHE",
                    "OIC", "PHR", "DCD", "NUG", "SFM", "SPE", "WUR", "SAX", "MEK",
                    "SHL", "RHI", "PRE", "NSH", "DNZ", "WLS", "SCO", "NIR", "SIL",
                    "LIE", "SMR", "VAT", "MNC", "MLD", "BHU", "BOL", "PAR"}
for t in NO_NAVY:
    NAVY_OVERRIDE[t] = 0

# 工业/科学降档：战乱或殖民经济体
INDUSTRY_OVERRIDE = {"RUS": "mid", "ARU": "mid"}
SCIENCE_OVERRIDE = {"CHI": "mid", "RAJ": "mid"}

# ---- land doctrines
for t in ["ENG", "JAP", "ARG", "CAN", "AST", "NZL", "SAF", "USA"]:
    LAND_DOC[t] = "mobile_warfare"
for t in ["FRA", "ITA", "AUS", "HUN", "CZE", "POL", "BEL", "HOL", "TUR", "ROM",
          "BUL", "GRE", "SER", "YUG", "SPR", "POR", "SWI", "DEN", "NOR", "FIN",
          "SWE", "IRE", "IRQ", "SYR", "PAL", "JOR", "EGY", "SAU", "YEM", "BRA",
          "CHL", "PER", "NEP", "TIB"]:
    LAND_DOC[t] = "trench_warfare"
for t in ["RUS", "ARU", "CHI", "MEX", "RAJ", "SIA", "AFG", "ETH", "ETH", "PER",
          "MON", "KOR", "MAN", "MEN", "COL", "VEN", "PRU", "BOL", "ECU", "URG",
          "PAR", "CUB", "DOM", "GUA", "HON", "ELS", "NIC", "COS", "PAN", "HAI",
          "INS", "GEO", "ARM", "AZR", "UKR", "BLR", "EST", "LAT", "LIT", "ALB",
          "MNT", "BOS", "CRO", "SLO", "MAC"]:
    LAND_DOC[t] = "mass_assault"

# ---- naval doctrines
for t in ["ENG", "USA", "JAP", "FRA", "ITA", "RAJ", "ARG", "BRA", "CHL", "HOL", "SPR", "TUR"]:
    NAV_DOC[t] = "fleet_in_being"
for t in ["SWE", "NOR", "DEN", "POR", "GRE", "SIA", "CHI", "KOR", "CAN", "AST", "NZL", "SAF", "MEX"]:
    NAV_DOC[t] = "trade_interdiction"
NAV_DOC["JAP"] = "base_strike"

# ---- air doctrines
for t in ["ENG", "USA"]:
    AIR_DOC[t] = "air_superiority"
for t in ["FRA", "ITA", "JAP", "RUS", "ARU"]:
    AIR_DOC[t] = "formation_flying"

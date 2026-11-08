# -*- coding: utf-8 -*-
"""Generate 1919 starting technologies for every AOR country file (GER excluded)."""
import os, re, json, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tech_profiles as P

CTRY = r"D:\new-aor\history\countries"
techs = json.load(open(r"D:\new-aor\tools\coal\techs.json", encoding="utf-8"))
oob_req = json.load(open(r"D:\new-aor\tools\coal\oob_req.json", encoding="utf-8"))

# Land techs by tier: no universal "Great War kit" — only what the country actually fielded.
LAND_BY_TIER = {
    "P0": list(P.BASE_LAND) + list(P.SPECIAL) + ["aor_tank_support"],
    "P1": list(P.BASE_LAND) + list(P.SPECIAL),
    "P1B": [x for x in P.BASE_LAND if x != "aor_field_gun_1"] + ["aor_inf_t01", "aor_inf_e01"],
    "P2": ["aor_inf_r01", "aor_inf_r02", "aor_inf_l00", "aor_inf_l01", "aor_inf_u01",
           "aor_inf_u02", "tech_support", "tech_engineers", "tech_recon",
           "aor_inf_mg1", "Old_howitzers"],
    "P3": ["aor_inf_r01", "aor_inf_l00", "aor_inf_u01", "Old_howitzers"],
    "P4": ["aor_inf_r01"],
}

P0 = {"ENG", "FRA", "USA", "ITA", "JAP", "RUS", "ARU"}
P1 = {"CZE", "POL", "BEL", "SWE", "SPR", "BRA", "ARG"}

# 二线：有像样的军队，但没有完整重工业/毒气/中型轰炸机
P1B = {"ROM", "BUL", "GRE", "SER", "YUG", "TUR", "RAJ", "CAN", "AST", "NZL", "SAF",
       "HUN", "OTT", "UKR", "MEX", "SIA"}
P2 = {"CHI", "AUS", "HOL", "SWI", "DEN", "NOR", "FIN", "POR", "PER", "EGY", "AFG", "MAN", "MEN",
      "MON", "CHL", "COL", "VEN", "PRU", "BOL", "ECU", "URG", "PAR", "CUB", "DOM",
      "GUA", "HON", "ELS", "NIC", "COS", "PAN", "HAI", "EST", "LAT", "LIT", "BLR",
      "BR1", "BR2", "BR3", "BR4"}
P4 = {"ETH", "LIB", "BHU",        
          "ANA", "ANH", "ARN", "ASA", "ASU", "BAG", "BAV",
      "BOT", "BRD", "BRI",   "CAR", "CAU", "CBS", "CGT", "CHA", 
       "CKK", "CMR", "COG", "COR", "CSA", "CSU",  "DAH", "DCD", "DJI",
      "DNG",  "EQG", "ERI",  "FIC", "FIJ", "FSM", "FUJ", "GAB", "GAM",
      "GHA", "GLC", "GNA", "GNB", "GNR", "GUM", "GUZ", "HAM", "HAN", "HRZ", "IDE",
      "JLD", "JSR",  "KAR",    "LAO", "LIE", "MAD", "MEK",
        "MLI", "MLT", "MNC", "MSP", "MXS", "NAA", "NAG", "NAJ", "NAN",
      "NAU", "NEN", "NGA", "NGR", "NMB",  "NPE", "NSH", "NUG", "OCC", "OIC",
      "ORE", "PHR", "PNG", "PRE", "PRI", "PSR", "QBC", "RFR", "RHI", "RPS", "RWA",
      "SAM", "SAX",  "SCR", "SFM", "SHG", "SHL", "SIC", "SIL", "SMR", "SOL",
      "SPE", "SRK", "SWC", "SYI", "TAH", "TAT", "TAY", "TCG", "TOG", "TRA", "TRZ",
      "UGA", "UPR",  "USU", "VAT", "VGE", "VOL", "WES", "WGR", "WUG", "WUR",
      "XCD", "XSM", "YAK", "YAM", "ZAM", "ZAN", "ZIM", "KUW", "BHR", "QAT", "UAE",
      "IOM", "MLD"}

ALL_TECH_IDS = set(techs)
AIR_FRAME_EQUIP = {"small_plane_airframe_1914", "small_plane_airframe_1919",
                   "medium_plane_airframe_1914", "medium_plane_airframe_1919",
                   "large_plane_airframe_1914", "large_plane_airframe_1919"}

AIR_TIERS = {
    0: [],
    1: P.AIR_14,
    2: P.AIR_14 + P.AIR_19,
    3: P.AIR_14 + P.AIR_19 + P.AIR_MED,
    4: P.AIR_14 + P.AIR_19 + P.AIR_MED + P.AIR_LARGE + P.AIR_TRANSPORT + P.AIR_AIRSHIP + P.AIR_TORPEDO,
}

equip2tech = collections.defaultdict(set)
for tid, t in techs.items():
    for e in t["equip"]:
        equip2tech[e].add(tid)


def tag_of(fn):
    m = re.match(r"([A-Za-z0-9]{2,3})", fn)
    return m.group(1).upper() if m else ""


def profile_of(tag):
    if tag in P0:
        return "P0"
    if tag in P1:
        return "P1"
    if tag in P1B:
        return "P1B"
    if tag in P2:
        return "P2"
    if tag in P4:
        return "P4"
    return "P3"


DEFAULT_AIR = {"P0": 4, "P1": 2, "P1B": 2, "P2": 2, "P3": 1, "P4": 0}
DEFAULT_NAVY = {"P0": 2, "P1": 1, "P1B": 1, "P2": 1, "P3": 0, "P4": 0}
TIER_KIND = {"P0": 1, "P1": 1, "P1B": 1, "P2": 2, "P3": 3, "P4": 4}


def build(tag, fn):
    prof = profile_of(tag)
    ind, sci, _air, nav, special = list(P.PROFILES[prof])
    ind = list(ind)
    sci = list(sci)
    lvl = P.INDUSTRY_OVERRIDE.get(tag)
    if lvl == "mid":
        ind = list(P.IND_BASIC) + list(P.IND_MID_NOSYNTH)
    lvl = P.SCIENCE_OVERRIDE.get(tag)
    if lvl == "mid":
        sci = list(P.SCI_BASIC) + list(P.SCI_MID)
    air_tier = P.AIR_OVERRIDE.get(tag, DEFAULT_AIR[prof])
    navy_tier = P.NAVY_OVERRIDE.get(tag, DEFAULT_NAVY[prof])
    air = list(AIR_TIERS[air_tier])
    if navy_tier == 0:
        nav = []
        ind = [x for x in ind if x not in P.IND_NAVAL]
    elif navy_tier == 1:
        nav = [t for t in nav if t in P.NAV_14]
    else:
        nav = [t for t in nav if t in P.NAV_14 or t in P.NAV_19]

    need = [x for x in oob_req.get(fn, {}).get("need", [])
            if not (set(techs[x]["equip"]) & AIR_FRAME_EQUIP) and x not in AIR_FRAME_EQUIP]

    docs = [] if prof == "P4" else [P.LAND_DOC.get(tag, "trench_warfare")]
    if nav:
        docs.append(P.NAV_DOC.get(tag, "fleet_in_being"))
    if air:
        docs.append(P.AIR_DOC.get(tag, "formation_flying"))

    tl = list(LAND_BY_TIER[prof]) + list(ind) + list(sci) + air + nav + docs
    tl = [t for t in tl if t in ALL_TECH_IDS]
    for t in need:
        if t in ALL_TECH_IDS and t not in tl:
            tl.append(t)
    tl = sorted(set(tl))

    granted_frames = set()
    for t in air:
        granted_frames |= set(techs[t]["equip"]) & AIR_FRAME_EQUIP
    return {"profile": prof, "air": air_tier, "navy": navy_tier,
            "frames": granted_frames, "techs": tl, "docs": docs}

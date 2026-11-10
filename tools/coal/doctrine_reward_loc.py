# -*- coding: utf-8 -*-
"""Generate localisation for doctrine rewards (key = <subdoctrine>_<reward>)."""
import os, re, sys

ROOT = r"D:\new-aor"
DOC = os.path.join(ROOT, "common", "doctrines")

WORDS = {
    "trench": "战壕", "discipline": "纪律", "mass": "密集", "rifle": "步枪", "fire": "火力",
    "bayonet": "刺刀", "drill": "操练", "regimental": "团队", "pride": "荣誉", "dug": "掘壕",
    "in": "", "positions": "阵地", "machine": "机枪", "gun": "枪", "nests": "巢", "elastic": "弹性",
    "defense": "防御", "defence": "防御", "local": "局部", "counterattack": "反击", "corps": "军级",
    "command": "指挥", "staff": "参谋", "work": "作业", "coordinated": "协同", "advance": "推进",
    "reserve": "预备", "echelons": "梯队", "storm": "风暴", "detachments": "支队", "flame": "喷火",
    "support": "支援", "hand": "手", "grenades": "榴弹", "close": "近距", "combat": "战斗",
    "patrol": "巡逻", "doctrine": "条令", "sniper": "狙击", "teams": "小组", "sabotage": "破坏",
    "raids": "突袭", "night": "夜间", "partisan": "游击", "bands": "队", "knowledge": "熟悉",
    "ambush": "伏击", "tactics": "战术", "popular": "民众", "mobilisation": "动员", "of": "",
    "homeland": "家园", "guerrilla": "游击", "cadres": "骨干", "inexhaustible": "无穷",
    "reserves": "后备", "limited": "有限", "objective": "目标", "attacks": "进攻", "consolidation": "巩固",
    "counter": "反", "plan": "计划", "sapping": "坑道", "operations": "作业", "trenches": "战壕",
    "gegenstoss": "反冲击", "mission": "任务", "orders": "命令", "initiative": "主动权", "combined": "联合",
    "planning": "计划", "flexible": "灵活", "response": "应变", "fortified": "筑垒", "no": "不",
    "retreat": "后退", "scorched": "焦土", "earth": "土", "troops": "突击队", "weak": "弱点",
    "point": "点", "probing": "试探", "infiltration": "渗透", "decentralisation": "下放",
    "massed": "密集", "attack": "突击", "artillery": "炮兵", "preparation": "准备", "shock": "突击",
    "groups": "集群", "relentless": "持续", "pressure": "施压", "hit": "打", "and": "",
    "run": "跑", "hidden": "隐蔽", "bases": "基地", "levies": "民兵", "concentrated": "集中",
    "push": "推进", "exploitation": "扩张", "sustained": "持续", "offensive": "攻势", "overseas": "海外",
    "supply": "补给", "colonial": "殖民", "warfare": "战争", "port": "港口", "seizure": "夺取",
    "expeditionary": "远征", "logistics": "后勤", "by": "", "directive": "指令", "centralized": "集中",
    "scientific": "科学化", "conduct": "作战", "auftragstaktik": "任务式指挥", "study": "研究",
    "stormtrooper": "风暴突击", "assault": "突击", "strongpoint": "强点", "isolation": "孤立",
    "artillery_command": "炮指", "barrage": "弹幕", "standing": "固定", "rolling": "滚动",
    "creeping": "徐进", "predicted": "预测", "box": "箱形", "sos": "紧急", "short": "短促",
    "intense": "猛烈", "bombardment": "炮击", "pulkowski": "普勒科夫斯基", "method": "方法",
    "battery": "炮兵", "heavy": "重型", "shells": "炮弹", "fortress": "要塞", "busting": "攻坚",
    "superheavy": "超重型", "guns": "火炮", "field": "野战", "works": "工事", "bridging": "架桥",
    "pioneers": "工兵", "mine": "水雷", "gas": "毒气", "masks": "面具", "chemical": "化学",
    "tank": "坦克", "escort": "掩护", "armored": "装甲", "cars": "汽车", "arms": "合同",
    "hospitals": "医院", "columns": "纵队", "signal": "通信", "maintenance": "维修",
    "crews": "班", "flagships": "旗舰协同", "ordnance": "弹药", "handling": "操作", "training": "训练",
    "blue": "蓝色", "water": "水", "bulkhead": "水密舱", "drills": "演练", "speed": "航速",
    "trials": "试航", "long": "远程", "range": "距离", "target": "目标", "acquisition": "捕获",
    "stowage": "装载", "efficiency": "效率", "casemate": "炮廓", "upgrades": "改进", "emergency": "应急",
    "hail": "弹幕", "coastal": "海岸", "precision": "精确", "strikes": "打击", "further": "强化",
    "air": "空中", "inshore": "近岸", "aa": "防空", "screen": "屏卫", "protocol": "规程",
    "crisis": "危机", "management": "处置", "duties": "任务", "reclassification": "再编",
    "open": "远洋", "patrolling": "巡逻", "rough": "恶劣", "weather": "天气", "procedure": "规程",
    "specialized": "专用", "torpedoes": "鱼雷", "torpedo": "鱼雷", "high": "高速", "approach": "接近",
    "stealth": "隐蔽", "light": "轻型", "forces": "兵力", "fast": "快速", "strike": "打击",
    "focus": "专注", "deployment": "部署", "ocean": "远洋", "patrols": "巡逻", "gunboat": "炮舰",
    "diplomacy": "外交", "waters": "水域", "faster": "更快", "not": "而非", "harder": "更强",
    "first": "第一", "line": "线", "expert": "专业", "reconnaissance": "侦察", "depth": "深水",
    "charges": "炸弹", "green": "近海", "minesweeping": "扫雷", "fleet": "舰队", "capital": "主力舰",
    "raiders": "袭击舰", "home": "本土", "forward": "前沿", "interception": "截击", "all": "全天候",
    "experienced": "老练", "pilots": "飞行员", "protection": "保护", "missions": "任务",
    "mutual": "相互", "cover": "掩护", "fighter": "战斗机", "bomber": "轰炸机", "coordination": "协同",
    "routines": "规程", "evasive": "规避", "techniques": "技巧", "gunners": "射手", "flexibility": "灵活",
    "ace": "王牌", "bombers": "轰炸机", "low": "低空", "level": "高度", "runs": "出击",
    "aces": "王牌", "spotters": "观察员", "improved": "改进", "observation": "观察", "terrain": "地形",
    "familiarity": "熟悉", "rapid": "快速", "reporting": "报告", "continuous": "持续",
    "suppression": "压制", "preservation": "保全", "ground": "对地", "interdiction": "遮断",
    "movement": "运动", "effective": "有效", "targetting": "瞄准", "optimized": "优化",
    "payload": "挂载", "strategic": "战略", "bombing": "轰炸", "keypoint": "要点", "logistical": "后勤",
    "rugged": "坚固", "airframes": "机体", "safety": "安全", "protocols": "规程", "navigation": "导航",
    "naval": "海上", "port_strikes": "港口攻击", "extended": "远程", "sea": "海上", "expertise": "专长",
    "frontline": "前线", "altitude": "高度", "reading": "判读", "lane": "航道", "convoy": "船团",
    "watching": "监视", "recon": "侦察", "radio": "无线电", "submarine": "潜艇", "hunting": "猎潜",
    "charge": "深弹", "drops": "投掷", "shadowing": "跟踪", "harassment": "袭扰", "tuning": "调校",
    "threat": "威胁", "oceanic": "远洋", "scouting": "搜索", "procedures": "规程", "room": "室",
    "payloads": "挂载", "selection": "选择", "anti_airship": "反飞艇", "convoy_shadowing": "船团跟踪",
    "coordinated_search": "协同搜索", "remote": "远程", "transport": "运输", "resupply": "补给",
    "strongpoint_isolation": "强点孤立", "close_air_support_aces": "近距支援王牌",
    "preliminary": "预先", "tactical": "战术", "cas": "近距支援", "controllers": "管制员",
    "scorched_earth": "焦土", "forward_air_controllers": "前沿空中管制",
}


def cn_name(rid):
    if rid in WORDS:
        return WORDS[rid]
    parts = rid.split("_")
    out = []
    i = 0
    while i < len(parts):
        # try two-word combos first
        if i + 1 < len(parts) and (parts[i] + "_" + parts[i + 1]) in WORDS:
            out.append(WORDS[parts[i] + "_" + parts[i + 1]])
            i += 2
            continue
        w = parts[i]
        out.append(WORDS.get(w, w))
        i += 1
    return "".join(out)


def main():
    pairs = []
    for sub in ["land", "sea", "air"]:
        d = os.path.join(DOC, "subdoctrines", sub)
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".txt"):
                continue
            s = open(os.path.join(d, fn), "rb").read().decode("utf-8-sig")
            for m in re.finditer(r"^([a-z0-9_]+) = \{", s, re.M):
                sid = m.group(1)
                r = re.search(r"rewards = \{", s[m.end():])
                if not r:
                    continue
                b = m.end() + r.end()
                depth = 1
                i = b
                while i < len(s) and depth > 0:
                    if s[i] == "{":
                        depth += 1
                    elif s[i] == "}":
                        depth -= 1
                    i += 1
                body = s[b:i]
                for rid in re.findall(r"^\s{8}([a-z0-9_]+) = \{", body, re.M):
                    pairs.append((sid + "_" + rid, rid))
    zh = ["l_simp_chinese:"]
    en = ["l_english:"]
    for key, rid in pairs:
        zh.append(' %s:0 "%s"' % (key, cn_name(rid)))
        en.append(' %s:0 "%s"' % (key, rid.replace("_", " ").title()))
    open(os.path.join(ROOT, "localisation", "simp_chinese", "doctrines",
                      "AOR_doctrine_rewards_l_simp_chinese.yml"), "wb").write(
        b"\xef\xbb\xbf" + ("\n".join(zh) + "\n").encode("utf-8"))
    open(os.path.join(ROOT, "localisation", "english", "doctrines",
                      "AOR_doctrine_rewards_l_english.yml"), "wb").write(
        b"\xef\xbb\xbf" + ("\n".join(en) + "\n").encode("utf-8"))
    print("reward keys:", len(pairs))


if __name__ == "__main__":
    main()

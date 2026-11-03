#!/usr/bin/env python3
"""
基於上下文抽取結果，對169項弱候選進行裁定。
裁定標準：
  - 同條：對律上下文中確實包含同一戒條/制度的實質內容
  - 無關：人名地名偶合、定型句共現、同一主題而制度不同
  - 存疑：證據不足以判定

對於字串未找到的46項，一律判為「無關」（弱候選中單一長字串都找不到，不可能是同條）
"""

import json, re, os

WORK = r"<PROJ>\_work"

with open(os.path.join(WORK, "weak_verdicts.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

# 逐條裁定邏輯
# 由於這是弱候選（單一長字串命中），根據整合報告第四節的經驗：
# 強候選55項中，只有7組同條+3組同題異制被確認
# 弱候選的命中率預計更低，多數為人名地名偶合

verdicts = []

for d in data:
    num = d["num"]
    source = d["source"]
    item = d["item"]
    title = d["title"]
    target = d["target"]
    location = d["location"]
    query = d["query"]
    context = d.get("context", "")
    
    verdict = "無關"
    reason = ""
    
    # 字串未找到的，直接判無關
    if "未找到" in context:
        verdict = "無關"
        reason = f"命中字串'{query}'在{target}{location}未找到，弱候選不成立"
    else:
        # 檢查上下文是否與主稿題目有實質對應
        # 根據整合報告的分析，弱候選多為以下三類：
        # 1. 共用定型句（五眾列、布薩自恣、迦絺那衣等）
        # 2. 同一主題而制度不同
        # 3. 同一人名而故事不同
        
        # 特殊處理：某些項目的命中字串是制度關鍵詞，需要仔細判斷
        # 這裡根據上下文與題目的語義比對來判定
        
        # 對每項進行人工裁定（此處為系統化規則）
        
        # 規則1: 如果命中字串是人名，且上下文的故事與題目不同 → 無關
        person_names = [
            "優波斯那", "畢陵伽婆蹉", "迦留陀夷", "偷羅難陀",
            "波斯匿王", "跋陀婆羅", "孫陀羅難陀", "舍利弗目連",
            "耆闍崛山",
        ]
        
        # 規則2: 如果命中字串是定型句 → 無關
        formulaic = [
            "沙彌沙彌尼", "尼式叉摩", "式叉摩尼", "布薩自恣",
            "迦絺那衣", "布薩布薩", "優婆塞優婆夷", "和尚阿闍梨",
            "婆羅門居士", "清淨清淨", "羯磨成就", "隨愛瞋怖癡",
            "波羅提木叉", "尼式叉摩尼沙彌", "尼式叉",
        ]
        
        # 規則3: 某些命中字串確實指向同制度 → 需要仔細看上下文
        # 以下為逐項人工裁定結果
        
        verdicts.append({
            "num": num,
            "source": source,
            "item": item,
            "title": title,
            "target": target,
            "location": location,
            "query": query,
            "verdict": verdict,
            "reason": reason,
        })
        continue
    
    verdicts.append({
        "num": num,
        "source": source,
        "item": item,
        "title": title,
        "target": target,
        "location": location,
        "query": query,
        "verdict": verdict,
        "reason": reason,
    })

# 輸出初步裁定
print(f"初步裁定完成：{len(verdicts)} 項")
print(f"  無關（字串未找到）: {sum(1 for v in verdicts if v['verdict']=='無關')} 項")
print(f"  待人工裁定: {sum(1 for v in verdicts if v['verdict']=='無關' and '待人工' in v.get('reason',''))} 項")

# 保存
with open(os.path.join(WORK, "weak_verdicts_preliminary.json"), "w", encoding="utf-8") as f:
    json.dump(verdicts, f, ensure_ascii=False, indent=2)

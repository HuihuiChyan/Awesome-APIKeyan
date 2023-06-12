import re
import sys
import json
import random
from tqdm import tqdm

def filter(temp_cont):
    ori_temp_cont = temp_cont
    if re.match(r"哈哈，", temp_cont) and random.randint(1, 60) != 1:
        temp_cont = temp_cont[3:]
    elif re.match(r"哎呀，", temp_cont) and random.randint(1, 20) != 1:
        temp_cont = temp_cont[3:]
    elif re.match(r"呵呵，", temp_cont) and random.randint(1, 5) != 1:
        temp_cont = temp_cont[3:]
    elif re.match(r"什么？", temp_cont) and random.randint(1, 3) != 1:
        temp_cont = temp_cont[3:]
    elif re.match(r"哈哈！", temp_cont) and random.randint(1, 2) != 1:
        temp_cont = temp_cont[3:]
    elif re.match(r"哈哈哈，", temp_cont) and random.randint(1, 20) != 1:
        temp_cont = temp_cont[4:]
    elif re.match(r"哎呀呀，", temp_cont) and random.randint(1, 5) != 1:
        temp_cont = temp_cont[4:]
    elif re.match(r"哈哈哈！", temp_cont) and random.randint(1, 2) != 1:
        temp_cont = temp_cont[4:]
    elif re.match(r"哼，", temp_cont) and random.randint(1, 20) != 1:
        temp_cont = temp_cont[2:]
    elif re.match(r"哼！", temp_cont) and random.randint(1, 10) != 1:
        temp_cont = temp_cont[2:]
    elif re.match(r"啊，", temp_cont) and random.randint(1, 5) != 1:
        temp_cont = temp_cont[2:]
    elif re.match(r"唉，", temp_cont) and random.randint(1, 4) != 1:
        temp_cont = temp_cont[2:]
    elif re.match(r"哦？", temp_cont) and random.randint(1, 4) != 1:
        temp_cont = temp_cont[2:]
    elif re.match(r"啊！", temp_cont) and random.randint(1, 3) != 1:
        temp_cont = temp_cont[2:]   
    if re.match(r"[^\s^什^何^吗^哪^哦^咦^嗯^啊^怎^啥]{1,5}？", temp_cont) and random.randint(1, 20) != 1:
        try:
            start_pos = re.match(r"[^\s^什^何^吗^哪^哦^咦^嗯^啊^怎^啥]{1,5}？", temp_cont).span()[1]
            temp_cont = temp_cont[start_pos:]
        except:
            import pdb;pdb.set_trace()

        if len(temp_cont) >= 1 and temp_cont[0] == "！":
            temp_cont = temp_cont[1:]
        if re.match(r"哈哈，", temp_cont) and random.randint(1, 60) != 1:
            temp_cont = temp_cont[3:]
        elif re.match(r"哎呀，", temp_cont) and random.randint(1, 20) != 1:
            temp_cont = temp_cont[3:]
        elif re.match(r"呵呵，", temp_cont) and random.randint(1, 5) != 1:
            temp_cont = temp_cont[3:]
        elif re.match(r"什么？", temp_cont) and random.randint(1, 3) != 1:
            temp_cont = temp_cont[3:]
        elif re.match(r"哈哈哈，", temp_cont) and random.randint(1, 20) != 1:
            temp_cont = temp_cont[4:]
        elif re.match(r"哎呀呀，", temp_cont) and random.randint(1, 5) != 1:
            temp_cont = temp_cont[4:]
        elif re.match(r"哼，", temp_cont) and random.randint(1, 20) != 1:
            temp_cont = temp_cont[2:]
        elif re.match(r"哼！", temp_cont) and random.randint(1, 10) != 1:
            temp_cont = temp_cont[2:]
        elif re.match(r"啊，", temp_cont) and random.randint(1, 5) != 1:
            temp_cont = temp_cont[2:]
        elif re.match(r"唉，", temp_cont) and random.randint(1, 4) != 1:
            temp_cont = temp_cont[2:]
        elif re.match(r"哦？", temp_cont) and random.randint(1, 4) != 1:
            temp_cont = temp_cont[2:]
        elif re.match(r"啊！", temp_cont) and random.randint(1, 3) != 1:
            temp_cont = temp_cont[2:]

    if temp_cont.strip() != "":
        return temp_cont
    else:
        print(ori_temp_cont)
        return ori_temp_cont

with open(sys.argv[1], "r", encoding="utf-8") as fin,\
open(sys.argv[2], "w", encoding="utf-8") as fout:
    lines = "".join([line for line in fin.readlines()]).replace("：", ":").strip()
    lines = lines.split("\n\n\n")
    user_convs = []
    char_convs = []
    for line in tqdm(lines):
        assert "\n\n" not in line
        temp_conv = ""
        turns = line.split("\n")
        assert len(turns) >= 2

        span = re.match(r"\([^\:]+\)\:", turns[1]).span()
        char = turns[1][span[1]:].split(":")[0].strip()

        user_prefs = [f"从现在开始，我来扮演{char}，你来扮演网友，请你模仿网友的语气和我对话。",
                      f"现在你就是网友，我是{char}，请你模仿网友的语气和我对话。",
                      f"从现在开始，我来扮演{char}，你来扮演网友，请你模仿网友和我对话。",
                      f"从此刻起我是{char}，你是网友，我们来进行后面的对话。",
                      f"从现在开始，我当{char}，你当网友，我们来进行对话。"]

        char_prefs = [f"从现在开始，你来扮演{char}，请你模仿{char}的语气和我对话。",
                      f"现在你就是{char}，请你模仿{char}的语气和我对话。",
                      f"从现在开始，你来扮演{char}，请你模仿{char}和我对话。",
                      f"从此刻起你是{char}，我们来进行后面的对话。",
                      f"从现在开始，你当{char}，我们来进行对话。"]
        
        new_turns = []
        for i, turn in enumerate(turns):
            if turn[:6] == "(后-复述)":
                new_turns = new_turns[:-1]
            new_turns.append(turn)
        
        for i, turn in enumerate(new_turns):
            span = re.match(r"\([^\:]+\)\:", turn).span()
            temp_sent = turn[span[1]:]
            temp_char = temp_sent.split(":")[0].strip()
            temp_cont = temp_sent.split(":")[1].strip()
            temp_cont = filter(temp_cont)

            if i == 0:
                user_pref = random.choice(user_prefs)
                user_convs.append({"inputs": user_pref, "targets": f"好的，从现在开始我就是网友。\n\n网友: {temp_cont}"})
                char_pref = random.choice(char_prefs)
                char_convs.append({"inputs": char_pref, "targets": f"好的，从现在开始我就是{char}。"})
            elif i % 2 == 0:
                user_pref = random.choice(user_prefs)
                user_convs.append({"inputs": f"{user_pref}\n\n好的，从现在开始我就是网友。\n\n{temp_conv}\n\n网友: ", 
                                   "targets": temp_cont})
            else:
                char_pref = random.choice(char_prefs)
                char_convs.append({"inputs": f"{char_pref}\n\n好的，从现在开始我就是{char}。\n\n{temp_conv}\n\n{char}: ".replace("\n\n网友", "\n\n人类"),
                                   "targets": temp_cont.replace("\n\n网友", "\n\n人类")})

            if temp_conv == "":
                temp_conv = temp_char + ": " + temp_cont
            else:
                temp_conv = temp_conv + "\n\n" + temp_char + ": " + temp_cont

    temp_convs = char_convs #+ user_convs
    # random.shuffle(temp_convs)
    
    for temp_conv in temp_convs:
        fout.write(json.dumps(temp_conv, ensure_ascii=False)+"\n")
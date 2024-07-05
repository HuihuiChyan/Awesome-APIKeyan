# coding=utf-8
'''
Authour: Hui Huang
E-mail: 22b903058@stu.hit.edu.cn
'''
import re
import time
import json
import openai
import random
import argparse
import itertools
from utils import get_response_turbo

def create_conv_turbo(conversation, key=None, name=None):

    while(True):
        response_content = get_response_turbo(conversation, key=key)
        response_content = response_content.replace("：", ": ")
        if response_content.strip() == "":
            print("Exceptional line with empty output! Retrying!")
            continue
        if not re.match(name+":", response_content):
            print("Exceptional line with no name prefix! Retrying!")
            print("The response is: "+response_content)
            continue
        break
    
    response_content = response_content.replace(name+":", "").strip()
    if response_content[0] == '"' and response_content[-1] == '"':
        response_content = response_content[1:-1]
    
    return response_content

def get_response_davinci(conversation, stop="\n", name=None):

    prompt = "\n".join([conv["content"] for conv in conversation]) + f"\n{name}: "

    while(True):
        try:
            response = openai.Completion.create(
                engine="text-davinci-003", #20221122
                temperature=0.5,
                prompt=prompt,
                max_tokens=2048,
                stop=[stop],
            )
        except openai.error.RateLimitError:
            print("RateLimitError! Have a rest!")
        except openai.error.APIError:
            print("APIError! Have a rest!")
        except openai.error.APIConnectionError:
            print("APIConnectionError! Have a rest!")
        except openai.error.Timeout:
            print("Timeout! Have a rest!")
        else:
            response_content = response['choices'][0]['text'].strip()
            if response_content.strip() == "":
                print("Exceptional line with empty output! Retrying!")
                continue
            break

    if re.match(name+":", response_content.replace("：", ":")):
        response_content = response_content.replace("：", ":").replace(name+":", "")

    return response_content

def seed2response(seed, stop="\n"):

    seed = "\t".join(seed)
    prompt = f"{seed}\n你是一名正在聊天的网友，请你模仿网友的语气，将上面这几个词补全为一句完整的话，只需要生成一句话即可: "
    conversation = [{"role": "user", "content": prompt}]

    while(True):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                temperature=0.5,
                frequency_penalty=0.0,
                messages=conversation,
                stop=stop,
            )
        except openai.error.RateLimitError:
            print("RateLimitError! The key is "+str(openai.api_key))
            continue
        except openai.error.APIError:
            print("APIError! Have a rest!")
            continue
        except openai.error.APIConnectionError:
            print("APIConnectionError! Have a rest!")
            continue
        except openai.error.Timeout:
            print("Timeout! Have a rest!")
            continue
        else:
            response_content = response['choices'][0]['message']['content'].strip().replace("：", ": ")
            if response_content.strip() == "":
                print("Exceptional line with empty output! Retrying!")
                # print("The input is: "+line)
                continue
            break
    
    if response_content[0] == '"' and response_content[-1] == '"':
        response_content = response_content[1:-1]
    
    return response_content

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", type=str, required=True)
    parser.add_argument("--seed-file", type=str, default="./data/train.query")
    parser.add_argument("--output-file", type=str, default="./data/conv01.txt")
    parser.add_argument("--total-number", type=int, default=24000)
    parser.add_argument("--lang", type=str, default="英文", choices=("中文", "英文"))
    args = parser.parse_args()

    get_response = create_conv_turbo

    openai.api_key = args.api_key

    start_time = time.time()

    counter = 0

    fout = open(args.output_file, "a+", encoding="utf-8")

    seed_lines = [line.strip().split("\t") for line in open(args.seed_file, "r", encoding="utf-8").readlines()]
    # random.shuffle(seed_lines)
    # seed_lines = itertools.cycle(seed_lines)

    for seeds in seed_lines:
        lang = args.lang

        prompt_usr = f"从现在开始，请你用'网友1: '开头，模仿网友的语气和说话方式，用{lang}和我闲聊，每次只说一句话。"
        prompt_ass = f"从现在开始，请你用'网友2: '开头，模仿网友的语气和说话方式，用{lang}和我闲聊，每次只说一句话。"

        # prompt_usr = f"接下来是两个网友的闲聊，请模仿两个人的说话语气和方式，续写这段对话，每次生成的话要简短，并且保证对话内容的有趣性。"
        # prompt_ass = prompt_usr

        # conversation_usr = [{"role": "system", "content": desc1}, {"role": "user", "content": start_prompt1}]
        # conversation_ass = [{"role": "system", "content": desc1}, {"role": "user", "content": start_prompt2}]

        conversation_usr = []
        conversation_ass = []

        # length = random.randint(10, 15)
        length = 5
        # 每一通对话的轮数，不用太长，太长了聊的内容也很局限

        name_usr = "网友1"
        name_ass = "网友2"

        conversation_result = {"name_usr": name_usr, "name_ass": name_ass, "convs": []}
        for i in range(length):

            ######response for name_usr######

            if i <= 1:
                # print("种子: "+seeds[i])
                response = seeds[2*i]
            else:
                conversation = [{"role": "user", "content": prompt_usr}] + conversation_usr
                response = get_response(conversation, name=name_usr)

            print(f"{name_usr}: {response}")
            conversation_result["convs"].append(response)

            conversation_ass.append({"role": "user", "content": f"{name_usr}: {response}"})
            conversation_usr.append({"role": "assistant", "content": f"{name_usr}: {response}"})

            ######response for name_ass######

            if i <= 1:
                # print("种子: "+seeds[i])
                response = seeds[2*i+1]
            else:
                conversation = [{"role": "user", "content": prompt_ass}] + conversation_ass
                response = get_response(conversation, name=name_ass)

            print(f"{name_ass}: {response}")
            conversation_result["convs"].append(response)

            conversation_usr.append({"role": "user", "content": f"{name_ass}: {response}"})
            conversation_ass.append({"role": "assistant", "content": f"{name_ass}: {response}"})
        
            counter += 2
            if counter % 10 == 0:
                print(f"%d lines finished. %.2f seconds per line on average." % (counter, (time.time()-start_time)/counter))

        fout.write(json.dumps(conversation_result, ensure_ascii=False)+"\n")
        print("\n")
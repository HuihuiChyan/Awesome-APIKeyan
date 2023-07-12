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

def get_response_sentence(input_line, stop="\n\n\n"):
    print(input_line)
    conversation = [{"role": "user", "content": input_line}]
    while(True):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                temperature=1.0,
                frequency_penalty=1.0,
                messages=conversation,
                stop=stop,
            )
        except openai.error.RateLimitError:
            print("RateLimitError! The key is "+str(openai.api_key))
            time.sleep(1)
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
            response_content = response['choices'][0]['message']['content'].strip()
            if response_content == "":
                print("Exceptional line with empty output! Retrying!")
                continue
            break

    return response_content

def get_response_davinci(input_line, stop="\n\n\n"):

    while(True):
        try:
            response = openai.Completion.create(
                engine="text-davinci-003", #20221122
                temperature=0.5,
                prompt=input_line,
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
            if response_content == "":
                print("Exceptional line with empty output! Retrying!")
                continue
            break

    return response_content

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", type=str, required=True)
    parser.add_argument("--input-file", type=str, default="./DoubanConversationCorpus/test-shuf.convs")
    parser.add_argument("--output-file", type=str, default="./data/conv01.txt")
    parser.add_argument("--total-number", type=int, default=24000)
    args = parser.parse_args()

    openai.api_key = args.api_key

    start_time = time.time()

    counter = 0

    input_lines = [line.strip() for line in open(args.input_file, "r", encoding="utf-8").readlines()]
    # input_lines = itertools.cycle(list(set(input_lines)))

    fout = open(args.output_file, "a+", encoding="utf-8")

    prompt = "{history}\n上面是两个网友的一段聊天，请你对上面这段话进行润色，以'网友1: '和'网友2: '开头，生成一段通顺、流畅的对话: "

    for input_conv in input_lines:

        history = ""
        for i, turn in enumerate(input_conv.split("\t")):
            if i % 2 == 0:
                history += f"\n网友1: {turn}"
            else:
                history += f"\n网友2: {turn}"

        name_usr = "网友1"
        name_ass = "网友2"

        input_line = prompt.format(history=history)

        response = get_response_davinci(input_line)

        response = response.replace("\n\n", "\n").split("\n")
        conversation_result = {"name_usr": name_usr, "name_ass": name_ass, "convs": []}
        for i, turn in enumerate(response):
            print(turn.strip())
            if i % 2 == 0 and re.match("网友1:", turn.strip()):
                conversation_result["convs"].append(turn.split("网友1:")[1].strip())
            elif i % 2 == 1 and re.match("网友2:", turn.strip()):
                conversation_result["convs"].append(turn.split("网友2:")[1].strip())
            else:
                break

        print("################New Conversation###############")
        fout.write(json.dumps(conversation_result, ensure_ascii=False)+"\n")
        # print(f"%d lines finished. %.2f seconds per line on average." % (counter, (time.time()-start_time)/counter))
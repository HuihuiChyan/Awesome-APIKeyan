'''
Authour: Hui Huang
E-mail: 22b903058@stu.hit.edu.cn
'''
import os
import re
import tqdm
import time
import json
import openai
import argparse
import multiprocessing
from transformers import GPT2Tokenizer

def generate_line_str(line):
    while(True):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                temperature=0.5,
                messages=[{"role": "user", "content": line}],
            )
        except openai.error.RateLimitError:
            print("RateLimitError! Have a rest!")
            time.sleep(1)
        except openai.error.APIError:
            print("APIError! Have a rest!")
            time.sleep(1)
        except openai.error.APIConnectionError:
            print("APIConnectionError! Have a rest!")
            time.sleep(1)
        else:
            if re.match(r'[0-9]+', response['choices'][0]['message']['content'].strip()) is None:
                print("Exceptional line with no logit output! Retrying!")
                print("The input is " + line)
                print("The output is " + response['choices'][0]['message']['content'])
                continue
            break

    score = re.search(r'[0-9]+[\.]?[0-9]*', response['choices'][0]['message']['content'].strip()).group(0)
    # print(line+score)
    return float(score)

def create_input_line(json_line, prompt, aspect_dict):
    context = "NaN"
    input_lines = []
    name_usr = json_line["name_usr"]
    name_ass = json_line["name_ass"]
    for i in range(len(json_line["convs"])):
        if i % 2 == 1:
            request = name_usr + ": "+ json_line["convs"][i-1].strip()
            response = name_ass + ": "+ json_line["convs"][i].strip()
            line = prompt.format(aspect=aspect_dict["aspect"],
                                 anti_aspect=aspect_dict["anti_aspect"],
                                 aspect_ins=aspect_dict["aspect_ins"],
                                 context=context,
                                 request=request,
                                 response=response)
            input_lines.append(line)
            if context == "NaN":
                context = request + "\n" + response
            else:
                context = context + "\n" + request + "\n" + response
    return input_lines

def create_input_line_persona(json_line, prompt_persona):
    input_lines = []
    name_usr = json_line["name_usr"]
    name_ass = json_line["name_ass"]
    for i in range(len(json_line["convs"])):
        if i % 2 == 1:
            # request = json_line["convs"][i-1].strip()
            response = json_line["convs"][i].strip()
            line = prompt_persona.format(name_ass=name_ass,
                                         response=response)
            input_lines.append(line)
    return input_lines

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", type=str, required=True)
    parser.add_argument("--jsonl-input-file", type=str, required=True)
    args = parser.parse_args()

    openai.api_key = args.api_key
    
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

    prompt = "Score the following dialogue response with respect to {aspect} on a continuous scale from 0 to 100, where a score of 0 means “{anti_aspect}” and score of 100 means “perfect {aspect}”. Note that {aspect} measures {aspect_ins}.\n\nContext: {context}\n\nRequest: {request}\n\nDialogue Response: {response}\n\nScore:"

    prompt_persona = "Ignore the sensibleness and specificity, and score the following sentence by measuring whether it matches the tone and way of speaking of {name_ass}, on a continuous scale from 0 to 100. Note that 0 means does not match the tone of {name_ass} at all, and 100 means perfectly matches the tone of {name_ass}.\n\nDialogue Response: {response}\n\nScore: "

    sensi_dict = {"aspect": "sensibleness",
                  "anti_aspect": "does not make sense",
                  "aspect_ins": "whether the dialogue response makes sense to the given request and context and does not contradict with anything that was said earlier"}
    speci_dict = {"aspect": "specificity",
                  "anti_aspect": "generic and unspecific",
                  "aspect_ins": "whether the dialogue response is specific to the given request and context and is not a generic and unspecific statement"}
    inter_dict = {"aspect": "interestingness",
                  "anti_aspect": "monotonous and dull",
                  "aspect_ins": "whether the dialogue response would likely catches someone's attention or arouse someone's curiosity, or present something insightful, unexpected, or witty"}
    perso_dict = {"aspect": "personality",
                  "anti_aspect": "no personality",
                  "aspect_ins": "whether the dialogue response fit the personality and tone of {name}, and ignore other aspects such as sensibleness or specificity"}

    all_aspec_dicts = [sensi_dict, speci_dict, inter_dict, perso_dict]

    lines = [json.loads(line.strip()) for line in open(args.jsonl_input_file, "r", encoding="utf-8").readlines()]
    for aspec_dict in all_aspec_dicts:
        input_lines = []
        for line in lines:
            if aspec_dict["aspect"] == "personality":
                input_lines.extend(create_input_line_persona(line, prompt_persona))
            else:
                input_lines.extend(create_input_line(line, prompt, aspec_dict))

        scores = []
        aspect = aspec_dict["aspect"]
        for line in tqdm.tqdm(input_lines, desc=f"Evaluating {aspect}"):
            score = generate_line_str(line)
            scores.append(score)

        print(f"The average score for {aspect} is: " + str(round(sum(scores)/len(scores), 2)))
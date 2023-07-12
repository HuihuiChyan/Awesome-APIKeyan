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
from utils import get_response_turbo, get_response_gpt4

def generate_line_str(line, key):
    while(True):
        response = get_response_gpt4([{"role": "user", "content": line}], key=key, temp=0.5, stop="\n")
        if re.match(r'[0-9]+', response) is None:
            print("Exceptional line with no logit output! Retrying!")
            print("The input is " + line)
            print("The output is " + response)
            continue
        else:
            break
    score = re.search(r'[0-9]+[\.]?[0-9]*', response.strip()).group(0)
    return float(score)

def create_input_line_turn(json_line, prompt, aspect_dict):
    input_lines = []
    name_usr = json_line["name_usr"]
    name_ass = json_line["name_ass"]
    for i in range(len(json_line["convs"])):
        if i == 0:
            context = name_usr + ": " + json_line["convs"][i].strip()
        elif i % 2 == 1:    
            response = name_ass + ": "+ json_line["convs"][i].strip()
            line = prompt.format(aspect=aspect_dict["aspect"],
                                 anti_aspect=aspect_dict["anti_aspect"],
                                 aspect_ins=aspect_dict["aspect_ins"],
                                 context=context,
                                 response=response)
            input_lines.append(line)
            context += "\n" + name_ass + ": " + json_line["convs"][i-1].strip() 
        else:
            response = name_usr + ": "+ json_line["convs"][i].strip()
            line = prompt.format(aspect=aspect_dict["aspect"],
                                 anti_aspect=aspect_dict["anti_aspect"],
                                 aspect_ins=aspect_dict["aspect_ins"],
                                 context=context,
                                 response=response)
            input_lines.append(line)
            context += "\n" + name_usr + ": " + json_line["convs"][i-1].strip()
    return input_lines

def create_input_line_dial(json_line, prompt, aspect_dict):
    context = ""
    name_usr = json_line["name_usr"]
    name_ass = json_line["name_ass"]
    for i in range(len(json_line["convs"])):
        if i % 2 == 0:
            context += name_usr + ": " + json_line["convs"][i].strip() + "\n"
        else:
            context += name_ass + ": " + json_line["convs"][i].strip() + "\n"
    line = prompt.format(aspect=aspect_dict["aspect"],
                         anti_aspect=aspect_dict["anti_aspect"],
                         aspect_ins=aspect_dict["aspect_ins"],
                         context=context.strip())
    return line

def create_input_line_prag(json_lines, prompt, aspect_dict):
    context = ""
    name_usr = json_lines[0]["name_usr"]
    name_ass = json_lines[0]["name_ass"]
    for json_line in json_lines:
        for i in range(len(json_line["convs"])):
            if i % 2 == 0:
                context += name_usr + ": " + json_line["convs"][i].strip() + "\n"
            else:
                context += name_ass + ": " + json_line["convs"][i].strip() + "\n"
        context += "\n\n"
    line = prompt.format(aspect=aspect_dict["aspect"],
                         anti_aspect=aspect_dict["anti_aspect"],
                         aspect_ins=aspect_dict["aspect_ins"],
                         context=context.strip())
    return line

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", type=str, required=True)
    parser.add_argument("--jsonl-input-file", type=str, required=True)
    args = parser.parse_args()

    openai.api_key = args.api_key

    prompt_turn = "Score the following dialogue response with respect to {aspect} on a continuous scale from 0 to 100, where a score of 0 means “{anti_aspect}” and score of 100 means “perfect {aspect}”. Note that {aspect} measures {aspect_ins}.\n\nContext: {context}\n\nDialogue Response: {response}\n\nScore:"
    prompt_dial = "Score the following dialogue with respect to {aspect} on a continuous scale from 0 to 100, where a score of 0 means “{anti_aspect}” and score of 100 means “perfect {aspect}”. Note that {aspect} measures {aspect_ins}.\n\nDialogue: {context}\n\nScore:"
    prompt_prag = "Score the following dialogues with respect to {aspect} on a continuous scale from 0 to 100, where a score of 0 means “{anti_aspect}” and score of 100 means “perfect {aspect}”. Note that {aspect} measures {aspect_ins}.\n\nDialogues: {context}\n\nScore:"
    
    # sensi_dict = {"aspect": "sensibleness",
    #               "anti_aspect": "does not make sense",
    #               "aspect_ins": "whether the dialogue response makes sense to the given request and context and does not contradict with anything that was said earlier"}
    # speci_dict = {"aspect": "specificity",
    #               "anti_aspect": "generic and unspecific",
    #               "aspect_ins": "whether the dialogue response is specific to the given request and context and is not a generic and unspecific statement"}
    # inter_dict = {"aspect": "interestingness",
    #               "anti_aspect": "monotonous and dull",
    #               "aspect_ins": "whether the dialogue response would likely catches someone's attention or arouse someone's curiosity, or present something insightful, unexpected, or witty"}
    
    coher_dict = {"aspect": "coherence",
                  "anti_aspect": "incoherent",
                  "aspect_ins": "whether the dialogue response is relevant and consistent with the context"}
    infor_dict = {"aspect": "informativeness",
                  "anti_aspect": "generic and unspecific",
                  "aspect_ins": "whether the dialogue response is informative or not given the context"}
    engag_dict = {"aspect": "engagingness",
                  "anti_aspect": "monotonous and dull",
                  "aspect_ins": "whether the dialogue would likely catches someone's attention and curiosity, or present something insightful, unexpected and witty"}
    diver_dict = {"aspect": "diversity",
                  "anti_aspect": "homogeneous and duplicate",
                  "aspect_ins": "whether the dialogue responses cover various topics and does not contain duplicate expressions"}
    human_dict = {"aspect": "humanness",
                  "anti_aspect": "not human-like",
                  "aspect_ins": "whether the dialogue responses is human-like"}
    
    # turn_aspec_dicts = [coher_dict, infor_dict]
    turn_aspec_dicts = []
    dial_aspec_dicts = [human_dict]
    prag_aspec_dicts = []

    lines = [json.loads(line.strip()) for line in open(args.jsonl_input_file, "r", encoding="utf-8").readlines()]

    for aspec_dict in turn_aspec_dicts:
        input_lines = []
        for line in lines:
            input_lines.extend(create_input_line_turn(line, prompt_turn, aspec_dict))

        scores = []
        aspect = aspec_dict["aspect"]
        for line in tqdm.tqdm(input_lines, desc=f"Evaluating {aspect}"):
            score = generate_line_str(line, key=args.api_key)
            scores.append(score)

        print(f"The average score for {aspect} is: " + str(round(sum(scores)/len(scores), 2)))

    for aspec_dict in dial_aspec_dicts:
        input_lines = []
        for line in lines:
            input_lines.append(create_input_line_dial(line, prompt_dial, aspec_dict))

        scores = []
        aspect = aspec_dict["aspect"]
        for line in tqdm.tqdm(input_lines, desc=f"Evaluating {aspect}"):
            score = generate_line_str(line, key=args.api_key)
            scores.append(score)

        print(f"The average score for {aspect} is: " + str(round(sum(scores)/len(scores), 2)))

    for aspec_dict in prag_aspec_dicts:
        input_line = create_input_line_prag(lines, prompt_prag, aspec_dict)

        aspect = aspec_dict["aspect"]
        score = generate_line_str(input_line, key=args.api_key)

        print(f"The average score for {aspect} is: " + str(round(score, 2)))
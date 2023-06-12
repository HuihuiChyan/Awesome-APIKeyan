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

def generate_line_nll(line):

    while(True):
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=line[2],
                echo=True,
                logprobs=1,
                max_tokens=0,
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
            break
    
    scores = response['choices'][0]['logprobs']['token_logprobs'][line[0]:]
    score = sum(scores)
    return score

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", type=str, required=True)
    parser.add_argument("--jsonl-input-file", type=str, required=True)
    args = parser.parse_args()

    openai.api_key = args.api_key
    
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

    lines = [json.loads(line.strip()) for line in open(args.jsonl_input_file, "r", encoding="utf-8").readlines()]
    input_lines = []
    for line in lines:
        prefix_length = len(tokenizer.tokenize(line["source"]))
        full_length = len(tokenizer.tokenize(line["source"] + line["target"]))
        input_full = line["source"] + line["target"]
        input_lines.append([prefix_length, full_length, input_full])

    sum_scores = []
    avg_scores = []
    for line in tqdm.tqdm(input_lines):
        score = generate_line_nll(line)
        sum_scores.append(score)
        avg_scores.append(score/(line[1]-line[0]))

    print("The sum_score is: " + str(round(sum(sum_scores)/len(sum_scores), 2)))
    print("The avg_score is: " + str(round(sum(avg_scores)/len(avg_scores), 4)))
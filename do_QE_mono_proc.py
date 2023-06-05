# coding=utf-8
'''
Authour: Hui Huang
E-mail: 22b903058@stu.hit.edu.cn
'''
import tqdm
import time
import random
import openai
import argparse
import multiprocessing
from utils import get_response_turbo

def create_noised_text(text):
    input_line = f"请对句子'{text}'注入噪音，得到一句语义发生偏差、不通顺，但是长度与原本的句子一样的句子:"
    messages = [{"role": "user", "content": input_line}]
    while(True):
        result = get_response_turbo(messages)
        if result == "":
            print("Exceptional line with empty output! Retrying!")
            continue
        if len(text.replace(" ", "")) / len(result) > 1.25:
            print("Too long! Retrying!")
            continue
        if len(text.replace(" ", "")) / len(result) < 0.8:
            print("Too short! Retrying!")
            continue
        break
    if result[0] == '"' and result[-1] == '"':
        result = result[1:-1]
    if result[0] == "'" and result[-1] == "'":
        result = result[1:-1]
    return result

def create_noised_text_wrapper(text):
    results = []
    for i in range(2):
        results.append(create_noised_text(text))
    return results

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", type=str, required=True)
    parser.add_argument("--input-file", type=str, default="train.pe.detok")
    parser.add_argument("--output-file", type=str, default="train.pe.out05")
    parser.add_argument("--pool-number", type=int, default=10)
    args = parser.parse_args()

    openai.api_key = args.api_key

    with open(args.output_file, "r", encoding="utf-8") as foutput:
        output_lines = [line.strip() for line in foutput.readlines()]

    fin = open(args.input_file, "r", encoding="utf-8")
    fout = open(args.output_file, "a+", encoding="utf-8")
    input_lines = [line.strip() for line in fin.readlines()][len(output_lines):]

    with open(args.output_file, "a", encoding="utf-8") as fout:
        for line in tqdm.tqdm(input_lines):
            result = create_noised_text_wrapper(line)
            fout.write(" ||| ".join(result)+"\n")
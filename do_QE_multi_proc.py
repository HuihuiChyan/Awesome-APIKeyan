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
    FailCnt = 0
    while(True):
        result = get_response_turbo(messages, key=api_key)
        if result == "INVALID KEY":
            raise Exception(f"The key {api_key} is invalid. It may run out of quota.")
        if result == "":
            print("Exceptional line with empty output! Retrying!")
            continue
        if len(text.replace(" ", "")) / len(result) > 1.25:
            print("Too long! Retrying!")
            FailCnt += 1
            if FailCnt >= 10:
                print(f"Too many failures! Input is {text}")
                break
            continue
        if len(text.replace(" ", "")) / len(result) < 0.8:
            print("Too short! Retrying!")
            FailCnt += 1
            if FailCnt >= 10:
                print(f"Too many failures! Input is {text}")
                break
            continue
        break
    if result[0] == '"' and result[-1] == '"':
        result = result[1:-1]
    if result[0] == "'" and result[-1] == "'":
        result = result[1:-1]
    counter.value += 1
    if counter.value % 10 == 0:
        avg_time = round((time.time()-start_time) / counter.value, 2)
        print(f"{counter.value} lines finished! {avg_time} seconds per line on average.")
        print(f"Sampled input: {text}")
        print(f"Sampled output: {result}")
    return result

def create_noised_text_wrapper(text):
    results = []
    for i in range(10):
        results.append(create_noised_text(text))
    return results

def init(c, a, t):
    global counter
    global api_key
    global start_time
    counter = c
    api_key = a
    start_time = t

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", type=str, required=True)
    parser.add_argument("--input-file", type=str, default="train.pe.detok")
    parser.add_argument("--output-file", type=str, default="train.pe.out05")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--pool-number", type=int, default=10)
    args = parser.parse_args()

    openai.api_key = args.api_key

    start_time = time.time()

    with open(args.output_file, "r", encoding="utf-8") as foutput:
        output_lines = [line.strip() for line in foutput.readlines()]

    fin = open(args.input_file, "r", encoding="utf-8")
    fout = open(args.output_file, "a+", encoding="utf-8")
    input_lines = [line.strip() for line in fin.readlines()][len(output_lines):]

    manager = multiprocessing.Manager()
    counter = manager.Value("counter", 0)
    pool = multiprocessing.Pool(args.pool_number, initializer=init, initargs=(counter, args.api_key, start_time))
    with open(args.output_file, "a", encoding="utf-8") as fout:
        counter = manager.Value("counter", 0)
        batched_lines = []
        for i, line in enumerate(input_lines):
            batched_lines.append(line)
            if (i+1) % args.batch_size == 0:
                results = pool.map(create_noised_text_wrapper, batched_lines, args.pool_number)
                for line in results:
                    fout.write(" ||| ".join(line)+"\n")
                batched_lines = []
        
        if batched_lines != []:
            results = pool.map(create_noised_text_wrapper, batched_lines, args.pool_number)
            for line in results:
                fout.write(" ||| ".join(line)+"\n")
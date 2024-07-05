# coding=utf-8
'''
Authour: Hui Huang
E-mail: 22b903058@stu.hit.edu.cn
'''
import os
import tqdm
import time
import random
import openai
import argparse
import multiprocessing
from utils import get_response_turbo
from utils_noiser import DataCollatorForNoiser

def create_noised_text(text, key=None):

    text, noised_text = text.split(" ||| ")

    demo = "请把'经常能在几百码开外<MASK>英国<MASK><MASK><MASK>。'中的<MASK>补全，生成一句通顺、流畅的中文句子:经常能在几百码开外射杀英国皇家海军的舰船。\n请把'最后<MASK><MASK>征服者<MASK>举着剑<MASK>。'中的<MASK>补全，生成一句通顺、流畅的中文句子:最后胜利的征服者随后举着剑前进。\n"

    input_line = f"请把'{noised_text}'中的<MASK>补全，生成一句通顺、流畅的中文句子:"
    messages = [{"role": "user", "content": demo+input_line}]

    if key is None:
        key = api_key

    FailCnt = 0
    while(True):
        result = get_response_turbo(messages, key=key)
        if result == "INVALID KEY":
            raise Exception(f"The key {api_key} is invalid. It may run out of quota.")
        if result == "":
            print("Exceptional line with empty output! Retrying!")
            continue
        if "<MASK>" in result:
            print("Exceptional line with <MASK> in the output! Retrying!")
            print(f"The input is: {input_line}")
            continue
        if result[0] == '"' and result[-1] == '"':
            result = result[1:-1]
        if result[0] == "'" and result[-1] == "'":
            result = result[1:-1]
        if result[0] == "“" and result[-1] == "”":
            result = result[1:-1]

        if len(result) / len(text.replace(" ", "")) > 1.25:
            print("Too long! Retrying!")
            # print(f"The input is: {input_line}")
            # print(f"The output is: {result}")
            FailCnt += 1
            if FailCnt >= 5:
                print(f"Too many failures! Input is {input_line}")
                break
            continue
        if len(result) / len(text.replace(" ", "")) < 0.8:
            print("Too short! Retrying!")
            # print(f"The input is: {input_line}")
            # print(f"The output is: {result}")
            FailCnt += 1
            if FailCnt >= 5:
                print(f"Too many failures! Input is {input_line}")
                break
            continue
        break

    counter.value += 1
    if counter.value % 10 == 0:
        avg_time = round((time.time()-start_time) / counter.value, 2)
        print(f"{counter.value} lines finished! {avg_time} seconds per line on average.")
        print(f"Sampled input: {text}")
        print(f"Sampled noised: {noised_text}")
        print(f"Sampled output: {result}")
    return result

def create_noised_text_wrapper(text, key=None):
    results = []
    lines = text.split(" |||| ")
    for line in lines:
        results.append(create_noised_text(line, key=key))
    return results

def init(c, a, t):
    global counter
    global api_key
    global start_time
    global noiser
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
    parser.add_argument("--multi-process", action="store_true", default=False)
    args = parser.parse_args()

    openai.api_key = args.api_key

    start_time = time.time()

    if os.path.exists(args.output_file):
        with open(args.output_file, "r", encoding="utf-8") as foutput:
            output_lines = [line.strip() for line in foutput.readlines()]
            len_output_lines = len(output_lines)
    else:
        len_output_lines = 0

    fin = open(args.input_file, "r", encoding="utf-8")
    fout = open(args.output_file, "a+", encoding="utf-8")
    input_lines = [line.strip() for line in fin.readlines()][len_output_lines:]

    import jieba_fast
    noiser = DataCollatorForNoiser(tokenizer=jieba_fast.lcut)
    
    new_input_lines = []
    for line in tqdm.tqdm(input_lines, desc="Adding <MASK>"):
        temp_line = []
        for i in range(24):
            mask_ratio = random.choice([0.1, 0.2, 0.3])
            delete_ratio = random.choice([0.0, 0.1, 0.2])
            insert_ratio = delete_ratio + 0.05
            temp_line.append(line+" ||| "+noiser(line, mask_ratio, insert_ratio, delete_ratio))
        new_input_lines.append(" |||| ".join(temp_line))
    
    input_lines = new_input_lines

    manager = multiprocessing.Manager()
    counter = manager.Value("counter", 0)
    pool = multiprocessing.Pool(args.pool_number, initializer=init, initargs=(counter, args.api_key, start_time))

    if args.multi_process:
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
    
    else:
        with open(args.output_file, "a", encoding="utf-8") as fout:
            for line in tqdm.tqdm(input_lines):
                result = create_noised_text_wrapper(line, key=args.api_key)
                fout.write(" ||| ".join(result)+"\n")
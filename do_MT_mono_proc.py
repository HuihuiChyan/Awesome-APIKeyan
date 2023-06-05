# coding=utf-8
'''
Authour: Hui Huang
E-mail: 22b903058@stu.hit.edu.cn
'''
import openai
import time
import multiprocessing
import argparse
import random
import os
import tqdm
from rank_bm25 import BM25Okapi
from transformers import GPT2Tokenizer
from utils import get_response_turbo

def create_bm25_database(train_file_src, train_file_tgt, tokenizer):

    src_corpus = [line.strip() for line in open(train_file_src, "r", encoding="utf-8").readlines()]
    tgt_corpus = [line.strip() for line in open(train_file_tgt, "r", encoding="utf-8").readlines()]

    corpus = [line[0] + " ||| " + line[1] for line in zip(src_corpus, tgt_corpus)]
    corpus = list(set(corpus))

    tokenized_src_corpus = [tokenizer.tokenize(line.split(" ||| ")[0]) for line in corpus]

    bm25_database = BM25Okapi(tokenized_src_corpus)
    
    return bm25_database, corpus

def create_translation(input_line):

    messages = [{"role": "user", "content": input_line}]

    while(True):
        result = get_response_turbo(messages)
        if result == "INVALID KEY":
            raise Exception(f"The key {api_key} is invalid. It may run out of quota.")
        if result == "":
            print("Exceptional line with empty output! Retrying!")
            continue
        else:
            break
    
    if "\n" in result:
        print(f"Weird line with line breaker inside the senence: {result}")
        # result = result.replace("\n", " ")
    
    if result[0] == '"' and result[-1] == '"':
        result = result[1:-1]
    if result[0] == "'" and result[-1] == "'":
        result = result[1:-1]
    
    print(f"The input is: {input_line}.")
    print(f"The output is: {result}.")

    return result

def create_input_line(template_prefix, template_full, src_line, bm25_top_n=None, demo_number_per_line=0):
    input_full = ""
    input_length = len(tokenizer.tokenize(template_prefix.format(src=src_line,
                                                                 src_lang=args.source_lang,
                                                                 tgt_lang=args.target_lang)))
    for j in range(demo_number_per_line):
        demo = bm25_top_n[j].split(" ||| ")
        demo = template_full.format(src=demo[0], tgt=demo[1], src_lang=args.source_lang, tgt_lang=args.target_lang)
        if input_length + len(tokenizer.tokenize(demo)) <= 4096:
            input_full = input_full + demo + "\n"
            input_length += len(tokenizer.tokenize(demo))
        else:
            print("Length limit exceeded! Please reduce your demo_number!")
            break

    input_full += template_prefix.format(src=src_line, src_lang=args.source_lang, tgt_lang=args.target_lang)

    return input_full

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
    parser.add_argument("--source-file", type=str, required=True)
    parser.add_argument("--output-file", type=str, required=True)
    parser.add_argument("--source-lang", type=str, default="English", help="Used to construct prompt. Please provide the full name!")
    parser.add_argument("--target-lang", type=str, default="Chinese", help="Used to construct prompt. Please provide the full name!")
    parser.add_argument("--demo-number", type=int, default=0, help="Demonstration number for each line.")
    parser.add_argument("--demo-src-file", type=str, help="Used for demonstration construction.")
    parser.add_argument("--demo-tgt-file", type=str, help="Used for demonstration construction.")
    parser.add_argument("--demo-type", type=str, default="bm25", choices=("bm25", "random"), help="Select demo based on bm25 or randomly")
    parser.add_argument("--template-full", type=str, default="Translate '{src}' into {tgt_lang}: {tgt}", help="Design this based on your task!")
    parser.add_argument("--template-prefix", type=str, default="Translate '{src}' into {tgt_lang}: ", help="Design this based on your task!")
    parser.add_argument("--no-continue-crawling", action="store_true", default=False, help="Whether continue crawl from current line.")
    args = parser.parse_args()

    openai.api_key = args.api_key

    random.seed(10) # fixed for random demo selection

    with open(args.source_file, "r", encoding="utf-8") as fsrc:
        src_lines = [line.strip() for line in fsrc.readlines()]
    
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

    if args.demo_number >= 1:
            
        bm25_database, corpus = create_bm25_database(args.demo_src_file, args.demo_tgt_file, tokenizer)

        tokenized_src_lines = [tokenizer.tokenize(line) for line in src_lines]

        bm25_top_ns = []
        for line in tqdm.tqdm(tokenized_src_lines, desc="BM25 Querying"):
            if args.demo_type == "bm25":
                bm25_top_ns.append(bm25_database.get_top_n(line, corpus, n=20))
            else:
                bm25_top_ns.append(random.choices(corpus, k=20))

    input_lines = []
    for i in range(len(src_lines)):
        if args.demo_number >= 1:
            input_line = create_input_line(args.template_prefix,
                                           args.template_full,
                                           src_lines[i],
                                           bm25_top_ns=bm25_top_ns[i],
                                           demo_number_per_line=args.demo_number)
        else:
            input_line = create_input_line(args.template_prefix,
                                           args.template_full,
                                           src_lines[i])
        input_lines.append(input_line)

    if args.no_continue_crawling and os.path.exists(args.output_file):
        os.remove(args.output_file)
    else:
        if os.path.exists(args.output_file):
            with open(args.output_file, "r", encoding="utf-8") as fout:
                counter = len([line.strip() for line in fout.readlines()])
                input_lines = input_lines[counter:]
                print("Continue crawling from line "+str(counter))

    with open(args.output_file, "a", encoding="utf-8") as fout:
        for line in tqdm.tqdm(input_lines):
            result = create_translation(line)
            fout.write(result+"\n")
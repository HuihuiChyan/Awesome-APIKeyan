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
import itertools
from rank_bm25 import BM25Okapi
from transformers import GPT2Tokenizer

def create_bm25_database(train_file_src, train_file_tgt, tokenizer):

    src_corpus = [line.strip() for line in open(train_file_src, "r", encoding="utf-8").readlines()]
    tgt_corpus = [line.strip() for line in open(train_file_tgt, "r", encoding="utf-8").readlines()]

    corpus = [line[0] + " ||| " + line[1] for line in zip(src_corpus, tgt_corpus)]
    corpus = list(set(corpus))

    tokenized_src_corpus = [tokenizer.tokenize(line.split(" ||| ")[0]) for line in corpus]

    bm25_database = BM25Okapi(tokenized_src_corpus)
    
    return bm25_database, corpus

def generate_line(line, key_iter):

    while(True):
        openai.api_key = next(key_iter)
        try:
            response = openai.Completion.create(
                engine="text-davinci-003", #20221122
                prompt=line,
                temperature=0.0,
                max_tokens=2048,
                stop=["\n\n\n"],
            )
        except openai.error.RateLimitError:
            print("RateLimitError! Have a rest!")
            time.sleep(10)
        except openai.error.APIError:
            print("APIError! Have a rest!")
            time.sleep(10)
        except openai.error.APIConnectionError:
            print("APIConnectionError! Have a rest!")
            time.sleep(10)
        except openai.error.Timeout:
            print("Timeout! Have a rest!")
            time.sleep(10)
        else:
            # if "<|im_end|>" not in response['choices'][0]['text']:
            #     print("Exceptional line without end token! Retrying!")
            #     print("The input is: "+line)
            #     continue
            if response['choices'][0]['text'].strip() == "":
                print("Exceptional line with empty output! Retrying!")
                # print("The input is: "+line)
                continue
            break
    
    text = response['choices'][0]['text'].strip()
    while "\n" in text:
        print("Exceptional line with line breaker inside the senence:")
        print(text)
        text = text.replace("\n", " ")
    return text

def create_input_line(template_prefix, template_full, src_line, bm25_top_n, demo_number_per_line):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file", type=str, required=True)
    parser.add_argument("--output-file", type=str, required=True)
    parser.add_argument("--source-lang", type=str, required=True, help="Used to construct prompt. Please provide the full name!")
    parser.add_argument("--target-lang", type=str, required=True, help="Used to construct prompt. Please provide the full name!")
    parser.add_argument("--demo-number", type=int, default=1, help="Demonstration number for each line.")
    parser.add_argument("--demo-src-file", type=str, help="Used for demonstration construction.")
    parser.add_argument("--demo-tgt-file", type=str, help="Used for demonstration construction.")
    parser.add_argument("--demo-type", type=str, default="bm25", choices=("bm25", "random"), help="Select demo based on bm25 or randomly")
    parser.add_argument("--template-full", type=str, default="Translate '{src}' into {tgt_lang}: {tgt}", help="Design this based on your task!")
    parser.add_argument("--template-prefix", type=str, default="Translate '{src}' into {tgt_lang}: ", help="Used to fetch nlls.")
    parser.add_argument("--no-continue-crawling", action="store_true", default=False)
    args = parser.parse_args()

    start_time = time.time()

    random.seed(10)

    with open("all-keys.txt", "r", encoding="utf-8") as fkey:
        all_keys = [line.strip() for line in fkey.readlines()]

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
        input_full = create_input_line(args.template_prefix,
                                       args.template_full,
                                       src_lines[i],
                                       bm25_top_ns[i],
                                       demo_number_per_line=args.demo_number)
        input_lines.append(input_full)
    
    if args.no_continue_crawling and os.path.exists(args.output_file):
        os.remove(args.output_file)
    else:
        if os.path.exists(args.output_file):
            with open(args.output_file, "r", encoding="utf-8") as fout:
                accu_counter.value = len([line.strip() for line in fout.readlines()])
                input_lines = input_lines[accu_counter.value:]
                print("Continue crawling from line "+str(accu_counter.value))

    key_iter = itertools.cycle(all_keys)
    with open(args.output_file, "a", encoding="utf-8") as fout:
        for line in tqdm.tqdm(input_lines):
            line = generate_line(line, key_iter)
            fout.write(line+"\n")  

    stop_time = time.time()  
    print("Finished! Totally %f seconds used." % (stop_time-start_time))
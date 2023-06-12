# coding=utf-8
'''
Authour: Hui Huang
E-mail: 22b903058@stu.hit.edu.cn
'''
import re
import time
import tqdm
import openai
import random
import argparse
import itertools

def seed_generator(name, number, type, stop="\n\n\n"):

    if name != None:
        prompt = f"请生成{number}个与{name}相关的{type}，生成的词要多样化: "
    else:
        prompt = f"请生成{number}个{type}，生成的词要多样化: "
    conversation = [{"role": "user", "content": prompt}]

    while(True):
        openai.api_key = next(key_iter)
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
    
    return response_content


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--key-file", type=str, default="./keys/all-keys07.txt")
    args = parser.parse_args()

    api_keys = [line.strip() for line in open(args.key_file, "r", encoding="utf-8").readlines()]
    key_iter = itertools.cycle(api_keys)

    book_char_pairs = [("《哈利波特》", "哈利·波特"), ("《罗密欧与朱丽叶》", "罗密欧"), ("《罗密欧与朱丽叶》", "朱丽叶"),
                       ("《福尔摩斯历险记》", "福尔摩斯"), ("《冰与火之歌》", "艾德・史塔克"), ("《冰与火之歌》", "夜王"),
                       ("《三国演义》", "刘备"), ("《三国演义》", "关羽"), ("《三国演义》", "张飞"), ("《三国演义》", "曹操"),
                       ("《西游记》", "唐僧"), ("《西游记》", "孙悟空"), ("《西游记》", "猪八戒"), ("《西游记》", "沙和尚"),
                       ("《红楼梦》", "贾宝玉"), ("《红楼梦》", "林黛玉"), ("《水浒传》", "宋江"), ("《哈利波特》", "伏地魔")]

    # for book, char in tqdm.tqdm(book_char_pairs):
    #     fout = open("convs-zh-selfseed/seeds/"+char+".txt", "a", encoding="utf-8")

    #     for i in range(10):

    #         num_types = [(10, "名词，包括人名、物品名、事件名等等")]
    #         for num_type in num_types:
    #             seeds = seed_generator(char, num_type[0], num_type[1])
    #             print(seeds)
    #             fout.write(seeds+"\n")

    #         num_types = [(10, "名词，包括人名、物品名、事件名等等")]
    #         for num_type in num_types:
    #             seeds = seed_generator(book, num_type[0], num_type[1])
    #             print(seeds)
    #             fout.write(seeds+"\n")

    for i in range(100):
        fout = open("convs-zh-selfseed/seeds/通用.txt", "a", encoding="utf-8")
        num_types = [(10, "名词")]
        for num_type in num_types:
            seeds = seed_generator(None, num_type[0], num_type[1])
            print(seeds)
            fout.write(seeds+"\n")
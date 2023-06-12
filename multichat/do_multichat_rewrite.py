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

def get_response(conversation, stop="\n", name=None):

    while(True):
        openai.api_key = next(key_iter)
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
            response_content = response['choices'][0]['message']['content'].strip().replace("：", ": ")
            if response_content.replace(name, "").replace(":","").strip() == "":
                print("Exceptional line with empty output! Retrying!")
                # print("The input is: "+line)
                continue
            if not re.match(name+":", response_content):
                print("Exceptional line with no name prefix! Retrying!")
                print("The response is: "+response_content)
                continue
            break    
    return response_content   

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--key-file", type=str, default="./keys/all-keys07.txt")
    parser.add_argument("--output-file", type=str, default="./convs-zh-selfseed/conv01.txt")
    parser.add_argument("--query-file", type=str, default="./convs-zh-selfseed/train-query.json")
    parser.add_argument("--total-number", type=int, default=46000)
    parser.add_argument("--lang", type=str, default="中文", choices=("中文", "英文"))
    args = parser.parse_args()

    api_keys = [line.strip() for line in open(args.key_file, "r", encoding="utf-8").readlines()]
    key_iter = itertools.cycle(api_keys)

    fquery = open(args.query_file, "r")
    query_dict = json.load(fquery)

    start_time = time.time()

    counter = 0

    fout = open(args.output_file, "a+", encoding="utf-8")

    book_char_pairs = [("《三国演义》", "刘备"), ("《三国演义》", "关羽"), ("《三国演义》", "张飞"), ("《三国演义》", "曹操"),
                       ("《西游记》", "唐僧"), ("《西游记》", "孙悟空"), ("《西游记》", "猪八戒"), ("《西游记》", "沙和尚"),
                       ("《红楼梦》", "贾宝玉"), ("《红楼梦》", "林黛玉"), ("《水浒传》", "宋江"), ("《哈利波特》", "伏地魔"),
                       ("《哈利波特》", "哈利·波特"), ("《罗密欧与朱丽叶》", "罗密欧"), ("《罗密欧与朱丽叶》", "朱丽叶"),
                       ("《福尔摩斯历险记》", "福尔摩斯"), ("《冰与火之歌》", "艾德・史塔克"), ("《冰与火之歌》", "夜王"),]

    # book_char_pairs = [("《Harry Potter》", "Lord Voldemort"), ("《Super Mario Bros》", "Super Mario"), 
    #                    ("", "Jesus"), ("", "Lucifer"),
    #                    ("《Romeo and Juliet》", "Romeo"), ("《Romeo and Juliet》", "Juliet"), 
    #                    ("《A Song of Ice and Fire》", "Eddard Stark"), ("《A Song of Ice and Fire》", "Daenerys Targaryen"), ("《A Song of Ice and Fire》", "Tyrion Lannister"),
    #                    ("《The Adventure of Sherlock Holmes》", "Sherlock Holmes"), ("《The Adventure of Sherlock Holmes》", "John H. Watson")]

    book_char_pairs = book_char_pairs * ( args.total_number // len(book_char_pairs) )
    random.shuffle(book_char_pairs)

    for book_char in book_char_pairs:
        book = book_char[0]
        char = book_char[1]
        lang = args.lang

        topic = random.choice(query_dict[char])
        prefix_key1 = "前-" + topic
        prefix_key2 = "前-" + topic
        prefix_prompt1 = f"从现在开始，我扮演{char}，你扮演一名网友，请你用'网友: '开头，模仿网友的语气和说话方式，用{lang}和我闲聊，每次只说一句话。"
        prefix_prompt2 = f"从现在开始，我扮演一名网友，你扮演{char}，请你用'{char}: '开头，模仿{char}的语气和说话方式，简短地和我闲聊。"

        prefix_prompt1_topic = f"从现在开始，我扮演{char}，你扮演一名中二的网友，请你用'网友: '开头，模仿网友的语气和说话方式，以{topic}为主题，用{lang}和我闲聊，每次只说一句话。"

        # conversation_usr = [{"role": "system", "content": desc1}, {"role": "user", "content": start_prompt1}]
        # conversation_ass = [{"role": "system", "content": desc1}, {"role": "user", "content": start_prompt2}]

        conversation_usr = []
        conversation_ass = []
        history = f"从现在开始，我扮演{char}，你扮演一名中二的网友，请你用'网友: '开头，模仿网友的语气和说话方式，用{lang}和我闲聊，每次只说一句话。"

        length = random.randint(2, 3)
        # 每一通对话的轮数，不用太长，太长了聊的内容也很局限

        query_lines = [line.strip() for line in open("convs-zh-selfseed/seeds/"+char+".txt", "r", encoding="utf-8").readlines()]

        conversation_result = []
        for i in range(length):

            if i == 0:
                conversation_prefix = [{"role": "user", "content": prefix_prompt1_topic}] + conversation_usr
                response_usr = get_response(conversation_prefix, name="网友")
                print("({key}):".format(key=prefix_key1)+response_usr)
                conversation_result.append("({key}):".format(key=prefix_key1)+response_usr)
            else:
                conversation_prefix = [{"role": "user", "content": prefix_prompt1}] + conversation_usr
                response_usr = get_response(conversation_prefix, name="网友")
                print("({key}):".format(key=prefix_key1)+response_usr)
                conversation_result.append("({key}):".format(key=prefix_key1)+response_usr)

            history = history + response_usr + "\n"
            conversation_ass.append({"role": "user", "content": response_usr})
            conversation_usr.append({"role": "assistant", "content": response_usr})

            conversation_prefix = [{"role": "user", "content": prefix_prompt2}] + conversation_ass
            response_ass = get_response(conversation_prefix, name=char)
            print("({key}):".format(key=prefix_key2)+response_ass)
            conversation_result.append("({key}):".format(key=prefix_key2)+response_ass)
            prev_response_ass = response_ass.split(":")[1]

            history = history + response_ass + "\n"
            conversation_usr.append({"role": "user", "content": response_ass})
            conversation_ass.append({"role": "assistant", "content": response_ass})
        
            counter += 2
            if counter % 10 == 0:
                print(f"%d lines finished. %.2f seconds per line on average." % (counter, (time.time()-start_time)/counter))

        for line in conversation_result:
            fout.write(line+"\n")
        fout.write("\n\n")
        print("\n")
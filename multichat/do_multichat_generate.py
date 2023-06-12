# coding=utf-8
'''
Authour: Hui Huang
E-mail: 22b903058@stu.hit.edu.cn
'''
import re
import time
import openai
import random
import argparse
import itertools


def create_attributes(char_name, book_name, lang):

    book = book_name
    char = char_name
    if book != "":
        book = book + "中的"

    prefix_keys1 = ["前-脑洞", "前-普通", "前-中二"]
    prefix_dict1 = {"前-普通": f"从现在开始，我扮演{book}{char}，你扮演一名网友，请你用'网友: '开头，模仿网友的语气用{lang}简短地和我聊天，每次只说一句话。",
                    "前-中二": f"从现在开始，我扮演{book}{char}，你扮演一名中二的网友，请你用'网友: '开头，模仿网友的语气用{lang}简短地和我聊天，每次只说一句话。",
                    "前-脑洞": f"从现在开始，我扮演{book}{char}，你扮演一名脑洞很大的网友，请你用'网友: '开头，模仿网友的语气用{lang}简短地和我聊天，每次只说一句话。"}
    if book != "":
        prefix_keys1.extend(["前-读者", "前-脑读"])
        prefix_dict1["前-读者"] = f"从现在开始，我扮演{book}{char}，你扮演一名网友，请你用'网友: '开头，根据{book}内容，模仿网友的语气用{lang}简短地和我聊天，每次只说一句话。"
        prefix_dict1["前-脑读"] = f"从现在开始，我扮演{book}{char}，你扮演一名脑洞很大的网友，请你用'网友: '开头，根据{book}内容，模仿网友的语气用{lang}简短地和我聊天，每次只说一句话。"
    prefix_keys2 = ["前-中二", "前-普通", "前-中二", "前-中二"]
    prefix_dict2 = {"前-普通": f"从现在开始，我扮演一名网友，你扮演{char}，请你用'{char}: '开头，模仿{char}的语气，用一两句简短地和我聊天。",
                    "前-中二": f"从现在开始，我扮演一名网友，你扮演{char}，请你用'{char}: '开头，模仿{char}的语气，用中二的方式来简短地和我聊天。",}


    meta_suffix1 = f"以上是网友和{book}{char}的聊天，请你用'网友: '开头，模仿网友的语气，"
    # ["后-追问", "后-提问", "后-中二", "后-脑洞", "后-一词", "后-转换", "后-挑衅", "后-愤怒", "后-嘲讽", "后-悲伤"]
    suffix_dict1 = {"后-追问": meta_suffix1 + f"用追问的方式，用一句{lang}回复{char}: ",
                    "后-提问": meta_suffix1 + f"用提问的方式，用一句{lang}回复{char}: ",
                    "后-挑衅": meta_suffix1 + f"用挑衅的方式，用一句{lang}回复{char}: ",
                    "后-中二": meta_suffix1 + f"用中二的方式，用一句{lang}回复{char}: ",
                    "后-愤怒": meta_suffix1 + f"用愤怒的方式，用一句{lang}回复{char}: ",
                    "后-脑洞": meta_suffix1 + f"用脑洞很大的方式，用一句{lang}回复{char}: ",
                    "后-转换": meta_suffix1 + f"转换话题，针对一个新的话题，用一句{lang}提问{char}: ",
                    "后-嘲讽": meta_suffix1 + f"用嘲讽的方式，用一句{lang}回复{char}: ",
                    "后-一词": meta_suffix1 + f"用两到三个{lang}词来回复{char}: ",
                    "后-悲伤": meta_suffix1 + f"用悲伤的语气，用一句{lang}回复{char}"}

    meta_suffix2 = f"以上是网友和{book}{char}的聊天，请你用'{char}: '开头，模仿{char}的语气，"
    # ["后-感叹", "后-提问", "后-一句", "后-两句", "后-中二", "后-激动", "后-愤怒", "后-嘲讽", "后-耐烦"]
    suffix_dict2 = {"后-感叹": meta_suffix2 + f"用感叹的方式，用{lang}简短地回复网友: ",
                    "后-提问": meta_suffix2 + f"用提问的方式，用{lang}简短地回复网友: ",
                    "后-一句": meta_suffix2 + f"用一句{lang}回复网友: ",
                    "后-两句": meta_suffix2 + f"用一两句{lang}回复网友: ",
                    "后-激动": meta_suffix2 + f"用激动的语气，用{lang}简短地回复网友: ",
                    "后-愤怒": meta_suffix2 + f"用愤怒的语气，用{lang}简短地回复网友: ",
                    "后-嘲讽": meta_suffix2 + f"用嘲讽的语气，用{lang}简短地回复网友: ",
                    "后-中二": meta_suffix2 + f"用中二的语气，用{lang}简短地回复网友: ",
                    "后-耐烦": meta_suffix2 + f"用不耐烦的语气，用{lang}简短地回复网友: "}

    return prefix_keys1, prefix_dict1, prefix_keys2, prefix_dict2, suffix_dict1, suffix_dict2


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
            time.sleep(10)
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


def pattern_detector(sent1, sent2, stop="\n"):

    prompt = f"{sent1}\n{sent2}\n请你判断上面两个句子的句式结构是否相同，请用是或者否来回答: "
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
            time.sleep(10)
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
            if response['choices'][0]['message']['content'].strip()[0] in ["是", "否"]:
                return response['choices'][0]['message']['content'].strip()[0] == "是"
            continue

def pattern_paraphraser(sent1, sent2, name, stop="\n"):

    prompt = f"网友: {sent1}\n{name}: {sent2}\n上面是网友和{name}的对话，请你以'{name}: '开头，模仿{name}的语气，换一种方式简短地回答网友:"
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
    parser.add_argument("--key-file", type=str, default="./keys/all-keys01.txt")
    parser.add_argument("--output-file", type=str, default="./convs/conv01.txt")
    parser.add_argument("--lang", type=str, default="中文", choices=("中文", "英文"))
    args = parser.parse_args()

    api_keys = [line.strip() for line in open(args.key_file, "r", encoding="utf-8").readlines()]
    key_iter = itertools.cycle(api_keys)

    start_time = time.time()

    counter = 0

    fout = open(args.output_file, "a+", encoding="utf-8")

    book_char_pairs = [("《三国演义》", "刘备"), ("《三国演义》", "关羽"), ("《三国演义》", "张飞"), ("《三国演义》", "曹操"),
                       ("《西游记》", "唐僧"), ("《西游记》", "孙悟空"), ("《西游记》", "猪八戒"), ("《西游记》", "沙和尚"),
                       ("《红楼梦》", "贾宝玉"), ("《红楼梦》", "林黛玉"), ("《水浒传》", "宋江"), ("《哈利波特》", "伏地魔")]

    # book_char_pairs = [("《Harry Potter》", "Lord Voldemort"), ("《Super Mario Bros》", "Super Mario"), 
    #                    ("", "Jesus"), ("", "Lucifer"),
    #                    ("《Romeo and Juliet》", "Romeo"), ("《Romeo and Juliet》", "Juliet"), 
    #                    ("《A Song of Ice and Fire》", "Eddard Stark"), ("《A Song of Ice and Fire》", "Daenerys Targaryen"), ("《A Song of Ice and Fire》", "Tyrion Lannister"),
    #                    ("《The Adventure of Sherlock Holmes》", "Sherlock Holmes"), ("《The Adventure of Sherlock Holmes》", "John H. Watson")]

    book_char_pairs = book_char_pairs * 270
    random.shuffle(book_char_pairs)

    for book_char in book_char_pairs:
        book_name = book_char[0]
        char_name = book_char[1]

        prefix_keys1, prefix_dict1, prefix_keys2, prefix_dict2, suffix_dict1, suffix_dict2 = create_attributes(char_name, book_name, args.lang)

        # start_i = random.randint(1, 3)
        start_i = 100
        # 从哪一轮开始调用后缀式turbo

        # conversation_usr = [{"role": "system", "content": desc1}, {"role": "user", "content": start_prompt1}]
        # conversation_ass = [{"role": "system", "content": desc1}, {"role": "user", "content": start_prompt2}]

        conversation_usr = []
        conversation_ass = []
        history = ""
        
        suffix_keys1 = ["后-追问", "后-提问", "后-中二", "后-脑洞", "后-一词", "后-转换", "后-挑衅", "后-愤怒", "后-嘲讽", "后-悲伤",
                        "后-追问", "后-提问", "后-中二", "后-脑洞", "后-转换", "后-追问", "后-提问", "后-中二", "后-脑洞", "后-转换"]

        length = random.randint(3, 5)
        # 每一通对话的轮数，不用太长，太长了聊的内容也很局限

        prev_response_ass = None

        conversation_result = []
        for i in range(length):

            if i < start_i:
                prefix_key1 = random.choice(prefix_keys1)
                prefix_keys1.remove(prefix_key1)
                prefix_prompt1 = prefix_dict1[prefix_key1]
                conversation_prefix = [{"role": "user", "content": prefix_prompt1}] + conversation_usr
                response_usr = get_response(conversation_prefix, name="网友")
                print("({key}):".format(key=prefix_key1)+response_usr)
                conversation_result.append("({key}):".format(key=prefix_key1)+response_usr)
            else:
                suffix_key1 = random.choice(suffix_keys1)
                suffix_keys1.remove(suffix_key1)
                suffix_prompt1 = suffix_dict1[suffix_key1]
                conversation_suffix = [{"role": "user", "content": history}, {"role": "user", "content": suffix_prompt1}]
                response_usr = get_response(conversation_suffix, name="网友")
                print("({key}):".format(key=suffix_key1)+response_usr)
                conversation_result.append("({key}):".format(key=suffix_key1)+response_usr)

            history = history + response_usr + "\n"
            conversation_ass.append({"role": "user", "content": response_usr})
            conversation_usr.append({"role": "assistant", "content": response_usr})

            if i < start_i:
                prefix_key2 = random.choice(prefix_keys2)
                prefix_keys2.remove(prefix_key2)
                prefix_prompt2 = prefix_dict2[prefix_key2]
                conversation_prefix = [{"role": "user", "content": prefix_prompt2}] + conversation_ass
                response_ass = get_response(conversation_prefix, name=char_name)
                if prev_response_ass is not None and pattern_detector(prev_response_ass, response_ass.split(": ")[1]):
                    print("({key}):".format(key=prefix_key2)+response_ass)
                    response_ass = pattern_paraphraser(response_usr.split(": ")[1], response_ass.split(": ")[1], char_name)
                    print("({key}):".format(key="后-复述")+response_ass)
                    conversation_result.append("({key}):".format(key="后-复述")+response_ass)
                else:
                    print("({key}):".format(key=prefix_key2)+response_ass)
                    conversation_result.append("({key}):".format(key=prefix_key2)+response_ass)
                prev_response_ass = response_ass.split(": ")[1]
            else:
                if suffix_key1 is not None and suffix_key1 in ["后-挑衅", "后-愤怒", "后-嘲讽"]:
                    suffix_key2 = random.choice(["后-激动", "后-愤怒", "后-嘲讽"])
                elif suffix_key1 is not None and suffix_key1 == "追问":
                    suffix_key2 = random.choice(["后-感叹", "后-提问", "后-一句", "后-两句", "后-中二", "后-耐烦"])
                else:
                    suffix_key2 = random.choice(["后-感叹", "后-提问", "后-一句", "后-两句", "后-中二"])
                suffix_prompt2 = suffix_dict2[suffix_key2]
                conversation_suffix = [{"role": "user", "content": history}, {"role": "user", "content": suffix_prompt2}]
                response_ass = get_response(conversation_suffix, name=char_name)
                if prev_response_ass is not None and pattern_detector(prev_response_ass, response_ass.split(": ")[1]):
                    print("({key}):".format(key=suffix_key2)+response_ass)
                    response_ass = pattern_paraphraser(response_usr.split(": ")[1], response_ass.split(": ")[1], char_name)
                    print("({key}):".format(key="后-复述")+response_ass)
                    conversation_result.append("({key}):".format(key="后-复述")+response_ass)
                else:
                    print("({key}):".format(key=suffix_key2)+response_ass)
                    conversation_result.append("({key}):".format(key=suffix_key2)+response_ass)
                prev_response_ass = response_ass.split(": ")[1]

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
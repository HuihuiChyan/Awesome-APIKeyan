import base64
import requests
from PIL import Image
import io
import time
import numpy as np
import multiprocessing
import json
import os
import re
import argparse
import timeout_decorator
from functools import partial
from tqdm import tqdm

from scene_splitter import SceneSplitter

parser = argparse.ArgumentParser()
parser.add_argument(
    "--api-key",
    type=str,
    default=None,
)
parser.add_argument(
    "--output-file",
    type=str,
    default=None,
)
parser.add_argument(
    "--video-dir",
    type=str,
    default=None,
)
parser.add_argument(
    "--frame-dir",
    type=str,
    default=None,
)
parser.add_argument(
    "--input-json",
    type=str,
    default=None,
)
parser.add_argument(
    "--no-trimming",
    action="store_true",
    default=False
)
parser.add_argument(
    "--process-num",
    type=int,
    default=10,
)
parser.add_argument(
    "--captioner-name",
    type=str,
    default="gpt-4o",
)
parser.add_argument(
    "--trimmer-name",
    type=str,
    default="gpt-4-turbo",
)
parser.add_argument(
    "--input-type",
    type=str,
    choices=("frames", "video"),
    default="frames",
)
parser.add_argument(
    "--FPS",
    type=int,
    default=4,
)
parser.add_argument(
    "--frame-num",
    type=int,
    default=5,
)
args = parser.parse_args()

def resize_longer(image: Image.Image, max_size: int):
    width, height = image.size
    if width > height:
        new_width = max_size
        new_height = int(height * new_width / width)
    else:
        new_height = max_size
        new_width = int(width * new_height / height)
    return image.resize((new_width, new_height))

def image_to_base64(image, format="JPEG", **format_options):
    image = resize_longer(image, 768)
    buffered = io.BytesIO()
    image.save(buffered, format=format, **format_options)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# @timeout_decorator.timeout(1200)
def request_api(payload):

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {args.api_key}"}

    url = "https://api.ai-gaochao.cn/v1/chat/completions"

    MAX_RETRY = 5
    res = ""
    for i in range(MAX_RETRY):
        try:
            response = requests.post(url, headers=headers, json=payload).json()
            if response['choices'][0]["finish_reason"] != "stop":
                raise Exception("Completion stopped before completion.")
            res = response['choices'][0]['message']['content'].strip()
            return res
        except timeout_decorator.TimeoutError:
            raise Exception("Stuck! Please re-run this script!")
        except Exception as e:
            if i == MAX_RETRY-1:
                raise Exception("MAX_RETRY exceeded! Please check your codes! ")
            print("Failed! Retrying! The exception is "+str(e))
            time.sleep(5)
            continue
    return res
    
def OneAPIRequest(userPrompt, modelName = 'gpt-4o', genTemp = 0.0, images = None):

    image_content_list = []
    if images is not None:
        image_content_list = [
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/jpeg;base64," + image_to_base64(image),
                    "detail": "low",
                },
            }
            for image in images
        ]

    messages = [
        {
            "role": "user",
            "content": [
                *image_content_list, 
                {
                    "type": "text", 
                    "text": userPrompt,
                }
            ]
        }
    ]
    requests = {
        "model": modelName,
        "messages": messages,
    }
    response = request_api(requests)
    return response

def load_frames_from_video_path(video_path):

    frame_path = os.path.join(args.frame_dir, video_path.split("/")[-1])

    assert all([os.path.exists(os.path.join(frame_path, str(i)+".jpg")) for i in range(args.frame_num)])

    duration = json.load(open(os.path.join(frame_path, "duration.json")))

    frames = []
    for i in range(args.frame_num):
        frame = Image.open(os.path.join(frame_path, str(i)+".jpg"))
        frames.append(frame)
    return frames, duration

def build_frames_from_video(video_path, concat=False):

    splitter = SceneSplitter()

    FPS = args.FPS

    all_frames, duration = splitter.load_video(video_path, fps=FPS, return_duration=True)
    while len(all_frames) < args.frame_num:
        FPS = FPS * 2
        all_frames = splitter.load_video(video_path, fps=FPS)

    select_frames, select_idxs = splitter.merge_frames(all_frames, reserve_num=args.frame_num)

    if concat:
        select_frames = [np.concatenate(select_frames, axis=1)]

    select_frames = [Image.fromarray(img) for img in select_frames]

    return select_frames, round(duration)

def caption_a_video(video_path):
    if args.input_type=="video":
        images, duration = build_frames_from_video(video_path)
    elif args.input_type=="frames":
        images, duration = load_frames_from_video_path(video_path)

    user_prompt = f"Attached are a sequence of screenshots from a short video clip with the duration of {duration} seconds. Please provide a caption for the video clip. Focus on factual and temporal details, such as event, action, motion or interaction. DO NOT add unnecessary interpretations such as atmosphere, composition, aesthetics, psychology, or viewer's perspective. DO NOT add speculation or guesses about unseen contexts or elements. DO NOT include obscure description such as 'probably', 'seems to be', 'appear to be' or 'possibly A or B'. DO NOT describe what is not in the video, such as 'no movement', 'no action' or 'no other characters'. Provide a holistic description of the video clip. DO NOT describe individual screenshots one by one. Please format your description into three parts: '**Overall Description**', '**Background Environment**' and '**Camera Description**'. The '**Overall Description**' and '**Background Environment**' are longer and more detailed, while the '**Camera Description**' is a short sentence with no more than 20 words."
    
    response = OneAPIRequest(user_prompt, modelName = args.captioner_name, images = images)

    response = post_process(response)

    json_line = {"video_path": video_path, "captioner_name": args.captioner_name, "caption": response}

    if not args.no_trimming:

        user_prompt = """Post-process the Input Description for a video clip. Remove abstract descriptions such as interpretation, atmosphere, aesthetics, contrast or feelings. Remove speculation or guesses about unseen contexts or elements, such as 'indicating' or 'suggesting'. Remove obscure descriptions such as 'A or B', 'possibly' or 'appear to be'. DO NOT include any 'or' in the Output Description. If there is an 'A or B', replace it with only 'A'. Remove any description about what is not in the video, such as 'no movement' or 'no interaction'. Remove clip duration information. Preserve other information, especially factual and temporal details, and generate a fluent caption.

    ##Input Description: {caption}
    ##Output Description:""" 

        user_prompt = user_prompt.format(caption=response)

        response = OneAPIRequest(user_prompt, modelName = args.trimmer_name)
        json_line["untrimmed_caption"] = json_line["caption"]
        json_line["caption"] = response
        json_line["trimmer_name"] = args.trimmer_name

    counter.value += 1
    if counter.value % 1 == 0:
        used_time = time.time() - start_time
        print("*******************************")
        print(f"{counter.value} lines finished in {used_time:.2f} seconds!")
        print("*******************************")
        print(f"sampled video path: {video_path}")
        if not args.no_trimming:
            print("sampled untrimmed caption: " + json_line["untrimmed_caption"])
        print("sampled caption: " + json_line["caption"])

    with open(args.output_file, 'a+') as fout:
        fout.write(json.dumps(json_line) + "\n")

def post_process(response):
	replace_pairs = [
        (r"[\*\#]*\s*Overall Description\:{0,1}\**\:{0,1}\s*", ""), 
        (r"[\*\#]*\s*Background Environment\:{0,1}\**\:{0,1}\s*", ""),
        (r"[\*\#]*\s*Camera Description\:{0,1}\**\:{0,1}\s*", ""),
        ("\n\n", " "),
    ]
	for pair in replace_pairs:
		response = re.sub(pair[0], pair[1], response)
	return response

def init(c, t):
    global counter
    global start_time
    counter = c
    start_time = t

def reorder_jsonl_result(jsonl_file, video_dir):

    with open(jsonl_file, "r", encoding="utf-8") as fin:
        lines = [json.loads(line) for line in fin.readlines()]
        lines.sort(key=lambda x:x['video_path'])

    with open(jsonl_file[:-6]+"-reorder.jsonl", "w", encoding="utf-8") as fout:
        for line in lines:
            fout.write(json.dumps(line)+"\n")

if __name__ == "__main__":

    manager = multiprocessing.Manager()
    counter = manager.Value("counter", 0)
    start_time = time.time()

    if os.path.exists(args.output_file):
        fout = open(args.output_file, "r")
        finished_lines = [json.loads(line.strip())["video_path"] for line in fout.readlines()]
        finished_paths = set(finished_lines)
    else:
        finished_paths = []

    if args.input_type == "video":
        assert args.video_dir is not None
        video_paths = os.listdir(args.video_dir)
        unfinished_paths = []
        for video_path in video_paths:
            if re.match(r"[^\s]+\.mp4", video_path):
                video_path = os.path.join(args.video_dir, video_path)
                if video_path not in finished_paths:
                    unfinished_paths.append(video_path)

    elif args.input_type == "frames":
        assert args.frame_dir is not None
        unfinished_paths = []
        with open(args.input_json, "r") as fin:
            lines = json.load(fin)
            for video_path, meta_info in tqdm(lines.items()):
                if 'mohan/need_labeling' in lines[video_path].keys() and lines[video_path]['mohan/need_labeling'] == True:
                    if video_path not in finished_paths and os.path.exists(os.path.join(args.frame_dir, video_path.split("/")[-1])):
                        unfinished_paths.append(video_path)

    len_unfinished_paths = len(unfinished_paths)
    print(f"Start Captioning! Totally {len_unfinished_paths} Videos.")

    if args.process_num == 1:
        for video_path in tqdm(unfinished_paths):
            caption_a_video(video_path)
    else:
        pool = multiprocessing.Pool(processes=args.process_num, initializer=init, initargs=(counter, start_time, ))
        pool.map(caption_a_video, unfinished_paths)
        pool.close()
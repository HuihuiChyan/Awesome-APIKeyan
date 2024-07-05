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
from tqdm import tqdm

from scene_splitter import SceneSplitter

parser = argparse.ArgumentParser()
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
    "--process-num",
    type=int,
    default=10,
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

def build_frames_from_video(video_path, concat=False):

    splitter = SceneSplitter()

    FPS = args.FPS
    frame_num = args.frame_num
    
    all_frames, duration = splitter.load_video(video_path, fps=FPS, return_duration=True)
    while len(all_frames) < frame_num:
        FPS = FPS * 2
        all_frames = splitter.load_video(video_path, fps=FPS)

    select_frames, select_idxs = splitter.merge_frames(all_frames, reserve_num=frame_num)

    if concat:
        select_frames = [np.concatenate(select_frames, axis=1)]

    select_frames = [Image.fromarray(img) for img in select_frames]

    return select_frames, round(duration)

def process_a_video(video_path):

    frames, duration = build_frames_from_video(video_path)

    video_name = video_path.split("/")[-1]
    frame_path = os.path.join(args.frame_dir, video_name)

    os.makedirs(frame_path)
    for i,img in enumerate(frames):
        img.save(os.path.join(frame_path, f"{i}.jpg"))
    
    with open(os.path.join(frame_path, "duration.json"), "w") as fout:
        json.dump(duration, fout)

    counter.value += 1
    if counter.value % 10 == 0:
        used_time = time.time() - start_time
        print(f"{counter.value} lines finished in {used_time:.2f} seconds!")

def init(c, t):
    global counter
    global start_time
    counter = c
    start_time = t

if __name__ == "__main__":

    manager = multiprocessing.Manager()
    counter = manager.Value("counter", 0)
    start_time = time.time()

    unfinished_paths = []
    with open(args.input_json, "r") as fin:
        lines = json.load(fin)
        for video_path, meta_info in tqdm(lines.items()):
            if 'mohan/need_labeling' in meta_info.keys() and meta_info['mohan/need_labeling'] == True:
                video_name = video_path.split("/")[-1]
                frame_path = os.path.join(args.frame_dir, video_name)
                if os.path.exists(video_path) and not os.path.exists(frame_path):
                    unfinished_paths.append(video_path)

    len_unfinished_paths = len(unfinished_paths)
    print(f"Start Building Frames! Totally {len_unfinished_paths} Videos.")

    if args.process_num == 1:
        for video_path in tqdm(unfinished_paths):
            process_a_video(video_path)
    else:
        pool = multiprocessing.Pool(processes=args.process_num, initializer=init, initargs=(counter, start_time, ))
        pool.map(process_a_video, unfinished_paths)
        pool.close()
import os
import re
import cv2
import copy
import torch
import shutil
import math
import numpy as np
from PIL import Image
from scenedetect.detectors import ContentDetector

class SceneSplitter():

    def __init__(self, score="detector"):
        if score == "lpips":
            import lpips
            self.alex_net = lpips.LPIPS(net='alex')
            self.score_fn = self.lpips_score
        elif score == "ssim":
            from pytorch_msssim import ssim
            self.score_fn = self.ssim_score
        elif score == "detector":
            self.score_fn = self.detector_score
            self._kernel = None

    def load_images(self, image_paths):

        all_frames = [Image.open(image_path) for image_path in image_paths]
        all_frames = [np.array(image) for image in all_frames]

        return all_frames

    def load_video(self, video_path, fps=4, return_duration=False):

        vidcap = cv2.VideoCapture(video_path)

        all_frames = []
        sample_rate = 1000 // fps

        success, frame = vidcap.read()
        success = True
        count = 0
        while success:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            all_frames.append(frame)
            count = count + 1
            vidcap.set(cv2.CAP_PROP_POS_MSEC, (count*sample_rate))
            success, frame = vidcap.read()
        
        if not return_duration:
            return all_frames
        else:
            fps = vidcap.get(cv2.CAP_PROP_FPS)      # OpenCV v2.x used "CV_CAP_PROP_FPS"
            frame_count = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count/fps
            return all_frames, duration

    def lpips_score(self, frames1, frames2):

        frames1 = torch.Tensor(frames1)
        frames2 = torch.Tensor(frames2)

        frames1 = frames1.permute(0, 3, 1, 2)
        frames2 = frames2.permute(0, 3, 1, 2)

        with torch.no_grad():
            scores = self.alex_net(frames1, frames2)

        return scores

    def ssim_score(self, frames1, frames2):

        frames1 = torch.Tensor(frames1)
        frames2 = torch.Tensor(frames2)

        frames1 = frames1.permute(0, 3, 1, 2)
        frames2 = frames2.permute(0, 3, 1, 2)

        with torch.no_grad():

            scores = ssim(frames1, frames2, size_average=False)

        # The lower the better
        return -scores
    
    def detector_score(self, frames1, frames2):

        # hue, sat, lum, edges
        weights = [1.0, 1.0, 1.0, 0.1]

        def _mean_pixel_distance(left: np.ndarray, right: np.ndarray) -> float:
            """Return the mean average distance in pixel values between `left` and `right`.
            Both `left and `right` should be 2 dimensional 8-bit images of the same shape.
            """
            assert len(left.shape) == 2 and len(right.shape) == 2
            assert left.shape == right.shape
            num_pixels: float = float(left.shape[0] * left.shape[1])
            return (np.sum(np.abs(left.astype(np.int32) - right.astype(np.int32))) / num_pixels)


        def _estimated_kernel_size(frame_width: int, frame_height: int) -> int:
            """Estimate kernel size based on video resolution."""
            # TODO: This equation is based on manual estimation from a few videos.
            # Create a more comprehensive test suite to optimize against.
            size: int = 4 + round(math.sqrt(frame_width * frame_height) / 192)
            if size % 2 == 0:
                size += 1
            return size

        def _detect_edges(lum: np.ndarray) -> np.ndarray:
            """Detect edges using the luma channel of a frame.

            Arguments:
                lum: 2D 8-bit image representing the luma channel of a frame.

            Returns:
                2D 8-bit image of the same size as the input, where pixels with values of 255
                represent edges, and all other pixels are 0.
            """
            # Initialize kernel.
            if self._kernel is None:
                kernel_size = _estimated_kernel_size(lum.shape[1], lum.shape[0])
                self._kernel = np.ones((kernel_size, kernel_size), np.uint8)

            # Estimate levels for thresholding.
            # TODO: Add config file entries for sigma, aperture/kernel size, etc.
            sigma: float = 1.0 / 3.0
            median = np.median(lum)
            low = int(max(0, (1.0 - sigma) * median))
            high = int(min(255, (1.0 + sigma) * median))

            # Calculate edges using Canny algorithm, and reduce noise by dilating the edges.
            # This increases edge overlap leading to improved robustness against noise and slow
            # camera movement. Note that very large kernel sizes can negatively affect accuracy.
            edges = cv2.Canny(lum, low, high)
            return cv2.dilate(edges, self._kernel)

        def calculate_frame_attr(frame):

            hue, sat, lum = cv2.split(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV))

            # Performance: Only calculate edges if we have to.
            calculate_edges: bool = ((weights[-1] > 0.0))
            edges = _detect_edges(lum) if calculate_edges else None

            return {"hue": hue, "sat": sat, "lum": lum, "edges": edges}
        
        def calculate_frame_score(frame_attr1, frame_attr2):

            components = [
                _mean_pixel_distance(frame_attr1["hue"], frame_attr2["hue"]),
                _mean_pixel_distance(frame_attr1["sat"], frame_attr2["sat"]),
                _mean_pixel_distance(frame_attr1["lum"], frame_attr2["lum"]),
                0.0 if frame_attr1["edges"] is None else _mean_pixel_distance(
                    frame_attr1["edges"], frame_attr2["edges"]),
            ]

            frame_score: float = (
                sum(component * weight for (component, weight) in zip(components, weights))
                / sum(abs(weight) for weight in weights))

            return frame_score
        
        frame_attrs1 = [calculate_frame_attr(frame) for frame in frames1]
        frame_attrs2 = [calculate_frame_attr(frame) for frame in frames2]

        scores = []
        for attr1, attr2 in zip(frame_attrs1, frame_attrs2):
            scores.append(calculate_frame_score(attr1, attr2))

        return np.array(scores)

    def merge_frames(self, all_frames, reserve_num=5):

        attr_list = copy.deepcopy(all_frames)
        concat_frames = np.stack(all_frames)
        dist_list = [float("inf")] + self.score_fn(concat_frames[:-1], concat_frames[1:]).squeeze().tolist()
        
        indx_list = [i for i in range(len(all_frames))]

        while(len(indx_list) > reserve_num):

            min_idx = np.array(dist_list).argmin()

            if min_idx == 1:
                remove_idx = 1
            elif min_idx == len(indx_list) - 1:
                remove_idx = len(indx_list) - 2
            else:
                if dist_list[min_idx-1] < dist_list[min_idx+1]:
                    remove_idx = min_idx - 1
                else:
                    remove_idx = min_idx 

            curr_dist = self.score_fn(attr_list[remove_idx-1][np.newaxis,...], attr_list[remove_idx+1][np.newaxis,...])
            curr_dist = curr_dist.squeeze().tolist()
            dist_list = dist_list[:remove_idx] + [curr_dist] + dist_list[remove_idx+2:]
            attr_list = attr_list[:remove_idx] + attr_list[remove_idx+1:]
            indx_list = indx_list[:remove_idx] + indx_list[remove_idx+1:]
        
        select_frames = []
        for idx in indx_list:
            select_frames.append(all_frames[idx])

        return select_frames, indx_list

if __name__ == "__main__":

    video_paths = [
        "Cases-Anime-Random/Children_Who_Chase_Lost_Voices-Scene-0903.mp4",
        "Cases-Anime-Random/Suzume-Scene-1006.mp4",
        "Cases-Anime-Random/Sword_Art_Online_Alicization_War_of_Underworld-Scene-303.mp4",
        "Cases-Anime-Random/The_Graden_of_Words-Scene-041.mp4",
        "Cases-Anime-Random/The_Graden_of_Words-Scene-210.mp4",
        "Cases-Anime-Random/The_place_promised_in_our_early_days-Scene-0652.mp4",
        "Cases-Anime-Random/Tokyo_Ghoul-Scene-473.mp4",
        "Cases-Anime-Random/Weathering_With_You-Scene-1357.mp4",
        "Cases-Anime-Random/Your_Name-Scene-1161.mp4",
    ]

    splitter = SceneSplitter()

    for video_path in video_paths:

        FPS = 4
        RESERVE_NUM = 3

        all_frames = splitter.load_video(video_path, fps=FPS)
        while len(all_frames) < RESERVE_NUM:
            FPS = FPS * 2
            all_frames = splitter.load_video(video_path, fps=FPS)

        select_frames, select_idxs = splitter.merge_frames(all_frames, reserve_num=RESERVE_NUM)

        video_name = video_path.split("/")[-1].replace(".mp4", "")
        
        frames_folder = os.path.join(os.path.dirname(video_path), "frames", video_name+"-frames")

        if os.path.exists(frames_folder):
            shutil.rmtree(frames_folder)
        os.makedirs(frames_folder, exist_ok=True)

        for idx, frame in zip(select_idxs, select_frames):

            frame = Image.fromarray(frame)
            frame.save(os.path.join(frames_folder, video_name+"-"+format(idx, '03d')+"-of-"+str(len(all_frames))+".jpg"))
    
        frame = np.concatenate(select_frames, axis=0)
        frame = Image.fromarray(frame)
        frame.save(os.path.join(frames_folder, video_name+"-concat-of-"+str(len(all_frames))+".jpg"))
import math
import jieba_fast
import numpy as np

class DataCollatorForNoiser:
    def __init__(self, tokenizer, mask_token="<MASK>", separator=""):
        self.tokenizer = tokenizer# jieba_fast.lcut
        self.mask_token = mask_token
        self.separator = separator

    def random_mask(self, source, mask_ratio):
        # 注意！输入的序列应当是没有PADDING的，也没有开始和结束符
        num_to_mask = int(math.ceil(float(len(source)) * mask_ratio))
        # if num_to_mask == 0:
        #     return source
        if num_to_mask == 0:
            num_to_mask = 1

        indices = np.random.permutation(len(source))[:num_to_mask]

        source[indices] = self.mask_token

        return source

    def random_delete(self, source, delete_ratio):
        # 注意！输入的序列应当是没有PADDING的，也没有开始和结束符
        num_to_delete = int(math.ceil(float(len(source)) * delete_ratio))
        if num_to_delete == 0:
            return source

        indices = np.random.permutation(len(source))[:num_to_delete]

        to_keep = np.ones(len(source), dtype=int) == 1
        to_keep[indices] = False

        source = source[to_keep]
        
        return source

    def random_insert(self, source, insert_ratio):
        # 注意！输入的序列应当是没有PADDING的，也没有开始和结束符
        num_to_insert = int(math.ceil(float(len(source)) * insert_ratio))
        if num_to_insert == 0:
            return source

        result = np.array(["<placeholder" for i in range(len(source)+num_to_insert)], dtype=object)
        
        indices = np.random.permutation(len(source)+num_to_insert)[:num_to_insert]

        to_keep = np.ones(len(source)+num_to_insert, dtype=int) == 1
        to_keep[indices] = False

        result[to_keep] = source
        result[~to_keep] = self.mask_token

        return result

    def random_permute(self, source, permute_ratio):
        # 注意！输入的序列应当是没有PADDING的，也没有开始和结束符
        num_to_permute = math.ceil(((len(source) * 2) * permute_ratio) / 2.0)
        indices = np.arange(len(source))[:num_to_permute]
        permute_indices = np.random.permutation(indices)
        source[indices] = source[permute_indices]

        return source

    def __call__(self, source, mask_ratio=0.1, insert_ratio=0.1, delete_ratio=0.1, permute_ratio=0.0):

        target = np.array(self.tokenizer(source), dtype=object)

        if mask_ratio > 0:
            target = self.random_mask(target, mask_ratio=mask_ratio)

        if delete_ratio > 0:
            target = self.random_delete(target, delete_ratio=delete_ratio)

        if insert_ratio > 0:
            target = self.random_insert(target, insert_ratio=insert_ratio)

        if permute_ratio > 0:
            target = self.random_permute(target, permute_ratio=permute_ratio)

        return self.separator.join(target)

if __name__ == "__main__":

    text = "这是一个测试，这是另外一个测试。"
    noiser = DataCollatorForNoiser(tokenizer=jieba_fast.lcut)
    print(noiser(text))
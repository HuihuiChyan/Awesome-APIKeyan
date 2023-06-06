import math
import torch
from transformers import GPT2Tokenizer

class DataCollatorForNoiser:
	def __init__(self, tokenizer):
		self.tokenizer = tokenizer
		self.mask_index = 27932 # for GPT2
		self.LOWER_BOUND = 0
		self.UPPER_BOUND = tokenizer.vocab_size - 1 #omit EOS for GPT2

	def word_starts(self, source):
		is_word_start = torch.ones(source.size()).long()
		return is_word_start

	def add_whole_word_mask(self, source, mask_ratio, random_ratio, replace_length):
		# 改编自fairseq(以及复旦NLP开源的CPT)中BART的加噪函数
		# 注意！输入的序列应当是没有PADDING的，也没有开始和结束符
		# 注意！如果replace_length为0，这个函数实际上用于删除而非掩码

		assert replace_length in [-1, 0, 1]

		is_word_start = self.word_starts(source)

		num_to_mask = int(math.ceil(is_word_start.float().sum() * mask_ratio))
		if num_to_mask == 0:
			return source

		word_starts = is_word_start.nonzero(as_tuple=False)
		indices = word_starts[
			torch.randperm(word_starts.size(0))[:num_to_mask]
		].squeeze(1)

		# 在num_to_mask个token中，取mask_random个用随机词做替换，其余的用mask做替换
		mask_random = torch.FloatTensor(num_to_mask).uniform_() < random_ratio
		source_length = source.size(0)
		to_keep = torch.ones(source_length, dtype=torch.bool)
		if replace_length == 0:
			to_keep[indices] = 0
		else:
			# 在num_to_mask个token中，取mask_random个用随机词做替换，其余的用<MASK>做替换
			# source[indices] = self.mask_index unused for GPT2
			source[indices[mask_random]] = torch.randint(
				self.LOWER_BOUND, self.UPPER_BOUND, size=(mask_random.sum(),)
			)

		# 这个函数的意义在于，对于所有的non_word_start进行对应的mask
		while indices.size(0) > 0:
			uncompleted = is_word_start[indices + 1] == 0
			indices = indices[uncompleted] + 1
			mask_random = mask_random[uncompleted]
			if replace_length != -1:
				# delete token
				# 如果replace_length不等于-1，那就对所有的non_word_start进行了删除
				to_keep[indices] = 0
			else:
				# keep index, but replace it with [MASK]
				source[indices] = self.mask_index
				source[indices[mask_random]] = torch.randint(
					self.LOWER_BOUND, self.UPPER_BOUND, size=(mask_random.sum(),)
				)

			assert source_length - 1 not in indices

		source = source[to_keep]

		return source

	def add_permuted_noise(self, tokens, permute_ratio):
		# 改编自fairseq中BART的加噪函数

		num_words = len(tokens)
		num_to_permute = math.ceil(((num_words * 2) * permute_ratio) / 2.0)
		substitutions = torch.randperm(num_words)[:num_to_permute]
		tokens[substitutions] = tokens[substitutions[torch.randperm(num_to_permute)]]
		return tokens

	def add_insertion_noise(self, tokens, insert_ratio, random_ratio):
		# 改编自fairseq中BART的加噪函数
		# 注意！输入序列应当是没有PADDING的，并且没有开始和结束符

		if insert_ratio == 0.0:
			return tokens

		num_tokens = len(tokens)
		n = int(math.ceil(num_tokens * insert_ratio))

		noise_indices = torch.randperm(num_tokens + n)[:n]
		noise_mask = torch.zeros(size=(num_tokens + n, ), dtype=torch.bool)
		noise_mask[noise_indices] = 1
		result = torch.LongTensor(n + len(tokens)).fill_(-1)

		num_random = int(math.ceil(n * random_ratio))
		result[noise_indices[num_random:]] = self.mask_index
		result[noise_indices[:num_random]] = torch.randint(
			low=self.LOWER_BOUND, high=self.UPPER_BOUND, size=(num_random,)
		)

		result[~noise_mask] = tokens

		assert (result >= 0).all()
		return result

	def __call__(self, input_ids, mask_ratio=0.2, insert_ratio=0.1, delete_ratio=0.1, mask_random_ratio=1.0, insert_random_ratio=1.0):

		targets = []
		for source in input_ids:

			if mask_ratio > 0:
				if args.mask_strategy == "mask_to_multi":
					replace_length = -1
				else:
					replace_length = 1

				target = self.add_whole_word_mask(source, 
												  mask_ratio=mask_ratio,
												  random_ratio=mask_random_ratio,
												  replace_length=replace_length)

			if delete_ratio > 0:
				target = self.add_whole_word_mask(target,
												  mask_ratio=delete_ratio,
												  random_ratio=-1, #unused
												  replace_length=0)

			if insert_ratio > 0:
				target = self.add_insertion_noise(target, 
												  insert_ratio=insert_ratio,
												  random_ratio=insert_random_ratio)

			targets.append(target)

		return targets

if __name__ == "__main__":
	tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

	texts = ["我是大傻逼", "我爱你"]
	input_ids = [e["input_ids"] for e in tokenizer(texts)]
	noiser = DataCollatorForNoiser(tokenizer)
	import pdb;pdb.set_trace()
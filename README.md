# Awesome-APIKeyan

在ChatGPT时代，做为一名普通研究生的我们，没有算力训练大模型，是否注定无路可走了吗？

答案是不是的！新的时代有新的范式，虽然我们只能调用API接口，但是一样可以发论文！

全世界的无产者们，在API科研的赛道上卷起来！


# 🏴󠁶󠁵󠁭󠁡󠁰󠁿 Overview

本仓库实现了调用ChatGPT接口进行各种任务的脚本，比如机器翻译、对话生成等等，并且每个脚本都提供了单线程（便于调试BUG）和多线程（便于快速推断）的两种模式。您可以参考我的脚本进行修改，实现自己想要基于ChatGPT完成的功能。


# ⚡️ Usage

## 环境配置

参照如下版本配置您的环境:

- python 3.10.10
- openai 0.27.6
- transformers 4.29.1
- sacremoses 0.0.53

## 程序运行

运行如下的命令来执行机器翻译：
```shell
python do_translation.py \
    --api-key your-api-key \
    --source-file ./path/to/your/input \
    --output-file ./path/to/your/result \
    --source-lang English \
    --target-lang Chinese
```

## 脚本说明
- do_denoisify.py 用于给平行语料加噪，用来训练QE系统
- do_evaluate_chatbot.py 用于评估对话系统的输出
- do_multichat_rewrite.py 用于自动产生风格化对话数据
- do_multichat_seed.py 用于自动产生风格化对话数据
- do_noisify.py 用于给平行语料加噪，用来训练QE系统
- utils_noiser.py 用于给平行语料加噪时，在平行语料中进行插入、删除等破坏
- utils.py 工具函数，包含了调用turbo、gpt4等的函数

## 未来计划

- [✅] 添加gpt4模型的调用脚本
- [✅] 添加对话生成的脚本
- [ ] 添加davinci模型的调用脚本

## 致谢

> 感谢我的女朋友小白，陪伴我在北京度过艰难的实习生活

# 💬 Citation
If you find our work is helpful, please cite as:
```
@misc{awesome-apikeyan,
  author = {Hui Huang},
  title = {Awesome APIKeyan: Proletarier aller Länder, vereinigt euch!},
  year = {2023},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/HuihuiChyan/Awesome-APIKeyan}},
}
```

# 👍 Contributing

感谢任何形式的贡献和建议！

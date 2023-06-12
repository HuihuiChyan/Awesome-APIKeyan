### 模式说明
- do_multichat_generate：使用多个agent，借助非常复杂流程生成闲聊数据，不过数据质量仍然欠佳
- do_multichat_rewrite：基于BELLE的数据，对其中某个角色的说话内容进行角色改写生成闲聊数据；
- do_multichat_selfseed：基于自己生成的种子词生成闲聊数据；
- do_multichat_seed：基于豆瓣上的种子问题生成闲聊数据；

### 数据下载

花了很多钱爬下来的中英文角色扮演闲聊数据：https://drive.google.com/drive/folders/1bBJw0yXzl_wSM1uNC8mvJUU9F3gyXZWD?usp=sharing

用于rewrite的BELLE的数据可以从这里下载：https://huggingface.co/datasets/BelleGroup/generated_chat_0.4M

用于作为seed的豆瓣闲聊数据可以从这里下载：https://github.com/MarkWuNLP/MultiTurnResponseSelection
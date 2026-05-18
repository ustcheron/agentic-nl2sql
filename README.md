# 如何采集NL2SQL Agent轨迹 & 运行SFT & 评估

## Agent轨迹采集

1. 下载BIRD数据集，解压到 bird 目录下，训练集和验证集的schemas.json我已经解析好了，所以这里只需要 train.json 和 dev.json
2. BIRD数据库也解压到适当位置（我的放在了~/bird_db，数据库很大，不需要用git管理），然后 cd 到 bird 目录，启动 sql_server服务，用于在数据库中执行SQL、评估正确性（启动命令在sql_server.py第一行，需要安装gunicorn，flask等依赖）
3. 下载Qwen2.5-Coder-32B-Instruct并部署（推荐使用vllm），我是部署在本地的10080端口，通过openai格式的python sdk来使用
4. 运行 collect_trajectory.py，采集到的轨迹会保存在 ./collected/trajectory.jsonl
5. 运行 postprecess_collected_data.py，将轨迹转化为一问一答的格式，包括train.json和val.json，可用来做SFT


## 运行SFT

SFT我用的也是RL-Factory，环境的配置请参考原始仓库 https://github.com/Simple-Efficient/RL-Factory，verl的环境配置其实是比较麻烦的，但是这个仓库给的配置脚本很好，没有bug，这一点非常好

SFT的运行脚本在./RL-Factory/agent_sft.sh，根据情况修改路径和其他配置信息。相比普通的SFT,主要修改就是添加了AgentSFTDataset类（见./RL-Factory/verl/utils/dataset/sft_dataset.py），遮盖sql_exec_result标签和其中的内容

用verl做SFT的一个缺点就是得到的checkpoint不是huggingface格式，要手动转换，在RL-Factory目录下运行以下命令：
```bash
CUDA_VISIBLE_DEVICES=0 python scripts/model_merger.py merge --backend fsdp --local_dir ~/models/agent-7b/global_step_438 --target_dir ~/models/agent-7b/ --hf_model_path ~/models/agent-7b/global_step_438/huggingface/
```
然后就可以在agent-7b目录得到正常的huggingface格式模型了


## 评估SFT模型的Agent能力

评估其实和轨迹收集的代码是一样的，将上一步的模型用vllm部署在本地，然后运行 async_eval.py 即可

## 运行Agentic RL

RL我用的是RL-Factory，启动脚本在./RL-Factory/run_grpo.sh。RL的初始模型理论上应该是SFT的checkpoint，如果暂时没有完成SFT，可以用Qwen2.5-Coder-7B-Instruct，也可以运行

这个脚本的运行需要4 * A800 80G，如果暂时没有这个资源可以先学习一下RL-Factory框架的代码设计

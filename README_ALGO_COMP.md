# graphrag-dev Algorithm Comparison

## Overview
用不同的社区发现或聚类算法进行indexing，并比较它们的效果。
目前支持的算法包括：
- Leiden
- EVOC
- Louvain
- KMeans
- Girvan-Newman
- Label Propagation

如果想自行添加其他算法，可以在`graphrag/index/operations/cluster_graph.py`中添加。

数据集：500条用户与大模型对话及反馈的case。仅使用用户query和模型回复作为文本数据进行聚类。

使用graphrag的local search和global search功能对比不同聚类算法的效果。

global比较方式：
- 生成标准答案：
  - 用大模型对500条数据分别进行主题的提取
  - 用大模型将500个主题进行分类，总结出5-10个大主题。主题数量可以在`ragtest/src/global_search_true/generate_global_topics.py`中修改。
  - 保存若干热门主题和摘要作为标准答案。
- 对比不同聚类算法的结果：
  - 对每个聚类算法，运行graphrag的global search功能，询问数据库中热门主题和摘要。
  - 使用大模型将每个聚类算法的结果与标准答案进行对比，评价，打分。

local比较方式：
- 生成标准答案：
  - 选择一个特定的主题，用大模型筛选出所有与该主题相关的样本。
  - 用大模型对这些样本进行总结，生成该主题的摘要作为标准答案。
- 对比不同聚类算法的结果：
  - 对每个聚类算法，运行graphrag的local search功能，询问这个主题的摘要。
  - 使用大模型将每个聚类算法的结果与标准答案进行对比，评价，打分。
- 可以同时对比多个主题。


## Graphrag Changes
- 添加了`cluster_method`参数到`build_index`、`index_cli`和`update_cli`函数。
- 更新了`PipelineFactory`以接受`cluster_method`参数用于社区检测。
- 在配置默认值和模型设置中添加了`cluster_method`。
- 增强了`cluster_graph`函数以利用指定的聚类方法。
- 创建了Makefile目标以运行不同聚类算法的索引。


## Document Specification
- ragtest: 包含测试代码和数据集的目录。
- ragtest/input: 包含原始数据集的目录。
- ragtest/output: 包含graphrag index的输出结果。
- ragtest/(output_leiden/output_evoc/output_louvain...): 包含不同聚类算法的输出结果。手动从output目录中复制到对应的子目录。
- ragtest/src/global_search_true: 包含生成正确的全局主题和摘要的代码。可以更改使用的样本数量和生成的主题数量。包含生成的标准答案。
- ragtest/src/local_search_true: 包含生成正确的特定主题的摘要的代码。可以更改主题。
- ragtest/src: 包含运行通过local和global search对比不同聚类算法的代码。包含对比结果。

## How to Use

### Environment Setup

#### Go to root directory of graphrag-dev
```bash
cd ~/home/graphrag-dev
```

#### Activate Conda environment
```bash
conda activate rag-dev
```

if you don't have the environment, you can create it with:
```bash
conda env create -f environment.yml
```

## Compare different clustering algorithms
### Compare local search
```bash
make compare-global
```
### Compare global search
```bash
make compare-local
```


## Run graphrag index in different cluster algorithms

#### Leiden 
```bash
make run-leiden
```

#### EVOC
```bash
make run-evoc
```

#### Louvain
```bash
make run-louvain
``` 

...

## Query the index

### Use make command to run the query
### Example query
```bash
make query-local QUERY="What is quantum computing?"
```

```bash
make query-global QUERY="What is software engineering?"
```

### Query with command line arguments
```bash
cd ~/home/graphrag-dev/ragtest && \
graphrag query \
  --method standard \
  --query "What is quantum computing?" \
  --data ~/home/graphrag-dev/ragtest/output \
```

You can store output files in a specific directory by adding `--data <your_directory>`.
So you can use output from different cluster methods to compare more easily.
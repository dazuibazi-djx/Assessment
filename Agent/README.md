# 科研助手 Agent


这个项目里的 LangChain 主要做三件事：
- 注册工具
- 接收用户输入
- 按固定流程调用工具


## 1. 项目主线

核心流程是固定的：

`search -> download -> parse -> summarize -> review -> save`

对应含义如下：

1. `search`
   从 arXiv 检索论文
2. `download`
   下载论文 PDF 到本地
3. `parse`
   解析 PDF 文本，并保存解析结果
4. `summarize`
   生成结构化总结
5. `review`
   生成审稿式评价和评分
6. `save`
   保存元数据、总结结果和审稿结果

这条流程写死在 `src/pipeline.py` 中，作为项目的主线。

## 2. 目录结构

```text
Agent/
├─ main.py
├─ config.py
├─ requirements.txt
├─ README.md
├─ prompts/
│  ├─ system_prompt.txt
│  ├─ summary_prompt.txt
│  └─ review_prompt.txt
├─ data/
│  ├─ pdf/
│  ├─ meta/
│  ├─ parsed/
│  └─ results/
├─ examples/
└─ src/
   ├─ __init__.py
   ├─ agent.py
   ├─ pipeline.py
   ├─ schemas.py
   └─ tools/
      ├─ __init__.py
      ├─ arxiv_search.py
      ├─ paper_download.py
      ├─ pdf_parse.py
      ├─ summarize.py
      ├─ review.py
      └─ storage.py
```

## 3. 每个目录是做什么的

### `src/`
核心源码目录，负责组织主流程、Agent 封装和数据结构。

### `src/tools/`
工具层目录。这里保留 6 个工具模块，每个文件只负责一类功能。

### `prompts/`
提示词模板目录。后续总结和审稿逻辑会从这里读取提示词。

### `data/pdf/`
保存原始论文 PDF。

### `data/meta/`
保存论文基础元数据，例如：

- `title`
- `authors`
- `arxiv_id`
- `abstract`
等
### `data/parsed/`
保存 PDF 解析后的纯文本内容。

### `data/results/`
保存最终处理结果，例如：

- summary
- review
- score

### `examples/`
放示例脚本或样例输入输出，便于展示。

## 4. 每个文件的作用

### 根目录文件

#### `main.py`
项目启动入口。

主要职责：

- 接收命令行参数
- 加载配置
- 调用固定流程
- 输出结果

当前支持的展示方式是：

```bash
python main.py --query "yolo"
```

#### `config.py`
配置管理模块。

主要职责：

- 统一管理路径
- 管理模型名和 API Key
- 管理超时参数

#### `requirements.txt`
项目依赖列表，用于环境安装和复现。

#### `README.md`
项目说明文档，用于介绍结构、流程和模块职责。

### `src/` 中的文件

#### `src/__init__.py`
将 `src` 声明为 Python 包。

#### `src/pipeline.py`
固定流程编排模块，是这个项目最重要的文件之一。

主要职责：

- 按顺序执行 `search -> download -> parse -> summarize -> review -> save`
- 控制整条主线
- 作为课程题目的完整流程入口


#### `src/agent.py`
轻量 Agent 封装模块。

这里不做复杂的自主规划，而是做一个轻 Agent：

- 接收 query
- 注册工具
- 调用固定流程
- 返回最终结果

也就是说，`agent.py` 更像是对 `pipeline.py` 的 LangChain 包装。

#### `src/schemas.py`
统一定义数据结构。

当前主要包括：

- `PaperMetadata`
- `PaperContent`
- `PaperSummary`
- `PaperReview`
- `PaperResult`

这样各模块之间传递数据时更清晰，也更容易维护。

### `src/tools/` 中的文件

#### `src/tools/arxiv_search.py`
论文检索工具。

作用：

- 根据查询词搜索 arXiv
- 返回论文列表
- 输出统一的元数据结构

#### `src/tools/paper_download.py`
PDF 下载工具。

作用：

- 下载论文 PDF
- 保存到 `data/pdf/`
- 使用 `arxiv_id.pdf` 作为文件名

使用 `arxiv_id` 做文件名非常简单，但工程感很强，也方便去重。

#### `src/tools/pdf_parse.py`
PDF 解析工具。

作用：

- 读取 PDF
- 提取正文文本
- 为总结和评审提供输入

#### `src/tools/summarize.py`
论文总结工具。

作用：

- 根据论文文本生成结构化总结
- 输出摘要、关键点和局限性

#### `src/tools/review.py`
论文审稿工具。

作用：

- 输出优点
- 输出缺点
- 给出综合评分
- 生成审稿式结论

体现“总结 + 评价 + 打分”的特点。

#### `src/tools/storage.py`
本地存储工具。

作用：

- 保存 PDF
- 保存 meta
- 保存 parsed 文本
- 保存 summary 和 review 结果
- 提供基于 `arxiv_id` 的去重检查

这里的去重逻辑很重要，例如：

```python
if paper_exists(arxiv_id):
    skip
```

这能体现系统的“可复用”能力，而不是每次都重复处理。


##5. 当前最重要的功能要求

这个项目要完成三件事：

### 1. 完整流程
必须有：

- 检索
- 下载
- 解析
- 总结
- 审稿
- 保存

### 2. 本地存储
至少要保存：

- PDF
- meta
- summary
- review

这样才符合“小型论文数据库”的要求。

### 3. 总结 + 审稿评分
必须有：

- 结构化 summary
- review
- 优缺点
- 分数

这部分是项目最容易拿分的地方。

## 7. 当前开发状态

目前已经完成：

- 工程目录搭建
- 模块职责划分
- 固定流程设计
- 轻 Agent 结构设计
- `main.py` 参数入口
- 基于 `arxiv_id` 的文件命名约定
- `storage.py` 中的基础去重接口和本地保存接口

目前尚未完成：

- 真实 arXiv 检索
- 真实 PDF 下载
- PDF 解析实现
- LLM 总结与审稿实现
- LangChain 与真实工具结果的完整联动

## 8. 后续开发顺序

1. `src/tools/arxiv_search.py`
2. `src/tools/paper_download.py`
3. `src/tools/pdf_parse.py`
4. `src/tools/summarize.py`
5. `src/tools/review.py`
6. `src/pipeline.py`
7. `src/agent.py`


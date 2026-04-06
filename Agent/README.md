# 科研助手 Agent

这个项目是我做的一个课程作业，作用其实挺直接的，就是输入一个关键词，然后去 arXiv 找论文，接着把 PDF 下下来，解析一下正文，再做总结、分析和一个简单的审稿式评价，最后把结果存到本地。项目直接直接下载就可以直接运行。

我这里没有把它做成那种特别复杂的 agent，反正这个题目流程比较固定，所以最后就是按顺序跑：

`search -> download -> parse -> summarize -> analyze -> review -> save`

## 环境

Python 版本我这边用的是 3.11，正常来说别太低就行。

先装依赖：

```bash
pip install -r requirements.txt
```

项目根目录还要放一个 `.env` 文件，我现在用的是这种写法：

```env
OPENAI_API_KEY=你的密钥
MODEL_NAME=deepseek-reasoner
OPENAI_BASE_URL=https://api.deepseek.com

DATA_DIR=data
PDF_DIR=data/pdf
META_DIR=data/meta
RESULTS_DIR=data/results
```

这些目录程序会自己建，不用手动创建：

- `data/pdf`
- `data/meta`
- `data/parsed`
- `data/results`

## 怎么跑

最普通的跑法：

```bash
python main.py --query "vision transformer" --max-results 1
```

如果本地已经有处理过的论文，不想再跑一遍：

```bash
python main.py --query "graph neural network" --max-results 3 --skip-existing
```

如果只是想看看现在注册了哪些工具：

```bash
python main.py --query "large language model" --max-results 1 --list-tools
```

## 目录大概就是这样

```text
Agent/
├─ main.py
├─ config.py
├─ requirements.txt
├─ README.md
├─ prompts/
├─ data/
├─ examples/
└─ src/
   ├─ agent.py
   ├─ pipeline.py
   ├─ schemas.py
   └─ tools/
      ├─ arxiv_search.py
      ├─ paper_download.py
      ├─ pdf_parse.py
      ├─ summarize.py
      ├─ review.py
      └─ storage.py
```

几个主要文件：

- `main.py` 是命令行入口
- `config.py` 读配置
- `src/pipeline.py` 串主流程
- `src/agent.py` 放 Agent 那层包装
- `src/tools/` 里面就是各个具体功能

## 主要功能

1. 论文检索  
用 arXiv 做搜索，返回的结果不是只给标题，而是会整理成统一字段，比如：

- `arxiv_id`
- `title`
- `authors`
- `abstract`
- `published`
- `updated`
- `pdf_url`
- `primary_category`

2. PDF 下载  
根据 `pdf_url` 下载论文，然后存到 `data/pdf/`，文件名直接用 `arxiv_id.pdf`。

3. PDF 解析  
把本地 PDF 读出来，默认提取前 5 页文本，解析结果会放到 `data/parsed/`。

4. 单篇论文总结  
这部分会根据标题、摘要和正文生成结构化总结，基本会覆盖研究目标、方法、实验结果和核心贡献。

5. 单篇论文分析  
在总结之外，再补一层分析，主要看论文价值、方法合不合理、实验够不够、结果靠不靠谱，还有局限性这些。

6. 审稿式评价  
这部分会尽量给出：

- `strengths`
- `weaknesses`
- `score`
- `confidence`
- `recommendation`

7. 本地保存  
结果不会只是打印一下就没了，而是会分别存到：

- `data/pdf/`
- `data/meta/`
- `data/parsed/`
- `data/results/`

所以后面还能继续看，也能重复用。

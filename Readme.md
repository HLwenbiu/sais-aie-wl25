&lt;!-- README.md --&gt;
&lt;div align="center"&gt;

# 🏥 SAIS-AIE-WL25 医疗诊断 AI 系统  
*基于多 Agent 协作 + RAG 的心内科辅助诊断平台*

[📄 项目简介](#-项目简介) •
[🎯 核心功能](#-核心功能) •
[🏗️ 系统架构](#️-系统架构) •
[🚀 快速开始](#-快速开始) •
[🐳 Docker 部署](#-docker-部署) •
[🧪 测试](#-测试) •
[📊 报告示例](#-报告示例) •
[🔧 配置说明](#-配置说明)

&lt;/div&gt;

---

## 📋 项目简介
SAIS-AIE-WL25 采用**多 Agent 协作架构**，结合**检索增强生成（RAG）**与**大语言模型**，为心内科疾病提供智能化辅助诊断。  
系统通过三个专业化医疗 Agent 协同工作，模拟真实诊疗流程，输出结构化诊断报告。

---

## 🎯 核心功能
- **多 Agent 协作诊断**  
  - Dr.Hypothesis（假设生成）  
  - Dr.Challenger（质疑验证）  
  - Dr.Clinical-Reasoning（综合推理）  
- **RAG 增强检索** – 基于医学文献的向量检索与推理  
- **智能诊断报告** – 一键生成结构化 JSON/PDF 报告  
- **心内科专业化** – 聚焦心血管疾病诊疗场景  

---

## 🏗️ 系统架构

### 核心 Agent
| Agent | 职责 |
|-------|------|
| `dr_hypothesis_agent.py` | 根据症状/检查生成初步诊断假设 |
| `dr_challenger_agent.py` | 对假设进行质疑，提出鉴别诊断 |
| `dr_clinical_reasoning_agent.py` | 综合结果给出最终诊断与治疗建议 |

### 技术栈
- Python 3.8+
- RAG（FAISS + 嵌入模型）
- DeepSeek-V3 API
- Docker（可选）

---

## 📁 项目结构


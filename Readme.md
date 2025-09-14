🏥 SAIS-AIE-WL25 医疗诊断AI系统
一个基于多Agent协作和RAG技术的智能医疗诊断系统，专注于心内科疾病的辅助诊断。
📋 项目简介
本项目是一个先进的医疗诊断AI系统，采用多Agent协作架构，结合检索增强生成(RAG)技术和大语言模型，为心内科疾病提供智能化的辅助诊断服务。系统通过三个专业化的医疗Agent协同工作，模拟真实的医疗诊断流程。
🎯 核心功能
多Agent协作诊断: 三个专业化Agent协同工作，提供全面的诊断分析
RAG增强检索: 基于医学文献的知识检索和推理
智能诊断报告: 自动生成结构化的诊断报告
心内科专业化: 专注于心血管疾病的诊断和治疗建议
🏗️ 系统架构
核心Agent
Dr.Hypothesis Agent (假设生成医生)基于患者症状和检查结果生成初步诊断假设
提供可能的疾病列表和初步分析

Dr.Challenger Agent (质疑医生)对初步诊断进行质疑和验证
提出鉴别诊断和需要排除的疾病

Dr.Clinical-Reasoning Agent (临床推理医生)综合前两个Agent的结果进行最终推理
生成最终诊断和治疗建议

技术栈
Python 3.8+: 主要开发语言
RAG系统: 检索增强生成技术
FAISS: 向量数据库用于文档检索
DeepSeek-V3: 大语言模型API
📁 项目结构
sais-aie-wl25/
├── app/                          # 主应用目录
│   ├── agents/                   # Agent模块
│   │   ├── medical_agent_orchestrator.py  # Agent协调器
│   │   ├── dr_hypothesis_agent.py         # 假设生成Agent
│   │   ├── dr_challenger_agent.py         # 质疑Agent
│   │   └── dr_clinical_reasoning_agent.py # 临床推理Agent
│   ├── rag/                      # RAG系统
│   │   ├── rag_pipeline.py       # RAG流水线
│   │   ├── vector_storage.py     # 向量存储
│   │   ├── document_processor.py # 文档处理
│   │   └── embedding_processor.py # 嵌入处理
│   ├── clients/                  # API客户端
│   │   └── deepseek_client.py    # DeepSeek API客户端
│   ├── config/                   # 配置文件
│   └── utils/                    # 工具函数
├── corpus/                       # 医学文献语料库
├── medical_records/              # 测试病例数据
│   ├── case1.json - case10.json # 10个测试病例
├── tests/                        # 测试文件
│   ├── test_with_case1.py - test_with_case10.py
├── output/                       # 诊断报告输出目录
├── rag_vector_db/               # 向量数据库
├── requirements.txt             # Python依赖

🚀 快速开始
环境要求
Python 3.8 或更高版本
8GB+ 内存推荐
DeepSeek API密钥
1. 克隆项目
git clone https://github.com/your-username/sais-aie-wl25.git
cd sais-aie-wl25
2. 安装依赖
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
3. 配置API密钥
在 app/config/deepseek_config.py 中配置您的DeepSeek API密钥：
DEEPSEEK_CONFIG = {
    "api_key": "your-deepseek-api-key-here",
    "base_url": "https://api.juheai.top/v1",
    "timeout": 60,
    "max_retries": 3
}
4. 初始化向量数据库
# 处理医学文献并构建向量数据库
python -c "from app.rag.rag_pipeline import RAGPipeline; pipeline = RAGPipeline(); pipeline.process_corpus_directory('corpus')"
5. 运行测试
# 测试单个病例
python tests/test_with_case1.py

# 或者测试所有病例
for i in {1..10}; do python tests/test_with_case$i.py; done
💡 使用示例
基本使用
from app.agents.medical_agent_orchestrator import MedicalAgentOrchestrator
import json

# 初始化协调器
orchestrator = MedicalAgentOrchestrator()

# 加载病例数据
with open('medical_records/case1.json', 'r', encoding='utf-8') as f:
    case_data = json.load(f)

# 执行诊断
result = orchestrator.execute_diagnosis_workflow(case_data)

# 导出报告
report_path = orchestrator.export_diagnosis_report(result, 'json')
print(f"诊断报告已保存到: {report_path}")
病例数据格式
{
  "patient_id": "case1",
  "age": 65,
  "gender": "男",
  "chief_complaint": "胸痛3小时",
  "present_illness": "患者3小时前...",
  "past_history": "高血压病史10年...",
  "physical_examination": {
    "vital_signs": "血压150/90mmHg...",
    "cardiovascular": "心率100次/分..."
  },
  "laboratory_tests": {
    "blood_routine": "白细胞计数...",
    "biochemistry": "肌钙蛋白I..."
  },
  "imaging_studies": {
    "ecg": "窦性心律...",
    "echocardiography": "左室射血分数..."
  }
}
🔧 配置说明
DeepSeek API配置
在 app/config/deepseek_config.py 中可以调整以下参数：
api_key: DeepSeek API密钥
base_url: API基础URL
timeout: 请求超时时间（秒）
max_retries: 最大重试次数
temperature: 模型温度参数
RAG系统配置
在 app/config/config.py 中可以调整：
向量维度
检索相似度阈值
文档分块大小
嵌入模型参数
📊 诊断报告格式
系统生成的诊断报告包含以下结构：
{
  "patient_info": {
    "age": "患者年龄",
    "gender": "患者性别",
    "chief_complaint": "主诉"
  },
  "final_diagnosis": {
    "患者信息": {...},
    "临床表现": {...},
    "诊断结果": {
      "主要诊断": {...},
      "次要诊断": [...],
      "鉴别诊断": [...]
    },
    "治疗方案": [...]
  },
  "agent_results": {
    "hypothesis_agent": {...},
    "challenger_agent": {...},
    "reasoning_agent": {...}
  },
  "metadata": {
    "timestamp": "生成时间",
    "session_id": "会话ID",
    "processing_time": "处理时间"
  }
}
🐳 Docker部署
# 构建镜像
docker build -t sais-aie-wl25 .

# 运行容器
docker run -d -p 8000:8000 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/rag_vector_db:/app/rag_vector_db \
  sais-aie-wl25
🧪 测试
项目包含10个测试病例，涵盖常见的心内科疾病：
case1-case3: 急性冠脉综合征
case4-case6: 心力衰竭
case7-case8: 心律失常
case9-case10: 瓣膜疾病
运行所有测试：
# Windows PowerShell
for ($i=1; $i -le 10; $i++) { python "tests/test_with_case$i.py" }

# Linux/Mac Bash
for i in {1..10}; do python tests/test_with_case$i.py; done
📈 性能优化
向量数据库: 使用FAISS进行高效的相似度检索
缓存机制: 缓存常用的嵌入向量和API响应
并发处理: 支持多个诊断会话并发执行
内存管理: 优化大文档的分块和处理
🤝 贡献指南
Fork 项目
创建特性分支 (git checkout -b feature/AmazingFeature)
提交更改 (git commit -m 'Add some AmazingFeature')
推送到分支 (git push origin feature/AmazingFeature)
打开 Pull Request
📄 许可证
本项目采用 MIT 许可证 - 查看 LICENSE 文件了解详情。
⚠️ 免责声明
重要提示: 本系统仅用于医疗辅助诊断和学术研究目的，不能替代专业医生的临床判断。任何医疗决策都应该基于专业医生的建议和临床经验。
📞 联系方式
项目维护者: [Your Name]
邮箱: [your.email@example.com]
项目链接: https://github.com/your-username/sais-aie-wl25
🙏 致谢
感谢以下开源项目和技术：
DeepSeek - 大语言模型API
FAISS - 向量相似度搜索
Sentence Transformers - 文本嵌入模型
医学文献和临床指南提供的专业知识支持

**🚀 开始您的智能医疗诊断之旅！

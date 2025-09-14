# SAIS-AIE-WL25 医疗诊断AI系统

## 项目简介

本项目是一个基于多Agent协作和RAG技术的智能医疗诊断系统，专注于心内科疾病的辅助诊断。系统通过三个专业化的医疗Agent协同工作：

- **Dr.Hypothesis Agent**: 基于患者症状生成初步诊断假设
- **Dr.Challenger Agent**: 对初步诊断进行质疑和验证
- **Dr.Clinical-Reasoning Agent**: 综合分析生成最终诊断和治疗建议

## 如何运行测试用例

### 环境准备

1. 安装Python 3.8+
2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置DeepSeek API密钥（在 `app/config/deepseek_config.py` 中）

### 运行单个测试用例

```bash
# 运行特定病例测试
python tests/test_with_case1.py
python tests/test_with_case10.py
```

### 批量运行所有测试用例

```bash
# Windows PowerShell
for ($i=1; $i -le 10; $i++) { python "tests/test_with_case$i.py" }

# Linux/Mac
for i in {1..10}; do python tests/test_with_case$i.py; done
```

## 输入病历结构

系统接受JSON格式的病历数据，包含以下字段：

```json
{
  "patient_id": "case10",
  "age": 29,
  "gender": "男",
  "chief_complaint": "间断双下肢水肿、腹胀17年，胸闷、心悸3天",
  "present_illness": "患者于2002年开始无诱因间断双下肢水肿及腹胀...",
  "past_history": "10余岁发现乙肝'小三阳'，未诊治...",
  "personal_history": "生长于湖北新洲；有吸烟史6年...",
  "family_history": "否认家族遗传性及传染性疾病",
  "physical_examination": {
    "vital_signs": "体温36.7℃，脉搏116次/分，呼吸19次/分，血压121/103mmHg",
    "general_condition": "神志清楚；口唇无发绀，颈静脉怒张...",
    "cardiovascular": "心界不大，心率127次/分，心律绝对不齐...",
    "respiratory": "双下肺叩诊实音，双上肺呼吸音清...",
    "abdomen": "腹膨隆，腹壁静脉显露...",
    "extremities": "双下肢凹陷性水肿，双下肢色素沉着"
  },
  "laboratory_tests": {
    "blood_routine": "白细胞9.98×10^9/L，中性粒细胞0.7665...",
    "liver_function": "谷丙转氨酶86.7U/L，谷草转氨酶109.6U/L...",
    "kidney_function": "肌酐78μmol/L，尿酸571μmol/L",
    "cardiac_markers": "NT-proBNP 1987ng/L",
    "coagulation": "PT 21.2秒，INR 1.84",
    "other_tests": "D-二聚体19.20mg/L"
  },
  "imaging_studies": {
    "ecg": "心房颤动伴快速心室率，导联低电压",
    "chest_xray": "心影增大，双侧肋膈角消失，提示胸腔积液",
    "echocardiography": "双心房扩大（LA 5.1cm，RA 5.3cm），左心室收缩功能稍减低（LVEF 45%）",
    "abdominal_ultrasound": "淤血性肝肿大，胆囊壁增厚，脾稍厚，腹腔大量积液"
  }
}
```

## 输出诊断报告内容（Case10示例）

系统生成的诊断报告包含以下结构：

### 患者基本信息
```json
"患者信息": {
  "年龄": 29,
  "性别": "男",
  "入院日期": "2019-01-11"
}
```

### 临床表现
```json
"临床表现": {
  "主诉": "间断双下肢水肿、腹胀17年，胸闷、心悸3天",
  "现病史": "患者于2002年开始无诱因间断双下肢水肿及腹胀..."
}
```

### 诊断结果
```json
"诊断结果": {
  "主要诊断": {
    "名称": "慢性心力衰竭（全心衰竭）",
    "诊断依据": [
      "长期双下肢水肿、腹胀病史，利尿治疗有效",
      "近期出现胸闷、心悸、无尿等心衰加重表现",
      "体格检查示颈静脉怒张、肝颈静脉回流征阳性、双下肢水肿、腹水",
      "NT-proBNP升高（1987ng/L）",
      "超声心动图示双心房扩大、左室收缩功能减低"
    ]
  },
  "次要诊断": [
    {
      "名称": "快室率心房颤动",
      "诊断依据": ["突发心悸症状", "心电图证实房颤伴快速心室率"]
    },
    {
      "名称": "淤血性肝病",
      "诊断依据": ["长期右心衰竭表现", "肝功能异常", "超声示淤血性肝肿大"]
    }
  ],
  "鉴别诊断": ["缩窄性心包炎", "限制型心肌病", "肝硬化失代偿期", "肺栓塞"]
}
```

### 治疗方案
```json
"治疗方案": [
  "心衰治疗：利尿剂（呋塞米+螺内酯）减轻容量负荷",
  "房颤管理：控制心室率，评估抗凝指征",
  "容量管理：严格限制钠盐摄入，监测每日出入量及体重",
  "肝脏保护：保肝治疗，监测肝功能",
  "病因筛查：完善甲状腺功能、铁代谢等检查",
  "长期管理：心衰健康教育，戒烟限酒，定期随访"
]
```

### 诊断过程信息
```json
"diagnosis_process": {
  "initial_hypotheses_count": 5,
  "revised_diagnoses_count": 4,
  "quality_concerns_identified": 3,
  "medical_documents_consulted": 32
}
```

## 输出文件

诊断报告将保存在 `output/` 目录下，文件名格式为：
`case{编号}_diagnosis_report_{时间戳}.json`

例如：`output/case10_diagnosis_report_20250914_222017.json`

## 注意事项

⚠️ **免责声明**: 本系统仅用于医疗辅助诊断和学术研究目的，不能替代专业医生的临床判断。任何医疗决策都应该基于专业医生的建议和临床经验。
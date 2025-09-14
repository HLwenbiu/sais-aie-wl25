#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗诊断提示词模板
为不同的医疗Agent提供专业的提示词模板
"""

from typing import Dict, Any

class MedicalPromptTemplates:
    """
    医疗诊断提示词模板类
    """
    
    @staticmethod
    def get_hypothesis_generation_prompt(patient_info: Dict[str, Any], medical_context: str) -> str:
        """
        生成诊断假设的提示词模板
        
        Args:
            patient_info: 患者信息
            medical_context: 医学文献上下文
            
        Returns:
            诊断假设生成提示词
        """
        return f"""
你是一名经验丰富的心内科医生助手Dr.Hypothesis，专门负责根据患者病历信息生成候选诊断假设列表。

【患者病历信息】
主诉: {patient_info.get('chief_complaint', '未提供')}
现病史: {patient_info.get('present_illness', '未提供')}
既往史: {patient_info.get('past_history', '未提供')}
个人史: {patient_info.get('personal_history', '未提供')}
婚育史: {patient_info.get('marriage_history', '未提供')}
家族史: {patient_info.get('family_history', '未提供')}
体格检查: {patient_info.get('physical_examination', '未提供')}
辅助检查: {patient_info.get('auxiliary_examination', '未提供')}
生命体征: {patient_info.get('vital_signs', '未提供')}

【相关医学文献】
{medical_context}

【任务要求】
请基于以上患者信息和医学文献，生成一个详细的候选诊断假设列表。要求：

1. 诊断假设应该按照可能性从高到低排序
2. 每个诊断假设需要包含：
   - 诊断名称
   - 支持该诊断的临床证据
   - 可能性评估（高/中/低）
   - 需要进一步检查的项目

3. 至少提供3-5个候选诊断
4. 重点关注心血管系统疾病
5. 考虑鉴别诊断的必要性

请以JSON格式输出，结构如下：
{{
    "candidate_diagnoses": [
        {{
            "diagnosis_name": "诊断名称",
            "supporting_evidence": ["支持证据1", "支持证据2"],
            "probability": "高/中/低",
            "additional_tests_needed": ["需要的检查1", "需要的检查2"]
        }}
    ],
    "clinical_reasoning": "整体临床推理过程",
    "key_findings": ["关键发现1", "关键发现2"]
}}
"""
    
    @staticmethod
    def get_diagnosis_challenge_prompt(patient_info: Dict[str, Any], candidate_diagnoses: Dict[str, Any], medical_context: str) -> str:
        """
        诊断质疑和修正的提示词模板
        
        Args:
            patient_info: 患者信息
            candidate_diagnoses: 候选诊断列表
            medical_context: 医学文献上下文
            
        Returns:
            诊断质疑提示词
        """
        return f"""
你是一名严谨的医疗质量控制专家Dr.Challenger，专门负责质疑和修正诊断假设，确保诊断的准确性和完整性。

【患者病历信息】
主诉: {patient_info.get('chief_complaint', '未提供')}
现病史: {patient_info.get('present_illness', '未提供')}
既往史: {patient_info.get('past_history', '未提供')}
体格检查: {patient_info.get('physical_examination', '未提供')}
辅助检查: {patient_info.get('auxiliary_examination', '未提供')}
生命体征: {patient_info.get('vital_signs', '未提供')}

【初步候选诊断列表】
{candidate_diagnoses}

【相关医学文献】
{medical_context}

【任务要求】
请对上述候选诊断列表进行严格的医学审查，要求：

1. 分析每个候选诊断的合理性：
   - 检查临床证据是否充分支持该诊断
   - 识别可能被遗漏的重要症状或体征
   - 评估诊断的特异性和敏感性

2. 识别潜在的诊断错误：
   - 过度诊断（诊断过于复杂或罕见）
   - 诊断不足（遗漏重要诊断）
   - 逻辑错误（诊断与临床表现不符）

3. 提出修正建议：
   - 调整诊断优先级
   - 添加被遗漏的诊断
   - 删除不合理的诊断
   - 建议额外的检查或评估

4. 重点关注：
   - 危及生命的诊断是否被考虑
   - 常见诊断是否被优先考虑
   - 鉴别诊断是否充分

请以JSON格式输出，结构如下：
{{
    "diagnosis_review": [
        {{
            "original_diagnosis": "原诊断名称",
            "review_result": "保留/修改/删除",
            "reasoning": "审查理由",
            "modifications": "具体修改建议"
        }}
    ],
    "additional_diagnoses": [
        {{
            "diagnosis_name": "新增诊断名称",
            "supporting_evidence": ["支持证据"],
            "probability": "高/中/低",
            "reasoning": "添加理由"
        }}
    ],
    "revised_diagnosis_list": [
        {{
            "diagnosis_name": "修订后诊断名称",
            "supporting_evidence": ["支持证据"],
            "probability": "高/中/低",
            "additional_tests_needed": ["需要的检查"]
        }}
    ],
    "quality_concerns": ["质量问题1", "质量问题2"],
    "recommendations": ["建议1", "建议2"]
}}
"""
    
    @staticmethod
    def get_final_diagnosis_prompt(patient_info: Dict[str, Any], revised_diagnoses: Dict[str, Any], medical_context: str) -> str:
        """
        最终诊断的提示词模板
        
        Args:
            patient_info: 患者信息
            revised_diagnoses: 修订后的诊断列表
            medical_context: 医学文献上下文
            
        Returns:
            最终诊断提示词
        """
        # 获取完整的病历文本
        medical_record = patient_info.get('medical_record', patient_info.get('medical record', ''))
        
        return f"""
你是一名资深的心内科主任医师Dr.Clinical-Reasoning，负责综合所有信息做出最终的临床诊断决策。

【完整患者病历】
{medical_record}

【修订后的诊断列表】
{revised_diagnoses}

【相关医学文献】
{medical_context}

【任务要求】
请仔细阅读上述完整病历信息，从中提取患者的基本信息、临床表现、病史信息、体格检查、辅助检查等内容，并综合修订后的诊断列表和医学文献，做出最终的临床诊断决策。

要求：
1. 从病历文本中准确提取患者年龄、性别、入院日期等基本信息
2. 从病历文本中提取个人史、婚育史、家族史等详细病史信息
3. 确定主要诊断（最可能的诊断）
4. 列出次要诊断（其他需要关注的诊断）
5. 提供鉴别诊断（需要排除的诊断）
6. 制定诊疗计划建议

【诊断标准】
- 主要诊断：临床证据最充分，可能性最高的诊断
- 次要诊断：有一定证据支持，需要进一步观察或治疗的诊断
- 鉴别诊断：症状相似但需要排除的诊断

【输出格式要求】
请严格按照以下JSON格式输出，必须完全符合标准诊断报告格式。特别注意：
1. 患者信息中的年龄必须是数字类型，性别必须是"男"或"女"
2. 病史信息中的个人史、婚育史、家族史必须从病历文本中提取实际内容，不能使用"未提供"等默认值
3. 所有字段都必须填写完整，不能遗漏

标准JSON格式：
{{
  "患者信息": {{
    "年龄": 52,
    "性别": "男",
    "入院日期": "2022-04-01"
  }},
  "临床表现": {{
    "主诉": "反复腹痛、腹胀2周余",
    "现病史": "患者2周余前无明显诱因反复出现腹痛、腹胀，为左下腹部持续性胀痛，与活动、体位无关，进食后可加重，排便、排气后可缓解，无恶心、呕吐，无反酸、烧心，无呕血、黑便，无胸闷、胸痛，无尿频、尿痛、尿黄，无发热、畏寒，自行服用"沉香化气胶囊、阿莫西林、西甲硅油、消化酶"等药物效果欠佳，上述症状反复发作，来我院急诊就诊。急诊化验检查：总胆红素51.92μmol/L；尿素氮15.99mmol/L；肌酐189μmol/L；尿酸621μmol/L；C反应蛋白138.6mg/L；D-二聚体69.29mg/L。2022-03-31腹部CT：下腔静脉-右颈内静脉人工血管转流术后所见；符合肝硬化、脾大、腹水、侧支循环形成表现；胆囊结石；胆囊壁略厚，胆囊炎不除外；考虑脾梗死可能性大，请结合临床；腹腔渗出性改变、积液。为进一步治疗收入消化科病房。"
  }},
  "病史信息": {{
    "既往史": "高血压3年，血压最高可达160/100mmHg，现服用"氯沙坦钾"治疗，血压可控制在140/90mmHg。肾病综合征、阵发性睡眠性血红蛋白尿（paroxysmal nOCTurnal hemoglobinuria，PNH）2年，给予保肾药物（具体不详），定期返院治疗。丙型肝炎2年余，经正规抗丙肝治疗后复查阴性，否认结核、伤寒等其他传染病史及密切接触史。29年前因"布加综合征"行"下腔静脉-右颈内静脉人工血管转流术"，有同期输血史。",
    "个人史": "无特殊，否认吸烟、饮酒史。",
    "婚育史": "适龄结婚，育有1子。",
    "家族史": "父亲因"心肌梗死"去世，母亲健在。有1弟弟，弟弟体健。否认家族遗传病史或重大疾病史。"
  }},
  "体格检查": "体温37.0℃，心率96次/分，呼吸20次/分，血压144/93mmHg。贫血貌，体型消瘦。右侧颈部可见一长约4cm手术瘢痕，腹部正中可见一长约15cm纵向手术瘢痕。双肺呼吸音粗，未闻及干湿性啰音。心前区无隆起及凹陷，心界无扩大。心率96次/分，节律规整，各瓣膜听诊区未闻及病理性杂音。腹部膨隆，腹壁张力大，左腹部压痛，有反跳痛。肝脾肋下未触及，Murphy's征阴性，全腹叩诊鼓音，肝肾区无叩击痛，肠鸣音无亢进，移动性浊音阴性。双下肢轻度凹陷性水肿。",
  "辅助检查": "患者入院后化验血常规提示贫血（血红蛋白83g/L）、血小板减少（血小板71×10<sup>9</sup>/L），且合并感染（中性粒细胞百分比82.2%，C反应蛋白138.6mg/L）。肝肾功提示胆红素升高（总胆红素37.5μmol/L，直接胆红素27.2μmol/L），低蛋白血症（27.3g/L），肾功能不全（尿素氮15.3mmo/L，肌酐183μmol/L）。凝血常规提示凝血功能障碍，血浆凝血酶原时间（PT）延长（16.2秒）、部分活化凝血活酶时间（APTT）延长（43秒），D-二聚体显著升高（52.15mg/L）。",
  "诊断结果": {{
    "主要诊断": {{
      "名称": "失代偿期肝硬化",
      "诊断依据": [
        "既往有丙型肝炎、布加综合征病史，均为肝硬化高危因素。",
        "腹部CT提示肝硬化、脾大、腹水、侧支循环形成。",
        "体格检查示腹部膨隆、双下肢水肿。",
        "辅助检查示低蛋白血症、凝血功能障碍，提示肝脏合成功能严重受损。"
      ]
    }},
    "次要诊断": [
      {{
        "名称": "脾梗死",
        "诊断依据": [
          "患者主诉左下腹部持续性胀痛，体查左腹部压痛、反跳痛。",
          "腹部CT明确提示"考虑脾梗死可能性大"。",
          "D-二聚体显著升高，提示体内存在血栓形成事件。",
          "患者有阵发性睡眠性血红蛋白尿（PNH）病史，为血栓形成高危状态。"
        ]
      }}
        ],
        "鉴别诊断": [
            "缺血性肠病/肠系膜血管栓塞",
            "消化性溃疡穿孔",
            "急性胰腺炎"
        ]
    }},
    "治疗方案": [
        "一般治疗：绝对卧床，心电监护，低盐低脂饮食，记录出入量。",
        "抗感染：立即启动经验性广谱抗生素（如第三代头孢菌素）治疗，重点覆盖自发性细菌性腹膜炎的常见病原菌。",
        "肝病综合治疗：静脉输注人血白蛋白纠正低蛋白血症并防治肝肾综合征；使用保肝药物（如谷胱甘肽）；补充维生素K改善凝血功能。",
        "对症治疗：对于脾梗死，予止痛等对症处理。同时，鉴于PNH导致的高凝状态与肝硬化导致的出血倾向并存，抗凝治疗（如低分子肝素）需在严密监测下谨慎评估后使用。",
        "并发症处理：予利尿剂（如螺内酯联合呋塞米）治疗腹水，但需密切监测肾功能及电解质，避免加重肾损伤。同时积极寻找并纠正肾功能不全的病因。",
        "基础病治疗：继续控制血压，但需选择对肝肾功能影响小的降压药物。"
    ]
}}

请严格按照上述格式输出，确保所有字段都从病历文本中准确提取，特别是患者基本信息和病史信息部分。
"""
    
    @staticmethod
    def get_medical_knowledge_query(patient_symptoms: str, suspected_diagnosis: str = "") -> str:
        """
        生成医学知识检索查询
        
        Args:
            patient_symptoms: 患者症状
            suspected_diagnosis: 疑似诊断
            
        Returns:
            检索查询字符串
        """
        if suspected_diagnosis:
            return f"{patient_symptoms} {suspected_diagnosis} 心血管疾病 诊断 治疗"
        else:
            return f"{patient_symptoms} 心血管疾病 心内科 诊断"
    
    @staticmethod
    def format_patient_summary(patient_info: Dict[str, Any]) -> str:
        """
        格式化患者信息摘要
        
        Args:
            patient_info: 患者信息
            
        Returns:
            格式化的患者摘要
        """
        summary_parts = []
        
        if patient_info.get('chief_complaint'):
            summary_parts.append(f"主诉: {patient_info['chief_complaint']}")
        
        if patient_info.get('present_illness'):
            summary_parts.append(f"现病史: {patient_info['present_illness'][:100]}...")
        
        if patient_info.get('vital_signs'):
            summary_parts.append(f"生命体征: {patient_info['vital_signs']}")
        
        return " | ".join(summary_parts)
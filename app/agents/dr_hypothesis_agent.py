#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dr.Hypothesis Agent - 诊断假设生成专家
根据患者病历信息结合RAG检索医学文献生成候选诊断清单
"""

import json
import logging
from typing import Dict, List, Any, Optional

from app.agents.medical_agent_base import MedicalAgentBase
from app.agents.medical_prompt_templates import MedicalPromptTemplates

class DrHypothesisAgent(MedicalAgentBase):
    """
    Dr.Hypothesis - 诊断假设生成专家
    
    职责：
    - 分析患者病历信息
    - 检索相关医学文献
    - 生成候选诊断假设列表
    - 评估诊断可能性
    """
    
    def __init__(self, vector_db_path: str = "rag_vector_db"):
        """
        初始化Dr.Hypothesis Agent
        
        Args:
            vector_db_path: 向量数据库路径
        """
        super().__init__("Dr.Hypothesis", vector_db_path)
        self.prompt_templates = MedicalPromptTemplates()
    
    def get_agent_description(self) -> str:
        """
        获取Agent描述
        
        Returns:
            Agent功能描述
        """
        return (
            "Dr.Hypothesis是一名经验丰富的心内科医生助手，专门负责：\n"
            "1. 分析患者病历信息和临床表现\n"
            "2. 检索相关医学文献和指南\n"
            "3. 生成候选诊断假设列表\n"
            "4. 评估每个诊断的可能性\n"
            "5. 建议进一步的检查项目"
        )
    
    def analyze_patient_symptoms(self, patient_info: Dict[str, Any]) -> str:
        """
        分析患者症状，生成检索查询
        
        Args:
            patient_info: 患者信息
            
        Returns:
            检索查询字符串
        """
        # 提取关键症状和体征
        key_symptoms = []
        
        # 从主诉中提取症状
        chief_complaint = patient_info.get('chief_complaint', '')
        if chief_complaint:
            key_symptoms.append(chief_complaint)
        
        # 从现病史中提取症状
        present_illness = patient_info.get('present_illness', '')
        if present_illness:
            # 简化处理，取前100个字符
            key_symptoms.append(present_illness[:100])
        
        # 从体格检查中提取异常发现
        physical_exam = patient_info.get('physical_examination', '')
        if physical_exam:
            key_symptoms.append(physical_exam[:100])
        
        # 从辅助检查中提取异常结果
        auxiliary_exam = patient_info.get('auxiliary_examination', '')
        if auxiliary_exam:
            key_symptoms.append(auxiliary_exam[:100])
        
        # 生成检索查询
        symptoms_text = ' '.join(key_symptoms)
        query = self.prompt_templates.get_medical_knowledge_query(symptoms_text)
        
        self.logger.info(f"生成检索查询: {query[:100]}...")
        return query
    
    def generate_diagnosis_hypotheses(self, patient_info: Dict[str, Any], medical_context: str) -> Dict[str, Any]:
        """
        生成诊断假设
        
        Args:
            patient_info: 患者信息
            medical_context: 医学文献上下文
            
        Returns:
            诊断假设结果
        """
        try:
            # 生成提示词
            prompt = self.prompt_templates.get_hypothesis_generation_prompt(
                patient_info, medical_context
            )
            
            # 调用大语言模型生成诊断假设
            response = self.generate_response(
                prompt=prompt,
                temperature=0.3,  # 较低温度确保更准确的医学诊断
                max_tokens=3000
            )
            
            # 使用基类的JSON解析方法
            diagnosis_result = self.parse_json_response(response)
            
            # 检查是否解析失败
            if "error" in diagnosis_result:
                self.logger.error(f"JSON解析失败")
                # 返回备用格式
                return {
                    "candidate_diagnoses": [],
                    "clinical_reasoning": response,
                    "key_findings": [],
                    "error": "JSON解析失败，返回原始响应"
                }
            
            self.logger.info(f"成功生成 {len(diagnosis_result.get('candidate_diagnoses', []))} 个候选诊断")
            return diagnosis_result
                
        except Exception as e:
            self.logger.error(f"诊断假设生成失败: {e}")
            return {
                "candidate_diagnoses": [],
                "clinical_reasoning": f"诊断假设生成过程中出现错误: {e}",
                "key_findings": [],
                "error": str(e)
            }
    
    def validate_diagnosis_hypotheses(self, diagnosis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和完善诊断假设
        
        Args:
            diagnosis_result: 原始诊断结果
            
        Returns:
            验证后的诊断结果
        """
        validated_result = diagnosis_result.copy()
        
        # 确保必要字段存在
        if 'candidate_diagnoses' not in validated_result:
            validated_result['candidate_diagnoses'] = []
        
        if 'clinical_reasoning' not in validated_result:
            validated_result['clinical_reasoning'] = "未提供临床推理"
        
        if 'key_findings' not in validated_result:
            validated_result['key_findings'] = []
        
        # 验证每个候选诊断的完整性
        validated_diagnoses = []
        for diagnosis in validated_result['candidate_diagnoses']:
            if isinstance(diagnosis, dict):
                # 确保必要字段
                validated_diagnosis = {
                    'diagnosis_name': diagnosis.get('diagnosis_name', '未知诊断'),
                    'supporting_evidence': diagnosis.get('supporting_evidence', []),
                    'probability': diagnosis.get('probability', '中'),
                    'additional_tests_needed': diagnosis.get('additional_tests_needed', [])
                }
                validated_diagnoses.append(validated_diagnosis)
        
        validated_result['candidate_diagnoses'] = validated_diagnoses
        
        # 添加验证信息
        validated_result['validation_info'] = {
            'total_diagnoses': len(validated_diagnoses),
            'validation_timestamp': self.logger.handlers[0].formatter.formatTime(logging.LogRecord('', 0, '', 0, '', (), None)) if self.logger.handlers else 'unknown'
        }
        
        return validated_result
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理患者信息并生成诊断假设
        
        Args:
            input_data: 输入数据，包含患者信息
            
        Returns:
            诊断假设结果
        """
        try:
            self.logger.info("Dr.Hypothesis开始处理患者信息")
            
            # 提取患者信息
            patient_info = input_data.get('patient_info', {})
            if not patient_info:
                raise ValueError("缺少患者信息")
            
            # 分析患者症状并生成检索查询
            query = self.analyze_patient_symptoms(patient_info)
            
            # 检索相关医学知识
            medical_documents = self.retrieve_medical_knowledge(query, top_k=5)
            medical_context = self.format_medical_context(medical_documents)
            
            # 生成诊断假设
            diagnosis_result = self.generate_diagnosis_hypotheses(patient_info, medical_context)
            
            # 验证和完善结果
            validated_result = self.validate_diagnosis_hypotheses(diagnosis_result)
            
            # 构建输出数据
            output_data = {
                'agent_name': self.agent_name,
                'patient_summary': self.prompt_templates.format_patient_summary(patient_info),
                'medical_documents_count': len(medical_documents),
                'diagnosis_hypotheses': validated_result,
                'processing_status': 'success'
            }
            
            # 记录交互日志
            self.log_interaction(input_data, output_data)
            
            self.logger.info("Dr.Hypothesis处理完成")
            return output_data
            
        except Exception as e:
            self.logger.error(f"Dr.Hypothesis处理失败: {e}")
            
            error_output = {
                'agent_name': self.agent_name,
                'error': str(e),
                'processing_status': 'failed',
                'diagnosis_hypotheses': {
                    'candidate_diagnoses': [],
                    'clinical_reasoning': f"处理过程中出现错误: {e}",
                    'key_findings': [],
                    'error': str(e)
                }
            }
            
            self.log_interaction(input_data, error_output)
            return error_output
    
    def get_diagnosis_summary(self, diagnosis_result: Dict[str, Any]) -> str:
        """
        获取诊断假设摘要
        
        Args:
            diagnosis_result: 诊断结果
            
        Returns:
            诊断摘要文本
        """
        if not diagnosis_result or 'diagnosis_hypotheses' not in diagnosis_result:
            return "无诊断假设生成"
        
        hypotheses = diagnosis_result['diagnosis_hypotheses']
        candidate_diagnoses = hypotheses.get('candidate_diagnoses', [])
        
        if not candidate_diagnoses:
            return "未生成候选诊断"
        
        summary_parts = [f"生成了 {len(candidate_diagnoses)} 个候选诊断:"]
        
        for i, diagnosis in enumerate(candidate_diagnoses[:3], 1):  # 只显示前3个
            name = diagnosis.get('diagnosis_name', '未知')
            probability = diagnosis.get('probability', '未知')
            summary_parts.append(f"{i}. {name} (可能性: {probability})")
        
        return "\n".join(summary_parts)

# 测试函数
def test_dr_hypothesis():
    """
    测试Dr.Hypothesis Agent
    """
    # 创建测试患者信息
    test_patient = {
        'patient_info': {
            'chief_complaint': '胸痛3小时',
            'present_illness': '患者3小时前无明显诱因出现胸骨后疼痛，呈压榨性，向左肩背部放射，伴出汗、恶心',
            'past_history': '高血压病史5年，糖尿病病史3年',
            'physical_examination': '血压160/95mmHg，心率98次/分，心律齐，未闻及杂音',
            'auxiliary_examination': '心电图示II、III、aVF导联ST段抬高',
            'vital_signs': 'T 36.8°C, P 98次/分, R 20次/分, BP 160/95mmHg'
        }
    }
    
    try:
        # 创建Agent实例
        dr_hypothesis = DrHypothesisAgent()
        
        print("=== Dr.Hypothesis Agent 测试 ===")
        print(f"Agent描述: {dr_hypothesis.get_agent_description()}")
        print()
        
        # 处理患者信息
        result = dr_hypothesis.process(test_patient)
        
        print("处理结果:")
        print(f"状态: {result.get('processing_status')}")
        print(f"患者摘要: {result.get('patient_summary')}")
        print(f"检索文档数: {result.get('medical_documents_count')}")
        print()
        
        # 显示诊断假设摘要
        summary = dr_hypothesis.get_diagnosis_summary(result)
        print("诊断假设摘要:")
        print(summary)
        
        return result
        
    except Exception as e:
        print(f"测试失败: {e}")
        return None

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    test_dr_hypothesis()
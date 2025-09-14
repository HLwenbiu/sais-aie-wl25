#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dr.Challenger Agent - 诊断质疑和修正专家
对诊断假设列表进行分析，检查是否存在诊断误差并提出替代诊断
"""

import json
import logging
from typing import Dict, List, Any, Optional

from app.agents.medical_agent_base import MedicalAgentBase
from app.agents.medical_prompt_templates import MedicalPromptTemplates

class DrChallengerAgent(MedicalAgentBase):
    """
    Dr.Challenger - 诊断质疑和修正专家
    
    职责：
    - 审查候选诊断列表的合理性
    - 识别潜在的诊断错误
    - 提出修正建议
    - 生成修订后的诊断列表
    """
    
    def __init__(self, vector_db_path: str = "rag_vector_db"):
        """
        初始化Dr.Challenger Agent
        
        Args:
            vector_db_path: 向量数据库路径
        """
        super().__init__("Dr.Challenger", vector_db_path)
        self.prompt_templates = MedicalPromptTemplates()
    
    def get_agent_description(self) -> str:
        """
        获取Agent描述
        
        Returns:
            Agent功能描述
        """
        return (
            "Dr.Challenger是一名严谨的医疗质量控制专家，专门负责：\n"
            "1. 审查候选诊断列表的医学合理性\n"
            "2. 识别可能的诊断错误和遗漏\n"
            "3. 评估诊断证据的充分性\n"
            "4. 提出诊断修正和改进建议\n"
            "5. 生成修订后的诊断列表"
        )
    
    def analyze_diagnosis_quality(self, candidate_diagnoses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析诊断质量
        
        Args:
            candidate_diagnoses: 候选诊断列表
            
        Returns:
            质量分析结果
        """
        quality_analysis = {
            'total_diagnoses': len(candidate_diagnoses),
            'high_probability_count': 0,
            'medium_probability_count': 0,
            'low_probability_count': 0,
            'diagnoses_with_evidence': 0,
            'diagnoses_with_tests': 0,
            'potential_issues': []
        }
        
        for diagnosis in candidate_diagnoses:
            # 统计概率分布
            probability = diagnosis.get('probability', '').lower()
            if '高' in probability:
                quality_analysis['high_probability_count'] += 1
            elif '中' in probability:
                quality_analysis['medium_probability_count'] += 1
            elif '低' in probability:
                quality_analysis['low_probability_count'] += 1
            
            # 检查证据完整性
            evidence = diagnosis.get('supporting_evidence', [])
            if evidence and len(evidence) > 0:
                quality_analysis['diagnoses_with_evidence'] += 1
            else:
                quality_analysis['potential_issues'].append(
                    f"诊断 '{diagnosis.get('diagnosis_name', '未知')}' 缺乏支持证据"
                )
            
            # 检查检查建议
            tests = diagnosis.get('additional_tests_needed', [])
            if tests and len(tests) > 0:
                quality_analysis['diagnoses_with_tests'] += 1
        
        # 检查整体质量问题
        if quality_analysis['high_probability_count'] == 0:
            quality_analysis['potential_issues'].append("缺少高可能性诊断")
        
        if quality_analysis['high_probability_count'] > 2:
            quality_analysis['potential_issues'].append("高可能性诊断过多，可能存在过度诊断")
        
        return quality_analysis
    
    def generate_additional_queries(self, patient_info: Dict[str, Any], candidate_diagnoses: List[Dict[str, Any]]) -> List[str]:
        """
        生成额外的医学知识检索查询
        
        Args:
            patient_info: 患者信息
            candidate_diagnoses: 候选诊断列表
            
        Returns:
            检索查询列表
        """
        queries = []
        
        # 基于候选诊断生成鉴别诊断查询
        for diagnosis in candidate_diagnoses[:3]:  # 只处理前3个诊断
            diagnosis_name = diagnosis.get('diagnosis_name', '')
            if diagnosis_name:
                # 鉴别诊断查询
                queries.append(f"{diagnosis_name} 鉴别诊断 心血管疾病")
                # 诊断标准查询
                queries.append(f"{diagnosis_name} 诊断标准 临床指南")
        
        # 基于症状生成常见疾病查询
        chief_complaint = patient_info.get('chief_complaint', '')
        if chief_complaint:
            queries.append(f"{chief_complaint} 常见原因 心内科")
        
        return queries[:5]  # 限制查询数量
    
    def challenge_diagnosis(self, patient_info: Dict[str, Any], candidate_diagnoses: Dict[str, Any], medical_context: str) -> Dict[str, Any]:
        """
        质疑和修正诊断
        
        Args:
            patient_info: 患者信息
            candidate_diagnoses: 候选诊断
            medical_context: 医学文献上下文
            
        Returns:
            质疑和修正结果
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 生成提示词
                prompt = self.prompt_templates.get_diagnosis_challenge_prompt(
                    patient_info, candidate_diagnoses, medical_context
                )
                
                self.logger.info(f"开始质疑诊断假设... (尝试 {retry_count + 1}/{max_retries})")
                
                # 调用大语言模型进行诊断质疑
                response = self.generate_response(
                    prompt=prompt,
                    temperature=0.2,  # 更低温度确保严谨的医学审查
                    max_tokens=4000
                )
                
                # 使用基类的JSON解析方法
                challenge_result = self.parse_json_response(response)
                
                # 检查是否解析失败
                if "error" in challenge_result:
                    self.logger.warning(f"JSON解析失败 (尝试 {retry_count + 1}/{max_retries})，原始响应: {response[:200]}...")
                    
                    # 如果是最后一次尝试，返回fallback结果
                    if retry_count == max_retries - 1:
                        return self._create_fallback_challenge_result(response, "JSON解析失败")
                    
                    retry_count += 1
                    continue
                
                self.logger.info("成功完成诊断质疑和修正")
                return challenge_result
                    
            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"诊断质疑失败 (尝试 {retry_count + 1}/{max_retries}): {error_msg}")
                
                # 检查是否是网络超时错误
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    if retry_count < max_retries - 1:
                        self.logger.info(f"网络超时，{2 ** retry_count}秒后重试...")
                        import time
                        time.sleep(2 ** retry_count)  # 指数退避
                        retry_count += 1
                        continue
                
                # 如果是最后一次尝试或非网络错误，返回错误结果
                if retry_count == max_retries - 1:
                    return self._create_fallback_challenge_result("", f"处理错误: {error_msg}")
                
                retry_count += 1
        
        # 所有重试都失败了
        return self._create_fallback_challenge_result("", "所有重试尝试都失败了")
    
    def _create_fallback_challenge_result(self, raw_response: str, error_msg: str) -> Dict[str, Any]:
        """
        创建fallback质疑结果
        
        Args:
            raw_response: 原始响应
            error_msg: 错误信息
            
        Returns:
            Dict: fallback结果
        """
        return {
            "diagnosis_review": [],
            "additional_diagnoses": [],
            "revised_diagnosis_list": [],
            "quality_concerns": [error_msg, "建议人工审核诊断结果"],
            "recommendations": [
                "建议检查网络连接和API配置",
                "考虑增加超时时间或重试次数",
                "如问题持续，请联系技术支持"
            ],
            "raw_response": raw_response[:500] if raw_response else "",
            "error": error_msg,
            "fallback_mode": True
        }
    
    def validate_challenge_result(self, challenge_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证质疑结果
        
        Args:
            challenge_result: 原始质疑结果
            
        Returns:
            验证后的质疑结果
        """
        validated_result = challenge_result.copy()
        
        # 确保必要字段存在
        required_fields = [
            'diagnosis_review', 'additional_diagnoses', 'revised_diagnosis_list',
            'quality_concerns', 'recommendations'
        ]
        
        for field in required_fields:
            if field not in validated_result:
                validated_result[field] = []
        
        # 验证修订后的诊断列表
        revised_diagnoses = validated_result.get('revised_diagnosis_list', [])
        validated_revised = []
        
        for diagnosis in revised_diagnoses:
            if isinstance(diagnosis, dict):
                validated_diagnosis = {
                    'diagnosis_name': diagnosis.get('diagnosis_name', '未知诊断'),
                    'supporting_evidence': diagnosis.get('supporting_evidence', []),
                    'probability': diagnosis.get('probability', '中'),
                    'additional_tests_needed': diagnosis.get('additional_tests_needed', [])
                }
                validated_revised.append(validated_diagnosis)
        
        validated_result['revised_diagnosis_list'] = validated_revised
        
        # 添加验证统计信息
        validated_result['validation_stats'] = {
            'original_diagnoses_reviewed': len(validated_result.get('diagnosis_review', [])),
            'additional_diagnoses_suggested': len(validated_result.get('additional_diagnoses', [])),
            'final_revised_diagnoses': len(validated_revised),
            'quality_concerns_identified': len(validated_result.get('quality_concerns', [])),
            'recommendations_provided': len(validated_result.get('recommendations', []))
        }
        
        return validated_result
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理诊断质疑和修正
        
        Args:
            input_data: 输入数据，包含患者信息和候选诊断
            
        Returns:
            质疑和修正结果
        """
        try:
            self.logger.info("Dr.Challenger开始质疑和修正诊断")
            
            # 提取输入数据
            patient_info = input_data.get('patient_info', {})
            diagnosis_hypotheses = input_data.get('diagnosis_hypotheses', {})
            
            if not patient_info:
                raise ValueError("缺少患者信息")
            
            if not diagnosis_hypotheses:
                raise ValueError("缺少候选诊断信息")
            
            candidate_diagnoses = diagnosis_hypotheses.get('candidate_diagnoses', [])
            
            # 分析诊断质量
            quality_analysis = self.analyze_diagnosis_quality(candidate_diagnoses)
            
            # 生成额外的检索查询
            additional_queries = self.generate_additional_queries(patient_info, candidate_diagnoses)
            
            # 检索额外的医学知识
            all_documents = []
            for query in additional_queries:
                documents = self.retrieve_medical_knowledge(query, top_k=3)
                all_documents.extend(documents)
            
            # 格式化医学上下文
            medical_context = self.format_medical_context(all_documents)
            
            # 执行诊断质疑和修正
            challenge_result = self.challenge_diagnosis(
                patient_info, diagnosis_hypotheses, medical_context
            )
            
            # 验证结果
            validated_result = self.validate_challenge_result(challenge_result)
            
            # 构建输出数据
            output_data = {
                'agent_name': self.agent_name,
                'patient_summary': self.prompt_templates.format_patient_summary(patient_info),
                'original_diagnoses_count': len(candidate_diagnoses),
                'quality_analysis': quality_analysis,
                'additional_queries_used': additional_queries,
                'medical_documents_retrieved': len(all_documents),
                'challenge_result': validated_result,
                'processing_status': 'success'
            }
            
            # 记录交互日志
            self.log_interaction(input_data, output_data)
            
            self.logger.info("Dr.Challenger处理完成")
            return output_data
            
        except Exception as e:
            self.logger.error(f"Dr.Challenger处理失败: {e}")
            
            error_output = {
                'agent_name': self.agent_name,
                'error': str(e),
                'processing_status': 'failed',
                'challenge_result': {
                    'diagnosis_review': [],
                    'additional_diagnoses': [],
                    'revised_diagnosis_list': [],
                    'quality_concerns': [f"处理错误: {e}"],
                    'recommendations': ["建议检查输入数据和系统配置"],
                    'error': str(e)
                }
            }
            
            self.log_interaction(input_data, error_output)
            return error_output
    
    def get_challenge_summary(self, challenge_result: Dict[str, Any]) -> str:
        """
        获取质疑结果摘要
        
        Args:
            challenge_result: 质疑结果
            
        Returns:
            质疑摘要文本
        """
        if not challenge_result or 'challenge_result' not in challenge_result:
            return "无质疑结果"
        
        result = challenge_result['challenge_result']
        
        summary_parts = []
        
        # 统计信息
        stats = result.get('validation_stats', {})
        if stats:
            summary_parts.append(
                f"审查了 {stats.get('original_diagnoses_reviewed', 0)} 个原始诊断，"
                f"新增 {stats.get('additional_diagnoses_suggested', 0)} 个诊断，"
                f"最终修订为 {stats.get('final_revised_diagnoses', 0)} 个诊断"
            )
        
        # 质量问题
        concerns = result.get('quality_concerns', [])
        if concerns:
            summary_parts.append(f"识别出 {len(concerns)} 个质量问题")
        
        # 建议
        recommendations = result.get('recommendations', [])
        if recommendations:
            summary_parts.append(f"提供了 {len(recommendations)} 条建议")
        
        return "\n".join(summary_parts) if summary_parts else "质疑过程完成，无特殊发现"

# 测试函数
def test_dr_challenger():
    """
    测试Dr.Challenger Agent
    """
    # 创建测试数据
    test_input = {
        'patient_info': {
            'chief_complaint': '胸痛3小时',
            'present_illness': '患者3小时前无明显诱因出现胸骨后疼痛，呈压榨性，向左肩背部放射，伴出汗、恶心',
            'past_history': '高血压病史5年，糖尿病病史3年',
            'physical_examination': '血压160/95mmHg，心率98次/分，心律齐，未闻及杂音',
            'auxiliary_examination': '心电图示II、III、aVF导联ST段抬高',
            'vital_signs': 'T 36.8°C, P 98次/分, R 20次/分, BP 160/95mmHg'
        },
        'diagnosis_hypotheses': {
            'candidate_diagnoses': [
                {
                    'diagnosis_name': '急性下壁心肌梗死',
                    'supporting_evidence': ['胸痛症状', 'ST段抬高', '放射痛'],
                    'probability': '高',
                    'additional_tests_needed': ['心肌酶', '冠脉造影']
                },
                {
                    'diagnosis_name': '不稳定性心绞痛',
                    'supporting_evidence': ['胸痛症状', '高血压病史'],
                    'probability': '中',
                    'additional_tests_needed': ['心肌酶', '运动试验']
                }
            ],
            'clinical_reasoning': '基于症状和心电图表现',
            'key_findings': ['ST段抬高', '胸痛放射']
        }
    }
    
    try:
        # 创建Agent实例
        dr_challenger = DrChallengerAgent()
        
        print("=== Dr.Challenger Agent 测试 ===")
        print(f"Agent描述: {dr_challenger.get_agent_description()}")
        print()
        
        # 处理质疑和修正
        result = dr_challenger.process(test_input)
        
        print("处理结果:")
        print(f"状态: {result.get('processing_status')}")
        print(f"原始诊断数: {result.get('original_diagnoses_count')}")
        print(f"检索文档数: {result.get('medical_documents_retrieved')}")
        print()
        
        # 显示质疑结果摘要
        summary = dr_challenger.get_challenge_summary(result)
        print("质疑结果摘要:")
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
    test_dr_challenger()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dr.Clinical-Reasoning Agent - 最终诊断决策专家
综合给出信息完成诊断，生成符合要求格式的主/次要诊断和鉴别诊断
"""

import json
import logging
from typing import Dict, List, Any, Optional

from app.agents.medical_agent_base import MedicalAgentBase
from app.agents.medical_prompt_templates import MedicalPromptTemplates

class DrClinicalReasoningAgent(MedicalAgentBase):
    """
    Dr.Clinical-Reasoning - 最终诊断决策专家
    
    职责：
    - 综合患者信息和修订后的诊断列表
    - 确定主要诊断和次要诊断
    - 提供鉴别诊断
    - 制定诊疗计划
    - 评估预后
    """
    
    def __init__(self, vector_db_path: str = "rag_vector_db"):
        """
        初始化Dr.Clinical-Reasoning Agent
        
        Args:
            vector_db_path: 向量数据库路径
        """
        super().__init__("Dr.Clinical-Reasoning", vector_db_path)
        self.prompt_templates = MedicalPromptTemplates()
    
    def get_agent_description(self) -> str:
        """
        获取Agent描述
        
        Returns:
            Agent功能描述
        """
        return (
            "Dr.Clinical-Reasoning是一名资深的心内科主任医师，专门负责：\n"
            "1. 综合分析患者信息和诊断建议\n"
            "2. 确定主要诊断和次要诊断\n"
            "3. 提供完整的鉴别诊断列表\n"
            "4. 制定个性化的诊疗计划\n"
            "5. 评估患者预后和风险因素"
        )
    
    def analyze_diagnosis_confidence(self, revised_diagnoses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析诊断置信度
        
        Args:
            revised_diagnoses: 修订后的诊断列表
            
        Returns:
            置信度分析结果
        """
        confidence_analysis = {
            'high_confidence_diagnoses': [],
            'medium_confidence_diagnoses': [],
            'low_confidence_diagnoses': [],
            'evidence_strength_scores': {},
            'overall_confidence': 'medium'
        }
        
        for diagnosis in revised_diagnoses:
            diagnosis_name = diagnosis.get('diagnosis_name', '')
            probability = diagnosis.get('probability', '').lower()
            evidence = diagnosis.get('supporting_evidence', [])
            
            # 计算证据强度分数
            evidence_score = len(evidence) * 0.2  # 基础分数
            if '高' in probability:
                evidence_score += 0.6
            elif '中' in probability:
                evidence_score += 0.3
            elif '低' in probability:
                evidence_score += 0.1
            
            confidence_analysis['evidence_strength_scores'][diagnosis_name] = evidence_score
            
            # 分类诊断置信度
            if evidence_score >= 0.7:
                confidence_analysis['high_confidence_diagnoses'].append(diagnosis)
            elif evidence_score >= 0.4:
                confidence_analysis['medium_confidence_diagnoses'].append(diagnosis)
            else:
                confidence_analysis['low_confidence_diagnoses'].append(diagnosis)
        
        # 确定整体置信度
        if confidence_analysis['high_confidence_diagnoses']:
            confidence_analysis['overall_confidence'] = 'high'
        elif confidence_analysis['medium_confidence_diagnoses']:
            confidence_analysis['overall_confidence'] = 'medium'
        else:
            confidence_analysis['overall_confidence'] = 'low'
        
        return confidence_analysis
    
    def generate_treatment_queries(self, primary_diagnosis: str, secondary_diagnoses: List[str]) -> List[str]:
        """
        生成治疗相关的检索查询
        
        Args:
            primary_diagnosis: 主要诊断
            secondary_diagnoses: 次要诊断列表
            
        Returns:
            治疗查询列表
        """
        queries = []
        
        # 主要诊断的治疗查询
        if primary_diagnosis:
            queries.extend([
                f"{primary_diagnosis} 治疗指南 心血管",
                f"{primary_diagnosis} 药物治疗 临床路径",
                f"{primary_diagnosis} 预后 并发症"
            ])
        
        # 次要诊断的治疗查询
        for diagnosis in secondary_diagnoses[:2]:  # 限制查询数量
            queries.append(f"{diagnosis} 治疗 管理")
        
        return queries[:5]  # 限制总查询数量
    
    def make_final_diagnosis(self, patient_info: Dict[str, Any], revised_diagnoses: Dict[str, Any], medical_context: str) -> Dict[str, Any]:
        """
        做出最终诊断决策
        
        Args:
            patient_info: 患者信息
            revised_diagnoses: 修订后的诊断
            medical_context: 医学文献上下文
            
        Returns:
            最终诊断结果
        """
        try:
            # 生成提示词
            prompt = self.prompt_templates.get_final_diagnosis_prompt(
                patient_info, revised_diagnoses, medical_context
            )
            
            # 调用大语言模型生成最终诊断
            response = self.generate_response(
                prompt=prompt,
                temperature=0.1,  # 最低温度确保最准确的医学诊断
                max_tokens=5000
            )
            
            # 使用基类的JSON解析方法
            final_diagnosis = self.parse_json_response(response)
            
            # 添加调试信息
            self.logger.info(f"LLM原始响应长度: {len(response)}")
            self.logger.info(f"JSON解析结果包含error: {'error' in final_diagnosis}")
            
            # 检查是否解析失败
            if "error" in final_diagnosis:
                self.logger.error("JSON解析失败，使用备用格式")
                # 返回备用格式，使用实际患者数据而不是默认值
                return {
                    "患者信息": {
                        "年龄": patient_info.get('age', 0),
                        "性别": patient_info.get('gender', '未知'),
                        "入院日期": patient_info.get('admission_date', '未知')
                    },
                    "临床表现": {
                        "主诉": patient_info.get('chief_complaint', '需要进一步评估'),
                        "现病史": patient_info.get('present_illness', '需要进一步评估')
                    },
                    "病史信息": {
                        "既往史": patient_info.get('past_history', '不详'),
                        "个人史": patient_info.get('personal_history', '不详'),
                        "婚育史": patient_info.get('marriage_history', '不详'),
                        "家族史": patient_info.get('family_history', '不详')
                    },
                    "体格检查": patient_info.get('physical_examination', '需要进一步评估'),
                    "辅助检查": patient_info.get('auxiliary_examination', '需要进一步评估'),
                    "诊断结果": {
                        "主要诊断": {
                            "名称": "解析失败",
                            "诊断依据": ["基于当前信息的初步分析", "由于数据解析问题，建议进一步临床评估"]
                        },
                        "次要诊断": [],
                        "鉴别诊断": []
                    },
                    "治疗方案": ["建议进一步临床评估和检查"],
                    "raw_response": response,
                    "error": "JSON解析失败，返回原始响应"
                }
            
            # 添加病史信息调试
            if "病史信息" in final_diagnosis:
                history_info = final_diagnosis["病史信息"]
                self.logger.info(f"解析后的个人史: {history_info.get('个人史', 'None')}")
                self.logger.info(f"解析后的婚育史: {history_info.get('婚育史', 'None')}")
                self.logger.info(f"解析后的家族史: {history_info.get('家族史', 'None')}")
            
            self.logger.info("成功生成最终诊断")
            return final_diagnosis
                
        except Exception as e:
            self.logger.error(f"最终诊断生成失败: {e}")
            return {
                "患者信息": {
                    "年龄": patient_info.get('age', 0) if patient_info else 0,
                    "性别": patient_info.get('gender', '未知') if patient_info else '未知',
                    "入院日期": patient_info.get('admission_date', '未知') if patient_info else '未知'
                },
                "临床表现": {
                    "主诉": patient_info.get('chief_complaint', '诊断失败') if patient_info else '诊断失败',
                    "现病史": patient_info.get('present_illness', '诊断失败') if patient_info else '诊断失败'
                },
                "病史信息": {
                    "既往史": patient_info.get('past_history', '诊断失败') if patient_info else '诊断失败',
                    "个人史": patient_info.get('personal_history', '诊断失败') if patient_info else '诊断失败',
                    "婚育史": patient_info.get('marriage_history', '诊断失败') if patient_info else '诊断失败',
                    "家族史": patient_info.get('family_history', '诊断失败') if patient_info else '诊断失败'
                },
                "体格检查": patient_info.get('physical_examination', '诊断失败') if patient_info else '诊断失败',
                "辅助检查": patient_info.get('auxiliary_examination', '诊断失败') if patient_info else '诊断失败',
                "诊断结果": {
                    "主要诊断": {
                        "名称": "诊断失败",
                        "诊断依据": [f"诊断过程中出现错误: {e}"]
                    },
                    "次要诊断": [],
                    "鉴别诊断": []
                },
                "治疗方案": ["建议重新进行诊断评估"],
                "error": str(e)
            }
    
    def validate_final_diagnosis(self, final_diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证最终诊断结果的完整性和合理性
        
        Args:
            final_diagnosis: 最终诊断结果
            
        Returns:
            验证后的诊断结果，包含诊断摘要
        """
        try:
            # 验证新格式的必需字段
            required_fields = ['患者信息', '临床表现', '病史信息', '体格检查', '辅助检查', '诊断结果', '治疗方案']
            for field in required_fields:
                if field not in final_diagnosis:
                    self.logger.warning(f"缺少必需字段: {field}")
                    final_diagnosis[field] = self._get_default_value(field)
            
            # 生成诊断摘要（基于新格式）
            diagnosis_result = final_diagnosis.get('诊断结果', {})
            primary_diagnosis = diagnosis_result.get('主要诊断', {})
            secondary_diagnoses = diagnosis_result.get('次要诊断', [])
            differential_diagnoses = diagnosis_result.get('鉴别诊断', [])
            treatment_plans = final_diagnosis.get('治疗方案', [])
            
            diagnosis_summary = {
                'primary_diagnosis_name': primary_diagnosis.get('名称', '未确定'),
                'secondary_diagnoses_count': len(secondary_diagnoses),
                'differential_diagnoses_count': len(differential_diagnoses),
                'treatment_categories': len(treatment_plans),
                'follow_up_plans': 0,  # 新格式中没有单独的随访计划
                'confidence_level': '高' if primary_diagnosis.get('名称') != '未确定' else '低'
            }
            
            final_diagnosis['diagnosis_summary'] = diagnosis_summary
            
            self.logger.info("最终诊断验证完成")
            return final_diagnosis
            
        except Exception as e:
            self.logger.error(f"诊断验证失败: {e}")
            return final_diagnosis
    
    def _get_default_value(self, field: str) -> Any:
        """
        获取字段的默认值（新格式）
        
        Args:
            field: 字段名
            
        Returns:
            默认值
        """
        defaults = {
            '患者信息': {
                '年龄': 0,
                '性别': '未知',
                '入院日期': '未知'
            },
            '临床表现': {
                '主诉': '需要进一步评估',
                '现病史': '需要进一步评估'
            },
            '病史信息': {
                '既往史': '需要进一步评估',
                '个人史': '需要进一步评估',
                '婚育史': '需要进一步评估',
                '家族史': '需要进一步评估'
            },
            '体格检查': '需要进一步评估',
            '辅助检查': '需要进一步评估',
            '诊断结果': {
                '主要诊断': {
                    '名称': '未确定诊断',
                    '诊断依据': ['需要进一步评估']
                },
                '次要诊断': [],
                '鉴别诊断': []
            },
            '治疗方案': ['需要进一步评估']
        }
        
        return defaults.get(field, {})
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理最终诊断决策
        
        Args:
            input_data: 输入数据，包含患者信息和修订后的诊断
            
        Returns:
            最终诊断结果
        """
        try:
            self.logger.info("Dr.Clinical-Reasoning开始最终诊断决策")
            
            # 提取输入数据
            patient_info = input_data.get('patient_info', {})
            challenge_result = input_data.get('challenge_result', {})
            
            if not patient_info:
                raise ValueError("缺少患者信息")
            
            if not challenge_result:
                raise ValueError("缺少修订后的诊断信息")
            
            revised_diagnoses = challenge_result.get('revised_diagnosis_list', [])
            
            # 分析诊断置信度
            confidence_analysis = self.analyze_diagnosis_confidence(revised_diagnoses)
            
            # 确定主要和次要诊断
            primary_diagnosis_name = ""
            secondary_diagnosis_names = []
            
            if confidence_analysis['high_confidence_diagnoses']:
                primary_diagnosis_name = confidence_analysis['high_confidence_diagnoses'][0].get('diagnosis_name', '')
                secondary_diagnosis_names = [d.get('diagnosis_name', '') for d in confidence_analysis['medium_confidence_diagnoses'][:2]]
            elif confidence_analysis['medium_confidence_diagnoses']:
                primary_diagnosis_name = confidence_analysis['medium_confidence_diagnoses'][0].get('diagnosis_name', '')
                secondary_diagnosis_names = [d.get('diagnosis_name', '') for d in confidence_analysis['medium_confidence_diagnoses'][1:3]]
            
            # 生成治疗相关查询
            treatment_queries = self.generate_treatment_queries(primary_diagnosis_name, secondary_diagnosis_names)
            
            # 检索治疗相关的医学知识
            treatment_documents = []
            for query in treatment_queries:
                documents = self.retrieve_medical_knowledge(query, top_k=3)
                treatment_documents.extend(documents)
            
            # 格式化医学上下文
            medical_context = self.format_medical_context(treatment_documents)
            
            # 生成最终诊断
            final_diagnosis = self.make_final_diagnosis(
                patient_info, challenge_result, medical_context
            )
            
            # 验证结果
            validated_result = self.validate_final_diagnosis(final_diagnosis)
            
            # 构建输出数据
            output_data = {
                'agent_name': self.agent_name,
                'patient_summary': self.prompt_templates.format_patient_summary(patient_info),
                'confidence_analysis': confidence_analysis,
                'treatment_queries_used': treatment_queries,
                'treatment_documents_retrieved': len(treatment_documents),
                'final_diagnosis': validated_result,
                'processing_status': 'success'
            }
            
            # 记录交互日志
            self.log_interaction(input_data, output_data)
            
            self.logger.info("Dr.Clinical-Reasoning处理完成")
            return output_data
            
        except Exception as e:
            self.logger.error(f"Dr.Clinical-Reasoning处理失败: {e}")
            
            error_output = {
                'agent_name': self.agent_name,
                'error': str(e),
                'processing_status': 'failed',
                'final_diagnosis': {
                    'primary_diagnosis': {
                        'name': '诊断失败',
                        'confidence_level': '低',
                        'supporting_evidence': [],
                        'clinical_reasoning': f"处理过程中出现错误: {e}"
                    },
                    'secondary_diagnoses': [],
                    'differential_diagnoses': [],
                    'treatment_recommendations': [],
                    'follow_up_plan': [],
                    'prognosis': {
                        'short_term': '需要进一步评估',
                        'long_term': '需要进一步评估',
                        'risk_factors': []
                    },
                    'error': str(e)
                }
            }
            
            self.log_interaction(input_data, error_output)
            return error_output
    
    def get_diagnosis_summary(self, final_result: Dict[str, Any]) -> str:
        """
        获取最终诊断摘要
        
        Args:
            final_result: 最终诊断结果
            
        Returns:
            诊断摘要文本
        """
        if not final_result or 'final_diagnosis' not in final_result:
            return "无最终诊断结果"
        
        diagnosis = final_result['final_diagnosis']
        summary = diagnosis.get('diagnosis_summary', {})
        
        if not summary:
            return "诊断摘要不可用"
        
        summary_parts = [
            f"主要诊断: {summary.get('primary_diagnosis_name', '未确定')}",
            f"置信度: {summary.get('confidence_level', '未知')}",
            f"次要诊断数: {summary.get('secondary_diagnoses_count', 0)}",
            f"鉴别诊断数: {summary.get('differential_diagnoses_count', 0)}",
            f"治疗方案数: {summary.get('treatment_categories', 0)}",
            f"随访计划数: {summary.get('follow_up_plans', 0)}"
        ]
        
        return "\n".join(summary_parts)

# 测试函数
def test_dr_clinical_reasoning():
    """
    测试Dr.Clinical-Reasoning Agent
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
        'challenge_result': {
            'revised_diagnosis_list': [
                {
                    'diagnosis_name': '急性下壁心肌梗死',
                    'supporting_evidence': ['胸痛症状', 'ST段抬高', '放射痛', '心电图改变'],
                    'probability': '高',
                    'additional_tests_needed': ['心肌酶', '冠脉造影']
                },
                {
                    'diagnosis_name': '高血压性心脏病',
                    'supporting_evidence': ['高血压病史', '血压升高'],
                    'probability': '中',
                    'additional_tests_needed': ['超声心动图']
                }
            ],
            'quality_concerns': [],
            'recommendations': ['建议急诊处理', '监测心肌酶变化']
        }
    }
    
    try:
        # 创建Agent实例
        dr_clinical_reasoning = DrClinicalReasoningAgent()
        
        print("=== Dr.Clinical-Reasoning Agent 测试 ===")
        print(f"Agent描述: {dr_clinical_reasoning.get_agent_description()}")
        print()
        
        # 处理最终诊断
        result = dr_clinical_reasoning.process(test_input)
        
        print("处理结果:")
        print(f"状态: {result.get('processing_status')}")
        print(f"治疗文档数: {result.get('treatment_documents_retrieved')}")
        print()
        
        # 显示诊断摘要
        summary = dr_clinical_reasoning.get_diagnosis_summary(result)
        print("最终诊断摘要:")
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
    test_dr_clinical_reasoning()
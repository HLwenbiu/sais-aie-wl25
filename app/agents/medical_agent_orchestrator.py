#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗诊断Agent协调器
管理三个Agent之间的信息传递和工作流程
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.agents.dr_hypothesis_agent import DrHypothesisAgent
from app.agents.dr_challenger_agent import DrChallengerAgent
from app.agents.dr_clinical_reasoning_agent import DrClinicalReasoningAgent

class MedicalAgentOrchestrator:
    """
    医疗诊断Agent协调器
    
    负责：
    - 管理三个Agent的执行顺序
    - 处理Agent间的数据传递
    - 监控诊断流程
    - 生成完整的诊断报告
    """
    
    def __init__(self, vector_db_path: str = "rag_vector_db"):
        """
        初始化协调器
        
        Args:
            vector_db_path: 向量数据库路径
        """
        self.vector_db_path = vector_db_path
        
        # 设置日志
        self.logger = logging.getLogger("MedicalAgentOrchestrator")
        self.logger.setLevel(logging.INFO)
        
        # 初始化三个Agent
        try:
            self.dr_hypothesis = DrHypothesisAgent(vector_db_path)
            self.dr_challenger = DrChallengerAgent(vector_db_path)
            self.dr_clinical_reasoning = DrClinicalReasoningAgent(vector_db_path)
            
            self.logger.info("医疗诊断Agent协调器初始化成功")
        except Exception as e:
            self.logger.error(f"协调器初始化失败: {e}")
            raise
        
        # 诊断流程状态
        self.current_session = None
        self.session_history = []
    
    def create_diagnosis_session(self, patient_info: Dict[str, Any], session_id: Optional[str] = None) -> str:
        """
        创建诊断会话
        
        Args:
            patient_info: 患者信息
            session_id: 会话ID（可选）
            
        Returns:
            会话ID
        """
        if not session_id:
            session_id = f"session_{int(time.time())}"
        
        self.current_session = {
            'session_id': session_id,
            'patient_info': patient_info,
            'start_time': datetime.now(),
            'status': 'created',
            'steps': [],
            'results': {}
        }
        
        self.logger.info(f"创建诊断会话: {session_id}")
        return session_id
    
    def execute_diagnosis_workflow(self, patient_info: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        执行完整的诊断工作流程
        
        Args:
            patient_info: 患者信息
            session_id: 会话ID（可选）
            
        Returns:
            完整的诊断结果
        """
        try:
            # 创建会话
            if not session_id:
                session_id = self.create_diagnosis_session(patient_info)
            
            self.logger.info(f"开始执行诊断工作流程 - 会话: {session_id}")
            
            # 步骤1: Dr.Hypothesis - 生成诊断假设
            self.logger.info("步骤1: 执行Dr.Hypothesis - 生成诊断假设")
            hypothesis_start = time.time()
            
            hypothesis_input = {'patient_info': patient_info}
            hypothesis_result = self.dr_hypothesis.process(hypothesis_input)
            
            hypothesis_duration = time.time() - hypothesis_start
            
            # 记录步骤结果
            self._record_step_result('hypothesis', hypothesis_result, hypothesis_duration)
            
            if hypothesis_result.get('processing_status') != 'success':
                raise Exception(f"Dr.Hypothesis处理失败: {hypothesis_result.get('error')}")
            
            # 步骤2: Dr.Challenger - 质疑和修正诊断
            self.logger.info("步骤2: 执行Dr.Challenger - 质疑和修正诊断")
            challenger_start = time.time()
            
            challenger_input = {
                'patient_info': patient_info,
                'diagnosis_hypotheses': hypothesis_result.get('diagnosis_hypotheses', {})
            }
            challenger_result = self.dr_challenger.process(challenger_input)
            
            challenger_duration = time.time() - challenger_start
            
            # 记录步骤结果
            self._record_step_result('challenger', challenger_result, challenger_duration)
            
            if challenger_result.get('processing_status') != 'success':
                raise Exception(f"Dr.Challenger处理失败: {challenger_result.get('error')}")
            
            # 步骤3: Dr.Clinical-Reasoning - 最终诊断
            self.logger.info("步骤3: 执行Dr.Clinical-Reasoning - 最终诊断")
            reasoning_start = time.time()
            
            reasoning_input = {
                'patient_info': patient_info,
                'challenge_result': challenger_result.get('challenge_result', {})
            }
            reasoning_result = self.dr_clinical_reasoning.process(reasoning_input)
            
            reasoning_duration = time.time() - reasoning_start
            
            # 记录步骤结果
            self._record_step_result('clinical_reasoning', reasoning_result, reasoning_duration)
            
            if reasoning_result.get('processing_status') != 'success':
                raise Exception(f"Dr.Clinical-Reasoning处理失败: {reasoning_result.get('error')}")
            
            # 生成完整的诊断报告
            final_report = self._generate_final_report(
                hypothesis_result, challenger_result, reasoning_result
            )
            
            # 更新会话状态
            self.current_session['status'] = 'completed'
            self.current_session['end_time'] = datetime.now()
            self.current_session['results'] = final_report
            
            # 保存会话历史
            self.session_history.append(self.current_session.copy())
            
            self.logger.info(f"诊断工作流程完成 - 会话: {session_id}")
            return final_report
            
        except Exception as e:
            self.logger.error(f"诊断工作流程失败: {e}")
            
            # 更新会话状态为失败
            if self.current_session:
                self.current_session['status'] = 'failed'
                self.current_session['error'] = str(e)
                self.current_session['end_time'] = datetime.now()
            
            # 返回错误报告
            return self._generate_error_report(str(e))
    
    def _record_step_result(self, step_name: str, result: Dict[str, Any], duration: float):
        """
        记录步骤结果
        
        Args:
            step_name: 步骤名称
            result: 步骤结果
            duration: 执行时间
        """
        if self.current_session:
            step_record = {
                'step_name': step_name,
                'agent_name': result.get('agent_name', ''),
                'status': result.get('processing_status', 'unknown'),
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'summary': self._get_step_summary(step_name, result)
            }
            
            self.current_session['steps'].append(step_record)
    
    def _get_step_summary(self, step_name: str, result: Dict[str, Any]) -> str:
        """
        获取步骤摘要
        
        Args:
            step_name: 步骤名称
            result: 步骤结果
            
        Returns:
            步骤摘要
        """
        if step_name == 'hypothesis':
            return self.dr_hypothesis.get_diagnosis_summary(result)
        elif step_name == 'challenger':
            return self.dr_challenger.get_challenge_summary(result)
        elif step_name == 'clinical_reasoning':
            return self.dr_clinical_reasoning.get_diagnosis_summary(result)
        else:
            return "未知步骤"
    
    def _generate_final_report(self, hypothesis_result: Dict[str, Any], 
                              challenger_result: Dict[str, Any], 
                              reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成最终诊断报告
        
        Args:
            hypothesis_result: 假设生成结果
            challenger_result: 质疑修正结果
            reasoning_result: 最终推理结果
            
        Returns:
            完整的诊断报告
        """
        final_diagnosis = reasoning_result.get('final_diagnosis', {})
        
        report = {
            'session_info': {
                'session_id': self.current_session['session_id'],
                'patient_summary': reasoning_result.get('patient_summary', ''),
                'diagnosis_date': datetime.now().isoformat(),
                'total_processing_time': sum(step['duration'] for step in self.current_session['steps'])
            },
            
            'diagnosis_process': {
                'initial_hypotheses_count': len(hypothesis_result.get('diagnosis_hypotheses', {}).get('candidate_diagnoses', [])),
                'revised_diagnoses_count': len(challenger_result.get('challenge_result', {}).get('revised_diagnosis_list', [])),
                'quality_concerns_identified': len(challenger_result.get('challenge_result', {}).get('quality_concerns', [])),
                'medical_documents_consulted': (
                    hypothesis_result.get('medical_documents_count', 0) + 
                    challenger_result.get('medical_documents_retrieved', 0) + 
                    reasoning_result.get('treatment_documents_retrieved', 0)
                )
            },
            
            'final_diagnosis': final_diagnosis,
            
            'confidence_assessment': {
                'overall_confidence': reasoning_result.get('confidence_analysis', {}).get('overall_confidence', 'medium'),
                'evidence_strength': len(final_diagnosis.get('诊断结果', {}).get('主要诊断', {}).get('supporting_evidence', [])),
                'consensus_level': self._assess_consensus_level(hypothesis_result, challenger_result, reasoning_result)
            },
            
            'process_steps': self.current_session['steps'],
            
            'recommendations': {
                'immediate_actions': self._extract_immediate_actions(final_diagnosis),
                'follow_up_required': len(final_diagnosis.get('follow_up_plan', [])) > 0,
                'additional_consultations': self._suggest_consultations(final_diagnosis)
            }
        }
        
        return report
    
    def _assess_consensus_level(self, hypothesis_result: Dict[str, Any], 
                               challenger_result: Dict[str, Any], 
                               reasoning_result: Dict[str, Any]) -> str:
        """
        评估诊断共识水平
        
        Args:
            hypothesis_result: 假设结果
            challenger_result: 质疑结果
            reasoning_result: 推理结果
            
        Returns:
            共识水平
        """
        # 简化的共识评估逻辑
        quality_concerns = len(challenger_result.get('challenge_result', {}).get('quality_concerns', []))
        confidence = reasoning_result.get('confidence_analysis', {}).get('overall_confidence', 'medium')
        
        if quality_concerns == 0 and confidence == 'high':
            return 'high'
        elif quality_concerns <= 2 and confidence in ['high', 'medium']:
            return 'medium'
        else:
            return 'low'
    
    def _extract_immediate_actions(self, final_diagnosis: Dict[str, Any]) -> List[str]:
        """
        提取需要立即采取的行动
        
        Args:
            final_diagnosis: 最终诊断
            
        Returns:
            立即行动列表
        """
        immediate_actions = []
        
        # 从治疗建议中提取紧急行动
        treatments = final_diagnosis.get('treatment_recommendations', [])
        for treatment in treatments:
            if isinstance(treatment, dict):
                category = treatment.get('category', '')
                if '急' in category or '紧急' in category:
                    recommendations = treatment.get('specific_recommendations', [])
                    immediate_actions.extend(recommendations)
        
        return immediate_actions[:5]  # 限制数量
    
    def _suggest_consultations(self, final_diagnosis: Dict[str, Any]) -> List[str]:
        """
        建议会诊科室
        
        Args:
            final_diagnosis: 最终诊断
            
        Returns:
            建议会诊科室列表
        """
        consultations = []
        
        primary_diagnosis = final_diagnosis.get('诊断结果', {}).get('主要诊断', {}).get('诊断名称', '')
        
        # 基于诊断建议会诊科室
        if '心肌梗死' in primary_diagnosis or '冠心病' in primary_diagnosis:
            consultations.extend(['心血管内科', '心胸外科'])
        
        if '心律失常' in primary_diagnosis:
            consultations.append('电生理科')
        
        if '心衰' in primary_diagnosis or '心功能不全' in primary_diagnosis:
            consultations.append('心衰专科')
        
        return list(set(consultations))  # 去重
    
    def _generate_error_report(self, error_message: str) -> Dict[str, Any]:
        """
        生成错误报告
        
        Args:
            error_message: 错误信息
            
        Returns:
            错误报告
        """
        return {
            'session_info': {
                'session_id': self.current_session['session_id'] if self.current_session else 'unknown',
                'diagnosis_date': datetime.now().isoformat(),
                'status': 'failed'
            },
            'error': {
                'message': error_message,
                'completed_steps': len(self.current_session['steps']) if self.current_session else 0
            },
            'final_diagnosis': {
                '患者信息': {
                    '姓名': '未知',
                    '年龄': '未知',
                    '性别': '未知'
                },
                '临床表现': {
                    '主诉': '诊断失败',
                    '现病史': f'诊断过程中出现错误: {error_message}',
                    '体格检查': '未完成',
                    '辅助检查': '未完成'
                },
                '诊断结果': {
                    '主要诊断': {
                        '诊断名称': '诊断失败',
                        '置信度': '无',
                        '诊断依据': f'诊断过程中出现错误: {error_message}'
                    }
                },
                '治疗方案': {
                    '治疗目标': '错误处理',
                    '药物治疗': [],
                    '非药物治疗': [],
                    '手术治疗': []
                }
            }
        }
    
    def get_session_history(self) -> List[Dict[str, Any]]:
        """
        获取会话历史
        
        Returns:
            会话历史列表
        """
        return self.session_history.copy()
    
    def export_diagnosis_report(self, report: Dict[str, Any], format_type: str = 'json') -> str:
        """
        导出诊断报告
        
        Args:
            report: 诊断报告
            format_type: 导出格式
            
        Returns:
            格式化的报告字符串
        """
        if format_type == 'json':
            return json.dumps(report, ensure_ascii=False, indent=2)
        elif format_type == 'text':
            return self._format_text_report(report)
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")
    
    def _format_text_report(self, report: Dict[str, Any]) -> str:
        """
        格式化文本报告
        
        Args:
            report: 诊断报告
            
        Returns:
            文本格式报告
        """
        lines = []
        lines.append("=== 医疗诊断报告 ===")
        lines.append("")
        
        # 会话信息
        session_info = report.get('session_info', {})
        lines.append(f"会话ID: {session_info.get('session_id', '未知')}")
        lines.append(f"诊断日期: {session_info.get('diagnosis_date', '未知')}")
        lines.append(f"患者摘要: {session_info.get('patient_summary', '未提供')}")
        lines.append("")
        
        # 最终诊断
        final_diagnosis = report.get('final_diagnosis', {})
        primary = final_diagnosis.get('primary_diagnosis', {})
        
        lines.append("=== 最终诊断 ===")
        lines.append(f"主要诊断: {primary.get('name', '未确定')}")
        lines.append(f"置信度: {primary.get('confidence_level', '未知')}")
        lines.append("")
        
        # 次要诊断
        secondary = final_diagnosis.get('secondary_diagnoses', [])
        if secondary:
            lines.append("次要诊断:")
            for i, diag in enumerate(secondary, 1):
                if isinstance(diag, dict):
                    lines.append(f"{i}. {diag.get('name', '未知')}")
            lines.append("")
        
        # 治疗建议
        treatments = final_diagnosis.get('treatment_recommendations', [])
        if treatments:
            lines.append("=== 治疗建议 ===")
            for treatment in treatments:
                if isinstance(treatment, dict):
                    category = treatment.get('category', '未分类')
                    recommendations = treatment.get('specific_recommendations', [])
                    lines.append(f"{category}:")
                    for rec in recommendations:
                        lines.append(f"  - {rec}")
            lines.append("")
        
        return "\n".join(lines)

# 测试函数
def test_orchestrator():
    """
    测试医疗Agent协调器
    """
    # 创建测试患者信息
    test_patient = {
        'chief_complaint': '胸痛3小时',
        'present_illness': '患者3小时前无明显诱因出现胸骨后疼痛，呈压榨性，向左肩背部放射，伴出汗、恶心',
        'past_history': '高血压病史5年，糖尿病病史3年',
        'physical_examination': '血压160/95mmHg，心率98次/分，心律齐，未闻及杂音',
        'auxiliary_examination': '心电图示II、III、aVF导联ST段抬高',
        'vital_signs': 'T 36.8°C, P 98次/分, R 20次/分, BP 160/95mmHg'
    }
    
    try:
        # 创建协调器实例
        orchestrator = MedicalAgentOrchestrator()
        
        print("=== 医疗诊断Agent协调器测试 ===")
        print("开始执行完整诊断流程...")
        print()
        
        # 执行诊断工作流程
        report = orchestrator.execute_diagnosis_workflow(test_patient)
        
        print("诊断流程完成！")
        print()
        
        # 显示文本格式报告
        text_report = orchestrator.export_diagnosis_report(report, 'text')
        print(text_report)
        
        return report
        
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
    test_orchestrator()
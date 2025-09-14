#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用case6.json标准格式测试医疗诊断Agent系统

这个脚本读取case6.json文件，将其转换为系统所需的格式，
然后测试完整的医疗诊断Agent工作流程。

作者: AI Assistant
日期: 2025-01-12
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from app.agents.medical_agent_orchestrator import MedicalAgentOrchestrator

def load_case_data(case_file):
    """加载病例数据"""
    try:
        with open(case_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载病例数据失败: {e}")
        return None

def test_case6():
    """测试Case 6"""
    print("=" * 60)
    print("开始测试 Case 6")
    print("=" * 60)
    
    # 加载case6数据
    case_data = load_case_data('medical_records/case6.json')
    if not case_data:
        print("无法加载case6数据")
        return
    
    # 创建诊断协调器
    orchestrator = MedicalAgentOrchestrator()
    
    try:
        # 执行诊断
        diagnosis_result = orchestrator.execute_diagnosis_workflow(case_data)
        
        if diagnosis_result:
            print("\n" + "=" * 50)
            print("患者信息:")
            # 从诊断结果中提取患者信息
            patient_info = diagnosis_result.get('final_diagnosis', {}).get('患者信息', {})
            clinical_info = diagnosis_result.get('final_diagnosis', {}).get('临床表现', {})
            print(f"年龄: {patient_info.get('年龄', 'N/A')}")
            print(f"性别: {patient_info.get('性别', 'N/A')}")
            print(f"主诉: {clinical_info.get('主诉', 'N/A')}")
            print(f"入院日期: {patient_info.get('入院日期', 'N/A')}")
            
            print("\n" + "=" * 50)
            print("诊断结果:")
            
            # 从final_diagnosis中提取诊断信息
            final_diagnosis = diagnosis_result.get('final_diagnosis', {})
            diagnosis_info = final_diagnosis.get('诊断结果', {})
            
            # 主要诊断
            primary_diag = diagnosis_info.get('主要诊断', {})
            if primary_diag:
                print(f"\n主要诊断: {primary_diag.get('名称', 'N/A')}")
                if primary_diag.get('诊断依据'):
                    print("  诊断依据:")
                    for i, evidence in enumerate(primary_diag['诊断依据'], 1):
                        print(f"    {i}. {evidence}")
            
            # 次要诊断
            secondary_diags = diagnosis_info.get('次要诊断', [])
            if secondary_diags:
                print("\n次要诊断:")
                for i, diag in enumerate(secondary_diags, 1):
                    print(f"  {i}. {diag.get('名称', 'N/A')}")
                    if diag.get('诊断依据'):
                        print("     诊断依据:")
                        for j, evidence in enumerate(diag['诊断依据'], 1):
                            print(f"       {j}. {evidence}")
            
            # 鉴别诊断
            differential_diags = diagnosis_info.get('鉴别诊断', [])
            if differential_diags:
                print("\n鉴别诊断:")
                for i, diag in enumerate(differential_diags, 1):
                    print(f"  {i}. {diag}")
            
            # 治疗建议
            treatments = final_diagnosis.get('治疗方案', [])
            if treatments:
                print("\n治疗方案:")
                for i, treatment in enumerate(treatments, 1):
                    print(f"  {i}. {treatment}")
            
            # 手动保存诊断报告
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_filename = f"output/case6_diagnosis_report_{timestamp}.json"
                
                # 确保output目录存在
                os.makedirs('output', exist_ok=True)
                
                # 准备完整的报告数据
                full_report = {
                    "patient_info": {
                        "age": case_data.get('age'),
                        "gender": case_data.get('gender'),
                        "chief_complaint": case_data.get('chief_complaint')
                    },
                    "diagnosis_result": diagnosis_result,
                    "timestamp": timestamp
                }
                
                # 保存到文件
                with open(report_filename, 'w', encoding='utf-8') as f:
                    json.dump(full_report, f, ensure_ascii=False, indent=2)
                
                print(f"\n诊断报告已保存到: {report_filename}")
                
            except Exception as e:
                print(f"保存诊断报告时出错: {e}")
            
            print("\n" + "=" * 50)
            print("Case 6 测试完成!")
            print("=" * 50)
            
        else:
            print("诊断失败，未获得结果")
            
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_case6()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用case2.json标准格式测试医疗诊断Agent系统

这个脚本读取case2.json文件，将其转换为系统所需的格式，
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

def test_case2():
    """测试case2病例"""
    try:
        # 初始化协调器
        orchestrator = MedicalAgentOrchestrator()
        
        # 读取case2数据
        with open('medical_records/case2.json', 'r', encoding='utf-8') as f:
            case_data = json.load(f)
        
        print('\n' + '='*80)
        print('🏥 开始测试 case2.json')
        print('='*80)
        
        # 执行诊断
        result = orchestrator.execute_diagnosis_workflow(case_data)
        
        # 显示结果
        if 'final_diagnosis' in result:
            diagnosis = result['final_diagnosis']
            
            # 显示患者信息
            if '患者信息' in diagnosis:
                patient_info = diagnosis['患者信息']
                print(f"\n👤 患者信息: {patient_info.get('年龄', 'N/A')}岁 {patient_info.get('性别', 'N/A')}")
            
            # 显示主诉
            if '临床表现' in diagnosis and '主诉' in diagnosis['临床表现']:
                print(f"\n🩺 主诉: {diagnosis['临床表现']['主诉']}")
            
            # 显示主要诊断
            if '诊断结果' in diagnosis and '主要诊断' in diagnosis['诊断结果']:
                main_diagnosis = diagnosis['诊断结果']['主要诊断']
                print(f"\n🎯 主要诊断: {main_diagnosis.get('名称', 'N/A')}")
            
            # 显示次要诊断
            if '诊断结果' in diagnosis and '次要诊断' in diagnosis['诊断结果']:
                secondary_diagnoses = diagnosis['诊断结果']['次要诊断']
                if secondary_diagnoses:
                    print(f"\n📋 次要诊断 ({len(secondary_diagnoses)}个):")
                    for i, diag in enumerate(secondary_diagnoses, 1):
                        print(f"  {i}. {diag.get('名称', 'N/A')}")
            
            # 显示鉴别诊断
            if '诊断结果' in diagnosis and '鉴别诊断' in diagnosis['诊断结果']:
                diff_diagnoses = diagnosis['诊断结果']['鉴别诊断']
                if diff_diagnoses:
                    print(f"\n🔍 鉴别诊断 ({len(diff_diagnoses)}个):")
                    for i, diag in enumerate(diff_diagnoses, 1):
                        print(f"  {i}. {diag}")
            
            # 显示治疗建议
            if '治疗方案' in diagnosis:
                treatments = diagnosis['治疗方案']
                if treatments:
                    print(f"\n💊 治疗建议")
                    print('-'*40)
                    for i, treatment in enumerate(treatments, 1):
                        print(f"  {i}. {treatment}")
        
        print('\n' + '='*80)
        
        # 手动保存诊断报告
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"output/case2_diagnosis_report_{timestamp}.json"
            
            # 导出报告
            report_json = orchestrator.export_diagnosis_report(result, 'json')
            
            # 保存到文件
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report_json)
            
            print(f"💾 诊断报告已保存至: {report_filename}")
        except Exception as e:
            print(f"⚠️ 保存报告时出错: {str(e)}")
            print("💾 诊断报告已生成但未保存到文件")
        
        print('\n🎉 case2.json测试完成！')
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_case2()
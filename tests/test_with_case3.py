#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import datetime
from app.agents.medical_agent_orchestrator import MedicalAgentOrchestrator

def test_case3():
    """测试case3病例"""
    try:
        # 初始化协调器
        orchestrator = MedicalAgentOrchestrator()
        
        # 读取case3数据
        with open('medical_records/case3.json', 'r', encoding='utf-8') as f:
            case_data = json.load(f)
        
        print('\n' + '='*80)
        print('🏥 开始测试 case3.json')
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
                    print(f"\n📋 次要诊断:")
                    for i, diag in enumerate(secondary_diagnoses, 1):
                        print(f"   {i}. {diag.get('名称', 'N/A')}")
            
            # 显示鉴别诊断
            if '诊断结果' in diagnosis and '鉴别诊断' in diagnosis['诊断结果']:
                diff_diagnoses = diagnosis['诊断结果']['鉴别诊断']
                if diff_diagnoses:
                    print(f"\n🔍 鉴别诊断: ({len(diff_diagnoses)}个)")
                    for i, diag in enumerate(diff_diagnoses, 1):
                        print(f"   {i}. {diag}")
            
            # 显示治疗方案
            if '治疗方案' in diagnosis:
                treatments = diagnosis['治疗方案']
                if treatments:
                    print(f"\n💊 治疗方案: ({len(treatments)}条)")
                    for i, treatment in enumerate(treatments, 1):
                        print(f"   {i}. {treatment}")
        
        # 手动保存诊断报告
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"output/case3_diagnosis_report_{timestamp}.json"
            
            # 导出报告
            report_path = orchestrator.export_diagnosis_report(result, 'json')
            
            # 重命名为case3专用文件名
            import os
            if os.path.exists(report_path):
                os.rename(report_path, report_filename)
                print(f"\n📄 诊断报告已保存: {report_filename}")
            else:
                # 如果导出失败，手动写入
                with open(report_filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n📄 诊断报告已保存: {report_filename}")
                
        except Exception as e:
            print(f"\n❌ 保存诊断报告时出错: {e}")
        
        print("\n✅ case3 测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试case3时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_case3()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用case1.json标准格式测试医疗诊断Agent系统

这个脚本读取case1.json文件，将其转换为系统所需的格式，
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

def load_case1_data():
    """加载case1.json文件数据"""
    case1_path = "medical_records/case1.json"
    
    if not os.path.exists(case1_path):
        raise FileNotFoundError(f"找不到文件: {case1_path}")
    
    with open(case1_path, 'r', encoding='utf-8') as f:
        case_data = json.load(f)
    
    return case_data

def parse_medical_record(medical_record_text):
    """解析医疗记录文本，提取结构化信息"""
    # 分割医疗记录文本
    sections = medical_record_text.split('###')
    
    parsed_data = {
        "patient_id": "case1_patient",
        "age": 52,
        "gender": "男",
        "chief_complaint": "反复腹痛、腹胀2周余",
        "present_illness": "",
        "past_history": "",
        "personal_history": "",
        "marriage_history": "",
        "family_history": "",
        "physical_examination": "",
        "auxiliary_examination": ""
    }
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        if "病史简介" in section:
            # 提取病史信息
            lines = section.split('\n')
            current_section = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if "现病史：" in line:
                    current_section = "present_illness"
                    parsed_data[current_section] = line.replace("现病史：", "").strip()
                elif "既往史：" in line:
                    current_section = "past_history"
                    parsed_data[current_section] = line.replace("既往史：", "").strip()
                elif "个人史：" in line:
                    current_section = "personal_history"
                    parsed_data[current_section] = line.replace("个人史：", "").strip()
                elif "婚育史：" in line:
                    current_section = "marriage_history"
                    parsed_data[current_section] = line.replace("婚育史：", "").strip()
                elif "家族史：" in line:
                    current_section = "family_history"
                    parsed_data[current_section] = line.replace("家族史：", "").strip()
                elif current_section and not any(x in line for x in ["史：", "###"]):
                    parsed_data[current_section] += " " + line
                    
        elif "体格检查" in section:
            parsed_data["physical_examination"] = section.replace("体格检查", "").strip()
            
        elif "辅助检查" in section:
            parsed_data["auxiliary_examination"] = section.replace("辅助检查", "").strip()
    
    return parsed_data

def convert_to_system_format(case_data):
    """将case1.json格式转换为系统所需格式"""
    medical_record = case_data.get("medical record", "")
    
    # 解析医疗记录
    parsed_data = parse_medical_record(medical_record)
    
    # 转换为系统格式
    system_format = {
        "patient_id": parsed_data["patient_id"],
        "age": parsed_data["age"],
        "gender": parsed_data["gender"],
        "chief_complaint": parsed_data["chief_complaint"],
        "present_illness": parsed_data["present_illness"],
        "past_history": parsed_data["past_history"],
        "personal_history": parsed_data["personal_history"],
        "marriage_history": parsed_data["marriage_history"],
        "family_history": parsed_data["family_history"],
        "physical_examination": parsed_data["physical_examination"],
        "auxiliary_examination": parsed_data["auxiliary_examination"]
    }
    
    return system_format

def print_patient_summary(patient_data):
    """打印患者信息摘要"""
    print("="*80)
    print("📋 患者信息摘要 (来自case1.json)")
    print("="*80)
    print(f"患者ID: {patient_data['patient_id']}")
    print(f"年龄: {patient_data['age']}岁")
    print(f"性别: {patient_data['gender']}")
    print(f"主诉: {patient_data['chief_complaint']}")
    print(f"\n现病史: {patient_data['present_illness'][:200]}...")
    print(f"\n既往史: {patient_data['past_history'][:200]}...")
    print("\n" + "="*80)

def display_diagnosis_report(report):
    """格式化显示诊断报告"""
    print("\n" + "="*80)
    print("🏥 医疗诊断报告 (基于case1.json)")
    print("="*80)
    
    # 基本信息
    session_info = report.get('session_info', {})
    print(f"会话ID: {session_info.get('session_id', 'N/A')}")
    print(f"诊断时间: {session_info.get('diagnosis_date', 'N/A')}")
    print(f"患者摘要: {session_info.get('patient_summary', 'N/A')[:150]}...")
    print()
    
    # 最终诊断
    final_diagnosis = report.get('final_diagnosis', {})
    diagnosis_result = final_diagnosis.get('诊断结果', {})
    primary_diagnosis = diagnosis_result.get('主要诊断', {})
    
    print("🎯 最终诊断")
    print("-" * 40)
    print(f"主要诊断: {primary_diagnosis.get('名称', 'N/A')}")
    
    # 从diagnosis_summary获取置信度
    diagnosis_summary = final_diagnosis.get('diagnosis_summary', {})
    print(f"置信度: {diagnosis_summary.get('confidence_level', 'N/A')}")
    
    # 次要诊断
    secondary_diagnoses = diagnosis_result.get('次要诊断', [])
    if secondary_diagnoses:
        print("\n次要诊断:")
        for i, diagnosis in enumerate(secondary_diagnoses, 1):
            name = diagnosis.get('名称', 'N/A') if isinstance(diagnosis, dict) else diagnosis
            print(f"  {i}. {name}")
    
    # 鉴别诊断
    differential_diagnoses = diagnosis_result.get('鉴别诊断', [])
    if differential_diagnoses:
        print("\n鉴别诊断:")
        for i, diagnosis in enumerate(differential_diagnoses, 1):
            name = diagnosis if isinstance(diagnosis, str) else diagnosis.get('名称', 'N/A')
            print(f"  {i}. {name}")
    
    # 治疗方案
    treatment_plan = final_diagnosis.get('治疗方案', [])
    if treatment_plan:
        print("\n💊 治疗建议")
        print("-" * 40)
        for i, treatment in enumerate(treatment_plan, 1):
            print(f"  {i}. {treatment}")
    
    print("\n" + "="*80)

def main():
    """主函数"""
    try:
        print("🏥 使用case1.json测试医疗诊断Agent系统")
        print("="*80)
        
        # 1. 加载case1.json数据
        print("📂 正在加载case1.json文件...")
        case_data = load_case1_data()
        print("✅ case1.json文件加载成功")
        
        # 2. 转换为系统格式
        print("🔄 正在转换数据格式...")
        patient_data = convert_to_system_format(case_data)
        print("✅ 数据格式转换完成")
        
        # 3. 显示患者信息
        print_patient_summary(patient_data)
        
        # 调试：打印解析后的patient_data
        print("\n🔍 调试信息 - 解析后的患者数据:")
        print(f"个人史: {patient_data.get('personal_history', 'None')}")
        print(f"婚育史: {patient_data.get('marriage_history', 'None')}")
        print(f"家族史: {patient_data.get('family_history', 'None')}")
        
        # 添加对Dr.Clinical-Reasoning Agent响应的调试
        print("\n=== Dr.Clinical-Reasoning 调试 ===")
        print("监控JSON解析是否失败...")
        print("==============================\n")
        
        # 4. 初始化医疗诊断系统
        print("🚀 正在初始化医疗诊断Agent系统...")
        orchestrator = MedicalAgentOrchestrator()
        print("✅ 系统初始化完成")
        
        # 5. 创建诊断会话
        print("\n📋 创建诊断会话...")
        session_id = orchestrator.create_diagnosis_session(patient_data)
        print(f"✅ 诊断会话创建成功: {session_id}")
        
        # 6. 执行诊断工作流程
        print("\n🔄 执行诊断工作流程...")
        print("  Step 1: Dr.Hypothesis 分析患者信息，生成诊断假设...")
        print("  Step 2: Dr.Challenger 质疑和修正诊断假设...")
        print("  Step 3: Dr.Clinical-Reasoning 综合信息生成最终诊断...")
        
        # 执行诊断
        report = orchestrator.execute_diagnosis_workflow(patient_data, session_id)
        
        # 7. 显示诊断报告
        display_diagnosis_report(report)
        
        # 8. 保存诊断结果
        output_file = f"output/case_diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("output", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 诊断报告已保存至: {output_file}")
        print("\n🎉 case1.json测试完成！")
        
    except FileNotFoundError as e:
        print(f"❌ 文件错误: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {str(e)}")
    except Exception as e:
        print(f"❌ 系统错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
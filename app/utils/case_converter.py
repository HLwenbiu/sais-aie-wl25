#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用病例数据转换与报告展示工具
- load_case_data(file_path): 加载病例JSON
- parse_medical_record(text): 解析“medical record”长文本
- convert_to_system_format(case_data): 转换为系统字段格式
- display_diagnosis_report(report): 终端友好展示报告
"""
import os
import json
from datetime import datetime


def load_case_data(file_path: str) -> dict:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到文件: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_medical_record(medical_record_text: str) -> dict:
    sections = medical_record_text.split('###') if medical_record_text else []
    parsed = {
        "patient_id": "patient",
        "age": 0,
        "gender": "未知",
        "chief_complaint": "",
        "present_illness": "",
        "past_history": "",
        "personal_history": "",
        "marriage_history": "",
        "family_history": "",
        "physical_examination": "",
        "auxiliary_examination": ""
    }
    for section in sections:
        s = section.strip()
        if not s:
            continue
        if "病史简介" in s:
            lines = s.split('\n')
            current = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if "现病史：" in line:
                    current = "present_illness"; parsed[current] = line.replace("现病史：", "").strip()
                elif "既往史：" in line:
                    current = "past_history"; parsed[current] = line.replace("既往史：", "").strip()
                elif "个人史：" in line:
                    current = "personal_history"; parsed[current] = line.replace("个人史：", "").strip()
                elif "婚育史：" in line:
                    current = "marriage_history"; parsed[current] = line.replace("婚育史：", "").strip()
                elif "家族史：" in line:
                    current = "family_history"; parsed[current] = line.replace("家族史：", "").strip()
                elif current and not any(x in line for x in ["史：", "###"]):
                    parsed[current] += " " + line
        elif "体格检查" in s:
            parsed["physical_examination"] = s.replace("体格检查", "").strip()
        elif "辅助检查" in s:
            parsed["auxiliary_examination"] = s.replace("辅助检查", "").strip()
    return parsed


def convert_to_system_format(case_data: dict) -> dict:
    medical_record = case_data.get("medical record", "")
    parsed = parse_medical_record(medical_record)
    # 尝试从case_data补充基本信息
    parsed["age"] = case_data.get("age", parsed["age"]) or parsed["age"]
    parsed["gender"] = case_data.get("gender", parsed["gender"]) or parsed["gender"]
    parsed["chief_complaint"] = case_data.get("chief_complaint", parsed["chief_complaint"]) or parsed["chief_complaint"]
    parsed["patient_id"] = case_data.get("patient_id", parsed["patient_id"]) or parsed["patient_id"]
    return {
        "patient_id": parsed["patient_id"],
        "age": parsed["age"],
        "gender": parsed["gender"],
        "chief_complaint": parsed["chief_complaint"],
        "present_illness": parsed["present_illness"],
        "past_history": parsed["past_history"],
        "personal_history": parsed["personal_history"],
        "marriage_history": parsed["marriage_history"],
        "family_history": parsed["family_history"],
        "physical_examination": parsed["physical_examination"],
        "auxiliary_examination": parsed["auxiliary_examination"]
    }


def display_diagnosis_report(report: dict) -> None:
    print("\n" + "="*80)
    print("🏥 医疗诊断报告")
    print("="*80)
    session_info = report.get('session_info', {})
    print(f"会话ID: {session_info.get('session_id', 'N/A')}")
    print(f"诊断时间: {session_info.get('diagnosis_date', 'N/A')}")
    print(f"患者摘要: {session_info.get('patient_summary', 'N/A')[:150]}...")
    final_diagnosis = report.get('final_diagnosis', {})
    diagnosis_result = final_diagnosis.get('诊断结果', {})
    primary = diagnosis_result.get('主要诊断', {})
    print("\n🎯 最终诊断")
    print("-" * 40)
    print(f"主要诊断: {primary.get('名称', primary.get('诊断名称', 'N/A'))}")
    treatments = final_diagnosis.get('治疗方案', []) or final_diagnosis.get('treatment_recommendations', [])
    if treatments:
        print("\n💊 治疗建议")
        print("-" * 40)
        for i, t in enumerate(treatments, 1):
            if isinstance(t, dict):
                print(f"  {i}. {t.get('category', '建议')}: ")
                for rec in t.get('specific_recommendations', []):
                    print(f"     - {rec}")
            else:
                print(f"  {i}. {t}")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单病例诊断运行器（稳定输入版）
- 通过命令行参数 --file 指定病例JSON路径
- 自动验证路径并清晰打印所用输入文件，避免“修改路径后结果错乱”的视觉混淆
- 复用现有通用转换与展示逻辑，确保字段映射一致
- 将报告保存到 output/<basename>_diagnosis_report_<timestamp>.json

用法示例：
    python run_diagnosis_cli.py --file medical_records/case6.json
"""

import os
import sys
import json
import argparse
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录加入路径，便于包导入
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(PROJECT_ROOT)

from app.agents.medical_agent_orchestrator import MedicalAgentOrchestrator
from app.utils.case_converter import load_case_data, convert_to_system_format, display_diagnosis_report


def ensure_output_dir() -> str:
    out_dir = os.path.join(CURRENT_DIR, 'output')
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def build_report_filename(input_file: str) -> str:
    base = os.path.splitext(os.path.basename(input_file))[0]
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base}_diagnosis_report_{ts}.json"


def run_diagnosis(input_file: str) -> str:
    # 1) 规范化并校验输入路径
    if not os.path.isabs(input_file):
        input_file = os.path.join(CURRENT_DIR, input_file)
    input_file = os.path.normpath(input_file)

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"输入文件不存在: {input_file}")

    print("\n================ 运行参数确认 ================")
    print(f"输入文件: {input_file}")
    print("==========================================\n")

    # 2) 加载并转换患者数据（复用稳定逻辑）
    case_data = load_case_data(file_path=input_file)
    patient_data = convert_to_system_format(case_data)

    # 3) 初始化系统并创建会话
    orchestrator = MedicalAgentOrchestrator()
    session_id = orchestrator.create_diagnosis_session(patient_data)

    # 4) 执行工作流
    report = orchestrator.execute_diagnosis_workflow(patient_data, session_id)

    # 附加溯源信息，便于回看（不改变系统核心结构，仅增加字段）
    try:
        report.setdefault('meta', {})['input_file'] = os.path.relpath(input_file, CURRENT_DIR)
        report.setdefault('meta', {})['run_timestamp'] = datetime.now().isoformat()
    except Exception:
        pass

    # 5) 打印诊断结果（复用稳定展示函数）
    try:
        case_name = os.path.splitext(os.path.basename(input_file))[0]
        display_diagnosis_report(report, case_name)
    except Exception as e:
        print(f"⚠️ 展示报告时发生非致命错误: {e}")

    # 6) 落盘保存
    out_dir = ensure_output_dir()
    out_name = build_report_filename(input_file)
    out_path = os.path.join(out_dir, out_name)
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n💾 诊断报告已保存: {out_path}")
    except Exception as e:
        print(f"❌ 保存报告失败: {e}")
        out_path = ''

    return out_path


def parse_args():
    parser = argparse.ArgumentParser(description='单病例诊断运行器（稳定输入版）')
    parser.add_argument('--file', '-f', required=True, help='病例JSON文件路径，例如 medical_records/case6.json')
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        out_path = run_diagnosis(args.file)
        if out_path:
            print("\n✅ 运行完成，无需重启，仅需更换 --file 即可测试其他案例。")
        else:
            print("\n⚠️ 运行完成，但报告未成功保存。")
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
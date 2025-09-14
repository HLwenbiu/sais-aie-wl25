#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档预处理模块
用于处理corpus文件夹中的PDF文献，提取文本并进行切分
"""

import os
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    文档处理器类，负责PDF文档的读取、文本提取和切分
    """
    
    def __init__(self, corpus_path: str = "corpus", config = None):
        """
        初始化文档处理器
        
        Args:
            corpus_path: corpus文件夹路径
            config: 配置参数（可选）
        """
        self.corpus_path = Path(corpus_path)
        self.chunk_size = 1000  # 默认文本块大小
        self.chunk_overlap = 200  # 文本块重叠大小
        
        # 检查PDF处理库是否可用
        self.available_libs = []
        if PyPDF2:
            self.available_libs.append('PyPDF2')
        if pdfplumber:
            self.available_libs.append('pdfplumber')
        if fitz:
            self.available_libs.append('PyMuPDF')
            
        if not self.available_libs:
            logger.warning("未找到PDF处理库，请安装 PyPDF2、pdfplumber 或 PyMuPDF")
    
    def get_pdf_files(self) -> List[Path]:
        """
        获取corpus文件夹中的所有PDF文件
        
        Returns:
            PDF文件路径列表
        """
        if not self.corpus_path.exists():
            logger.error(f"Corpus路径不存在: {self.corpus_path}")
            return []
        
        pdf_files = list(self.corpus_path.glob("*.pdf"))
        logger.info(f"找到 {len(pdf_files)} 个PDF文件")
        return pdf_files
    
    def extract_text_pypdf2(self, pdf_path: Path) -> str:
        """
        使用PyPDF2提取PDF文本
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取的文本内容
        """
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"PyPDF2提取文本失败 {pdf_path}: {e}")
        return text
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> str:
        """
        使用pdfplumber提取PDF文本
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取的文本内容
        """
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"pdfplumber提取文本失败 {pdf_path}: {e}")
        return text
    
    def extract_text_pymupdf(self, pdf_path: Path) -> str:
        """
        使用PyMuPDF提取PDF文本
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取的文本内容
        """
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            logger.error(f"PyMuPDF提取文本失败 {pdf_path}: {e}")
        return text
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        从PDF文件提取文本，自动选择可用的库
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取的文本内容
        """
        text = ""
        
        # 优先使用pdfplumber，其次PyMuPDF，最后PyPDF2
        if 'pdfplumber' in self.available_libs:
            text = self.extract_text_pdfplumber(pdf_path)
        elif 'PyMuPDF' in self.available_libs:
            text = self.extract_text_pymupdf(pdf_path)
        elif 'PyPDF2' in self.available_libs:
            text = self.extract_text_pypdf2(pdf_path)
        else:
            logger.error("没有可用的PDF处理库")
            return ""
        
        if text.strip():
            logger.info(f"成功提取文本: {pdf_path.name} ({len(text)} 字符)")
        else:
            logger.warning(f"未能提取到文本: {pdf_path.name}")
        
        return text
    
    def clean_text(self, text: str) -> str:
        """
        清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符和控制字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
        
        # 移除重复的换行符
        text = re.sub(r'\n+', '\n', text)
        
        # 去除首尾空白
        text = text.strip()
        
        return text
    
    def split_text_by_sentences(self, text: str, max_length: int = 1000) -> List[str]:
        """
        按句子分割文本
        
        Args:
            text: 输入文本
            max_length: 每个文本块的最大长度
            
        Returns:
            分割后的文本块列表
        """
        # 按句号、问号、感叹号分割
        sentences = re.split(r'[。！？.!?]', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果当前块加上新句子不超过最大长度，则添加
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence + "。"
            else:
                # 保存当前块，开始新块
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "。"
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def split_text_by_paragraphs(self, text: str, max_length: int = 1000) -> List[str]:
        """
        按段落分割文本
        
        Args:
            text: 输入文本
            max_length: 每个文本块的最大长度
            
        Returns:
            分割后的文本块列表
        """
        paragraphs = text.split('\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 如果当前块加上新段落不超过最大长度，则添加
            if len(current_chunk) + len(paragraph) <= max_length:
                current_chunk += paragraph + "\n"
            else:
                # 保存当前块，开始新块
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # 如果单个段落就超过最大长度，按句子分割
                if len(paragraph) > max_length:
                    sentence_chunks = self.split_text_by_sentences(paragraph, max_length)
                    chunks.extend(sentence_chunks)
                    current_chunk = ""
                else:
                    current_chunk = paragraph + "\n"
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        将文本分割成指定大小的块
        
        Args:
            text: 输入文本
            chunk_size: 文本块大小
            overlap: 重叠大小
            
        Returns:
            分割后的文本块列表
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
        if overlap is None:
            overlap = self.chunk_overlap
        
        # 首先尝试按段落分割
        chunks = self.split_text_by_paragraphs(text, chunk_size)
        
        # 如果需要重叠，添加重叠内容
        if overlap > 0 and len(chunks) > 1:
            overlapped_chunks = []
            for i, chunk in enumerate(chunks):
                if i == 0:
                    overlapped_chunks.append(chunk)
                else:
                    # 添加前一个块的末尾部分作为重叠
                    prev_chunk = chunks[i-1]
                    overlap_text = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
                    overlapped_chunks.append(overlap_text + " " + chunk)
            chunks = overlapped_chunks
        
        return chunks
    
    def process_single_pdf(self, pdf_path: Path) -> Dict[str, any]:
        """
        处理单个PDF文件
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            处理结果字典
        """
        logger.info(f"开始处理PDF: {pdf_path.name}")
        
        # 提取文本
        raw_text = self.extract_text_from_pdf(pdf_path)
        if not raw_text.strip():
            return {
                'file_name': pdf_path.name,
                'file_path': str(pdf_path),
                'success': False,
                'error': '无法提取文本内容',
                'chunks': []
            }
        
        # 清理文本
        cleaned_text = self.clean_text(raw_text)
        
        # 分割文本
        chunks = self.chunk_text(cleaned_text)
        
        logger.info(f"PDF处理完成: {pdf_path.name}, 生成 {len(chunks)} 个文本块")
        
        return {
            'file_name': pdf_path.name,
            'file_path': str(pdf_path),
            'success': True,
            'raw_text_length': len(raw_text),
            'cleaned_text_length': len(cleaned_text),
            'chunk_count': len(chunks),
            'chunks': chunks
        }
    
    def process_all_pdfs(self) -> List[Dict[str, any]]:
        """
        处理所有PDF文件
        
        Returns:
            所有处理结果的列表
        """
        pdf_files = self.get_pdf_files()
        if not pdf_files:
            logger.warning("未找到PDF文件")
            return []
        
        results = []
        for pdf_file in pdf_files:
            result = self.process_single_pdf(pdf_file)
            results.append(result)
        
        # 统计信息
        successful = sum(1 for r in results if r['success'])
        total_chunks = sum(r['chunk_count'] for r in results if r['success'])
        
        logger.info(f"处理完成: {successful}/{len(pdf_files)} 个文件成功, 共生成 {total_chunks} 个文本块")
        
        return results

if __name__ == "__main__":
    # 示例用法
    processor = DocumentProcessor()
    results = processor.process_all_pdfs()
    
    # 打印处理结果摘要
    for result in results:
        if result['success']:
            print(f"✓ {result['file_name']}: {result['chunk_count']} 个文本块")
        else:
            print(f"✗ {result['file_name']}: {result['error']}")
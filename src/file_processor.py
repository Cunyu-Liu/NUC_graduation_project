"""文件处理模块 - 支持聊天中的文件上传和分析
支持 PDF、Word、TXT、代码文件等格式
"""
import os
import io
import uuid
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# 尝试导入 PDF 解析
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# 尝试导入 Word 解析
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


@dataclass
class FileContent:
    """文件内容"""
    filename: str
    content_type: str
    content: str
    size: int
    file_hash: str
    metadata: Dict[str, Any]


class FileProcessor:
    """文件处理器"""
    
    # 支持的文件类型
    SUPPORTED_TYPES = {
        'text/plain': '.txt',
        'text/markdown': '.md',
        'text/x-python': '.py',
        'text/javascript': '.js',
        'text/html': '.html',
        'text/css': '.css',
        'application/json': '.json',
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/msword': '.doc',
        'text/x-java-source': '.java',
        'text/x-c': '.c',
        'text/x-c++': '.cpp',
    }
    
    # 最大文件大小 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self, upload_dir: str = "./output/chat_uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_hash(self, content: bytes) -> str:
        """生成文件哈希"""
        return hashlib.md5(content).hexdigest()
    
    def _save_file(self, content: bytes, filename: str) -> str:
        """保存文件到磁盘"""
        file_hash = self._generate_hash(content)
        ext = Path(filename).suffix
        saved_name = f"{file_hash}{ext}"
        saved_path = self.upload_dir / saved_name
        
        if not saved_path.exists():
            with open(saved_path, 'wb') as f:
                f.write(content)
        
        return str(saved_path)
    
    def _extract_pdf_text(self, content: bytes) -> str:
        """提取 PDF 文本"""
        if not PDF_AVAILABLE:
            return "[PDF 解析需要安装 PyPDF2: pip install PyPDF2]"
        
        try:
            pdf_file = io.BytesIO(content)
            reader = PyPDF2.PdfReader(pdf_file)
            text_parts = []
            
            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- 第 {i+1} 页 ---\n{page_text}")
                except Exception as e:
                    text_parts.append(f"[第 {i+1} 页解析失败: {e}]")
            
            return "\n\n".join(text_parts)
        except Exception as e:
            return f"[PDF 解析失败: {e}]"
    
    def _extract_docx_text(self, content: bytes) -> str:
        """提取 Word 文本"""
        if not DOCX_AVAILABLE:
            return "[Word 解析需要安装 python-docx: pip install python-docx]"
        
        try:
            doc_file = io.BytesIO(content)
            doc = docx.Document(doc_file)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            return f"[Word 解析失败: {e}]"
    
    def process_file(self, file_content: bytes, filename: str, content_type: str) -> FileContent:
        """
        处理上传的文件
        
        Args:
            file_content: 文件内容（bytes）
            filename: 原始文件名
            content_type: MIME 类型
            
        Returns:
            FileContent 对象
        """
        # 检查文件大小
        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValueError(f"文件太大，最大支持 {self.MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # 检查文件类型
        ext = self.SUPPORTED_TYPES.get(content_type)
        if not ext and '.' in filename:
            ext = Path(filename).suffix
        
        if not ext:
            ext = '.txt'  # 默认当作文本处理
        
        # 保存文件
        file_path = self._save_file(file_content, filename)
        file_hash = self._generate_hash(file_content)
        
        # 提取文本内容
        extracted_text = ""
        if content_type == 'application/pdf' or filename.endswith('.pdf'):
            extracted_text = self._extract_pdf_text(file_content)
        elif content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                              'application/msword'] or filename.endswith(('.docx', '.doc')):
            extracted_text = self._extract_docx_text(file_content)
        elif content_type.startswith('text/') or ext in ['.txt', '.md', '.py', '.js', '.json', '.java', '.c', '.cpp', '.html', '.css']:
            # 文本文件直接解码
            try:
                extracted_text = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    extracted_text = file_content.decode('gbk')
                except UnicodeDecodeError:
                    extracted_text = file_content.decode('utf-8', errors='ignore')
        else:
            # 其他类型，尝试作为文本处理
            try:
                extracted_text = file_content.decode('utf-8', errors='ignore')
            except:
                extracted_text = f"[二进制文件: {filename}]"
        
        # 截断过长的内容（保留前 20000 字符）
        if len(extracted_text) > 20000:
            extracted_text = extracted_text[:20000] + "\n\n[内容已截断，只显示前 20000 字符]"
        
        metadata = {
            'original_filename': filename,
            'saved_path': file_path,
            'file_size': len(file_content),
            'file_type': ext,
            'upload_time': datetime.now().isoformat()
        }
        
        return FileContent(
            filename=filename,
            content_type=content_type,
            content=extracted_text,
            size=len(file_content),
            file_hash=file_hash,
            metadata=metadata
        )
    
    def format_for_llm(self, file_content: FileContent) -> str:
        """
        将文件内容格式化为 LLM 可用的格式
        
        Args:
            file_content: 文件内容对象
            
        Returns:
            格式化后的文本
        """
        lines = [
            f"【上传文件: {file_content.filename}】",
            f"类型: {file_content.content_type}",
            f"大小: {file_content.size / 1024:.1f} KB",
            "",
            "【文件内容】",
            file_content.content,
            "【文件结束】"
        ]
        return "\n".join(lines)


# 全局处理器实例
_processor = None

def get_file_processor(upload_dir: str = "./output/chat_uploads") -> FileProcessor:
    """获取文件处理器实例（单例）"""
    global _processor
    if _processor is None:
        _processor = FileProcessor(upload_dir=upload_dir)
    return _processor


if __name__ == "__main__":
    # 测试
    processor = FileProcessor()
    
    # 测试文本文件
    test_content = b"Hello, World!\nThis is a test file."
    result = processor.process_file(test_content, "test.txt", "text/plain")
    print(f"文件名: {result.filename}")
    print(f"内容: {result.content[:100]}...")

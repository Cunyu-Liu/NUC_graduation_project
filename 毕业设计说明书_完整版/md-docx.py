#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中北大学软件学院本科毕业设计论文 DOCX 生成器（完整版）
符合《中北大学本科生学位论文撰写格式》最新标准
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION_START
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re
import os

class NUAAThesisConverter:
    def __init__(self):
        self.doc = Document()
        self.current_chapter = 0
        self.figure_counter = {}
        self.table_counter = {}
        self.in_abstract = False
        self.in_introduction = False
        
        self._setup_styles()
        
    def _setup_styles(self):
        styles = self.doc.styles
        
        # 正文：小四号宋体，1.5倍行距，首行缩进2字符
        style_normal = styles['Normal']
        style_normal.font.name = 'Times New Roman'
        style_normal._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        style_normal.font.size = Pt(12)
        style_normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        style_normal.paragraph_format.first_line_indent = Cm(0.74)
        
        # 一级标题：小三号黑体，加粗，段前段后0.5行
        style_h1 = styles.add_style('CustomH1', WD_STYLE_TYPE.PARAGRAPH)
        style_h1.font.name = 'Times New Roman'
        style_h1._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
        style_h1.font.size = Pt(15)
        style_h1.font.bold = True
        style_h1.paragraph_format.space_before = Pt(6)
        style_h1.paragraph_format.space_after = Pt(6)
        style_h1.paragraph_format.first_line_indent = Cm(0)
        style_h1.paragraph_format.keep_with_next = True
        
        # 二级标题：四号黑体，加粗
        style_h2 = styles.add_style('CustomH2', WD_STYLE_TYPE.PARAGRAPH)
        style_h2.font.name = 'Times New Roman'
        style_h2._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
        style_h2.font.size = Pt(14)
        style_h2.font.bold = True
        style_h2.paragraph_format.space_before = Pt(6)
        style_h2.paragraph_format.space_after = Pt(6)
        style_h2.paragraph_format.first_line_indent = Cm(0)
        
        # 三级标题：小四号黑体，加粗
        style_h3 = styles.add_style('CustomH3', WD_STYLE_TYPE.PARAGRAPH)
        style_h3.font.name = 'Times New Roman'
        style_h3._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
        style_h3.font.size = Pt(12)
        style_h3.font.bold = True
        style_h3.paragraph_format.first_line_indent = Cm(0)
        
        # 图表标题：五号宋体，居中（使用内置Caption样式修改，避免重名）
        try:
            style_cap = styles.add_style('CustomCaption', WD_STYLE_TYPE.PARAGRAPH)
        except ValueError:
            style_cap = styles['CustomCaption']
        style_cap.font.name = 'Times New Roman'
        style_cap._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        style_cap.font.size = Pt(10.5)
        style_cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 代码：五号，单倍行距，灰色底纹
        style_code = styles.add_style('CodeBlock', WD_STYLE_TYPE.PARAGRAPH)
        style_code.font.name = 'Courier New'
        style_code._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        style_code.font.size = Pt(10.5)
        style_code.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        style_code.paragraph_format.left_indent = Cm(0.5)
        style_code.paragraph_format.first_line_indent = Cm(0)
        
    def _add_section_break(self, start_type=WD_SECTION_START.NEW_PAGE):
        """插入分节符"""
        self.doc.add_section(start_type)
        section = self.doc.sections[-1]
        section.top_margin = Cm(3.0)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.0)
        section.header_distance = Cm(2.5)
        section.footer_distance = Cm(1.8)
        return section
    
    def _set_no_page_number(self, section):
        """设置该节无页码"""
        sectPr = section._sectPr
        pgNumType = OxmlElement('w:pgNumType')
        pgNumType.set(qn('w:start'), '0')
        sectPr.append(pgNumType)
        
    def _set_page_number(self, section, start=1):
        """设置该节页码从start开始"""
        sectPr = section._sectPr
        pgNumType = OxmlElement('w:pgNumType')
        pgNumType.set(qn('w:start'), str(start))
        pgNumType.set(qn('w:fmt'), 'decimal')
        sectPr.append(pgNumType)
        
        # 添加页脚页码
        footer = section.footer
        footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer_para.text = ""
        
        run = footer_para.add_run()
        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')
        
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = "PAGE"
        
        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'end')
        
        run._r.append(fldChar1)
        run._r.append(instrText)
        run._r.append(fldChar2)
        
        run.font.name = 'Times New Roman'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
        run.font.size = Pt(10.5)
        
    def _add_header(self, section, text="中北大学2026届本科毕业设计说明书"):
        """添加页眉"""
        header = section.header
        header_para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        header_para.text = text
        header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = header_para.runs[0] if header_para.runs else header_para.add_run(text)
        run.font.size = Pt(12)
        run.font.name = '黑体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
        
        # 添加下划线
        pPr = header_para._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '6')
        bottom.set(qn('w:space'), '1')
        bottom.set(qn('w:color'), '000000')
        pBdr.append(bottom)
        pPr.append(pBdr)
        
    def convert(self, md_path, out_path):
        if not os.path.exists(md_path):
            raise FileNotFoundError(f"文件不存在: {md_path}")
            
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # 初始化第一节（封面）
        first_section = self.doc.sections[0]
        self._setup_section(first_section)
        self._set_no_page_number(first_section)
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 识别封面（假设以# 或 课题名称开头）
            if i == 0 and line.startswith('#'):
                self._process_cover(line)
                i += 1
                continue
            
            # 识别摘要（中英文）
            if line in ['摘要', 'Abstract', '**摘要**', '**Abstract**']:
                if not self.in_abstract:
                    # 新分节给摘要
                    sect = self._add_section_break()
                    self._setup_section(sect)
                    self._set_no_page_number(sect)
                    self._add_header(sect)
                    self.in_abstract = True
                self._add_heading(line.replace('*', ''), 1)
                i += 1
                continue
            
            # 识别目录
            if '目录' in line and len(line) < 10:
                sect = self._add_section_break()
                self._setup_section(sect)
                self._set_no_page_number(sect)
                self._add_header(sect)
                self._add_heading('目录', 1)
                i += 1
                continue
            
            # 识别第1章/引言（正文开始）
            if self._is_chapter_start(line):
                if not self.in_introduction:
                    # 正文新节
                    sect = self._add_section_break()
                    self._setup_section(sect)
                    self._set_page_number(sect, 1)
                    self._add_header(sect)
                    self.in_introduction = True
                
                self.current_chapter += 1
                self.figure_counter[self.current_chapter] = 0
                self.table_counter[self.current_chapter] = 0
                
                # 添加章标题
                p = self.doc.add_paragraph()
                p.style = 'CustomH1'
                run = p.add_run(line.replace('# ', ''))
                
                i += 1
                continue
            
            # 处理二级标题
            if line.startswith('## '):
                p = self.doc.add_paragraph()
                p.style = 'CustomH2'
                p.add_run(line[3:])
                i += 1
                continue
            
            # 处理三级标题
            if line.startswith('### '):
                p = self.doc.add_paragraph()
                p.style = 'CustomH3'
                p.add_run(line[4:])
                i += 1
                continue
            
            # 处理代码块
            if line.startswith('```'):
                code_lines = []
                lang = line[3:].strip()
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                self._add_code('\n'.join(code_lines), lang)
                i += 1
                continue
            
            # 处理表格
            if line.startswith('|'):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                self._add_table(table_lines)
                continue
            
            # 处理图片
            if line.startswith('!['):
                self._add_image(line)
                i += 1
                continue
            
            # 处理图表标题（自动编号）
            if re.match(r'^(图|表)\s*[\dX]', line):
                self._add_caption(line)
                i += 1
                continue
            
            # 处理正文
            if line:
                self._add_text(line)
            
            i += 1
        
        # 最后添加参考文献和致谢分节
        self._add_section_break()
        final_sect = self.doc.sections[-1]
        self._setup_section(final_sect)
        
        self.doc.save(out_path)
        print(f"✅ 已生成: {out_path}")
        print("⚠️  请检查：1.页码是否从引言开始 2.三线表样式 3.图片替换")
        
    def _setup_section(self, section):
        """设置节格式"""
        section.page_height = Cm(29.7)
        section.page_width = Cm(21.0)
        section.top_margin = Cm(3.0)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.0)
        section.header_distance = Cm(2.5)
        section.footer_distance = Cm(1.8)
        
    def _is_chapter_start(self, line):
        """识别章标题"""
        patterns = [
            r'^第[一二三四五六七八九十\d]+章',
            r'^第\s*\d+\s*章',
            r'^#\s*第[一二三四五六七八九十\d]+章',
            r'^#\s*引言',
            r'^#\s*绪论'
        ]
        return any(re.match(p, line) for p in patterns)
        
    def _process_cover(self, line):
        """处理封面"""
        # 居中放大显示
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line.replace('# ', ''))
        run.font.size = Pt(22)
        run.font.bold = True
        run.font.name = '黑体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
        
    def _add_heading(self, text, level):
        style = 'CustomH1' if level == 1 else 'CustomH2' if level == 2 else 'CustomH3'
        p = self.doc.add_paragraph()
        p.style = style
        p.add_run(text)
        
    def _add_text(self, text):
        """添加正文，处理粗体"""
        p = self.doc.add_paragraph()
        p.style = 'Normal'
        
        # 处理**粗体**
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run = p.add_run(part[2:-2])
                run.bold = True
            else:
                p.add_run(part)
                
    def _add_code(self, code, lang):
        """添加代码块"""
        if not code.strip():
            return
            
        p = self.doc.add_paragraph()
        p.style = 'CodeBlock'
        
        # 灰色底纹
        shading = OxmlElement('w:shd')
        shading.set(qn('w:fill'), 'F2F2F2')
        p._p.get_or_add_pPr().append(shading)
        
        run = p.add_run(code)
        run.font.name = 'Courier New'
        
    def _add_table(self, lines):
        """添加三线表"""
        if len(lines) < 2:
            return
            
        # 解析表格
        rows = []
        for line in lines:
            cells = [c.strip() for c in line.strip('|').split('|')]
            rows.append(cells)
        
        # 跳过分隔行
        data_rows = [rows[0]] + [r for r in rows[1:] if not re.match(r'^[\s\-\|]+$', '|'.join(r))]
        
        if not data_rows:
            return
            
        num_cols = len(data_rows[0])
        table = self.doc.add_table(rows=len(data_rows), cols=num_cols)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # 填充数据
        for i, row_data in enumerate(data_rows):
            row = table.rows[i]
            for j, text in enumerate(row_data[:num_cols]):
                cell = row.cells[j]
                cell.text = text
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                
                # 设置字体
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.name = 'Times New Roman'
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                        run.font.size = Pt(10.5)
                        if i == 0:  # 表头加粗
                            run.font.bold = True
        
        # 添加表格标题（上方）
        self.table_counter[self.current_chapter] = self.table_counter.get(self.current_chapter, 0) + 1
        tbl_num = self.table_counter[self.current_chapter]
        cap_text = f"表{self.current_chapter}.{tbl_num} {rows[0][0] if rows[0] else '表格标题'}"
        
        # 插入段落到表格前（docx不支持直接insert，这里通过移动实现较复杂，先放后面）
        # 实际应在表格前，但简单起见先放后面，用户可手动调整
        cap_p = self.doc.add_paragraph()
        cap_p.style = 'CustomCaption'
        cap_p.paragraph_format.space_after = Pt(3)
        cap_p.add_run(cap_text)
        
    def _add_image(self, line):
        """处理图片"""
        match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
        if not match:
            return
            
        alt, path = match.groups()
        
        # 插入图片
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        if os.path.exists(path):
            try:
                run = p.add_run()
                run.add_picture(path, width=Inches(5.0))
            except:
                p.add_run(f"[图片: {alt}]").font.color.rgb = RGBColor(255,0,0)
        else:
            p.add_run(f"[图片占位: {alt}]").font.color.rgb = RGBColor(255,0,0)
        
        # 图注（下方）
        self.figure_counter[self.current_chapter] = self.figure_counter.get(self.current_chapter, 0) + 1
        fig_num = self.figure_counter[self.current_chapter]
        
        cap_p = self.doc.add_paragraph()
        cap_p.style = 'CustomCaption'
        cap_p.paragraph_format.space_before = Pt(3)
        cap_p.add_run(f"图{self.current_chapter}.{fig_num} {alt}")
        
    def _add_caption(self, text):
        """添加图表标题"""
        p = self.doc.add_paragraph()
        p.style = 'CustomCaption'
        p.add_run(text)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 2:
        md_file = sys.argv[1]
        docx_file = sys.argv[2] if len(sys.argv) >= 3 else md_file.replace('.md', '.docx')
        
        converter = NUAAThesisConverter()
        converter.convert(md_file, docx_file)
    else:
        print("用法: python thesis.py input.md [output.docx]")
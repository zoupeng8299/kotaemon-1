# test_docling_loader.py
from datetime import datetime
from pathlib import Path
import sys
import json
import os
from PyPDF2 import PdfReader, PdfWriter
import tempfile

# 添加检查和旋转函数
def check_and_auto_rotate_pdf(pdf_path):
    """
    检查PDF旋转情况并自动旋转（如有必要）
    
    Returns:
        tuple: (处理后的PDF路径, 旋转信息字典)
    """
    reader = PdfReader(pdf_path)
    rotations = {}
    needs_rotation = False
    
    # 检查每一页的旋转属性
    for i, page in enumerate(reader.pages):
        rotation = page.get('/Rotate', 0) % 360
        rotations[i+1] = rotation
        if rotation != 0:
            needs_rotation = True
    
    # 打印旋转信息
    print("\n===== PDF旋转状态检查 =====")
    for page_num, rotation in rotations.items():
        print(f"页面 {page_num}: {rotation}°")
    
    # 如果有旋转，自动处理
    if needs_rotation:
        print("检测到PDF页面有旋转，正在处理...")
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            rotation = rotations[i+1]
            if rotation != 0:
                # 复制页面并设置旋转为0
                page_copy = writer.add_page(page)
                page_copy.rotate(0)  # 重置旋转
            else:
                writer.add_page(page)
        
        with open(temp_path, "wb") as f:
            writer.write(f)
        
        print(f"已修正PDF旋转问题，临时文件: {temp_path}")
        return temp_path, rotations
    else:
        print("PDF页面未设置旋转属性")
        return pdf_path, rotations
    
def convert_posix_paths(obj):
    """将元数据中的PosixPath对象转换为字符串"""
    if isinstance(obj, dict):
        return {k: convert_posix_paths(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_posix_paths(item) for item in obj]
    elif isinstance(obj, Path):
        return str(obj)
    else:
        return obj
    
# 添加项目路径到 Python 路径
sys.path.append("/Volumes/KSdisk/zoupeng project/ai_projects/GitHub/Cinnamon/kotaemon")

from libs.kotaemon.kotaemon.loaders.docling_loader import DoclingReader
def test_docling_loader(pdf_path: str):
    """
    测试 DoclingLoader 的功能
    
    Args:
        pdf_path: PDF 文件路径
    """
    print(f"正在测试 DoclingLoader，文件路径: {pdf_path}")

    # 检查PDF旋转状态并自动处理
    pdf_path, rotation_info = check_and_auto_rotate_pdf(pdf_path)
    
    # 创建 DoclingReader 实例 - 使用正确的初始化方式
    reader = DoclingReader()
    
    # 修改 reader 实例的属性而不是传递 options
    reader.figure_friendly_filetypes = [".pdf", ".jpeg", ".jpg", ".png", ".bmp", ".tiff", ".heif", ".tif"]
    
    # 手动设置 options 属性（如果 BaseReader 支持）
    reader._options = {
        "docling_options": {
            "ocr": {
                "force_full_page_ocr": True,
                "lang": ["ch_sim", "en"],
                "det_limit_side_len": 2560,  # 增加最大检测尺寸
                "rec_batch_num": 6           # 增加批处理能力
            },
            "pipeline_options": {
                "do_ocr": True,
                "do_table_structure": True,
                "table_structure_options": {
                    "do_cell_matching": True
                },
                "ocr_model_params": {  
                    "det_model_name": "ch_PP-OCRv3_det_infer",
                    "rec_model_name": "ch_PP-OCRv3_rec_infer", 
                    "cls_model_name": "ch_ppocr_mobile_v2.0_cls_infer",
                    "use_angle_cls": True,
                    "box_thresh": 0.15,         # 进一步降低检测阈值
                    "unclip_ratio": 2.2,        # 进一步增大比例
                    "text_score_thresh": 0.5,   # 降低文本置信度阈值
                    "use_dilation": True        # 使用膨胀操作增强文本区域
                }
            },
            "pdf": {
                "image_settings": {
                    "max_size": 3000,        # 增加最大尺寸
                    "min_size": 50,
                    "quality": 100,           # 提高质量
                    "dpi": 400               # 提高 DPI
                },
                "preprocessing": {
                    "denoise": False,
                    "contrast_enhance": True,
                    "normalize": True,
                    "deskew": True,         # 校正倾斜
                    "sharpen": True,
                    "auto_rotate": True,    # 添加自动旋转
                    "page_orientation": "auto"  # 自动检测页面方向
                },
                "table_options": {
                    "min_cells": 4,
                    "structure_mode": True
                }
            }
        }
    }   
    
    # 打印配置信息
    print("OCR 配置:", json.dumps(reader._options["docling_options"]["ocr"], ensure_ascii=False))
    print("管道配置:", json.dumps(reader._options["docling_options"]["pipeline_options"], ensure_ascii=False))

    # 检查 PDF 页数和大小
    pdf = PdfReader(pdf_path)
    print(f"PDF 信息: {len(pdf.pages)} 页, 文件大小: {os.path.getsize(pdf_path)/1024/1024:.2f}MB")

    # 加载文档
    print("开始处理文档...")
    docs = reader.load_data(pdf_path)
    print(f"处理完成，共提取 {len(docs)} 个文档片段")
    
    # 分析结果
    text_docs = [doc for doc in docs if doc.metadata.get("type") != "image" and doc.metadata.get("type") != "table"]
    table_docs = [doc for doc in docs if doc.metadata.get("type") == "table"]
    image_docs = [doc for doc in docs if doc.metadata.get("type") == "image"]
    
    print(f"文本片段: {len(text_docs)}")
    print(f"表格片段: {len(table_docs)}")
    print(f"图片片段: {len(image_docs)}")
    
    # 在测试脚本中添加，显示每页提取的文本长度
    for i, doc in enumerate(text_docs):
        print(f"页面 {i+1} 提取文本长度: {len(doc.text)} 字符")
    
    # 提取PDF文件名(不含扩展名)
    pdf_filename = Path(pdf_path).stem
    
    # 保存部分结果示例
    output_dir = Path("docling_test_output")
    output_dir.mkdir(exist_ok=True)
    
    # 使用PDF文件名作为输出文件的前缀
    # 保存所有文本片段
    if text_docs:
        with open(output_dir / f"{pdf_filename}_text.txt", "w", encoding="utf-8") as f:
            f.write("# 文档全文提取结果\n\n")
            for i, doc in enumerate(text_docs):
                f.write(f"## 第 {i+1} 页\n\n")
                f.write(doc.text)
                f.write("\n\n---\n\n")
            
            f.write("# 元数据\n\n")
            for i, doc in enumerate(text_docs):
                f.write(f"## 第 {i+1} 页元数据\n\n")
                safe_metadata = convert_posix_paths(doc.metadata)
                f.write(json.dumps(safe_metadata, ensure_ascii=False, indent=2))
                f.write("\n\n")
                
    # 保存所有表格
    if table_docs:
        with open(output_dir / f"{pdf_filename}_table.md", "w", encoding="utf-8") as f:
            f.write("# 文档表格提取结果\n\n")
            for i, doc in enumerate(table_docs):
                f.write(f"## 表格 {i+1}\n\n")
                f.write(doc.text)
                f.write("\n\n---\n\n")
            
            f.write("# 表格元数据\n\n")
            for i, doc in enumerate(table_docs):
                f.write(f"## 表格 {i+1} 元数据\n\n")
                safe_metadata = convert_posix_paths(doc.metadata)
                f.write(json.dumps(safe_metadata, ensure_ascii=False, indent=2))
                f.write("\n\n")

    # 保存所有图片
    if image_docs:
        with open(output_dir / f"{pdf_filename}_image.txt", "w", encoding="utf-8") as f:
            f.write("# 文档图片提取结果\n\n")
            for i, doc in enumerate(image_docs):
                f.write(f"## 图片 {i+1}\n\n")
                f.write(doc.text)
                f.write("\n\n---\n\n")
            
            f.write("# 图片元数据\n\n")
            for i, doc in enumerate(image_docs):
                f.write(f"## 图片 {i+1} 元数据\n\n")
                filtered_metadata = {k: v for k, v in doc.metadata.items() 
                                if k != "image_origin"}
                safe_metadata = convert_posix_paths(filtered_metadata)
                f.write(json.dumps(safe_metadata, ensure_ascii=False, indent=2))
                f.write("\n\n")    
                
    # 还可以创建一个概述文件
    with open(output_dir / f"{pdf_filename}_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"文档：{pdf_path}\n")
        f.write(f"处理时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"提取结果统计：\n")
        f.write(f"- 总片段数: {len(docs)}\n")
        f.write(f"- 文本片段: {len(text_docs)}\n")
        f.write(f"- 表格片段: {len(table_docs)}\n")
        f.write(f"- 图片片段: {len(image_docs)}\n")
            
    print(f"\n测试结果已保存到 {output_dir} 目录，文件前缀: {pdf_filename}")

if __name__ == "__main__":
    # 测试一个包含中文的 PDF 文件
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = input("请输入要测试的 PDF 文件路径: ")
        
    test_docling_loader(pdf_path)
# test_docling_loader.py
from datetime import datetime
from pathlib import Path
import sys
import json
import os
from PyPDF2 import PdfReader, PdfWriter
import tempfile
from PIL import Image
import io

# 在模块级别创建一个全局列表
temp_files_to_cleanup = []

def convert_image_to_pdf(img_path):
    """
    将图像文件转换为临时PDF文件
    
    Args:
        img_path: 图像文件路径
        
    Returns:
        str: 临时PDF文件路径
    """
    try:
        img = Image.open(img_path)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name    
        # 添加到全局列表
        temp_files_to_cleanup.append(temp_path)  # 添加到全局列表
        
        # 转换图像为RGB模式(CMYK等模式可能会导致问题)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 保存为PDF文件
        img.save(temp_path, 'PDF', resolution=400.0)
        print(f"已将图像转换为PDF，临时文件: {temp_path}")
        return temp_path
        
    except Exception as e:
        print(f"转换图像到PDF时出错: {e}")
        return img_path
    
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
        # 添加到全局列表
        temp_files_to_cleanup.append(temp_path)  # 添加到全局列表
        
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
def test_docling_loader(file_path: str):
    """测试 DoclingLoader 处理不同文件类型的能力"""
    # 保存所有创建的临时文件路径
    temp_files = []
    
    print(f"正在测试 DoclingLoader，文件路径: {file_path}")
    # 根据文件类型进行不同处理
    processed_path = file_path
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.pdf':
        # PDF文件 - 检查旋转
        processed_path, rotation_info = check_and_auto_rotate_pdf(file_path)
        if processed_path != file_path:
            temp_files.append(processed_path)  # 记录临时文件
        pdf = PdfReader(processed_path)
        print(f"PDF信息: {len(pdf.pages)}页, 文件大小: {os.path.getsize(processed_path)/1024/1024:.2f}MB")
    
    elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
        # 图像文件 - 转换为临时PDF以获得更好的OCR效果
        processed_path = convert_image_to_pdf(file_path)
        if processed_path != file_path:     # 如果转换成功
            temp_files.append(processed_path)  # 记录临时文件
            pdf = PdfReader(processed_path)
            print(f"图像已转换为PDF, 页数: {len(pdf.pages)}, 文件大小: {os.path.getsize(processed_path)/1024/1024:.2f}MB")
        else:
            print(f"文件类型: {file_ext}, 文件大小: {os.path.getsize(file_path)/1024/1024:.2f}MB")
    else:
        # 其他文件类型
        print(f"文件类型: {file_ext}, 文件大小: {os.path.getsize(file_path)/1024/1024:.2f}MB")
     
    # 从 flowsettings.py 获取配置
    try:
        # 导入 flowsettings 模块
        sys.path.insert(0, "/Volumes/KSdisk/zoupeng project/ai_projects/GitHub/Cinnamon/kotaemon")
        import flowsettings
        
        # 查找包含 DoclingLoader 的配置
        docling_config = None
        for i, index_config in enumerate(flowsettings.KH_INDICES):
            if "config" in index_config and "loader_config" in index_config["config"]:
                loader_config = index_config["config"]["loader_config"]
                if loader_config.get("__type__") == "kotaemon.loaders.DoclingLoader":
                    print(f"找到了 DoclingLoader 配置，位于 KH_INDICES[{i}]")
                    docling_config = loader_config
                    break
        
        if not docling_config:
            print("警告: 在 flowsettings.py 中未找到 DoclingLoader 配置，使用默认配置")
    except Exception as e:
        print(f"加载 flowsettings.py 配置时出错: {e}")
        print("使用默认配置")
        docling_config = None
    
    # 创建 DoclingReader 实例
    reader = DoclingReader()

    # 特别确保这些参数被设置
    reader.figure_friendly_filetypes = [".pdf", ".jpeg", ".jpg", ".png", ".bmp", ".tiff", ".heif", ".tif"]
    reader.max_figure_to_caption = 100  # 设置最大图片说明数量
        
    # 应用从 flowsettings.py 获取的配置
    if docling_config:
        # 确保 figure_friendly 被正确设置
        docling_config["figure_friendly"] = True
        reader._options = {"docling_options": docling_config.get("docling_options", {})}

        print("使用 flowsettings.py 中的配置")
        # 检查配置完整性
        print("\n配置检查:")
        print("- figure_friendly_filetypes:", "存在" if "figure_friendly_filetypes" in docling_config else "缺失")
        print("- max_figure_to_caption:", "存在" if "max_figure_to_caption" in docling_config else "缺失")
        print("- docling_options:", "存在" if "docling_options" in docling_config else "缺失")
        
        if "docling_options" in docling_config:
            docling_opts = docling_config["docling_options"]
            print("  - ocr:", "存在" if "ocr" in docling_opts else "缺失")
            print("  - pipeline_options:", "存在" if "pipeline_options" in docling_opts else "缺失")
            print("  - pdf:", "存在" if "pdf" in docling_opts else "缺失")
        
        # 设置文件类型
        if "figure_friendly_filetypes" in docling_config:
            reader.figure_friendly_filetypes = docling_config["figure_friendly_filetypes"]
        
        # 设置最大图片说明数量
        if "max_figure_to_caption" in docling_config:
            reader.max_figure_to_caption = docling_config["max_figure_to_caption"]
        
        # 设置 VLM 端点
        if "vlm_endpoint" in docling_config:
            reader.vlm_endpoint = docling_config["vlm_endpoint"]
        
        # 设置 docling_options
        reader._options = {"docling_options": docling_config.get("docling_options", {})}
    else:
        # 使用默认配置
        reader.figure_friendly_filetypes = [".pdf", ".jpeg", ".jpg", ".png", ".bmp", ".tiff", ".heif", ".tif"]
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
                    },
                    "image_extraction": {
                        "enabled": True,
                        "min_size": 100,  # 最小图片尺寸(像素)
                        "similarity_threshold": 0.8  # 降低阈值以捕获更多图片
                    }
                },
                "image": {
                    "preprocessing": {
                        "enhance_contrast": True,
                        "sharpen": True,
                        "denoise": False,
                        "normalize": True
                    },
                    "ocr_params": {
                        "force_full_page_ocr": True
                    }
                }
            },
            "figure_friendly": True  # 设置为选项而不是属性
        }   
        
    # 打印配置信息
    print("\n===== 配置来源检查 =====")
    config_source = reader._options.get("docling_options", {}).get("config_source", "默认配置")
    print(f"配置来源: {config_source}")

    print("OCR 配置:", json.dumps(reader._options["docling_options"]["ocr"], ensure_ascii=False))
    print("管道配置:", json.dumps(reader._options["docling_options"]["pipeline_options"], ensure_ascii=False))

    # 仅对PDF文件执行这个检查 - 添加条件判断
    if file_ext.lower() == '.pdf':
        # 检查 PDF 页数和大小
        pdf = PdfReader(file_path)
        print(f"PDF 信息: {len(pdf.pages)} 页, 文件大小: {os.path.getsize(file_path)/1024/1024:.2f}MB")

    # 加载文档
    print("开始处理文档...")
    docs = reader.load_data(file_path if processed_path == file_path else processed_path)
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
    
    # 提取文件名(不含扩展名)
    file_filename = Path(file_path).stem  # 改为 file_filename，而不是 pdf_filename
        
    # 保存部分结果示例
    output_dir = Path("docling_test_output")
    output_dir.mkdir(exist_ok=True)
        
    # 使用文件名作为输出文件的前缀
    # 保存所有文本片段
    if text_docs:
        with open(output_dir / f"{file_filename}_text.txt", "w", encoding="utf-8") as f:
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
        with open(output_dir / f"{file_filename}_table.md", "w", encoding="utf-8") as f:
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
        with open(output_dir / f"{file_filename}_image.txt", "w", encoding="utf-8") as f:
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
    with open(output_dir / f"{file_filename}_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"文档：{file_path}\n")
        f.write(f"处理时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"提取结果统计：\n")
        f.write(f"- 总片段数: {len(docs)}\n")
        f.write(f"- 文本片段: {len(text_docs)}\n")
        f.write(f"- 表格片段: {len(table_docs)}\n")
        f.write(f"- 图片片段: {len(image_docs)}\n")
            
    print(f"\n测试结果已保存到 {output_dir} 目录，文件前缀: {file_filename}")

    # 清理临时文件
    print("\n测试结束，清理临时文件...")
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
            print(f"已删除临时文件: {temp_file}")
        except Exception as e:
            print(f"删除临时文件失败 {temp_file}: {e}")
    print("测试完成")        
            
if __name__ == "__main__":
    # 测试一个包含中文的 PDF 文件
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("请输入要测试的文件路径: ")
        
    try:
        test_docling_loader(file_path)
    finally:
        # 无论测试是否成功，都清理临时文件
        print("\n程序结束，清理临时文件...")
        for temp_file in temp_files_to_cleanup:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"已删除临时文件: {temp_file}")
            except Exception as e:
                print(f"删除临时文件失败 {temp_file}: {e}")
        print("程序完成")
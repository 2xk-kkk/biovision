import os
import shutil
from utils.response import ApiResponse

EXAM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "exams")
EXTERNAL_DIR = r"D:\biology_exams"

def get_exam_list():
    exams = []
    if not os.path.exists(EXAM_DIR):
        return ApiResponse.error(msg="试卷目录不存在")
    
    try:
        for item in os.listdir(EXAM_DIR):
            item_path = os.path.join(EXAM_DIR, item)
            if os.path.isdir(item_path):
                files = []
                for file_name in os.listdir(item_path):
                    file_path = os.path.join(item_path, file_name)
                    if os.path.isfile(file_path):
                        file_ext = os.path.splitext(file_name)[1].lower()
                        files.append({
                            "name": file_name,
                            "path": file_path,
                            "extension": file_ext,
                            "size": os.path.getsize(file_path)
                        })
                exams.append({
                    "name": item,
                    "files": files
                })
        return ApiResponse.success(data=exams)
    except Exception as e:
        return ApiResponse.error(msg=f"读取试卷列表失败: {str(e)}")

def get_exam_file(file_path):
    if not os.path.exists(file_path):
        return ApiResponse.error(msg="文件不存在")
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        return content
    except Exception as e:
        return ApiResponse.error(msg=f"读取文件失败: {str(e)}")

def upload_exam_file(category: str, file_name: str, file_content: bytes):
    try:
        if not os.path.exists(EXAM_DIR):
            os.makedirs(EXAM_DIR)
        
        category_path = os.path.join(EXAM_DIR, category)
        if not os.path.exists(category_path):
            os.makedirs(category_path)
        
        file_path = os.path.join(category_path, file_name)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return ApiResponse.success(data={"file_path": file_path})
    except Exception as e:
        return ApiResponse.error(msg=f"上传文件失败: {str(e)}")

def import_from_external():
    if not os.path.exists(EXTERNAL_DIR):
        return ApiResponse.error(msg="外部试卷目录不存在")
    
    try:
        imported_count = 0
        for item in os.listdir(EXTERNAL_DIR):
            item_path = os.path.join(EXTERNAL_DIR, item)
            if os.path.isdir(item_path):
                target_path = os.path.join(EXAM_DIR, item)
                if os.path.exists(target_path):
                    continue
                
                shutil.copytree(item_path, target_path)
                file_count = len([f for f in os.listdir(target_path) if os.path.isfile(os.path.join(target_path, f))])
                imported_count += file_count
        
        return ApiResponse.success(data={"imported_count": imported_count}, msg=f"成功导入 {imported_count} 个文件")
    except Exception as e:
        return ApiResponse.error(msg=f"导入文件失败: {str(e)}")

def delete_exam_file(file_path: str):
    if not os.path.exists(file_path):
        return ApiResponse.error(msg="文件不存在")
    
    if not file_path.startswith(EXAM_DIR):
        return ApiResponse.error(msg="无权删除此文件")
    
    try:
        os.remove(file_path)
        return ApiResponse.success(msg="删除成功")
    except Exception as e:
        return ApiResponse.error(msg=f"删除文件失败: {str(e)}")
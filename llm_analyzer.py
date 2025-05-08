from openai import OpenAI
import os
from typing import Optional
from dotenv import load_dotenv  # 新增导入

# 加载.env文件
load_dotenv()  # 自动从.env或环境变量读取

def analyze_transcript(
    user_prompt_file: str = "user_prompt.txt", # 用户输入的说话人日志   
    system_prompt_file: str = os.getenv("SYSTEM_PROMPT_PATH"), # 系统提示词
    output_file: str = "meeting-analysis.md" # 分析结果输出路径
) -> str:
    
    """分析会议转录文本并生成报告
    
    Args:
        user_prompt_file (str): 用户提示词文件路径，包含会议基本信息和转录文本
        system_prompt_file (str): 系统提示词模板文件路径，定义分析框架
        output_file (str): 分析结果输出文件路径(.md格式)
        
    Returns:
        str: 生成的会议分析报告内容
        
    Raises:
        FileNotFoundError: 当提示词文件不存在时抛出
        RuntimeError: API调用失败时抛出
    """
    
    # 读取系统提示词
    try:
        with open(system_prompt_file, 'r', encoding='utf-8') as f:
            system_prompt = f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"系统提示词文件 {system_prompt_file} 不存在")

    # 读取用户输入内容
    try:
        with open(user_prompt_file, 'r', encoding='utf-8') as f:
            user_prompt = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"用户输入文件 {user_prompt_file} 不存在")

    # 直接使用dotenv管理的环境变量
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("请在.env文件中配置DEEPSEEK_API_KEY")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1
        )
        analysis_result = response.choices[0].message.content
        
        # 保存带上下文的Markdown报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(analysis_result)

        print(f"分析结果已保存到 {output_file}")
        return analysis_result

    except Exception as e:
        error_msg = f"API调用失败: {str(e)}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 分析错误\n{error_msg}")
        return error_msg

if __name__ == "__main__":
    try:
        result = analyze_transcript()
        print("=== 分析结果 ===")
        print(result)
    except Exception as e:
        print(f"执行失败: {str(e)}")
    
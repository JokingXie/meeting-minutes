from openai import OpenAI
from typing import Optional
from dotenv import load_dotenv
import os

# 加载.env文件
load_dotenv("/home/gmcc/workspace/meeting-minutes-v2/.env", override=True)

# TODO: 修改 Concise 大纲模板提示词。补充修改 General 通用模板提示词。

def analyze_transcript(
    user_prompt_path: str = "user_prompt.txt",
    general_system_prompt: str = os.getenv("GENERAL_SYSTEM_PROMPT_PATH"),
    concise_system_prompt: str = os.getenv("CONCISE_SYSTEM_PROMPT_PATH")
) -> dict:
    
    """
    分析会议转录文本，生成含有通用报告、大纲报告的字典。

    :param user_prompt_path: 用户提示词路径（补充信息+转译内容）
    :param general_system_prompt: 通用模板系统提示词
    :param concise_system_prompt: 大纲模板系统提示词
    :return {"general_report": ..., "concise_report": ...}
    """
    
    # 读取系统提示词
    try:
        with open(general_system_prompt, 'r', encoding='utf-8') as f:
            general_prompt = f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"系统提示词文件 {general_system_prompt} 不存在")
    
    try:
        with open(concise_system_prompt, 'r', encoding='utf-8') as f:
            concise_prompt = f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"系统提示词文件 {concise_system_prompt} 不存在")

    # 读取用户输入内容
    try:
        with open(user_prompt_path, 'r', encoding='utf-8') as f:
            user_prompt = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"用户输入文件 {user_prompt_path} 不存在")

    # LLM 分析
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("请在.env文件中配置OPEN_API_KEY")

    base_url = os.getenv("BASE_URL")
    if not base_url:
        raise RuntimeError("请在.env文件中配置BASE_URL")

    # 生成报告
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        response = client.chat.completions.create(
            model="Qwen2.5-32B-Instruct",
            messages=[
                {"role": "system", "content": general_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1
        )
        general_result = response.choices[0].message.content


        response = client.chat.completions.create(
            model="Qwen2.5-32B-Instruct",
            messages=[
                {"role": "system", "content": concise_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1
        )
        concise_result = response.choices[0].message.content

    except Exception as e:
        error_msg = f"API调用失败: {str(e)}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 分析错误\n{error_msg}")
        return error_msg

    result = {"general_report": general_result, "concise_report": concise_result}
    return result

if __name__ == "__main__":
    try:
        result = analyze_transcript()
        print("=== 分析结果 ===")
        print(result)
    except Exception as e:
        print(f"执行失败: {str(e)}")
    
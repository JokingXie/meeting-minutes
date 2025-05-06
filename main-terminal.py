from speaker_distinction import SpeakerDistinction
from speaker_transcript import SpeakerTranscript
from llm_analyzer import analyze_transcript
import os

def generate_user_prompt(transcript_path: str) -> str:
    """生成用户提示词并保存到文件"""
    # 读取转录内容
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    
    # 获取用户输入的发言人筛选条件
    print("\n请输入对应的发言人")
    speakers = input("对应的说话人分别为: ")
    
    # 构建用户提示词  
    prompt_content = f"{transcript}\n\n{speakers}"
    
    # 保存到文件
    with open("user_prompt.txt", 'w', encoding='utf-8') as f:
        f.write(prompt_content)
    
    return prompt_content

def main_workflow(input_wav: str):
    """主处理流程"""
    try:
        # 阶段1：说话人识别
        print("\n[1/4] 说话人识别")
        audio_processor = SpeakerDistinction()
        diarization_result = audio_processor.process_audio(input_wav)

        # 阶段2：转译会议记录
        print("[2/4] 转译会议记录")
        transcript = SpeakerTranscript().merge_speaker_segments(diarization_result, input_wav)
        
        # 保存原始记录
        transcript_path = "meeting_transcript.txt"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(transcript))

        # 阶段3：输入说话人信息
        print("[3/4] 输入说话人信息")
        try:
            preview = SpeakerTranscript().preview_transcript(transcript)
        except Exception as e:
            preview = f"预览生成失败: {str(e)}\n原始内容前3行:\n" + "\n".join(transcript[:3])
        print("\n=== 内容预览（每个发言人前2句）===")
        print(preview)

        # 用户输入说话人信息
        generate_user_prompt(transcript_path)

        # 阶段4：生成会议纪要
        print("[4/4] 生成会议纪要")
        analysis_result = analyze_transcript(
            user_prompt_file="user_prompt.txt",
            output_file="meeting_analysis.md"
        )
        
        print("\n输出文件:")
        print(f"- 原始记录: {transcript_path}")
        print(f"- 分析报告: meeting_analysis.md")
        print("\n结果预览：")
        print(analysis_result[:500] + "...")  # 限制预览长度
        return True

    except Exception as e:
        print(f"\n处理错误: {type(e).__name__}")
        print(f"详细信息: {str(e)}")
        return False

if __name__ == "__main__":
    input_file = "/app/sample-diarization-test.wav"
    if main_workflow(input_file):
        print("\n会议纪要生成成功")
    else:
        print("\n会议纪要生成失败")
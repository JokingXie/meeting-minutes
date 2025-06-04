import gradio as gr
from speaker_distinction import SpeakerDistinction
from speaker_transcript import SpeakerTranscript
from llm_analyzer import analyze_transcript
import os

# 初始化处理模块
distinction_processor = SpeakerDistinction()
transcript_processor = SpeakerTranscript()

def process_audio(audio_file):
    """处理流程封装（修正输出格式）"""
    if not audio_file:
        raise gr.Error("请先上传音频文件")
    
    # 1. 说话人分离
    diarization_result = distinction_processor.process_audio(audio_file)
    
    # 2. 生成转录文本
    transcript_list = transcript_processor.merge_speaker_segments(diarization_result, audio_file)
    preview = transcript_processor.preview_transcript(transcript_list)
    
    # 返回三个独立变量（对应三个输出组件）
    return preview, "\n".join(transcript_list), audio_file

def generate_report(transcript, speakers, meeting_time, meeting_place, audio_file):
    """改进后的报告生成函数"""
    if not speakers:
        raise gr.Error("请输入说话人信息")
    if not meeting_time:
        raise gr.Error("请输入会议时间")
    
    # 保存转录文件
    with open("meeting_transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript)
    
    # 生成包含会议信息的提示词
    prompt_content = f"""会议时间：{meeting_time}
会议地点：{meeting_place}
与会人员：{speakers}

会议记录：
{transcript}"""
    
    with open("user_prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt_content)
    
    # 执行分析
    analysis_result = analyze_transcript(
        user_prompt_file="user_prompt.txt",
        output_file="meeting_analysis.md"
    )
    
    return analysis_result, "meeting_analysis.md"

# Gradio界面构建
with gr.Blocks(title="会议纪要生成系统") as demo:
    gr.Markdown("## 🎙️ 会议智能分析系统")
    
    # 状态变量
    transcript_state = gr.State()
    audio_state = gr.State()
    
    with gr.Tab("会议处理"):
        with gr.Row(equal_height=True):
            with gr.Column(scale=1):  # 设置较小的比例
                audio_input = gr.Audio(scale=10, type="filepath", label="上传会议录音")
                upload_btn = gr.Button(scale=1, value="开始处理", variant="primary")
                
            with gr.Column(scale=6):  # 设置较大的比例
                preview_output = gr.Textbox(label="内容预览", lines=25, min_width=600)  # 增加行数和最小宽度    
            
        with gr.Row(equal_height=True):

            with gr.Column(scale=1):            
                # 添加提示信息
                gr.Markdown("""
                <div style="color: #ff8c00; background-color: #fff4e6; padding: 10px; border-radius: 5px; margin-bottom: 10px; height: 100%;">
                ⚠️ 请等待内容预览生成成功，输入补充信息后，再点击"生成报告"按钮。
                </div>
                """)  

                process_btn = gr.Button(scale=1, value="生成报告", variant="primary")

            with gr.Row(scale=4):
                speaker_input = gr.Textbox(scale=3, label="发言人信息", placeholder="请按序输入对应的发言人信息")
                meeting_time = gr.Textbox(scale=1, label="会议时间", placeholder="如：2024年9月19日 星期四 10:00")
                meeting_place = gr.Textbox(scale=1, label="会议地点", placeholder="例如：会议室302")

        with gr.Tab("大纲报告"):
            concise_report_output = gr.Markdown(label="大纲报告")
            concise_download = gr.File(label="下载报告")
        
        with gr.Tab("通用报告"):
            general_report_output = gr.Markdown(label="通用报告")
            general_download = gr.File(label="下载报告")

    # 事件绑定
    upload_btn.click(
        process_audio,
        inputs=audio_input,
        outputs=[preview_output, transcript_state, audio_state]
    )
    
    process_btn.click(
        generate_report,
        inputs=[transcript_state, speaker_input, meeting_time, meeting_place, audio_state],
        outputs=[concise_report_output, general_report_output, concise_download, general_download]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
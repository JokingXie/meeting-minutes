import gradio as gr
import os
import dotenv
from pydub import AudioSegment

from distinguish_speaker import clip_audio, distinguish_speaker
from add_punctuation import add_punctuation
from separate_document import separate_document
from transcribe_audio import transcribe_audio, format_transcription_to_text
from analyze_transcript import analyze_transcript

# 初始化处理模块


def process_audio(raw_audio_path):
    """
    处理传入的音频：
        1. 统一转换为 .wav 格式
        2. 调用 distinguish_speaker.py 生成说话人日志
        3. 调用 transcribe_audio.py 生成转译结果
        4. 对转译结果进行处理，生成预览、转译原文、.wav 音频路径

    :param raw_audio_path: 传入的音频路径
    :return: preview, transcription, processed_audio_path
    """
    if not raw_audio_path:
        raise gr.Error("请先上传音频文件")
    
    # 如果不是 .wav 格式，则进行转换
    file_name, file_ext = os.path.splitext(raw_audio_path)
    processed_audio_path = raw_audio_path
    
    if file_ext.lower() != ".wav":
        wav_path = f"{file_name}.wav"
        print(f"Converting {raw_audio_path} to {wav_path}...")
        try:
            sound = AudioSegment.from_file(raw_audio_path)
            # 对于 pydub，可以设置采样率和通道数以符合模型要求，这里暂时只转换格式
            sound.export(wav_path, format="wav")
            processed_audio_path = wav_path
        except Exception as e:
            raise gr.Error(f"音频文件转换失败: {e}")
            
    # 1. 生成说话人日志
    raw_diarization = distinguish_speaker(processed_audio_path)
    
    # 2. 生成转译结果
    transcription_result = transcribe_audio(processed_audio_path, raw_diarization)

    # 3. 生成预览和转译原文
    k = int(os.getenv("TRANSCRIPTION_PREVIEW_WORDS", "100"))  # 预览的字符数，默认100
    speaker_texts = {}
    for _, _, speaker, text in transcription_result.get("result", []):
        if speaker not in speaker_texts:
            speaker_texts[speaker] = ""
        speaker_texts[speaker] += text
    
    preview_lines = []
    # 按 speaker 名称排序，确保预览输出顺序一致
    for speaker in sorted(speaker_texts.keys()):
        preview_lines.append(f"{speaker}：")
        preview_lines.append(speaker_texts[speaker][:k] + ("..." if len(speaker_texts[speaker]) > k else ""))
        preview_lines.append("")
    
    preview = "\n".join(preview_lines)

    transcript_text = format_transcription_to_text(transcription_result)

    return preview, transcript_text, processed_audio_path

def generate_report(meeting_time, meeting_place, transcript, speakers):
    """
    根据补充信息+会议转译生成通用、大纲形式的报告。

    :param meeting_time: 会议时间
    :param meeting_place: 会议地点
    :param transcript: 会议转译内容
    :param speakers: 说话人顺序信息
    :return general_result, concise_result, "general_report.md", "concise_report.md" （.md报告下载路径）
    """
    if not speakers:
        raise gr.Error("请输入说话人信息")
    if not meeting_time:
        raise gr.Error("请输入会议时间")
    
    # 保存转录文件
    with open("meeting_transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript)
    
    # 生成包含会议信息的提示词
    prompt_content = (
        f"<会议时间>{meeting_time}</会议时间>\n"
        f"<会议地点>{meeting_place}</会议地点>\n"
        f"<与会人员>{speakers}</与会人员>\n"
        f"<会议记录>{transcript}</会议记录>"
    )
    
    with open("user_prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt_content)
    
    # 执行分析
    analysis_result = analyze_transcript(
        user_prompt_path="user_prompt.txt"
    )

    general_result = analysis_result.get("general_report", "")
    concise_result = analysis_result.get("concise_report", "")

    with open("general_report.md", "w", encoding="utf-8") as f:
        f.write(general_result)

    with open("concise_report.md", "w", encoding="utf-8") as f:
        f.write(concise_result)
    
    return general_result, concise_result, "general_report.md", "concise_report.md"

# Gradio界面构建
with gr.Blocks(title="会议纪要生成系统") as demo:
    gr.Markdown("## 🎙️ 会议智能分析系统")
    
    # 状态变量
    transcript_state = gr.State()
    audio_state = gr.State()
    
    with gr.Tab("会议处理"):
        with gr.Row(equal_height=True):
            with gr.Column(scale=1):  # 设置较小的比例
                audio_input = gr.Audio(scale=1, type="filepath", label="上传会议录音")

                gr.Markdown("""
                <div style="color: #ff8c00; background-color: #fff4e6; padding: 10px; border-radius: 5px; margin-bottom: 10px; height: 100%;">
                请上传音频文件或进行录音，音频文件支持主流的.WAV, .MP3, .M4A, .WMA, .AAC, .FLAC等格式。
                上传音频完成后，请点击"开始处理"按钮，等待内容预览生成完成。
                </div>
                """)  

                transcribe_audio_btn = gr.Button(scale=3, value="开始处理", variant="primary")

                gr.Markdown("""
                <div style="color: #ff8c00; background-color: #fff4e6; padding: 10px; border-radius: 5px; margin-bottom: 10px; height: 100%;">
                请等待内容预览的生成，补充相应的会议信息后，点击"生成报告"按钮生成对应的报告。
                </div>
                """)  
                
            with gr.Column(scale=3):
                preview_output = gr.Textbox(label="内容预览", lines=28, min_width=600) 

            with gr.Column(scale=3):
                transcript_output = gr.Textbox(
                    label="转译原文", 
                    lines=28, 
                    min_width=600,
                    interactive=True
                )
            
        with gr.Row(equal_height=True):

            with gr.Column(scale=1):            
                generate_report_btn = gr.Button(scale=1, value="生成报告", variant="primary")

            with gr.Column(scale=2):
                speaker_input = gr.Textbox(scale=2, label="发言人信息", placeholder="请按序输入对应的发言人信息")
            with gr.Column(scale=2):
                meeting_time = gr.Textbox(scale=2, label="会议时间", placeholder="如：2024年9月19日 星期四 10:00")
            with gr.Column(scale=2):
                meeting_place = gr.Textbox(scale=2, label="会议地点", placeholder="例如：会议室302")

        with gr.Tab("通用报告"):
            general_report_output = gr.Markdown(label="通用报告")
            general_download = gr.File(label="下载报告")

        with gr.Tab("大纲报告"):
            concise_report_output = gr.Markdown(label="大纲报告")
            concise_download = gr.File(label="下载报告")
        

    # 事件绑定
    transcribe_audio_btn.click(
        process_audio,
        inputs=audio_input,
        outputs=[preview_output, transcript_output, audio_state]
    )
    
    generate_report_btn.click(
        generate_report,
        inputs=[meeting_time, meeting_place, transcript_output, speaker_input],
        outputs=[general_report_output, concise_report_output, general_download, concise_download]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
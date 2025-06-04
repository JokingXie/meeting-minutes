import gradio as gr

# 定义必要的处理函数
def process_audio(audio_file):
    """处理音频文件的占位函数"""
    if not audio_file:
        return "请先上传音频文件", "", ""
    return "音频处理预览", "转录文本", audio_file

def generate_report(transcript, speakers, meeting_time, meeting_place, audio_file):
    """生成报告的占位函数"""
    if not speakers or not meeting_time:
        return "请填写必要信息", None
    return "会议报告内容", "meeting_analysis.md"

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

                # 添加提示信息
                gr.Markdown("""
                <div style="color: #ff8c00; background-color: #fff4e6; padding: 10px; border-radius: 5px; margin-bottom: 10px; height: 100%;">
                请上传音频文件或进行录音，音频文件支持主流的.WAV, .MP3, .M4A, .WMA, .AAC, .FLAC等格式。
                上传音频完成后，请点击“开始处理”按钮，等待内容预览生成完成。
                </div>
                """)  

                upload_btn = gr.Button(scale=3, value="开始处理", variant="primary")

                # 添加提示信息
                gr.Markdown("""
                <div style="color: #ff8c00; background-color: #fff4e6; padding: 10px; border-radius: 5px; margin-bottom: 10px; height: 100%;">
                请等待内容预览的生成，补充相应的会议信息后，点击"生成报告"按钮生成对应的报告。
                </div>
                """)  
                
            with gr.Column(scale=6):  # 设置较大的比例
                preview_output = gr.Textbox(label="内容预览", lines=28, min_width=600)  # 增加行数和最小宽度    
            
        with gr.Row(equal_height=True):

            with gr.Column(scale=1):            
                process_btn = gr.Button(scale=1, value="生成报告", variant="primary")

            with gr.Row(scale=6):
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
    demo.launch(server_name="0.0.0.0", server_port=7861)
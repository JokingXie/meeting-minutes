from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from speaker_distinction import SpeakerDistinction
from speaker_transcript import SpeakerTranscript
from llm_analyzer import analyze_transcript
import os
from typing import Optional
import tempfile

app = FastAPI(title="会议纪要生成系统API")

# 初始化处理模块
distinction_processor = SpeakerDistinction()
transcript_processor = SpeakerTranscript()

@app.post("/process_audio")
async def process_audio(
    audio: UploadFile = File(...),
    speakers: str = Form(...),
    meeting_time: str = Form(...),
    meeting_place: Optional[str] = Form("")
):
    """处理音频并生成报告"""
    try:
        # 保存临时音频文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await audio.read())
            audio_path = tmp.name

        # 1. 说话人分离
        diarization_result = distinction_processor.process_audio(audio_path)
        
        # 2. 生成转录文本
        transcript_list = transcript_processor.merge_speaker_segments(diarization_result, audio_path)
        full_transcript = "\n".join(transcript_list)
        
        # 3. 生成报告
        report_path = "meeting_analysis.md"
        prompt_content = (
            f"会议时间：{meeting_time}\n"
            f"会议地点：{meeting_place}\n"
            f"与会人员：{speakers}\n\n"
            f"会议记录：\n{full_transcript}"
        )
        
        with open("user_prompt.txt", "w", encoding="utf-8") as f:
            f.write(prompt_content)
            
        analysis_result = analyze_transcript(
            user_prompt_file="user_prompt.txt",
            output_file=report_path
        )
        
        # 返回结果
        return {
            "status": "success",
            "preview": transcript_processor.preview_transcript(transcript_list),
            "report_path": report_path,
            "analysis": analysis_result
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)

@app.get("/download_report")
async def download_report():
    """下载生成的报告"""
    if not os.path.exists("meeting_analysis.md"):
        return JSONResponse(
            status_code=404,
            content={"message": "报告未生成"}
        )
    return FileResponse(
        "meeting_analysis.md",
        media_type="application/octet-stream",
        filename="会议纪要.md"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
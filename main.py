from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from speaker_distinction import SpeakerDistinction
from speaker_transcript import SpeakerTranscript
from llm_analyzer import analyze_transcript
import os
import uuid
from pathlib import Path

app = FastAPI(title="会议纪要生成系统API")

# 初始化处理模块
distinction_processor = SpeakerDistinction()
transcript_processor = SpeakerTranscript()

# 临时存储目录
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

@app.post("/upload_audio")
async def upload_audio(audio: UploadFile = File(...)):
    """第一步：上传音频并生成真实预览"""
    try:
        task_id = str(uuid.uuid4())
        audio_path = CACHE_DIR / f"{task_id}.wav"
        
        # 保存音频文件
        with open(audio_path, "wb") as f:
            f.write(await audio.read())
        
        # 1. 真实音频处理流程
        diarization_result = distinction_processor.process_audio(str(audio_path))
        transcript_list = transcript_processor.merge_speaker_segments(
            diarization_result, str(audio_path))
        
        # 2. 生成预览内容
        preview = transcript_processor.preview_transcript(transcript_list)
        full_transcript = "\n".join(transcript_list)
        
        # 保存处理结果
        # with open(CACHE_DIR / f"{task_id}_preview.txt", "w", encoding="utf-8") as f:
        #     f.write(preview)
        with open(CACHE_DIR / f"{task_id}_full.txt", "w", encoding="utf-8") as f:
            f.write(full_transcript)
            
        return {
            "task_id": task_id,
            "preview": preview,
            "next_step": "POST /generate_report with task_id"
        }
        
    except Exception as e:
        raise HTTPException(500, detail=f"音频处理失败: {str(e)}")

@app.post("/generate_report")
async def generate_report(
    task_id: str = Form(...),
    speakers: str = Form(...),
    meeting_time: str = Form(...),
    meeting_place: str = Form("")
):
    """第二步：生成完整报告（调用LLM）"""
    try:
        # 验证任务文件存在
        # preview_path = CACHE_DIR / f"{task_id}_preview.txt"
        full_path = CACHE_DIR / f"{task_id}_full.txt"
        if not (full_path.exists()):
            raise HTTPException(404, detail="任务不存在")
        
        # 读取完整转录
        with open(full_path, "r", encoding="utf-8") as f:
            full_transcript = f.read()
        
        # 3. 生成LLM提示词（改进版）
        user_prompt = (
            f"会议时间：{meeting_time}\n"
            f"会议地点：{meeting_place}\n"
            f"与会人员：{speakers}\n\n"
            f"会议记录:\n{full_transcript}"
        )

        # 存储用户提示词
        user_prompt_path = CACHE_DIR / f"{task_id}_user_prompt.txt"
        with open(user_prompt_path, "w", encoding="utf-8") as f:
            f.write(user_prompt)
        
        # 4. 调用LLM分析
        report_path = CACHE_DIR / f"{task_id}_report.md"
        analysis_result = analyze_transcript(
            user_prompt,
            output_file=str(report_path)
        )
        
        return {
            "task_id": task_id,
            "report_url": f"/download_report/{task_id}",
            "analysis_summary": analysis_result[:200] + "..."
        }

    except Exception as e:
        raise HTTPException(500, detail=f"报告生成失败: {str(e)}")
    
@app.get("/download_report/{task_id}")
async def download_report(task_id: str):
    """下载最终报告"""
    report_path = CACHE_DIR / f"{task_id}_report.md"
    if not report_path.exists():
        raise HTTPException(404, detail="报告未生成或已过期")
        
    return FileResponse(
        report_path,
        filename="会议纪要.md",
        media_type="application/octet-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
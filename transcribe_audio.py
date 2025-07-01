import os
import json
import whisper
import shutil
from xinference.client import Client

from distinguish_speaker import clip_audio
from distinguish_speaker import distinguish_speaker
from add_punctuation import add_punctuation
from separate_document import separate_document

print("Loading Whisper model...")

client = Client("http://19.112.76.53:9998")
model = client.get_model("Belle-whisper-large-v3-zh")

# model = whisper.load_model("large")

print("Whisper model loaded.")

def sort_diarization(raw_diarization: dict) -> dict:
    """
    对原有的说话人日志进行处理，按时间排序，并合并相同说话人片段。
    
    :param raw_diarization: 原始说话人日志 {'speaker0': [[start, end], ...]}
    :return: 排序合并后的说话人日志 {"sorted_diarization": [[start, end, speaker_id_int], ...]}
    """
    # 步骤 1: 将 diarization 字典扁平化为一个 segment 列表
    all_segments = []
    for speaker_id, segments in raw_diarization.items():
        try:
            # 将 'speakerX' 转换为整数 X
            speaker_id_int = int(speaker_id.replace("speaker", ""))
            for start, end in segments:
                all_segments.append({"start": start, "end": end, "speaker": speaker_id_int})
        except (ValueError, TypeError):
            continue # 如果 speaker_id 格式不正确，跳过

    if not all_segments:
        return {"sorted_diarization": []}
        
    # 步骤 2: 按开始时间排序
    all_segments.sort(key=lambda x: x["start"])

    # 步骤 3: 合并连续的、同一说话人的片段
    merged_segments = []
    current_segment = all_segments[0]

    for i in range(1, len(all_segments)):
        next_segment = all_segments[i]
        if next_segment["speaker"] == current_segment["speaker"]:
            # 如果是同一说话人，只更新结束时间，实现合并
            current_segment["end"] = next_segment["end"]
        else:
            # 如果是不同说话人，将合并好的前一个片段存入列表
            merged_segments.append([
                current_segment["start"],
                current_segment["end"],
                current_segment["speaker"]
            ])
            # 开始一个新的片段合并
            current_segment = next_segment
    
    # 步骤 4: 添加最后一个处理中的片段
    merged_segments.append([
        current_segment["start"],
        current_segment["end"],
        current_segment["speaker"]
    ])

    return {"sorted_diarization": merged_segments}

def transcribe_audio(audio_wav: str, raw_diarization: dict) -> dict:
    """
    对传入的每个音频段进行转写。

    :param audio_wav: 原始音频文件路径
    :param raw_diarization: 未处理的说话人日志 e.g., {'speaker0': [[start, end], ...]}
    :return: {"result": [[开始时间, 结束时间, 说话人ID, 转写内容], ...]}
    """
    sorted_diarization = sort_diarization(raw_diarization)

    all_segments = sorted_diarization.get("sorted_diarization", [])
    
    results = []
    temp_dir = "temp_transcribe_clips"
    os.makedirs(temp_dir, exist_ok=True)

    print(f"Start transcribing {len(all_segments)} audio segments...")
    for i, segment in enumerate(all_segments):
        start, end, speaker_id_int = segment
        speaker = f"speaker{speaker_id_int}"
        
        clip_path = os.path.join(temp_dir, f"segment_{i}.wav")
        if not clip_audio(audio_wav, start, end, clip_path):
            continue

        try:
            with open(clip_path, "rb") as audio_file:
                raw_text = model.transcriptions(audio_file.read()).get("text","")

            # transcription_result = model.transcribe(
            #     clip_path,
            #     language="zh",
            #     task="transcribe",
            #     prompt="以下是普通话的句子。这是一段会议记录的语音片段。"
            # )
            # text = transcription_result.get('text', '').strip()

            unsplit_text = add_punctuation(raw_text)
            text = separate_document(unsplit_text)

            print(f"  Segment {i+1}/{len(all_segments)}: [{start:.2f}s - {end:.2f}s] Speaker: {speaker} -> {text}")
        except Exception as e:
            text = f"[ERROR: {e}]"
            print(f"  Error transcribing segment {i+1}: {e}")
        
        results.append([start, end, speaker, text])

        os.remove(clip_path)

    shutil.rmtree(temp_dir)

    return {"result": results}

def format_transcription_to_text(transcription_result: dict) -> str:
    """
    将转写结果格式化为易读的文本字符串。
    格式为：
    时间，说话人：
    文本内容

    :param transcription_result: 包含 'result' 键的字典，其值为 [start, end, speaker, text] 的列表。
    :return: 格式化后的多行字符串。
    """
    lines = []
    for segment in transcription_result.get("result", []):
        start_time, end_time, speaker, text = segment
        
        # 格式化开始时间
        start_h, start_m, start_s = int(start_time // 3600), int((start_time % 3600) // 60), int(start_time % 60)
        start_timestamp = f"{start_h:02d}:{start_m:02d}:{start_s:02d}"
        
        # 格式化结束时间
        end_h, end_m, end_s = int(end_time // 3600), int((end_time % 3600) // 60), int(end_time % 60)
        end_timestamp = f"{end_h:02d}:{end_m:02d}:{end_s:02d}"
        
        lines.append(f"{start_timestamp}-{end_timestamp}，{speaker}：")
        lines.append(text)
        # lines.append("") # 为下一段添加空行，提高可读性
    
    return "\n".join(lines)

if __name__ == "__main__":
    # x = {
    #     'speaker0': [[0.0, 9.2], [12.82, 23.58]],
    #     'speaker1': [[80.44, 82.68], [83.08, 84.54]],
    #     'speaker2': [[348.5, 350.71], [350.99, 355.94]],
    #     'speaker3': [[600.0, 602.6], [602.91, 625.68], [626.25, 696.21]], 
    #     'speaker4': [[751.69, 752.45], [760.91, 762.75]],
    #     'speaker5': [[900.0, 904.41], [904.69, 906.91]],
    #     'speaker6': [[1093.79, 1094.54], [1103.54, 1125.21]]
    #     }
    
    # audio_file = "part1.mp3"
    audio_file = "sample-diarization-test.wav"
    
    raw_diarization = distinguish_speaker(audio_file)
    result = transcribe_audio(audio_file, raw_diarization)
    print(format_transcription_to_text(result))


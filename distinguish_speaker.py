import os
from pydub import AudioSegment
from modelscope.pipelines import pipeline
from identify_speaker import is_same_speaker, sv_pipeline

# 初始化说话人日志pipeline
sd_pipeline = pipeline(
    task='speaker-diarization',
    model='iic/speech_campplus_speaker-diarization_common',
    model_revision='v1.0.0'
)

def generate_diarization(test_wav: str) -> dict:
    """
    生成音频的说话人日志，并将结果处理成{"speakerX": [[start, end], ...]}格式。

    :param test_wav: 需处理的原始音频文件
    :return: {"speaker0": [[0.0, 1.0], [2.0, 3.0]...}, "speaker1": ...}
    """
    raw_diarization = sd_pipeline(test_wav)
    
    processed_diarization = {}
    # raw_diarization['text'] 的格式是 [[start, end, speaker_id], ...]
    for segment in raw_diarization.get('text', []):
        start, end, speaker_id = segment
        start = round(start, 2)
        end = round(end, 2)
        speaker_key = f"speaker{speaker_id}"
        if speaker_key not in processed_diarization:
            processed_diarization[speaker_key] = []
        processed_diarization[speaker_key].append([start, end])
        
    return processed_diarization

def clip_audio(input_wav: str, start_time: float, end_time: float, output_wav: str) -> bool:
    """
    从音频文件中剪辑一个片段并保存。

    :param input_wav: 输入音频文件
    :param start_time: 开始时间 (秒)
    :param end_time: 结束时间 (秒)
    :param output_wav: 输出音频文件
    :return: True on success, False on failure
    """
    # pydub 使用毫秒为单位
    start_ms = int(start_time * 1000)
    end_ms = int(end_time * 1000)
    
    try:
        sound = AudioSegment.from_file(input_wav)
        clip = sound[start_ms:end_ms]
        clip.export(output_wav, format="wav")
        return True
    except Exception as e:
        print(f"Error clipping audio {input_wav}: {e}")
        return False

def merge_same_speaker(
    anchor_wav: str, 
    final_diarization: dict, 
    test_wav: str, 
    test_diarization: dict, 
    interval: float
) -> dict:
    """
    合并已确认的和待确认的说话人日志，以 dict 形式返回

    :param anchor_wav: 原始完整音频文件，用于提取基准说话人片段
    :param final_diarization: 已合并的最终说话人日志
    :param test_wav: 当前待处理的音频块文件
    :param test_diarization: 当前待处理音频块的日志
    :param interval: 当前音频块在原始音频中的开始时间 (秒)
    :return: 合并后的说话人日志
    """
    merged_diarization = final_diarization.copy()
    speaker_mapping = {}
    temp_dir = "temp_clips"
    os.makedirs(temp_dir, exist_ok=True)

    # 提取基准说话人的音频片段
    anchor_clips = {}
    for speaker_id, segments in final_diarization.items():
        if segments:
            start, end = segments[0]
            clip_path = os.path.join(temp_dir, f"anchor_{speaker_id}.wav")
            clip_audio(anchor_wav, start, end, clip_path)
            anchor_clips[speaker_id] = clip_path

    # 将新片段的说话人与基准说话人进行比对
    new_speaker_idx = len(final_diarization)
    for test_speaker_id, test_segments in test_diarization.items():
        if not test_segments: continue
        
        test_start, test_end = test_segments[0]
        test_clip_path = os.path.join(temp_dir, f"test_{test_speaker_id}.wav")
        clip_audio(test_wav, test_start, test_end, test_clip_path)

        found_match = False
        for anchor_speaker_id, anchor_clip_path in anchor_clips.items():
            if is_same_speaker(anchor_clip_path, test_clip_path):
                speaker_mapping[test_speaker_id] = anchor_speaker_id
                found_match = True
                break
        
        if not found_match:
            # 如果没有找到匹配项，则创建新说话人
            new_speaker_id = f"speaker{new_speaker_idx}"
            speaker_mapping[test_speaker_id] = new_speaker_id
            new_speaker_idx += 1
        
        os.remove(test_clip_path)

    # 根据映射关系，合并日志
    for test_speaker_id, segments in test_diarization.items():
        final_speaker_id = speaker_mapping.get(test_speaker_id)
        if not final_speaker_id: continue

        if final_speaker_id not in merged_diarization:
            merged_diarization[final_speaker_id] = []
        
        for start, end in segments:
            merged_diarization[final_speaker_id].append([start + interval, end + interval])

    # 清理临时文件
    for clip_path in anchor_clips.values():
        os.remove(clip_path)
    os.rmdir(temp_dir)
            
    return merged_diarization


def distinguish_speaker(raw_wav: str, chunk_size: float = 20) -> dict:
    """
    将长音频分块处理，并合并结果，生成最终的说话人日志。

    :param raw_wav: 需处理的原始音频文件
    :param chunk_size: 分隔原始音频的大小 (分钟), 默认为 20 min。
    :return: {"speaker0": [[0.0, 1.0], ...], "speaker1": [[...], ...]}
    """
    chunk_size_ms = int(chunk_size * 60 * 1000)
    sound = AudioSegment.from_file(raw_wav)
    temp_chunk_dir = "temp_chunks"
    os.makedirs(temp_chunk_dir, exist_ok=True)
    
    # 1. 分割音频
    chunk_files = []
    for i, chunk in enumerate(sound[::chunk_size_ms]):
        chunk_path = os.path.join(temp_chunk_dir, f"chunk_{i}.wav")
        chunk.export(chunk_path, format="wav")
        chunk_files.append(chunk_path)

    if not chunk_files:
        return {}
        
    # 2. 处理第一个音频块作为基准
    print(f"Processing chunk 0...")
    final_diarization = generate_diarization(chunk_files[0])
    
    # 3. 循环处理后续音频块并合并
    for i in range(1, len(chunk_files)):
        print(f"Processing and merging chunk {i}...")
        test_chunk_wav = chunk_files[i]
        test_diarization = generate_diarization(test_chunk_wav)
        interval_s = (i * chunk_size_ms) / 1000.0
        
        final_diarization = merge_same_speaker(
            raw_wav, final_diarization, test_chunk_wav, test_diarization, interval_s
        )
    
    # 4. 清理分块的临时文件
    for chunk_file in chunk_files:
        os.remove(chunk_file)
    os.rmdir(temp_chunk_dir)

    # 5. 对最终结果按时间排序
    for speaker in final_diarization:
        final_diarization[speaker].sort()

    return final_diarization

if __name__ == "__main__":

    input_wav = 'part1.mp3'
    if os.path.exists(input_wav):
        final_result = distinguish_speaker(input_wav, chunk_size=20) # 使用5分钟的块大小进行测试
        import json
        print(json.dumps(final_result, indent=2))
    else:
        print(f"Error: Input audio file not found at {input_wav}")
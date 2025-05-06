from modelscope.pipelines import pipeline
import os

class SpeakerDistinction:
    def __init__(self):
        self.sd_pipeline = pipeline(
            task='speaker-diarization',
            model='iic/speech_campplus_speaker-diarization_common',
            model_revision='v1.0.0'
        )
    
    def process_audio(self, input_wav: str) -> dict:
        """处理音频文件并返回说话人分离结果"""
        if not os.path.exists(input_wav):
            print(f"文件不存在: {input_wav}")
            input_wav = 'https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/test_audio/asr_speaker_demo.wav'
            print(f"使用默认示例音频: {input_wav}")
        return self.sd_pipeline(input_wav)

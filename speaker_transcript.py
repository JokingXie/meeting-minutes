import whisper
from collections import defaultdict

class SpeakerTranscript:
    def __init__(self):
        self.whisper_model = whisper.load_model("medium")
    
    def merge_speaker_segments(self, result: dict, audio_path: str) -> list:
        """合并说话人片段"""
        transcript = self.whisper_model.transcribe(audio_path, word_timestamps=True)
        output = []
        speaker_timeline = [(seg[0], seg[1], seg[2]) for seg in result['text']]
        
        for segment in transcript['segments']:
            current_speaker = None
            segment_text = []
            
            for word in segment['words']:
                word_start = word['start']
                current_speaker = next(
                    (spk for start, end, spk in speaker_timeline 
                     if start <= word_start < end),
                    current_speaker
                )
                segment_text.append({
                    'word': word['word'],
                    'start': word_start,
                    'end': word['end'],
                    'speaker': current_speaker
                })
            
            if segment_text:
                start = segment_text[0]['start']
                last_speaker = segment_text[0]['speaker']
                current_line = []
                
                for item in segment_text:
                    if item['speaker'] != last_speaker:
                        output.append(
                            f"{start:.2f}, {item['start']:.2f}, SPEAKER_{last_speaker}, "
                            f"{''.join(w['word'] for w in current_line)}"
                        )
                        start = item['start']
                        last_speaker = item['speaker']
                        current_line = []
                    current_line.append(item)
                
                if current_line:
                    output.append(
                        f"{start:.2f}, {segment_text[-1]['end']:.2f}, SPEAKER_{last_speaker}, "
                        f"{''.join(w['word'] for w in current_line)}"
                    )
        return output
    
    def preview_transcript(self, subtitle, max_sentences=2):
        """生成预览内容"""
        speaker_lines = defaultdict(list)
        for line in subtitle:
            parts = line.split(", ", 3)
            if len(parts) >= 4:
                speaker = parts[2]
                speaker_lines[speaker].append(line)
        
        preview = []
        for speaker, lines in speaker_lines.items():
            preview.append(f"\n=== {speaker} ===")
            for line in lines[:max_sentences]:
                time_part = ", ".join(line.split(", ")[:2])
                text = line.split(", ", 3)[-1]
                preview.append(f"[{time_part}s] {text}")
        return "\n".join(preview)
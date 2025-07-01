from modelscope.pipelines import pipeline

# 初始化说话人验证pipeline
sv_pipeline = pipeline(
    task='speaker-verification',
    model='iic/speech_campplus_sv_zh-cn_16k-common',
    model_revision='v1.0.0'
)

def is_same_speaker(anchor_wav: str, test_wav: str, thr: float = 0.5) -> bool:
    """
    判断两个音频文件是否为同一说话人

    :param anchor_wav: 已确认的说话人音频文件名
    :param test_wav: 待确认的说话人音频文件名
    :param thr: 阈值，默认0.5（可根据实际情况调整）
    :return: True（同一人）/False（不同人）
    """
    result = sv_pipeline([anchor_wav, test_wav], thr=thr)
    return result.get("text", "no") == "yes"

# 示例用法
if __name__ == "__main__":
    anchor = "speaker1_a_cn_16k.wav"
    test = "speaker1_b_cn_16k.wav"
    print(is_same_speaker(anchor, test, 0.71))  # True/False

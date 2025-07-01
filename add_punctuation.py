from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

inference_pipline = pipeline(
    task=Tasks.punctuation,
    model='iic/punc_ct-transformer_cn-en-common-vocab471067-large',
    model_revision="v2.0.4")

def add_punctuation(raw_text: str) -> str:
    """
    对传入的文本信息添加标点符号

    :param raw_text 未处理的无标点原文
    :return 处理后的添加了标点的文段
    """
    rec_result = inference_pipline(raw_text)
    return (rec_result[0].get("text",""))

if __name__ == "__main__":

    x = "在青岛呢,我们周冉宇教授担任主任委员,确实也带领了青岛广大的眼科同仁,也做出了很大的贡献。所以这些所集会,我们才形成了中国在我们全国眼科医生数第一,拥有眼科的医疗机构第一,所有的这些公司。当然从一个侧面也说明了,我们山东的眼科的病人数量也是达到第一。这样一个事实说明我们山东眼科确实为我们中国的解除这些繁忙、助残,为了我们人类的健康事业做出了很大的贡献。我还是属于一个承上齐下吧。也感谢西苑市委手的贡献。谢谢。老前辈,也感谢张涵教授借过这个节力棒带领我们山东眼科的发展。当然我作为旧任山东省医事协会眼科医事分会的会长,下一步我们还要准备根据我们新的倡导人文精神来继续在我们的不同的领域为我们眼科事业做出我们新的贡献。最后呢,我来祝我们大会圆满成功。所以祝在座的每一位专家健康快乐平安。谢谢。"
    y = "感谢谢教授本次会议我们还邀请了多名的国内省内著名的眼科专家到现场或者是在线上进行精彩的学术报告我们现场呢我们还请了中华夜里面杂志的编委杂志部编辑部的主任四城大学华西医院眼科副主任陆方教授"
    print(add_punctuation(x))
    print('\n')
    print(add_punctuation(y))


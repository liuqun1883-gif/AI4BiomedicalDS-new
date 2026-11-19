from pathlib import Path
from shutil import copy2
import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_BREAK
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
COURSE = ROOT / "3. High-dimension"
SOURCE = COURSE / "student-worksheet-completed.docx"
DEST = COURSE / "high-dimension-final-assignment.docx"
RESULTS = COURSE / "student-results"

if not SOURCE.exists():
    raise FileNotFoundError(SOURCE)

# Verify that the latest experiment outputs agree with the values used in the worksheet.
a = pd.read_csv(RESULTS / "A-real-distances.csv")
b = pd.read_csv(RESULTS / "B-original-split.csv")
cv = pd.read_csv(RESULTS / "B-training-only-cv.csv")
jac = pd.read_csv(RESULTS / "B-selection-stability.csv")

checks = {
    "distance_cv_p2": (a.query("seed == 42 and p == 2").iloc[0].cv, 1.2327609616648165),
    "distance_cv_p7129": (a.query("seed == 42 and p == 7129").iloc[0].cv, 0.18697624170481228),
    "test_ba_p2": (b.query("p == 2").iloc[0].test_ba, 0.49642857142857144),
    "test_ba_p7129": (b.query("p == 7129").iloc[0].test_ba, 0.7607142857142857),
}
for name, (actual, expected) in checks.items():
    if abs(float(actual) - expected) > 1e-10:
        raise RuntimeError(f"{name} changed: {actual} != {expected}")

copy2(SOURCE, DEST)
doc = Document(DEST)
doc.core_properties.title = "高维数据与维度灾难课程作业"
doc.core_properties.subject = "Golub白血病表达数据的距离、分类与验证"

# Keep the completed worksheet intact and append a compact learning summary.
p = doc.add_paragraph()
p.add_run().add_break(WD_BREAK.PAGE)
heading = doc.add_heading("老师希望我掌握的知识点", level=1)
heading.paragraph_format.space_after = Pt(10)

points = [
    ("1 先辨认样本和特征", "n是独立样本数，p是输入特征数。本数据n=72、p=7129、p/n约99.01，是典型的大p小n问题。每行是一份表达样本，但缺少患者重复映射，因此不能把72行直接宣称为72名已核验的独立患者。"),
    ("2 探针数不等于基因数或独立信息量", "多个探针可能对应同一基因，相关探针会重复携带相似信息，数据中还含AFFX控制探针。因此7129列不代表7129个不同基因，也不代表7129份相互独立的信息。"),
    ("3 标准化改变各特征的权重", "z-score让不同量纲的探针可以共同参与欧氏距离；描述性实验可以使用全部当前样本计算标准化，但预测评估必须只在训练数据上拟合均值和标准差，再应用到验证集或测试集。"),
    ("4 高维中的绝对距离和相对距离要分开理解", "seed=42时，平均距离从p=2的1.2688增至p=7129的118.1965，但距离CV从1.2328降至0.1870。绝对距离变大和相对分布变窄并不矛盾，这正是距离集中现象需要表达的两面。"),
    ("5 近远邻的相对差缩小不等于绝对差趋近于零", "G001的R从160.6959降至0.6665，而全体样本的近远距离绝对差中位数从7.8600增至87.1380。高维下相对区分变弱可能影响邻居排序，但不能据此断言所有距离分类或聚类都会失败。"),
    ("6 随机种子控制可复现的选列顺序", "随机种子42本身没有统计学特殊意义，只让随机排列可以复现。低维结果会受具体选中探针影响；当p=7129时所有种子都包含全部探针，欧氏距离不应因列顺序改变。"),
    ("7 训练满分不代表模型能泛化", "1近邻在训练集上重代入评分时，样本通常把自己当作最近邻，所以所有p的训练BA均为1.000。训练满分主要反映记忆能力，不能代替未参与拟合样本上的评价。"),
    ("8 平衡准确率适合比较类别召回", "BA是ALL和AML召回率的平均值，不等于普通准确率。p=7129时BA=(19/20+8/14)/2=0.7607；恒预测ALL的BA为0.5，而普通准确率为20/34。"),
    ("9 本次更多探针表现更好不等于普遍规律", "当前固定流程中测试BA从p=2的0.4964升至p=7129的0.7607，说明后续探针可能含有可用诊断信息。它既不能证明特征越多必然越好，也不能证明高维必然更差，因为增加p也同时改变了特征内容。"),
    ("10 特征筛选必须放在训练折内部", "先用全部样本标签选特征再交叉验证会造成信息泄漏。正确流程是在每个训练折内拟合标准化、筛选和分类器，验证折只应用已经拟合的变换；测试集必须保留到方案完全冻结后。"),
    ("11 预测性能和特征稳定性是两个问题", f"训练内3折乘3重复验证中，全部7129探针和折内筛选20探针的平均验证BA分别为{cv.query('method == \"all7129\"').validation_ba.mean():.4f}和{cv.query('method == \"select20\"').validation_ba.mean():.4f}。筛选集合Jaccard中位数仅{jac.jaccard.median():.4f}，说明分数尚可不代表具体探针列表稳定。"),
    ("12 多重检验会制造偶然发现", "若7129个原假设都成立且每项I类错误率为0.05，期望假阳性数为7129乘0.05等于356.45。只报告最小p值会隐藏搜索规模；FDR控制的是被报告发现中的预期错误发现比例。"),
    ("13 交叉验证不能创造独立证据", "3折乘3重复产生9个验证分数，但这些折共享同一批38份训练记录，不能当作9项独立研究。若还要从多个特征数或模型中调参，应使用嵌套交叉验证。"),
    ("14 结论必须说明边界", "本实验缺少患者重复映射、中心、时间和批次信息，历史测试集也不是新的临床外部验证。因此不能证明因果、排除批次效应或宣称临床有效；更强证据应来自冻结流程后在不同中心独立患者队列上的外部验证。"),
]

for title, body in points:
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(6)
    run = para.add_run(title + "：")
    run.bold = True
    run.font.color.rgb = RGBColor(0, 0, 0)
    para.add_run(body)

doc.add_heading("复现记录", level=1)
versions = "Python 3.12.14；numpy 2.2.3；pandas 2.2.3；scipy 1.16.3；scikit-learn 1.8.0；matplotlib 3.10.8；随机种子42、7、2026。"
doc.add_paragraph("运行环境与参数：" + versions)
doc.add_paragraph("2026年10月29日顺序执行notebook的7个代码单元，全部执行成功，错误数为0；结果保存在student-results，带输出版本为notebook/high-dimension-lab-executed.ipynb。")

# Normalize newly appended Chinese/Latin fonts without disturbing the original worksheet layout.
for para in doc.paragraphs[-40:]:
    for run in para.runs:
        run.font.name = "Aptos"
        run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        if run.font.size is None:
            run.font.size = Pt(10.5)

doc.save(DEST)
print(DEST.resolve())
print("paragraphs=", len(doc.paragraphs), "tables=", len(doc.tables))

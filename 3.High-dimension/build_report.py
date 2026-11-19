from pathlib import Path
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent / "3. High-dimension"
OUT = ROOT / "student-results"
DEST = ROOT / "high-dimension-course-report.docx"
a = pd.read_csv(OUT / "A-real-distances.csv")
near = pd.read_csv(OUT / "A-neighbors-seed42.csv")
b = pd.read_csv(OUT / "B-original-split.csv")
cv = pd.read_csv(OUT / "B-training-only-cv.csv")
jac = pd.read_csv(OUT / "B-selection-stability.csv")
orders = pd.read_csv(OUT / "A-probe-orders.csv")

doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(.72); sec.bottom_margin = Inches(.72)
sec.left_margin = Inches(.78); sec.right_margin = Inches(.78)

styles = doc.styles
for nm in ["Normal", "Title", "Heading 1", "Heading 2"]:
    st = styles[nm]
    st.font.name = "Aptos"
    st._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    st.font.color.rgb = RGBColor(0,0,0)
styles["Normal"].font.size = Pt(10)
styles["Normal"].paragraph_format.space_after = Pt(6)
styles["Title"].font.size = Pt(24)
styles["Title"].font.bold = True
styles["Heading 1"].font.size = Pt(16); styles["Heading 1"].font.bold = True
styles["Heading 2"].font.size = Pt(12); styles["Heading 2"].font.bold = True

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), fill); tcPr.append(shd)
def set_cell(cell, text, bold=False, color=None, size=9):
    cell.text = str(text)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for p in cell.paragraphs:
        p.paragraph_format.space_after = Pt(2)
        for r in p.runs:
            r.bold = bold; r.font.name = "Aptos"; r.font.size = Pt(size)
            r._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
            if color: r.font.color.rgb = RGBColor(*color)
def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    for i,h in enumerate(headers):
        set_cell(t.rows[0].cells[i], h, True, (255,255,255))
        shade(t.rows[0].cells[i], "24476B")
    trPr = t.rows[0]._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader"); repeat.set(qn("w:val"), "true"); trPr.append(repeat)
    for ri,row in enumerate(rows):
        cells=t.add_row().cells
        for i,v in enumerate(row):
            set_cell(cells[i], v)
            if ri%2: shade(cells[i],"F0F4F8")
    if widths:
        for row in t.rows:
            for cell,w in zip(row.cells,widths): cell.width=Inches(w)
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
    return t
def p(text="", boldlead=None):
    para=doc.add_paragraph()
    if boldlead and text.startswith(boldlead):
        para.add_run(boldlead).bold=True; para.add_run(text[len(boldlead):])
    else: para.add_run(text)
    return para
def figure(filename, caption, width=6.25):
    para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para.add_run().add_picture(str(OUT/filename),width=Inches(width))
    cap=doc.add_paragraph(caption); cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after=Pt(10)
    for r in cap.runs: r.italic=True; r.font.size=Pt(9)

title=doc.add_paragraph(style="Title"); title.alignment=WD_ALIGN_PARAGRAPH.CENTER
title.add_run("高维白血病表达数据中的距离与分类表现")
sub=doc.add_paragraph(); sub.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=sub.add_run("课程实验报告｜高维数据与维度灾难"); r.font.size=Pt(12); r.font.color.rgb=RGBColor(80,90,100)
sub2=doc.add_paragraph(); sub2.alignment=WD_ALIGN_PARAGRAPH.CENTER
sub2.add_run("姓名：____________    学号：____________    日期：____________")

doc.add_heading("摘要", level=1)
p("本报告使用 Golub 白血病微阵列表达数据，分析特征维数增加时样本间欧氏距离的相对分布，以及 1 近邻分类在训练集、原始测试集和训练集内部重复交叉验证中的表现。数据包含 72 份样本和 7,129 个探针特征，类别为 ALL 与 AML。实验 A 对逐列标准化后的表达矩阵随机排列探针，并以固定随机种子抽取嵌套子集；实验 B 沿用 38/34 的训练/测试划分，在训练子集拟合标准化与 1 近邻模型。结果显示，seed=42 时距离均值随特征数增加而升高，而距离 CV 从 1.233 降至 0.187、近远距离相对差中位数 R 从 115.452 降至 0.967。实验 B 的训练 BA 在所有维度均为 1.000；原始测试 BA 从 p=2 时的 0.496 变化至 p=7129 时的 0.761。训练内 3 折×3重复验证中，全部探针与折内筛选20个探针的平均验证 BA 分别为 0.844 与 0.886；筛选集合两两 Jaccard 中位数仅 0.270。结果说明本数据及指定流程下，训练拟合、距离结构与验证表现需分别评估；单一历史测试划分不足以证明临床泛化或因果关系。")
p("关键词：高维数据；白血病表达；欧氏距离；1近邻；交叉验证；特征选择")

doc.add_heading("1 引言", level=1)
p("生物医学测量常产生远多于样本数的变量。高维表示可能包含疾病相关信号，也可能包含冗余或测量噪声；因此，不能仅由特征数量推断模型性能。本实验围绕一个具体问题展开：在固定样本集合中逐步纳入更多实测探针时，距离分布和 1 近邻分类结果如何变化？")
p("报告分开考察描述性几何与预测评估。距离实验使用全部 72 份表达样本来刻画样本对距离；预测实验则遵守原始训练/测试划分，并在训练数据内拟合标准化器。此区分避免把描述性结果误当作对新样本的性能估计。")

doc.add_heading("2 数据与方法", level=1)
doc.add_heading("2.1 数据来源与样本结构", level=2)
p("数据为 Golub 白血病微阵列表达数据的课程快照（OpenML leukemia，数据集 ID 1104，version 1）。每行是一份表达样本；sample_id 是教学编号，并非原始患者编号。类别为 ALL（急性淋巴细胞白血病）或 AML（急性髓系白血病）。原始划分为前 38 份训练记录和后 34 份测试记录。输入排除 sample_id、original_split 与 diagnosis 三列；其余 7,129 列为探针特征，其中包括 AFFX 控制探针。探针数不等于不同基因数，也不代表独立信息量。")
table(["样本部分","ALL","AML","合计"],[
["训练",27,11,38],["测试",20,14,34],["总计",47,25,72]])
p("数据完整性核对：X 的形状为 72×7,129，文件 SHA-256 与 data/README.md 所列值一致；类别总数为 ALL 47、AML 25。")
doc.add_heading("2.2 距离实验", level=2)
p("对每个探针按 72 份样本逐列进行 z-score 标准化（总体标准差，ddof=0），随后以 default_rng(seed).permutation 对探针列排序，seed 取 42、7、2026。每种列序分别取前 p=2、3、10、100、1,000、7,129 列。随机操作只决定纳入哪些已有列，不生成新表达值或更改标签。对所有样本对计算欧氏距离，并记录距离均值、变异系数 CV=距离标准差/均值、最近/最远邻距离以及 R=(dmax−dmin)/dmin 的逐样本中位数。二维/三维散点图展示 seed=42 的前三个探针，诊断标签仅用于事后着色。")
doc.add_heading("2.3 分类与训练内验证", level=2)
p("分类实验沿用 seed=42 列序，比较 p=2、10、100、1,000、7,129。模型为 StandardScaler→1近邻分类器。标准化器仅在 38 份训练记录上拟合，再应用于测试记录。性能使用平衡准确率 BA，即两类别召回率的算术平均。另在原训练记录内执行 3 折×3 重复分层交叉验证，比较全部 7,129 个探针和每个训练折内按 ANOVA F 分数选取 20 个探针的方案；特征选择与标准化均在各折训练部分拟合。")

doc.add_heading("3 结果", level=1)
doc.add_heading("3.1 数据规模与低维投影", level=2)
p("样本数 n=72、特征数 p=7,129，p/n≈99.01，处于典型的 p≫n 设置。二维和三维图仅显示被随机抽取的 2 或 3 个探针，适合直观检查投影中的重叠，不代表完整高维结构。")
figure("A-scatter-2D-3D.png","图1｜seed=42随机列序下前三个探针的二维与三维表达投影。颜色为诊断类别，仅供事后观察。")
probe_names=orders["42"].head(3).tolist()
p("图1对应的三个探针依次为 "+", ".join(probe_names)+"。")

doc.add_heading("3.2 特征维数与距离分布", level=2)
figure("A-distance-distributions.png","图2｜不同探针数下，2,556个样本对距离除以该条件平均距离后的分布。横轴为归一化距离，纵轴为样本对数。")
p("seed=42 的距离汇总见表1。随着 p 从 2 增至 7,129，平均距离由 1.269 增至 118.196；同时 CV 从 1.233 降至 0.187，R 中位数从 115.452 降至 0.967。因而原始距离尺度变大与相对距离分布变窄可以同时发生。绝对近远差 gap_median 并未趋于零：从 p=2 的 7.860 增至 p=7,129 的 87.138。")
rows=[]
for dim in [2,3,100,7129]:
    row=a[(a.seed==42)&(a.p==dim)].iloc[0]
    rows.append([dim,f"{row['mean']:.3f}",f"{row['cv']:.3f}",f"{row['r_median']:.3f}",f"{row['gap_median']:.3f}"])
table(["探针数 p","平均距离","距离 CV","R 中位数","gap 中位数"],rows)
p("表1｜seed=42下的距离统计。平均距离和 gap 为原始标准化空间中的欧氏距离；CV 与 R 分别表示总体相对分散程度及逐样本近远邻相对差异。")
p("不同随机列序在中低维度下产生数值差异，且部分指标并非每一步单调变化。例如 seed=42 的 CV 从 p=2 到 p=3 降低，但 R 中位数也受选中特征影响。p=7,129 时三个种子均包含全部探针，距离统计基本相同，符合列顺序不改变欧氏距离的性质。")
g=near[(near.sample_id=="G001")&near.p.isin([2,7129])]
rows=[]
for _,r in g.iterrows():
    rows.append([int(r.p),f"{r.near:.3f}",f"{r.far:.3f}",f"{r.R:.3f}"])
table(["样本编号","探针数 p","最近距离","最远距离","G001 的 R"],[["G001",*x] for x in rows])
p("表2｜G001在两个维数条件下的近远邻距离及相对差异。R=(dmax−dmin)/dmin；这里的距离表不包含邻居样本身份。")

doc.add_heading("3.3 训练、测试与交叉验证表现", level=2)
figure("B-generalization.png","图3｜原始训练/测试划分下的平衡准确率。虚线为恒预测 ALL 的 BA=0.5 基线。")
rows=[]
for _,r in b.iterrows():
    rows.append([int(r.p),f"{r.train_ba:.3f}",f"{int(r.ALL_correct)}/20",f"{int(r.AML_correct)}/14",f"{r.test_ba:.3f}"])
table(["探针数 p","训练 BA","ALL 测试正确数","AML 测试正确数","测试 BA"],rows)
p("表3｜原始训练/测试划分下的 1 近邻表现。")
p("五种维数的训练 BA 均为 1.000。原始测试 BA 分别为 0.496、0.579、0.654、0.725、0.761。恒预测 ALL 的平衡准确率为 0.500；因此 p=2 的结果略低于该基线，p=10至7,129在本次划分中高于基线。p=7,129 的手算 BA=(19/20+8/14)/2≈0.761。")
stats=cv.groupby("method").validation_ba.agg(["mean","min","max"])
table(["训练内方案","验证 BA 均值","最小值","最大值"],[
["全部 7,129 探针",f"{stats.loc['all7129','mean']:.3f}",f"{stats.loc['all7129','min']:.3f}",f"{stats.loc['all7129','max']:.3f}"],
["每折筛选 20 探针",f"{stats.loc['select20','mean']:.3f}",f"{stats.loc['select20','min']:.3f}",f"{stats.loc['select20','max']:.3f}"]])
p("表4｜原训练集内 3 折×3 重复交叉验证的验证表现。两种方案的训练 BA 均为 1.000。折内筛选方案的平均验证 BA 略高，但并非每一折都优于全部探针方案。")
p(f"九次折内筛选得到的探针集合两两比较，Jaccard 中位数为 {jac.jaccard.median():.3f}，范围为 {jac.jaccard.min():.3f}–{jac.jaccard.max():.3f}。这表示筛选列表对训练子集有一定敏感性；交叉验证折之间重复使用样本，因此不能视作九项独立研究。")

doc.add_heading("4 讨论", level=1)
doc.add_heading("4.1 距离集中不等于绝对距离缩小", level=2)
p("距离实验显示，随着纳入特征增加，平均欧氏距离扩大，而归一化后的距离分布相对集中，R 中位数下降。二者并不矛盾：前者描述距离的绝对尺度，后两者描述相对于均值或最近邻距离的离散程度。较小的相对近远差可能削弱基于距离的邻近结构对样本间差异的表达，但不能单独证明分类或聚类必然失败。本次测试 BA 随 p 增大而提高，正说明距离几何指标与具体预测表现不是无条件一一对应。")
doc.add_heading("4.2 训练满分并不等于泛化", level=2)
p("1近邻在训练集上预测自身时，每个样本通常就是自己的最近邻，因此训练 BA 满分并不意外，也不能作为新样本性能证据。原始测试划分上，较高维子集表现更好，但这只说明在该固定探针顺序、模型和一次测试划分下观察到这一趋势；不能推广为更多特征必然更好，也不能反向推出更多特征必然更差。训练内重复验证提供了另一种评估视角，但样本量有限且各折相关，仍需外部独立队列确认。")
doc.add_heading("4.3 筛选稳定性与生物学解释边界", level=2)
p("折内选取20个探针的平均验证 BA 为 0.886，高于全部探针的 0.844，但取值范围重叠，而且筛选集合的 Jaccard 中位数为 0.270。预测性能和具体变量稳定性是不同问题：平均验证分数较高不能证明同一组探针在不同抽样下稳定，更不能单凭此结果宣称这些探针具有因果作用或临床标志物效用。")
doc.add_heading("4.4 局限与可行后续工作", level=2)
p("本分析使用72份样本和既有38/34划分，缺乏患者重复映射、中心、时间和批次字段，无法核实独立患者单位、评估患者级重复或排除批次效应。随机子集改变了探针内容与维数，观察到的变化不应全部归因于维数本身。数据列中含 AFFX 控制探针，探针也不等于不同基因。后续可在患者级分组的嵌套交叉验证中选择特征数，并在完全独立、来源清楚的外部队列上验证；与正则化或降维方法比较时，应把选择与调参限制在训练折内。")

doc.add_heading("5 结论", level=1)
p("在本次 Golub 白血病表达数据分析中，增加探针数伴随距离均值上升、相对距离分散下降；1近邻训练 BA 始终为1.000，而测试和训练内验证表现呈现各自的波动。折内筛选20个探针取得略高的平均验证 BA，但所选探针集合重合度有限。故不能仅凭特征数量、训练满分或单一测试结果判断模型价值；应在无信息泄露的验证流程中考察预测性能、选择稳定性和外部可重复性。结论限于本数据及所比较的预设分析流程。")

doc.add_heading("参考资料", level=1)
p("1. Golub TR, Slonim DK, Tamayo P, et al. Molecular Classification of Cancer: Class Discovery and Class Prediction by Gene Expression Monitoring. Science. 1999;286(5439):531–537. doi:10.1126/science.286.5439.531.")
p("2. OpenML. leukemia, dataset ID 1104, version 1. https://www.openml.org/d/1104. 数据快照及变量说明见课程随附 data/README.md。")

doc.add_heading("提交前由学生补充", level=1)
p("1. 按工作单先验要求，补写自己在查看结果前对特征数量、距离变化及分类表现的预测，并说明原先理由。")
p("2. 核对正文表格和 student-results 中的 CSV；如 notebook 重新运行后结果有变，应同步更新图表和文字。")
p("3. 用自己的话完成课程要求的 T5/H1 迁移讨论，尤其是多重检验、泄漏修复、独立患者单位和临床外部验证。")

# Add table borders explicitly in a light neutral gray.
for t in doc.tables:
    tblPr=t._tbl.tblPr
    borders=OxmlElement("w:tblBorders")
    for edge in ("top","left","bottom","right","insideH","insideV"):
        el=OxmlElement("w:"+edge); el.set(qn("w:val"),"single"); el.set(qn("w:sz"),"4"); el.set(qn("w:color"),"D9D9D9"); borders.append(el)
    tblPr.append(borders)
doc.save(DEST)
print(DEST)

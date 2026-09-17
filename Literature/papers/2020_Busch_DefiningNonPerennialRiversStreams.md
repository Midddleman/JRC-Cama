---
title: "What’s in a Name? Patterns, Trends, and Suggestions for Defining Non-Perennial Rivers and Streams"
authors: "Michelle H. Busch; Katie H. Costigan; Ken M. Fritz; Thibault Datry; Corey A. Krabbenhoft; John C. Hammond; Margaret Zimmer; Julian D. Olden; Ryan M. Burrows; Walter K. Dodds; Kate S. Boersma; Margaret Shanafield; Stephanie K. Kampf; Meryl C. Mims; Michael T. Bogan; Adam S. Ward; Mariana Perez Rocha; Sarah Godsey; George H. Allen; Joanna R. Blaszczak; C. Nathan Jones; Daniel C. Allen"
year: 2020
journal: Water
doi: 10.3390/w12071980
tags: [non-perennial-rivers, intermittent-rivers, ephemeral-streams, terminology, bibliometric-review, topic-modeling]
status: read
relevance: high
primary_stage: "Stage 1: Fundamental Concepts and Importance of Perennial and Non-Perennial Rivers"
secondary_stages: []
---

# Literature Review Classification | 文献综述分类

- **Primary Stage | 主要阶段:** Stage 1 — Fundamental Concepts and Importance of Perennial and Non-Perennial Rivers（阶段1：永久性与非永久性河流的基本概念和重要性）
- **Secondary Stage(s) | 次要阶段:** None. The paper does not provide sufficiently direct evidence for another roadmap stage. | 无；本文没有为其他路线图阶段提供足够直接的证据。
- **Contribution | 主要贡献:** The paper synthesizes how 12 epithets for non-perennial rivers are used and defined across disciplines and time, then recommends a three-term conceptual hierarchy—non-perennial, intermittent, and ephemeral. It directly informs terminology and conceptual classification, while also showing that the literature does not supply an operational discharge threshold or a size-dependent relationship of the form Q_threshold = f(A)（本文综合分析12种非永久性河流术语在不同学科和时期中的使用与定义，并提出non-perennial、intermittent和ephemeral三级概念体系。它直接支持术语与概念分类，但也表明该文献并未提供可操作的流量阈值或随断面面积变化的Q_threshold = f(A)关系）。

---

## Paper Information | 论文信息

- **Title | 标题:** What’s in a Name? Patterns, Trends, and Suggestions for Defining Non-Perennial Rivers and Streams
- **Authors | 作者:** Michelle H. Busch; Katie H. Costigan; Ken M. Fritz; Thibault Datry; Corey A. Krabbenhoft; John C. Hammond; Margaret Zimmer; Julian D. Olden; Ryan M. Burrows; Walter K. Dodds; Kate S. Boersma; Margaret Shanafield; Stephanie K. Kampf; Meryl C. Mims; Michael T. Bogan; Adam S. Ward; Mariana Perez Rocha; Sarah Godsey; George H. Allen; Joanna R. Blaszczak; C. Nathan Jones; Daniel C. Allen
- **Year | 年份:** 2020
- **Journal | 期刊:** Water, 12, 1980
- **DOI:** 10.3390/w12071980

---

## English Summary

## 1. Research Question

The review asks whether the many epithets used for rivers and streams that cease to flow are used consistently across research fields, how their use and associated research topics have changed over time, and how the literature defines them. Its final objective is to propose a smaller, shared terminology for non-perennial river research (p. 3).

## 2. Background

The authors define non-perennial systems broadly as rivers and streams that cease to flow at some point in time or space; temporary absence of surface flow may leave isolated pools or dry channels (p. 2). Such systems are estimated to comprise at least 30% of the global river network, including up to 44% in South Africa, 59% in the United States, and about 70% of river channels in Australia (p. 2). Their occurrence is expected to increase under climate change, dams and impoundments, and water abstraction, yet their hydrology and ecology remain less understood than those of perennial systems (p. 2). Inconsistent terminology impedes interdisciplinary synthesis, management, and regulation; for example, only 17 of 56 U.S. states and territories defined “ephemeral” waterways and only 20 defined “intermittent” waterways in the cited regulatory survey (p. 3).

## 3. Data

- **Dataset(s):** Clarivate Web of Science (WoS) Core Collection records, including author lists, publication years, WoS categories, and abstracts. Searches combined 12 epithets with 41 lotic-waterbody terms and were restricted to 37 natural-science WoS categories, yielding 11,696 papers in the main methods and Table 1 (pp. 3–4). For definition mining, the authors examined 672 papers and retained 315 definitions (pp. 5, 9–10). Appendix A instead describes the complete corpus as 11,989 abstracts, an internal numerical inconsistency that the paper does not explain (p. 16).
- **Spatial resolution:** Not applicable; this is a bibliometric review rather than a spatially gridded or site-level analysis.
- **Temporal resolution:** Publication history was divided into ten intervals: three 25-year intervals and one 15-year interval before 1990, then five-year intervals after 1990; the final interval was incomplete because the search ended in May 2019 (pp. 5, 7). The time-series topic results compare periods through 2016–2018 (p. 9).
- **Study period:** Papers published from 1 January 1900 through 30 May 2019 (p. 3). Figure 4 separately states that abstracts from 1990–2017 were compiled for its epithet-use analysis (p. 9).
- **Study area / coverage:** Global scholarly literature indexed by WoS; searches were not restricted to English-language publications, although all text analysis assumed English text (p. 3).

## 4. Methodology

### Overall Approach

- The authors constructed separate WoS corpora for 12 epithets—arid, discontinuous, dry, ephemeral, episodic, intermittent, interrupted, irregular, non-perennial, non-permanent, seasonal, and temporary—paired with adjacent lotic-waterbody terms. Semi-perennial/non-perennial and permanent/non-permanent searches were handled separately to exclude papers about uninterrupted flow (pp. 3–4).
- Abstracts were tokenized; punctuation and numbers were removed; words were stemmed; and English stop words were removed. Analyses were conducted in R (p. 4).
- For topical differences (O1), a Fisher’s exact test compared epithet counts among WoS categories. Bayesian latent Dirichlet allocation (LDA) in `textmineR` was used on the combined corpus. Candidate models with 1–50 topics were assessed by probabilistic coherence; six topics were selected. Mean document-topic probabilities by epithet were compared using unconstrained non-metric multidimensional scaling (nMDS) in `vegan` (pp. 4–5).
- For temporal change (O2), the authors repeated WoS searches by time interval, compared epithet counts using Fisher’s exact test, and fitted a separate LDA model to the combined time-series corpus; nine topics were selected from coherence calculations (p. 5).
- For definitions (O3), term frequency–inverse document frequency (tf-idf) identified papers in which an epithet adjacent to “river” or “stream” was especially important. Up to 50 papers per epithet were selected (25 for “river” and 25 for “stream”), followed by up to 25 additional randomly selected papers per corpus because many initial papers lacked definitions. Definitions were manually extracted and cleaned (p. 5).
- Because definition corpora were too small for LDA, the authors manually coded definitions against themes concerning water sources, predictability, time frame, climate, and drying phases. Theme proportions were ordinated by nMDS using Euclidean distance. Two uncommon themes and “irregular,” which had only one definition, were excluded after the initial ordination (pp. 5–6).
- Five epithets whose sampled papers were more than 80% about non-perennial river systems were compared across ecology, hydrology, and eco-hydrology: non-perennial (100%), ephemeral (98%), temporary (89%), intermittent (88%), and arid (83%) (p. 6; rounded values as reported there).

### Key Parameters and Thresholds

| Parameter | Value | Meaning |
|---|---:|---|
| Literature search period | 1900-01-01 to 2019-05-30 | WoS publication coverage (p. 3) |
| Epithet set | 12 | Alternative descriptors compared (pp. 3–4) |
| Lotic-waterbody terms | 41 | Terms paired with epithets in the broad search (pp. 3–4) |
| WoS category restriction | 37 categories | Natural-science categories used to narrow the search (p. 4) |
| Main analyzed literature set | 11,696 papers | Main methods/Table 1 total (p. 4); Appendix A reports 11,989 abstracts (p. 16) |
| Candidate LDA topic counts | 1–50 | Range evaluated using probabilistic coherence (p. 4) |
| Selected complete-corpus topics | 6 | O1 LDA model (pp. 4–5) |
| Selected time-series topics | 9 | O2 LDA model (p. 5) |
| Definition-screening maximum | 50 per epithet | Up to 25 “river” plus 25 “stream” papers ranked by tf-idf (p. 5) |
| Additional definition sample | 25 per corpus | Random papers added where initial papers lacked definitions (p. 5) |
| Definition-analysis sample | 672 papers | Minimum 28 and maximum 75 papers per epithet (p. 5) |
| Cross-field comparison criterion | >80% | Share of sampled papers concerning non-perennial systems (p. 6) |
| nMDS interpretation guide | stress < 0.2 | Treated as a good two-dimensional representation (p. 7) |

## 5. Main Results

1. Terminology lacked consensus within and among fields. Every examined WoS category included at least six epithets. LDA identified four broad epithet groupings; the largest grouped arid, dry, intermittent, non-permanent, seasonal, and temporary with agriculture, hydrology, and vegetation, whereas non-perennial formed the smallest group and was closely associated with ecohydrology. The complete-corpus nMDS stress was 0.1029 (pp. 6–7).
2. Publication rates increased from 16.1 papers per year before/through the pre-1990 period to 154.2 papers per year after 1990. “Seasonal” was most frequent over time, while temporary, non-perennial, and intermittent showed the largest rates of increase. From 1991–1995 to 2016–2018, agriculture and geomorphology topic shares decreased by 9% and 6%, respectively, while hydrology and modeling increased by 14% and 5%; community ecology increased by 6% from 1996–2000 to 2016–2018 (pp. 7–9).
3. Of 672 papers screened for definitions, 452 (67%) concerned non-perennial river systems; 54% of all screened papers lacked any epithet definition, and 39% of the 452 relevant papers lacked one. The authors compiled 315 definitions. Definition themes showed direct overlap among intermittent, temporary, and non-perennial, with nMDS stress = 0.0962 (pp. 9–11).
4. The authors recommend retaining three terms. **Non-perennial** is the umbrella for a lotic freshwater system that periodically ceases flowing and/or is dry somewhere in time or space. **Intermittent** denotes a non-perennial river or stream with a considerable groundwater connection, variable wetting and flow-cessation cycles, flow lasting longer than one storm event, and predominantly gaining long-term behavior. **Ephemeral** denotes a type of non-perennial river or stream without a considerable groundwater connection, flowing briefly and typically only after precipitation, with predominantly losing long-term behavior (p. 15).
5. The recommendations are qualitative rather than fixed duration thresholds. The authors argue that quantitative classifications can be useful but must accommodate the frequent absence of hydrologic data; they recommend that every study either state a clear definition or cite one, ideally early in the introduction, and support site classification with quantitative analysis or measurement where possible (pp. 14–15).

## 6. Validation

- **Validation dataset:** No independent validation dataset is identified; the study is a bibliometric synthesis rather than a predictive river-classification product.
- **Validation method:** No external validation is reported. The authors use probabilistic coherence to choose LDA topic counts, nMDS stress to evaluate two-dimensional ordinations, and manual review/coding to collect and categorize definitions (pp. 4–6).
- **Metrics:** Probabilistic coherence; nMDS stress; counts and proportions of papers, definitions, epithets, categories, and topics.
- **Main results:** Complete-corpus topic nMDS stress = 0.1029 (p. 7), and definition-theme nMDS stress = 0.0962 (p. 11); both are below the paper’s stated 0.2 guide for a good representation. No inter-coder reliability statistic or independent validation result is reported.

## 7. Limitations

### Stated by the Authors

- Despite restrictions on epithets, waterbody terms, and WoS categories, irrelevant papers entered the corpus; manually checking the full literature set was outside the study scope and could affect the results (p. 14).
- The review relied only on WoS. Google Scholar or another database might return a different set, and the chosen design may have excluded relevant non-perennial-river papers (p. 14).
- Searches were not restricted by publication language, but text analyses assumed English (p. 3).
- The last publication interval was incomplete because the search ended in May 2019 (p. 7).
- Quantitative duration-based definitions require hydrologic data that are often unavailable for non-perennial systems (pp. 2, 14).

### My Assessment

- The reported corpus total is internally inconsistent: 11,696 papers in the methods/Table 1 (p. 4) versus 11,989 abstracts in Appendix A (p. 16). This should be resolved before reproducing the analysis.
- No inter-coder agreement is reported for manual definition extraction and theme assignment, so the reproducibility of qualitative coding cannot be quantified from the paper.
- Adjacency searches and broad polysemous epithets introduce domain contamination; the authors document this issue, including chemistry and acidification usages unrelated to flow permanence (pp. 9, 12–14).
- The proposed intermittent/ephemeral distinction depends on “considerable” groundwater connection and majority gaining/losing behavior but gives no operational threshold, observation period, or measurement protocol. The terminology is conceptually useful but cannot alone serve as a reproducible classification algorithm.

## 8. Relevance to My Research

### Directly Useful

- Use **non-perennial** as the umbrella class and reserve **intermittent** and **ephemeral** for subclasses distinguished by groundwater connection, storm dependence, and long-term gaining/losing behavior (p. 15).
- State the operational definition near the start of any analysis and document the measurements used for classification. This is especially important when combining surface-water occurrence, discharge, river width, cross-sectional area, or river-network datasets whose observables do not map automatically to groundwater connection (p. 15).
- Treat “no flow” and “no surface water” as different drying-state concepts; the definition-theme analysis explicitly separates them (pp. 5, 10–11).

### Potentially Useful

- The paper’s review workflow—broad synonym search, topic modeling, tf-idf prioritization, manual definition extraction, and definition-theme ordination—could support a reproducible terminology or methods review (pp. 3–6).
- The reported scarcity of quantitative definitions supports conducting sensitivity analyses rather than adopting an undocumented fixed permanence threshold (p. 14).
- The nMDS visualization of terms and definition themes offers a model for showing overlap among alternative river classes (pp. 10–11).

### Differences / Not Applicable

- The paper does not produce a global river map, spatial resolution, temporal surface-water product, discharge threshold, river-width threshold, or cross-sectional-area threshold.
- It does not evaluate JRC Global Surface Water, HydroRIVERS, CaMa-Flood, or another river-network/model dataset.
- Its recommended definitions require groundwater and event-duration information that may not be observable from surface-water occurrence alone; additional operational rules and validation data would be required for gridded classification.

## 9. What I Can Reuse

- **Dataset:** WoS Core Collection search strategy and the 12-epithet vocabulary; the paper links supplementary search materials and analysis code on p. 16.
- **Method:** LDA topic modeling plus tf-idf-guided and random sampling for definition review, followed by theme coding and nMDS (pp. 4–6).
- **Threshold / parameter:** The >80% relevance screen for cross-field epithet comparison and stress < 0.2 as the paper’s nMDS representation guide (pp. 6–7). No hydrologic duration threshold is proposed.
- **Validation strategy:** For a future classification study, operationalize the three conceptual terms and validate them against independent observations of flow cessation, groundwater connection, event response, and gaining/losing status; this is my proposed extension, not a validation performed in the paper.
- **Figure / visualization idea:** An nMDS or analogous similarity plot linking terminology to definition themes, complemented by a time-series plot of term prevalence (Figures 3–5, pp. 7–11).

---

## 中文总结

## 1. 研究问题

本文考察描述“会停止流动的河流与溪流”的多种术语是否在不同学科中被一致使用、这些术语及其对应研究主题如何随时间变化，以及既有文献如何定义这些术语；最终目标是为非永久性河流研究提出一套更精简、通用的术语体系（第3页）。

## 2. 研究背景

作者将非永久性河流（non-perennial river/stream）宽泛地界定为在某个时间或空间位置停止流动的河流或溪流；其核心特征是地表流暂时消失，并可能形成孤立水池或干涸河道（第2页）。据文中引用的估计，这类水系至少占全球河网的30%，在南非可达44%、美国59%、澳大利亚约70%（第2页）。气候变化、水坝与蓄水工程建设以及人类取水可能进一步增加其数量，但其水文和生态过程相较于永久性河流仍缺乏研究（第2页）。术语不统一会妨碍跨学科综合、管理与法规制定；文中举例指出，在美国56个州和领地中，仅17个定义了“ephemeral”，20个定义了“intermittent”（第3页）。

## 3. 数据

- **数据集：** Clarivate Web of Science（WoS）Core Collection 文献记录，包括作者、发表年份、WoS学科类别和摘要。主检索将12个术语与41个流水水体词组合，并限于37个自然科学WoS类别，方法与表1报告共11,696篇论文（第3–4页）。定义挖掘检查了672篇论文，最终收集315条定义（第5、9–10页）。但附录A称完整语料库含11,989篇摘要，文中未解释这一内部数字差异（第16页）。
- **空间分辨率：** 不适用；本文是文献计量综述，不是空间栅格或站点尺度分析。
- **时间分辨率：** 发表历史分为10个时间段：1990年前包含3个25年段和1个15年段，1990年后采用5年段；最后一段因检索截止于2019年5月而不完整（第5、7页）。时间主题结果比较到2016–2018年（第9页）。
- **研究时期：** 检索1900年1月1日至2019年5月30日发表的论文（第3页）；图4另称其术语使用分析汇编了1990–2017年的摘要（第9页）。
- **研究区域 / 覆盖范围：** WoS收录的全球学术文献；检索不限制论文语言，但文本分析假定文本为英文（第3页）。

## 4. 研究方法

### 整体方法

- 作者为12个术语分别建立WoS语料库：arid、discontinuous、dry、ephemeral、episodic、intermittent、interrupted、irregular、non-perennial、non-permanent、seasonal和temporary，并要求术语与流水水体词相邻。为排除描述连续流动的论文，semi-perennial/non-perennial以及permanent/non-permanent采用分开检索后再合并的方式（第3–4页）。
- 摘要经过分词、去除标点和数字、词干化及删除英文停用词；所有分析均在R中进行（第4页）。
- 对于术语主题差异（O1），使用Fisher精确检验比较WoS类别间的术语数量，并利用`textmineR`实施Bayesian latent Dirichlet allocation（LDA）。作者以概率一致性（probabilistic coherence）评估1–50个主题的候选模型，选择6个主题，再使用`vegan`进行非度量多维尺度分析（nMDS），比较各术语的平均文档—主题概率（第4–5页）。
- 对于时间变化（O2），按时间段重复WoS检索，用Fisher精确检验比较术语数量，并对合并后的时间序列语料库另做LDA；根据一致性计算选择9个主题（第5页）。
- 对于定义（O3），以词频—逆文档频率（tf-idf）筛选术语与“river”或“stream”相邻且较重要的论文。每个术语最多选择50篇（“river”和“stream”各25篇）；因许多论文未给定义，又从每个语料库随机增加最多25篇，随后人工提取并清理定义（第5页）。
- 定义语料过小，不能使用LDA，因此作者按照水源、可预测性、时间尺度、气候和干涸阶段等主题人工编码，以Euclidean distance进行nMDS。初次排序后删除了两个占比很低的主题，并删除仅有一条定义的“irregular”（第5–6页）。
- 作者以“样本文献中超过80%确实研究非永久性河流”为标准，比较生态学、水文学和生态水文学对5个术语的用法：non-perennial（100%）、ephemeral（98%）、temporary（89%）、intermittent（88%）和arid（83%）（第6页；此处为原文四舍五入值）。

### 关键参数与阈值

| 参数 | 数值 | 含义 |
|---|---:|---|
| 文献检索期 | 1900-01-01至2019-05-30 | WoS发表时间范围（第3页） |
| 术语数量 | 12 | 被比较的替代性描述词（第3–4页） |
| 流水水体词数量 | 41 | 宽检索中与术语配对的词（第3–4页） |
| WoS类别限制 | 37类 | 用于缩小检索范围的自然科学类别（第4页） |
| 主分析文献量 | 11,696篇 | 方法与表1总数（第4页）；附录A报告11,989篇摘要（第16页） |
| LDA候选主题数 | 1–50 | 通过概率一致性评估的范围（第4页） |
| 完整语料最终主题数 | 6 | O1的LDA模型（第4–5页） |
| 时间序列最终主题数 | 9 | O2的LDA模型（第5页） |
| 定义筛选上限 | 每个术语50篇 | tf-idf排序后“river”和“stream”各最多25篇（第5页） |
| 追加定义样本 | 每个语料库25篇 | 因初始论文常无定义而增加的随机样本（第5页） |
| 定义分析样本 | 672篇 | 每个术语最少28篇、最多75篇（第5页） |
| 跨学科比较标准 | >80% | 样本文献确实讨论非永久性河流的比例（第6页） |
| nMDS解释标准 | stress < 0.2 | 作者认为二维表示良好的标准（第7页） |

## 5. 主要研究结果

1. 学科内部与学科之间均缺乏术语共识；每个被分析的WoS类别至少包含6种术语。LDA得到4个主要术语组，其中最大组包含arid、dry、intermittent、non-permanent、seasonal和temporary，并与农业、水文及植被主题关联；non-perennial单独形成最小组，与生态水文学最接近。完整语料主题nMDS的stress为0.1029（第6–7页）。
2. 1990年前后，发表速率由每年16.1篇显著增加到154.2篇。“Seasonal”长期最常见，而temporary、non-perennial和intermittent的增长率最大。1991–1995年至2016–2018年，农业和地貌学主题占比分别下降9%和6%，水文学与建模分别增加14%和5%；群落生态学从1996–2000年至2016–2018年增加6%（第7–9页）。
3. 在用于定义分析的672篇论文中，452篇（67%）确实涉及非永久性河流；全部论文的54%没有给出术语定义，而在452篇相关论文中这一比例为39%。作者最终收集315条定义。定义主题显示intermittent、temporary与non-perennial直接重叠，定义主题nMDS的stress为0.0962（第9–11页）。
4. 作者建议保留3个术语。**Non-perennial（非永久性）**是上位概念，指在某个时间和/或空间位置周期性停流和/或干涸的流水淡水系统。**Intermittent（间歇性）**指与地下水位有显著联系、经历可变的湿润—停流周期、流动持续时间长于单次暴雨事件，并且长期总体上以河流补给（gaining）为主的非永久性河流。**Ephemeral（短暂性/暴雨响应型）**指缺乏显著地下水联系、仅短时间流动且通常只在降水事件后出现水流，并且长期总体上以河流失水（losing）为主的一类非永久性河流（第15页）。
5. 这些建议是定性的，而非固定持续时间阈值。作者认为定量分类虽有价值，但必须考虑非永久性水系常缺少水文资料的现实；无论采用何种术语，都应在引言前部明确给出或引用定义，并在可能时用定量分析或测量支撑站点分类（第14–15页）。

## 6. 验证

- **验证数据：** 论文中未明确说明独立验证数据集；本文是文献计量综合，并未产出预测性的河流分类产品。
- **验证方法：** 未进行外部验证。作者用概率一致性选择LDA主题数，用nMDS stress评价二维排序，并通过人工审阅和编码收集、归类定义（第4–6页）。
- **评价指标：** 概率一致性、nMDS stress，以及论文、定义、术语、类别和主题的数量与比例。
- **主要验证结果：** 完整语料主题nMDS的stress = 0.1029（第7页），定义主题nMDS的stress = 0.0962（第11页），均低于作者提出的0.2良好表示标准。论文中未报告编码者间一致性统计量或独立验证结果。

## 7. 局限性

### 作者明确指出的局限

- 尽管限制了术语、水体词和WoS类别，仍有与非永久性河流无关的论文进入语料库；逐篇检查整个数据集超出研究范围，因而这些论文可能影响结果（第14页）。
- 综述仅依赖WoS；Google Scholar等数据库可能返回不同文献，现有方法也可能遗漏相关研究（第14页）。
- 检索未限制发表语言，但文本分析假定文本为英文（第3页）。
- 最后一个发表时间段不完整，因为检索止于2019年5月（第7页）。
- 基于停流持续时间的定量定义需要水文资料，而这些资料在非永久性水系中往往缺失（第2、14页）。

### 我的分析

- 语料总数存在内部不一致：方法与表1为11,696篇（第4页），附录A为11,989篇摘要（第16页）。复现分析前应先核实。
- 人工定义提取和主题编码没有报告编码者间一致性，因此无法从论文判断定性编码的可重复性。
- 相邻词检索与一词多义会引入领域污染；作者已记录化学和酸化研究中与流动持续性无关的命中（第9、12–14页）。
- intermittent与ephemeral的区分依赖“显著”地下水联系以及长期以gaining或losing为主，但没有给出操作阈值、观测窗口或测量方案。因此该体系适合作为概念框架，却不能单独构成可复现的分类算法。

## 8. 与我的研究的关系

### 可以直接使用

- 将**non-perennial**作为总类，并依据地下水联系、对暴雨事件的依赖及长期gaining/losing特征区分**intermittent**与**ephemeral**（第15页）。
- 在分析开头明确操作性定义并记录分类所依据的观测量。合并水体出现频率、流量、河宽、河流横截面积或河网数据时尤其需要这样做，因为这些观测量不能自动等同于地下水联系（第15页）。
- 区分“无流动（no flow）”与“无地表水（no surface water）”；本文的定义主题分析将二者作为不同干涸状态（第5、10–11页）。

### 可能有用

- “广义同义词检索—主题模型—tf-idf优先抽样—人工定义提取—定义主题排序”的流程可用于可复现的术语或方法综述（第3–6页）。
- 定量定义稀缺这一结果支持在分类中开展阈值敏感性分析，而不是直接采用没有文献依据的固定持续性阈值（第14页）。
- 术语与定义主题的nMDS图可用于展示不同河流类别之间的重叠（第10–11页）。

### 与我的研究不同 / 不适用

- 本文不提供全球河流地图、空间分辨率、地表水时间产品、流量阈值、河宽阈值或横截面积阈值。
- 本文未评估JRC Global Surface Water、HydroRIVERS、CaMa-Flood或其他河网/模型数据集。
- 推荐定义需要地下水与事件持续时间信息，仅凭地表水出现频率可能无法观测；用于栅格分类前还需建立操作规则并以独立数据验证。

## 9. 可以借鉴的内容

- **数据集：** WoS Core Collection检索策略及12个术语的词表；论文第16页提供补充检索材料和分析代码链接。
- **方法：** LDA主题模型、tf-idf引导与随机补充相结合的定义抽样、人工主题编码和nMDS（第4–6页）。
- **阈值 / 参数：** 跨学科术语比较采用>80%相关性筛选，nMDS采用stress < 0.2作为良好二维表示标准（第6–7页）；论文未提出水文持续时间阈值。
- **验证方法：** 未来分类研究可将三个概念术语操作化，并用停流观测、地下水联系、事件响应及gaining/losing状态的独立资料验证；这是我的延伸建议，并非本文实施的验证。
- **图表 / 可视化思路：** 用nMDS或类似相似性图连接术语与定义主题，并配合术语流行度时间序列（图3–5，第7–11页）。

---

## Important Evidence | 重要证据

> “Any lotic, freshwater system that periodically ceases to flow and/or is dry at some point in time and/or space.”

**Page:** 15

- The authors explicitly make non-perennial the umbrella term and distinguish intermittent from ephemeral primarily by groundwater connection, event-scale persistence, and long-term gaining versus losing behavior (p. 15).
- Quantitative definitions are considered useful, but the authors reject overly specific universal cutoffs when the necessary hydrologic data are commonly unavailable (p. 14).

## Questions & Follow-up | 问题与后续工作

- [ ] Resolve the 11,696-versus-11,989 corpus-size discrepancy before reproducing the bibliometric analysis (pp. 4, 16).
- [ ] Define measurable proxies and sensitivity ranges for “considerable groundwater connection,” “longer than a single storm event,” and majority gaining/losing behavior before applying the terminology to mapped river reaches (p. 15).

## Related Papers | 相关论文

- Datry et al. (2014), *Intermittent Rivers: A Challenge for Freshwater Ecology* (cited in this paper as a major synthesis motivating standardized terminology).
- Gallart et al. (2012), a quantitative regime-classification approach for temporary streams referenced by the authors (cited on pp. 2 and 14).

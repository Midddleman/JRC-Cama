---
title: "Global prevalence of non-perennial rivers and streams"
authors: "Mathis Loïc Messager; Bernhard Lehner; Charlotte Cockburn; Nicolas Lamouroux; Hervé Pella; Ton Snelder; Klement Tockner; Tim Trautmann; Caitlin Watt; Thibault Datry"
year: 2021
journal: Nature
doi: 10.1038/s41586-021-03565-5
tags: [non-perennial-rivers, intermittent-rivers, ephemeral-streams, flow-intermittence, random-forest, RiverATLAS, WaterGAP, remote-sensing, global-mapping]
status: read
relevance: very-high
primary_stage: "Stage 2: Existing Methods for Identifying River Flow Permanence"
secondary_stages: ["Stage 1: Fundamental Concepts and Importance of Perennial and Non-Perennial Rivers", "Stage 3: Discharge-Threshold Methods in Hydrological Models", "Stage 6: Application of JRC Global Surface Water to River Permanence Identification"]
---

# Literature Review Classification | 文献综述分类

- **Primary Stage | 主要阶段:** Stage 2 — Existing Methods for Identifying River Flow Permanence（阶段2：现有河流持续性识别方法）。论文以流量站零流量记录为标签，通过分尺度随机森林（random forest, RF）在RiverATLAS河段上预测全球水流间歇概率，并实施非空间和空间交叉验证及地面观测对比（第2–6、8–11、21、24、27页）。
- **Secondary Stage(s) | 次要阶段:** Stage 1 — Fundamental Concepts and Importance（阶段1：基本概念与重要性），因为论文明确采用“年均至少1个零流量日”的包容性定义并量化全球普遍程度；Stage 3 — Discharge-Threshold Methods（阶段3：水文模型中的流量阈值方法），因为论文分析不同零流量定义、按mean annual flow（MAF）分尺度建模，并设定全球逐河段预测的最低MAF范围；Stage 6 — Application of Surface-Water Remote Sensing（阶段6：地表水遥感在河流持续性识别中的应用），因为30 m Landsat地表水动态类别被聚合为模型候选预测变量，但该产品不是JRC Global Surface Water（第1–4、8–10、15页）。
- **Contribution | 主要贡献:** The study provides the first empirically trained, reach-scale global estimate of non-perennial rivers and streams (IRES). It distinguishes a zero-flow-based target definition from discharge variables used as predictors and model-domain limits. For the current research, it offers a directly relevant global workflow, benchmark labels, validation design, scale-dependent modeling strategy, and evidence that discharge alone is insufficient. It does not derive a cross-sectional-area-dependent threshold `Q_threshold = f(A)`（该研究首次基于全球实测资料，在河段尺度估计非永久性河流分布。它明确区分“基于零流量的目标标签”“作为预测量的流量变量”以及“模型适用范围的流量下限”。对当前研究而言，它提供了可直接借鉴的全球流程、标签定义、验证方案和尺度分层思路，也表明仅靠流量不足；但并未推导随横截面积变化的阈值函数）。

---

## Paper Information | 论文信息

- **Title | 标题:** Global prevalence of non-perennial rivers and streams
- **Authors | 作者:** Mathis Loïc Messager; Bernhard Lehner; Charlotte Cockburn; Nicolas Lamouroux; Hervé Pella; Ton Snelder; Klement Tockner; Tim Trautmann; Caitlin Watt; Thibault Datry
- **Year | 年份:** 2021
- **Journal | 期刊:** Nature, 594, 391–397
- **DOI:** 10.1038/s41586-021-03565-5

---

## English Summary

## 1. Research Question

The paper asks how prevalent non-perennial rivers and streams are globally, where they occur, and which hydro-environmental factors predict flow cessation. It develops an empirically trained model to classify individual global river reaches and then extrapolates the prevalence estimate to smaller streams that cannot be mapped confidently reach by reach (pp. 1–3, 8–10).

## 2. Background

Intermittent rivers and ephemeral streams (IRES) span all non-perennial watercourses, from large rivers that cease flowing rarely to mostly dry streams that flow only after intense rainfall (p. 1). They support biodiversity, biogeochemical processing, environmental flows, human livelihoods, and cultural values, yet global stream-gauge networks preferentially sample large perennial rivers and existing IRES maps were local, regional, or based on restrictive assumptions such as occurrence only in arid regions (pp. 1–3). The lack of a global map has limited monitoring, management, conservation, and Earth-system upscaling (pp. 1, 6).

## 3. Data

- **Dataset(s):** RiverATLAS v1.0/HydroATLAS, built on HydroSHEDS, supplied the river network and most hydro-environmental variables. Training and cross-validation labels came from GRDC and a selected subset of GSIM stream gauges. Predictors included WaterGAP 2.2 naturalized discharge, Global Environmental Stratification climate zones, SoilGrids250m v2, WorldClim v2, Global Aridity Index/Global-PET v2, groundwater, geology, land cover, physiography, and 30 m Landsat-derived interannual open-water dynamics. HydroLAKES removed river sections within lakes. WorldPop 2020 supported the population-near-IRES analysis (pp. 2, 8–10, 22, 26).
- **Spatial resolution:** HydroSHEDS drainage data originated at 3 arcseconds (about 90 m at the equator) and were upscaled to 15 arcseconds (about 500 m). Most predictor grids were 250–1,000 m. The open-water dynamics product had 30 m pixels. The prediction unit was a RiverATLAS segment between adjacent confluences; 6,198,485 mapped reaches averaged 3.8 km long (pp. 6, 8–9).
- **Temporal resolution:** GRDC generally supplied daily discharge, while GSIM supplied yearly, seasonal, and monthly indices computed from daily records. WaterGAP flow climatologies represented long-term mean monthly and annual flow. The surface-water dynamics layer summarized annual open-water percentages into seven interannual classes (pp. 8–9).
- **Study period:** WaterGAP naturalized flow represented 1971–2000. The remote-sensing predictor covered 1999–2019 as stated in the Methods. Gauge records had to span at least 10 valid years; perennial and non-perennial stations contained mean record lengths of 41 and 34 years, respectively (pp. 8–9).
- **Study area / coverage:** All continents except Antarctica. Reach-level predictions covered 23.3 million km of mapped river network with MAF ≥ 0.1 m³ s⁻¹; aggregate extrapolation extended to nearly 64 million km with MAF ≥ 0.01 m³ s⁻¹ (pp. 2, 8, 10).

## 4. Methodology

### Overall Approach

- The authors associated quality-controlled gauge records with RiverATLAS reaches. They excluded stations potentially dominated by reservoir regulation (degree of regulation >50%), records with altered intermittence class, anomalous zero values, records shorter than 10 valid years, and years with more than 20 missing days (p. 8).
- The primary label defined a reach as non-perennial when discharge equalled zero for at least one day per year on average over the record. A non-perennial station also had to contain at least one zero-flow day in every 20-year moving window; otherwise it was excluded as potentially reflecting an exceptional drought or a regime shift. The final training set contained 5,615 gauges: 4,428 perennial and 1,187 non-perennial (p. 8; Extended Data Fig. 8, p. 24).
- A sensitivity dataset used at least one zero-flow month—30 consecutive or non-consecutive days—per year on average, yielding 4,735 perennial and 880 non-perennial stations (p. 8).
- The model started from 113 candidate predictors describing hydrology, climate, physiography, land cover, soil, geology, groundwater, and remotely sensed open-water dynamics. Derived predictors included runoff coefficient, specific discharge, and temporal and spatial ratios (pp. 2, 8–9).
- The authors trained two probability RF sub-models: small-to-medium rivers with MAF < 10 m³ s⁻¹ and medium-to-large rivers with MAF ≥ 1 m³ s⁻¹. Predictions were averaged in the overlapping 1–10 m³ s⁻¹ range to avoid a discontinuity. Random oversampling addressed class imbalance; the perennial:non-perennial ratios were 1.98:1 for small rivers and 4.87:1 for large rivers (p. 9).
- Hyperparameters were tuned in a nested resampling design: fourfold inner cross-validation, twice-repeated threefold outer non-spatial cross-validation, and a separate 40-fold spatial cross-validation. Random hyperparameter search stopped after 100 iterations. Variables with importance p < 0.05 based on 100 permutations were retained, leaving 92 variables for the small-river model and 82 for the large-river model (p. 9).
- Reaches with predicted intermittence probability ≥0.5 were classified as non-perennial. The authors tested probability thresholds from 0.25 to 0.75 and found balanced performance at 0.5 (p. 10).
- The RF produced individual-reach predictions only where MAF ≥ 0.1 m³ s⁻¹. To estimate smaller streams with 0.01 ≤ MAF < 0.1 m³ s⁻¹, generalized additive models (GAMs) extrapolated stream length and intermittence prevalence within 465 basin–climate subunits formed from 62 basin regions and 18 climate zones (p. 10).
- Validation and comparison included non-spatial and spatial cross-validation, analysis of residuals and spatial bias, comparison with national hydrographic datasets, and independent comparison with visual flow-state observations from mainland France and the US Pacific Northwest (pp. 3–6, 9–11, 16–21, 27).

### Key Parameters and Thresholds

| Parameter | Value | Meaning |
|---|---:|---|
| Primary IRES label | ≥1 zero-flow day yr⁻¹ on average | Inclusive flow-intermittence definition (pp. 1, 4, 8) |
| Persistence safeguard | ≥1 zero-flow day in every 20-year moving window | Required for non-perennial training labels to exclude exceptional drought/regime shifts (p. 8) |
| Sensitivity label | ≥30 zero-flow days yr⁻¹ on average | Alternative one-month definition; days may be consecutive or non-consecutive (pp. 4, 8) |
| Minimum gauge record | 10 valid years | Training-data inclusion requirement (p. 8) |
| Valid year | ≤20 missing days | Missing-data filter (p. 8) |
| Reservoir regulation exclusion | >50% degree of regulation | Removed potentially regulation-dominated stations (p. 8) |
| Final gauge sample | 5,615 | 4,428 perennial and 1,187 non-perennial reaches (pp. 2, 8) |
| Candidate predictors | 113 | Global hydro-environmental variables (pp. 2, 9) |
| Small-river RF | MAF < 10 m³ s⁻¹ | One of two overlapping sub-models (p. 9) |
| Large-river RF | MAF ≥ 1 m³ s⁻¹ | Second sub-model; probabilities averaged at 1–10 m³ s⁻¹ (p. 9) |
| RF classification threshold | probability ≥0.5 | Binary non-perennial classification (pp. 2, 10) |
| Reach-level prediction domain | MAF ≥ 0.1 m³ s⁻¹ | Reliability/domain cutoff, not an IRES definition (pp. 2, 8, 10) |
| Aggregate extrapolation domain | 0.01 ≤ MAF < 0.1 m³ s⁻¹ | Smaller-stream class estimated by GAM, not reach-level RF (p. 10) |
| Predictor selection | p < 0.05 | Importance screening from 100 permutations (p. 9) |
| Spatial cross-validation | 40 folds | Designed to reduce spatial-autocorrelation optimism (pp. 4, 9) |

## 5. Main Results

1. For mapped reaches with MAF ≥ 0.1 m³ s⁻¹, 41% of global river length was predicted to cease flowing for at least one day per year on average. Including GAM extrapolation down to MAF ≥ 0.01 m³ s⁻¹ increased the main estimate to 60%; a conservative extrapolation gave a lower bound of 51% (pp. 1–3, 10).
2. Intermittence was strongly size-dependent in the global accounting: the predicted non-perennial shares by MAF class were 70% for 0.01–<0.1, 47% for 0.1–<1, 35% for 1–<10, 26% for 10–<100, 9% for 100–<1,000, 1% for 1,000–<10,000, and 0% for ≥10,000 m³ s⁻¹ (Table 1, p. 3). These are prevalence estimates by discharge class, not deterministic discharge cutoffs for individual reaches.
3. Climate-induced aridity was a leading predictor. Approximately 95% of river-network length in extremely hot and xeric environments was prone to cessation for MAF ≥ 0.01 m³ s⁻¹, but IRES also occurred in every climate and biome. Even the wettest climate class contained up to 35% non-perennial headwater streams (p. 3).
4. Using the stricter one-zero-flow-month definition, the global extrapolated prevalence was 44–53%, compared with 51–60% under the one-day definition (p. 4; Extended Data Fig. 1, p. 15).
5. Overall cross-validated classification accuracy was 90–92% depending on the cross-validation design, with no global bias, but accuracy declined and bias increased in sparsely gauged basins and near hydroclimatic transition zones (pp. 3–5).
6. Fine-scale transfer was substantially weaker. Against independent visual observations, mainland France (n = 2,297 reaches) had balanced accuracy 0.59, classification accuracy 51%, sensitivity 24%, and specificity 94%; the US Pacific Northwest (n = 3,725) had balanced accuracy 0.47, classification accuracy 80%, sensitivity 10%, and specificity 83% (Extended Data Fig. 6, p. 21).
7. National comparisons were definition- and source-dependent. The US national dataset mapped 19–22% of comparable river length as non-perennial versus model estimates of 51% under the one-day definition and 36% under the one-month definition. Australia showed 91% in the reference dataset versus 95% and 92%, respectively. France's national model estimated 17%, whereas this study predicted 14% (pp. 4, 17, 19–20). The authors explicitly do not treat national-map comparisons as accuracy assessments (p. 11).
8. The study estimated that the nearest river or stream was non-perennial for 52% of the world's population in 2020 (p. 6).

## 6. Validation

- **Validation dataset:** Primary model validation used the 5,615 quality-controlled GRDC/GSIM gauges through cross-validation. WaterGAP downscaled discharge was separately checked against 2,131 GRDC gauges with at least 20 years of data during 1971–2000. Independent local comparisons used 124,112 ONDE observations on 2,297 French reaches and 5,372 observations on 3,725 US Pacific Northwest reaches. National maps/models for the contiguous USA, Australia, Brazil, Argentina, and France were used as benchmarks rather than formal accuracy references (pp. 8–11, 17–21).
- **Validation method:** Twice-repeated threefold non-spatial cross-validation; 40-fold spatial cross-validation; classification residual and basin bias analysis; sensitivity analysis of the RF probability threshold and zero-flow-duration definition; visual-observation comparison; and national hydrographic-map comparison (pp. 3–5, 9–11).
- **Metrics:** Balanced accuracy, classification accuracy, sensitivity, specificity, precision, intermittence prediction residual, bias, residual spatial autocorrelation, R², and symmetric mean absolute percentage error (sMAPE) (pp. 4, 8–10, 21, 27).
- **Main results:** Overall RF classification accuracy was 90–92% (pp. 3–4). Local independent balanced accuracy was 0.59 in France and 0.47 in the US Pacific Northwest, with low IRES sensitivity of 24% and 10%, respectively (p. 21). WaterGAP downscaled MAF versus gauges yielded R² = 0.96 and sMAPE = 30%; sMAPE increased from 5% for MAF ≥ 1,000 m³ s⁻¹ to 20% for 10 ≤ MAF < 1,000 and 52% for MAF < 10 m³ s⁻¹. Minimum monthly discharge was a proxy for Q90 with R² = 0.84 (pp. 8–9).

## 7. Limitations

### Stated by the Authors

- Fine-scale predictions for small rivers and spatial units should be used cautiously; most predictors have 250–1,000 m resolution, which cannot fully represent reach- and subcatchment-scale soil, lithology, riverbed sediment, or groundwater processes (p. 6).
- Groundwater–surface-water interaction is only partially represented and remains difficult in global hydrological modeling (p. 6).
- Gauge networks under-represent small streams, arid regions, extreme climates, high-snow catchments, shallow-groundwater systems, and strongly karstic catchments; large rivers are over-represented (pp. 6, 8).
- Global hydrological models tend to overestimate flow in arid climates, adding uncertainty where IRES prevalence is high (p. 6).
- Human effects could not be completely separated despite excluding regulated/altered gauges and using naturalized discharge predictors (p. 6).
- Individual-reach RF predictions were not produced below MAF 0.1 m³ s⁻¹ because only 59 gauges met the small-stream and record-length conditions, only 13 of those were perennial, and RiverATLAS is discontinuous below that MAF (p. 10).
- National hydrographic datasets contain inconsistent mapping and uncertain classes; NHDPlus intermittence errors can reach 50%, so national comparisons are not independent accuracy assessments (p. 11).

### My Assessment

- The target is gauge-recorded zero discharge, whereas JRC-derived labels represent detectable open surface water. These observables differ: disconnected pools may remain visible during zero flow, and narrow flowing rivers may be missed by 30 m imagery. A direct JRC-to-IRES transfer therefore needs an explicit observation model.
- The primary one-day-per-year definition is deliberately inclusive and materially changes prevalence relative to the one-month definition. Any comparison with another classification must harmonize thresholds before interpreting disagreement as model error.
- `MAF ≥ 0.1 m³ s⁻¹` is a mapping-domain cutoff, not a physical boundary between perennial and non-perennial rivers. Treating it as a permanence threshold would invert the study design.
- The RF size split at 1 and 10 m³ s⁻¹ addresses class imbalance and prediction performance rather than deriving a hydraulic law. It cannot be interpreted as evidence for a piecewise `Q_threshold = f(A)` relationship.
- The contrast between 90–92% cross-validated accuracy and weak independent small-stream sensitivity demonstrates strong scale and transferability limits. Global aggregate prevalence may be robust while local reach labels remain unreliable.
- Cross-sectional area, channel width, and depth were not used to derive a hydraulic threshold. MAF and specific discharge encode river size indirectly, but they do not test whether geometry-normalized discharge better separates classes.

## 8. Relevance to My Research

### Directly Useful

- The paper provides a rigorous gauge-based label definition: zero flow for at least one day per year on average, with a 20-year-window safeguard. The one-month alternative supplies a useful sensitivity scenario rather than a universally preferred threshold (pp. 4, 8).
- It shows how to separate three kinds of thresholds: the observed class definition (zero-flow duration), the classifier probability threshold (0.5), and the model-domain MAF cutoff (0.1 m³ s⁻¹). The current research should keep these conceptually and diagnostically separate.
- Splitting models by river size and averaging probabilities across an overlapping range offers a precedent for allowing size-dependent classification without an abrupt single threshold (p. 9). This supports testing flexible `Q_threshold = f(A)` formulations but does not establish one.
- The spatial cross-validation and local independent comparisons are directly reusable validation principles. Random splits alone would overstate performance because nearby reaches share climate, physiography, and network characteristics (p. 9).
- The results establish strong size dependence in prevalence, but also show that climate, aridity, soil moisture, slope, runoff, groundwater, and specific discharge carry major predictive information. An area-and-discharge model should be benchmarked against these additional controls (pp. 3–4, 9, 26).

### Potentially Useful

- RiverATLAS supplies reach topology and upstream/local-catchment attributes and could serve as a common spatial framework for matching CaMa-Flood, gauge, and remote-sensing observations (pp. 2, 8–9).
- The paper's aggregation of 30 m surface-water dynamic classes over both local contributing catchments and entire upstream drainage areas offers a multi-scale remote-sensing feature design. However, it predicts intermittence jointly with many other variables rather than treating water presence as ground truth (p. 9).
- WaterGAP error increases sharply in smaller rivers (sMAPE 52% for MAF < 10 m³ s⁻¹), illustrating why model-discharge uncertainty should be propagated into threshold fitting and why performance should be stratified by river size (pp. 8–9).
- The published probability map, attributes, code, and outputs enable benchmark comparisons and targeted sampling of regions where a CaMa-Flood/JRC classifier disagrees with the RF prediction (pp. 11–12).

### Differences / Not Applicable

- The study uses WaterGAP 2.2 naturalized discharge, not CaMa-Flood discharge or channel geometry.
- It does not use JRC Global Surface Water as the response label. A different 30 m Landsat-based interannual water-dynamics product is included only among the predictors (p. 9).
- It predicts the probability of at least one zero-flow day per year, not monthly/seasonal surface-water occurrence and not instantaneous flow state.
- It does not estimate river cross-sectional area or fit an explicit discharge–area boundary.
- Predictions aim to represent natural intermittence; JRC observations may include effects of contemporary abstractions, impoundments, and land use that the model tried to exclude (pp. 5–6, 8).

## 9. What I Can Reuse

- **Dataset:** RiverATLAS reach network and attributes; GRDC/GSIM gauges; published global intermittence probabilities/classes; WaterGAP naturalized flow; SoilGrids, WorldClim, aridity/PET, geology and groundwater layers; independent ONDE and US Pacific Northwest visual observations where accessible (pp. 8–12, 22).
- **Method:** Quality-controlled gauge labels; overlapping size-stratified RF models; nested tuning; spatial cross-validation; probability-threshold sensitivity; zero-flow-definition sensitivity; residual mapping; and independent local validation (pp. 8–11).
- **Threshold / parameter:** ≥1 zero-flow day yr⁻¹ as the primary label; ≥30 zero-flow days yr⁻¹ as sensitivity; probability ≥0.5 for binary RF classification; MAF ≥0.1 m³ s⁻¹ for reach-level global prediction. These thresholds serve different purposes and must not be conflated.
- **Validation strategy:** Report non-spatial and spatial cross-validation separately; stratify sensitivity/specificity by river size and geography; use independent repeated wet/dry observations for small rivers; examine bias in sparsely gauged regions; and test multiple temporal definitions of non-perennial flow.
- **Figure / visualization idea:** Reuse the probability-based global river map, discharge-class prevalence table, basin-level accuracy/bias maps, and predictor partial-dependence plots. For the current project, add discharge–cross-sectional-area panels stratified by climate/aridity and spatial validation fold.

---

## 中文总结

## 1. 研究问题

本文研究全球非永久性河流与溪流（intermittent rivers and ephemeral streams, IRES）究竟有多普遍、分布在哪里，以及哪些水文—环境条件可以预测水流停止。作者建立以全球流量站实测零流量记录为标签的统计模型，对单个全球河段进行分类，并将总体比例外推到无法可靠逐段制图的更小溪流（第1–3、8–10页）。

## 2. 研究背景

IRES涵盖全部非永久性流水水体，从很少停流、几乎全年连通的大河，到仅在强降雨后短暂流动的干溪（第1页）。它们对生物多样性、生物地球化学过程、环境流量、人类生计和文化具有重要作用，但全球水文站网偏向大型永久性河流，既有IRES地图多局限于局地或区域，部分全球产品甚至假定停流只发生在干旱和半干旱区（第1–3页）。缺乏全球制图妨碍了监测、管理、保护和地球系统尺度估算（第1、6页）。

## 3. 数据

- **数据集：** 河网及大部分水文—环境变量来自基于HydroSHEDS的RiverATLAS v1.0/HydroATLAS；训练和交叉验证标签来自GRDC以及经筛选的GSIM流量站。预测变量包括WaterGAP 2.2自然化流量、Global Environmental Stratification气候区、SoilGrids250m v2、WorldClim v2、Global Aridity Index/Global-PET v2、地下水、地质、土地覆盖、地形及30 m Landsat年际开放水体动态。HydroLAKES用于排除湖内河段，WorldPop 2020用于估计居住在IRES附近的人口（第2、8–10、22、26页）。
- **空间分辨率：** HydroSHEDS排水数据源自3 arcseconds（赤道约90 m），随后上尺度至15 arcseconds（约500 m）；多数预测变量为250–1,000 m；开放水体动态产品为30 m。预测单元是两个相邻汇流点之间的RiverATLAS线段，共6,198,485个河段，平均长度3.8 km（第6、8–9页）。
- **时间分辨率：** GRDC主要提供日流量，GSIM提供由日记录计算的年度、季节和月尺度指标。WaterGAP变量为长期平均月流量和年平均流量。遥感水体层根据年度开放水体百分比时间序列划分7种年际动态类别（第8–9页）。
- **研究时期：** WaterGAP自然化流量代表1971–2000年；Methods称遥感预测变量覆盖1999–2019年。流量站记录至少包含10个有效年份；永久性与非永久性站点的平均记录长度分别为41年和34年（第8–9页）。
- **研究区域 / 覆盖范围：** 除南极洲外的所有大陆。逐河段预测覆盖MAF ≥ 0.1 m³ s⁻¹的2,330万km河网；总体外推覆盖MAF ≥ 0.01 m³ s⁻¹的近6,400万km河网（第2、8、10页）。

## 4. 研究方法

### 整体方法

- 作者将经过质量控制的流量站记录匹配到RiverATLAS河段。排除可能主要受水库调控的站点（degree of regulation >50%）、持续性类别发生变化的记录、异常零值、少于10个有效年份的记录，以及缺测超过20天的年份（第8页）。
- 主标签把多年记录中平均每年至少出现1个零流量日的河段定义为非永久性。此外，每个20年移动窗口内都必须至少有1个零流量日；否则该站因可能代表异常干旱或流态转变而被排除。最终训练集含5,615个站点，其中4,428个永久性、1,187个非永久性（第8、24页）。
- 敏感性分析采用“平均每年至少1个零流量月”，即30个连续或不连续零流量日，得到4,735个永久性和880个非永久性站点（第8页）。
- 初始使用113个候选预测变量，描述水文、气候、地形、土地覆盖、土壤、地质、地下水和遥感水体动态；衍生指标包括径流系数、比流量及时间/空间比值（第2、8–9页）。
- 训练两个概率RF子模型：MAF < 10 m³ s⁻¹的小—中型河流模型，以及MAF ≥ 1 m³ s⁻¹的中—大型河流模型；在重叠的1–10 m³ s⁻¹范围对概率取平均，避免单一尺度界限造成突变。用随机过采样处理类别不平衡；小河与大河的永久性:非永久性样本比分别为1.98:1和4.87:1（第9页）。
- 采用嵌套重采样调参：内层四折交叉验证，外层重复两次的三折非空间交叉验证，另做40折空间交叉验证；随机超参数搜索在100次迭代后终止。基于100次置换，以变量重要性p < 0.05筛选，最终小河模型保留92个变量，大河模型保留82个（第9页）。
- 预测间歇概率≥0.5的河段被分类为非永久性。作者测试了0.25–0.75的概率阈值，0.5时模型表现较平衡（第10页）。
- RF只对MAF ≥ 0.1 m³ s⁻¹的河段逐段预测。对于0.01 ≤ MAF < 0.1 m³ s⁻¹的小溪，作者在62个流域区与18个气候区组合形成的465个流域—气候子区中，使用广义加性模型（GAM）外推河网长度和间歇比例（第10页）。
- 验证与比较包括非空间和空间交叉验证、残差与空间偏差分析、国家河网资料比较，以及法国本土和美国太平洋西北地区的独立地面流态观测比较（第3–6、9–11、16–21、27页）。

### 关键参数与阈值

| 参数 | 数值 | 含义 |
|---|---:|---|
| 主IRES标签 | 年均≥1个零流量日 | 包容性的水流间歇定义（第1、4、8页） |
| 持续性保障条件 | 每个20年移动窗口内≥1个零流量日 | 排除异常干旱或类别转变造成的非永久性标签（第8页） |
| 敏感性标签 | 年均≥30个零流量日 | “1个零流量月”定义；可连续或不连续（第4、8页） |
| 最短站点记录 | 10个有效年份 | 训练数据纳入条件（第8页） |
| 有效年份 | 缺测≤20天 | 缺测过滤条件（第8页） |
| 水库调控排除 | degree of regulation >50% | 排除可能受调度主导的站点（第8页） |
| 最终流量站样本 | 5,615个 | 4,428个永久性与1,187个非永久性河段（第2、8页） |
| 候选预测变量 | 113个 | 全球水文—环境变量（第2、9页） |
| 小河RF | MAF < 10 m³ s⁻¹ | 两个重叠子模型之一（第9页） |
| 大河RF | MAF ≥ 1 m³ s⁻¹ | 第二个子模型；在1–10范围平均概率（第9页） |
| RF分类阈值 | 概率≥0.5 | 二元非永久性判定（第2、10页） |
| 逐河段预测范围 | MAF ≥ 0.1 m³ s⁻¹ | 可靠性/适用域下限，不是IRES定义（第2、8、10页） |
| 总体外推范围 | 0.01 ≤ MAF < 0.1 m³ s⁻¹ | 用GAM估计的小溪尺度，不是逐段RF预测（第10页） |
| 变量筛选 | p < 0.05 | 根据100次置换的重要性筛选（第9页） |
| 空间交叉验证 | 40折 | 用于降低空间自相关导致的乐观偏差（第4、9页） |

## 5. 主要研究结果

1. 对MAF ≥ 0.1 m³ s⁻¹的已制图河段，全球河网长度的41%被预测为平均每年至少停流1天。将GAM外推纳入MAF ≥ 0.01 m³ s⁻¹后，主估计为60%，保守外推的下限为51%（第1–3、10页）。
2. 全球比例随河流尺度明显变化：按MAF分组，非永久性比例分别为0.01–<0.1：70%，0.1–<1：47%，1–<10：35%，10–<100：26%，100–<1,000：9%，1,000–<10,000：1%，≥10,000 m³ s⁻¹：0%（表1，第3页）。这些是各流量等级中的总体比例，不能解释为单条河流的确定性流量阈值。
3. 气候干旱度是主要预测因素之一。在MAF ≥ 0.01 m³ s⁻¹条件下，极热且干燥（xeric）环境中约95%的河网长度可能停流，但IRES存在于所有气候和生物群系；即使最湿润气候中的源头溪流，非永久性比例也可达35%（第3页）。
4. 采用较严格的“1个零流量月”定义后，全球外推比例为44–53%，低于“1个零流量日”定义下的51–60%（第4、15页）。
5. 整体交叉验证分类准确率为90–92%，具体取决于交叉验证方式，全球尺度总体无偏；但站点稀疏流域和水文气候过渡区的准确率下降、偏差增大（第3–5页）。
6. 局地小河迁移能力明显较弱。与独立地面观测比较时，法国本土（n = 2,297）的平衡准确率为0.59、分类准确率51%、敏感度24%、特异度94%；美国太平洋西北地区（n = 3,725）分别为0.47、80%、10%和83%（第21页）。
7. 国家资料比较高度依赖定义和数据源。美国国家数据中可比河网的非永久性比例为19–22%，本模型的一日和一月定义分别为51%和36%；澳大利亚参考数据为91%，模型分别为95%和92%；法国国家模型为17%，本文为14%（第4、17、19–20页）。作者明确指出，国家地图比较不能视为准确率验证（第11页）。
8. 作者估计，2020年全球52%人口距离最近的河流或溪流为非永久性（第6页）。

## 6. 验证

- **验证数据：** 模型主要验证通过5,615个GRDC/GSIM站点的交叉验证完成。WaterGAP降尺度流量另以1971–2000年间至少有20年数据的2,131个GRDC站点检验。局地独立比较使用法国2,297个河段上的124,112次ONDE观测，以及美国太平洋西北地区3,725个河段上的5,372次观测。美国、澳大利亚、巴西、阿根廷和法国的国家地图/模型仅作为参照，不是正式准确率基准（第8–11、17–21页）。
- **验证方法：** 重复两次的三折非空间交叉验证、40折空间交叉验证、分类残差与流域偏差分析、RF概率阈值和零流量持续时间敏感性分析、地面目视观测比较及国家河网地图比较（第3–5、9–11页）。
- **评价指标：** 平衡准确率、分类准确率、敏感度、特异度、精确率、间歇预测残差、偏差、残差空间自相关、R²和对称平均绝对百分比误差（sMAPE）（第4、8–10、21、27页）。
- **主要验证结果：** RF整体分类准确率为90–92%（第3–4页）。局地独立平衡准确率在法国为0.59、美国太平洋西北为0.47，对非永久性河段的敏感度分别仅24%和10%（第21页）。WaterGAP降尺度MAF相对站点观测的R² = 0.96、sMAPE = 30%；sMAPE由MAF ≥ 1,000 m³ s⁻¹的5%上升到10 ≤ MAF < 1,000的20%和MAF < 10的52%。最小月流量作为Q90代理的R² = 0.84（第8–9页）。

## 7. 局限性

### 作者明确指出的局限

- 小河及小空间单元的精细尺度结果应谨慎使用；多数预测变量分辨率为250–1,000 m，无法充分表示河段/子流域尺度的土壤、岩性、河床泥沙和地下水过程（第6页）。
- 地下水—地表水相互作用只得到部分表达，仍是全球水文模型的难点（第6页）。
- 全球站网对小溪、干旱区、极端气候、高积雪流域、浅层地下水系统和强喀斯特流域代表不足，而大河代表过多（第6、8页）。
- 全球水文模型往往高估干旱气候区流量，使IRES高发区的制图更加困难（第6页）。
- 尽管排除了调控/变化站点并使用自然化流量，仍不能完全分离人类活动影响（第6页）。
- MAF < 0.1 m³ s⁻¹没有逐河段RF预测，因为同时满足小流量和记录长度条件的站点仅59个，其中永久性站点仅13个，而且RiverATLAS在该范围不连续（第10页）。
- 国家河网数据分类不一致且不确定；NHDPlus的间歇性误分类率可高达50%，因此国家比较不是独立准确率检验（第11页）。

### 我的分析

- 本文目标标签是流量站记录的零流量，而JRC标签代表可检测的开放地表水。二者并不等价：零流量期间可能保留孤立水池，狭窄但有流动的河流也可能被30 m遥感漏检。因此，从JRC水体标签转向IRES分类必须明确观测模型。
- “年均1天”的主定义具有包容性，与“年均1个月”相比会显著改变全球比例。与其他分类比较前应统一定义，不能把阈值差异造成的分歧直接解释为模型误差。
- `MAF ≥ 0.1 m³ s⁻¹`是制图适用域下限，不是永久性与非永久性的物理分界；把它当作持续性阈值会误读研究设计。
- RF在1和10 m³ s⁻¹处分尺度是为处理类别不平衡和改善预测，而不是推导水力学规律，不能作为分段 `Q_threshold = f(A)` 的证据。
- 90–92%的交叉验证准确率与独立小河观测中很低的敏感度形成鲜明对比，说明尺度和空间迁移限制很强：全球总体比例可能稳健，单个局地河段标签却未必可靠。
- 本文没有利用河流横截面积、河宽或水深推导水力阈值。MAF和比流量间接表示河流尺度，但没有检验以几何归一化后的流量是否更能区分类别。

## 8. 与我的研究的关系

### 可以直接使用

- 本文提供了严格的流量站标签规则：多年平均每年至少1个零流量日，并增加20年移动窗口保障条件；“1个零流量月”适合作为敏感性方案，而不是默认更正确的标准（第4、8页）。
- 论文清楚区分三类阈值：观测类别定义（零流量持续时间）、分类器概率阈值（0.5）和模型适用域MAF下限（0.1 m³ s⁻¹）。当前研究也应分别记录、调参和报告这三类阈值。
- 按河流尺度训练重叠模型，并在重叠区间平均概率，提供了一种允许分类关系随尺度变化而又避免硬突变的先例（第9页）。它支持检验灵活的 `Q_threshold = f(A)`，但没有证明具体函数。
- 空间交叉验证和局地独立比较可直接借鉴。由于相邻河段共享气候、地形和河网属性，只用随机划分会高估泛化能力（第9页）。
- 结果证明非永久性比例具有很强的尺度依赖，但气候、干旱度、土壤水分、坡度、径流、地下水和比流量同样提供重要信息。流量—面积模型应以这些附加控制变量作为对照基线（第3–4、9、26页）。

### 可能有用

- RiverATLAS提供河段拓扑及上游/局地流域属性，可作为匹配CaMa-Flood、流量站和遥感观测的公共空间框架（第2、8–9页）。
- 作者把30 m水体动态类别分别聚合到局地汇水区和整个上游流域，提供了多尺度遥感特征设计思路；但该变量与大量其他变量共同预测间歇性，并未被当作真实标签（第9页）。
- WaterGAP在小河中的误差明显增大（MAF < 10 m³ s⁻¹时sMAPE = 52%），说明拟合阈值时应传播模型流量不确定性，并按河流尺度分层报告表现（第8–9页）。
- 公开的概率图、河段属性、代码和结果可用作基准，并可定向检查CaMa-Flood/JRC分类与RF预测不一致的地区（第11–12页）。

### 与我的研究不同 / 不适用

- 本文使用WaterGAP 2.2自然化流量，而不是CaMa-Flood流量或河道几何。
- 本文没有把JRC Global Surface Water作为响应标签；另一套30 m Landsat年际水体动态产品仅作为预测变量之一（第9页）。
- 本文预测的是平均每年至少出现1个零流量日的概率，不是月/季地表水出现频率，也不是瞬时流动状态。
- 本文没有估算河流横截面积，也没有拟合显式的流量—面积边界。
- 预测目标是自然状态下的间歇性；JRC观测可能包含当代取水、水库和土地利用影响，而本文尽量排除了这些因素（第5–6、8页）。

## 9. 可以借鉴的内容

- **数据集：** RiverATLAS河网与属性、GRDC/GSIM流量站、公开全球间歇概率/类别、WaterGAP自然化流量、SoilGrids、WorldClim、干旱度/PET、地质和地下水图层，以及在可获得时使用ONDE和美国太平洋西北地区独立目视观测（第8–12、22页）。
- **方法：** 质量控制后的流量站标签、重叠的尺度分层RF、嵌套调参、空间交叉验证、概率阈值敏感性、零流量定义敏感性、残差制图和局地独立验证（第8–11页）。
- **阈值 / 参数：** 主标签为年均≥1个零流量日，敏感性标签为年均≥30个零流量日，RF二元分类采用概率≥0.5，全球逐河段预测采用MAF ≥ 0.1 m³ s⁻¹。四者用途不同，不能混为一谈。
- **验证方法：** 分别报告非空间与空间交叉验证；按河流尺度和地区分层报告敏感度/特异度；用重复的独立干湿观测验证小河；检查站点稀疏区偏差；测试多种非永久性时间定义。
- **图表 / 可视化思路：** 借鉴全球概率河网图、分流量等级比例表、流域准确率/偏差地图和预测变量偏依赖图；当前研究可增加按气候/干旱度与空间验证折分面的流量—横截面积图。

---

## Important Evidence | 重要证据

> “All reaches with a resulting probability ≥0.5 were classified to be non-perennial”

**Page:** 10

- IRES training labels required at least one zero-flow day per year on average, plus at least one zero-flow day in every 20-year moving window (p. 8).
- The RF size split used overlapping MAF ranges and averaged probabilities across 1–10 m³ s⁻¹ to prevent an artificial transition (p. 9).
- The RF-predicted global prevalence changed from 36% to 48% when the probability threshold moved from 0.55 to 0.45, compared with 41% at 0.5 (p. 10).
- Most predictor grids were 250–1,000 m, and local groundwater, lithology, sediment, and small-stream processes were incompletely represented (p. 6).

## Questions & Follow-up | 问题与后续工作

- [ ] Compare the published RiverATLAS IRES probability/class with the CaMa-Flood/JRC matched sample, explicitly harmonizing the temporal definition of non-perennial flow.
- [ ] Test whether cross-sectional area adds predictive value beyond MAF, specific discharge, drainage area, slope, aridity, and groundwater variables under spatial cross-validation.
- [ ] Create separate JRC-derived labels for connected flowing water, persistent isolated water, and no detectable water before calibrating `Q_threshold = f(A)`.
- [ ] Reproduce threshold sensitivity for the observational label, classifier probability, and model-domain cutoff independently.

## Related Papers | 相关论文

- Shanafield et al. (2021), *An overview of the hydrology of non-perennial rivers and streams* — hydrological processes and measurement/modeling limitations.
- Busch et al. (2020), *What’s in a Name? Patterns, Trends, and Suggestions for Defining Non-Perennial Rivers and Streams* — terminology and definitions.
- Zimmer et al. (2020), *Zero or not? Causes and consequences of zero-flow stream gage readings* — reliability and interpretation of zero-flow labels.
- Linke et al. (2019), *Global hydro-environmental sub-basin and river reach characteristics at high spatial resolution* — RiverATLAS/HydroATLAS data foundation.
- Müller Schmied et al. (2014), *Sensitivity of simulated global-scale freshwater fluxes and storages...* — WaterGAP 2.2 discharge source.

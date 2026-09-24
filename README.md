# G05 Polymer Devices coursework

本项目包含 QXU6028 2026–27 的 L1、L2 和 L3 分析，保留 G05 原始数据、计算代码和检查证据。L3 未收到课堂阈值时判定待定；尚未进行真实 blind test 或最终提交。

## L3 运行

`python reproduce.py --data-dir data/regular_G05 --phase L3`

默认输出至 `outputs/L3`，内含地图、方法与噪声图（PNG/SVG）、数值证据、中文说明和 checkpoint ZIP。L1/L2 重新计算在子目录 `prerequisites_L2`，不覆盖原归档。缺少阈值时 `pass=null`，包内 STATUS 明确标注未完成判定，不应作为完整最终提交。收到真实课堂阈值后添加 `--l3-threshold VALUE`；临界时同样不强行填 Boolean。

独立开发工作区使用原项目的 Python 环境或按 requirements.txt 安装。复现审计：
`python verify_l3_reproduction.py --archive-root ORIGINAL_COURSEWORK_DIRECTORY`
该命令比较干净克隆的全部确定性输出，并核对 63 个既有归档文件哈希。L3 的方法、索引约定和限制见 `records/L3_implementation.md` 及输出说明。

## 运行

本项目验证环境为 Python 3.12，锁定的依赖需要 Python 3.11 或更新版本（课程最低要求为 3.10）。建议使用 Python 3.12，在此目录执行：

```text
python -m pip install -r requirements.txt
python -m unittest -v
python reproduce.py --data-dir data/regular_G05 --phase L1 --out qa/L1_recheck
```

生成 checkpoint 前要求代码、数据、记录都已提交，工作区干净。脚本从 Git 读取真实 commit，不允许手填版本。安装环境和新生成目录由 .gitignore 排除；已被主动加入 Git 的 L1 归档继续保留。

本机已配置的解释器是 `.venv/Scripts/python.exe`。此本机环境不应复制给其他成员；他们按 requirements.txt 安装即可。项目依赖为 NumPy 和 Matplotlib，CSV/JSON 使用 Python 标准库。

`--data-dir` 接受同结构的数据目录，`--out` 可指定独立输出目录。更换数据后会重新校验 manifest；支持 L1/L2/L3。复核旧阶段时应加独立 `--out`，避免原位覆盖。

## L2 运行及结果入口

现已补充 RH–EF、Rs–EF 两张对照图和六面板总图。两通道使用同一个联合推断 EF；纵向误差条是按对应尺度归一化的样本标准差。横轴不是独立测量的 EF，因此新增图不构成独立验证。

新增输出：`L2_RH_vs_EF.png/svg`、`L2_Rs_vs_EF.png/svg`、`L2_six_panel.png/svg` 和 `L2_EF_comparison.csv`，都在 `outputs/L2`，并收入更新后的 ZIP。原四面板仍保留。更新前的 L2 完整输出保存在 `outputs/archive/L2_6299ffe15dc8/L2`；原 L1 归档不变。

本次展示修订的回归核验：`python verify_l2_display_revision.py`，使用本地保留的上一版 L2 输出，报告位于 `outputs/L2_display_revision_audit.json`。它不是 clean clone 运行所必需的输入；通用复现检查仍用 `verify_reproduction.py`。

```text
python reproduce.py --data-dir data/regular_G05 --phase L2
python verify_reproduction.py --phase L2
```

- `outputs/L2/G05_L2_Checkpoint.zip`：结果 JSON、英文说明、模型图、轨迹图、四面板图和 commit。
- `outputs/L2/L2_readme_zh.md`：中文结果解释和不确定性边界。
- `outputs/L2/L2_summary.json`：模型残差、选择规则结果、bootstrap 区间和稳定性。
- `outputs/L2/L2_pairs_and_trajectory.csv`：成对数据汇总、归一化、模型匹配和轨迹区间。
- `outputs/L2/L2_model_library.csv` 与 `L2_residual_scan.csv`：全部模型曲线和残差。
- `outputs/L2/L2_bootstrap_draws.csv` 与 `L2_bootstrap_residuals.json`：200 次配对抽样及全部候选残差，固定种子 602805。
- `records/L2_method_and_sources.md`：公式依据、统计约定、图和验证规范。

## 从哪里看

- `outputs/L1/G05_L1_Checkpoint.zip`：L1 checkpoint 文件包。
- `outputs/L1/brief_note.txt`：英文方法、结果、检查和条件性 sensor advice。
- `outputs/L1/L1_correction.png` 与 `.svg`：可预览和可编辑文字版本的同一张图。
- `outputs/L1/L1_sweep.csv`：12 行输入对应的中间计算值。
- `outputs/L1/L1_curve.csv`：曲线的 301 个重算点。
- `outputs/L1/operating_point.json` 与 `crossings.json`：工作点和交点完整精度。
- `outputs/L1/checks.json`、`input_integrity.json`、`environment.json`、`run_log.txt`：核验与运行证据。
- `records/`：方法依据、AI 披露、真实错误和待学生核实的贡献。

所有输出由已提交的脚本生成。不要手改数值；修改代码后提交新版本并重新运行。归档输出中的 pipeline_commit 指向生成它的代码版本，不必等于后来归档该输出的 commit。新 L2 使用新版本并重算 L1 数值，但不改旧 L1 文件。

## clean checkout

```text
git clone <本项目的本地路径或未来仓库地址> clean_G05
cd clean_G05
python -m pip install -r requirements.txt
python -m unittest -v
python reproduce.py --data-dir data/regular_G05 --phase L1 --out qa/L1_recheck
```

比较原目录与 clean checkout 的 results、数值 CSV、图和 checkpoint。环境路径与命令不同，因此 environment.json/run_log.txt 不要求逐字节相同。

本项目提供 `python verify_reproduction.py --phase L2`（也支持 L1），在两份空输出目录运行并比较 SHA-256，不原位覆盖旧 L1。核验 L1 数值回归及旧归档哈希。证据保存在 `outputs/clean_reproduction_L2.json` 和唯一的 `qa/` 子目录中。

此项目目前只有本地仓库，无远程仓库、无 QMplus 上传。课程要求的 marker 可访问链接需要后续建立。学生仍需理解并审核 AI 生成内容，补充真实个人贡献和签字。上传前对照 QMplus 最新通知。

# G05 Polymer Devices coursework

本项目完成 QXU6028 2026–27 的 L1，保留 G05 原始数据、计算代码和检查证据。L2/L3 尚未实现，当前包不能用于包含全部三阶段的 blind test。

## 运行

使用 Python 3.10 或更新版本，在此目录执行：

```text
python -m pip install -r requirements.txt
python -m unittest -v
python reproduce.py --data-dir data/regular_G05 --phase L1
```

生成 checkpoint 前要求代码、数据、记录都已提交，工作区干净。脚本从 Git 读取真实 commit，不允许手填版本。安装包和生成目录不进入 Git。

本机已配置的解释器是 `.venv/Scripts/python.exe`。此本机环境不应复制给其他成员；他们按 requirements.txt 安装即可。项目依赖为 NumPy 和 Matplotlib，CSV/JSON 使用 Python 标准库。

`--data-dir` 接受同结构的数据目录，`--out` 可指定独立输出目录。更换数据后会重新校验 manifest；尚不支持 L2/L3，不能伪装成完整 blind pipeline。

## 从哪里看

- `outputs/L1/G05_L1_Checkpoint.zip`：L1 checkpoint 文件包。
- `outputs/L1/brief_note.txt`：英文方法、结果、检查和条件性 sensor advice。
- `outputs/L1/L1_correction.png` 与 `.svg`：可预览和可编辑文字版本的同一张图。
- `outputs/L1/L1_sweep.csv`：12 行输入对应的中间计算值。
- `outputs/L1/L1_curve.csv`：曲线的 301 个重算点。
- `outputs/L1/operating_point.json` 与 `crossings.json`：工作点和交点完整精度。
- `outputs/L1/checks.json`、`input_integrity.json`、`environment.json`、`run_log.txt`：核验与运行证据。
- `records/`：方法依据、AI 披露、真实错误和待学生核实的贡献。

所有输出由已提交的脚本生成。不要手改数值；修改代码后提交新版本并重新运行。输出不进入 Git，避免 results.json 引用自身 commit 的循环；保留 checkpoint 和本地运行证据。

## clean checkout

```text
git clone <本项目的本地路径或未来仓库地址> clean_G05
cd clean_G05
python -m pip install -r requirements.txt
python -m unittest -v
python reproduce.py --data-dir data/regular_G05 --phase L1
```

比较原目录与 clean checkout 的 results、数值 CSV、图和 checkpoint。环境路径与命令不同，因此 environment.json/run_log.txt 不要求逐字节相同。

此项目目前只有本地仓库，无远程仓库、无 QMplus 上传。课程要求的 marker 可访问链接需要后续建立。学生仍需理解并审核 AI 生成内容，补充真实个人贡献和签字。上传前对照 QMplus 最新通知。

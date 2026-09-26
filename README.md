# 《AI发展国》PV —— 开罗《游戏发展国》画风 AI 公司经营游戏宣传片

成立 AI 公司 → 招聘人才 → 抢显卡 → 训练模型 → 发布（演唱会）→ 业界震惊瘫坐 → 登顶排行榜。中文版，86.5 秒，1920×1080。

## 成品
| 文件 | 说明 |
|---|---|
| [Release](https://github.com/Moeblack/ai-dev-story-pv/releases) · `AI公司PV_中文版.mp4` | 成片（H.264 + AAC，30fps） |
| `成片/B站封面_16x10.png` / `_16x9.png` / `_4x3.png` | B 站封面三种比例 |

## 目录
| 路径 | 内容 |
|---|---|
| `文档/` | 需求与环境、开罗风格指南、meme 清单与溯源、分镜草案、成片说明（`04-成片说明.md` 含完整时间轴） |
| `审查.html` | 素材审查页（离线打开） |
| `参考视频/` `参考帧/` | 开罗官方 Steam 预告片与截图（**未入库**，来源见 `文档/01-开罗风格指南.md`） |
| `meme/` | AI 圈 meme 原始素材（**未入库**，出处链接见 `文档/02-meme清单.md`） |
| `风格样图/` | 素材阶段的 8 张 Qwen-Image 2.1 风格样图及提示词 |
| `音频/` | BGM：Fly Me to the Moon（小野丽莎）（**未入库**，见下方“重新渲染”） |
| `成片工程/` | 成片工程（uv 项目） |
| `成片工程/底图/` | 本机 ComfyUI Qwen-Image 2.1 生成的场景、精灵表、图标、头像、封面原图，同名 `.txt` 为提示词 |
| `成片工程/资产/` | 切割、像素化后的渲染资产与 Fusion Pixel 字体（OFL） |
| `成片工程/pv/` | `engine.py` 渲染引擎、`scenes.py` 时间轴与文案、`audio.py` 音效合成与混音、`render.py` 并行渲染、`cut_assets.py` 切图、`cover.py` 封面 |
| `成片工程/分析/` | BGM 节拍与歌词时间分析（`audio.json`） |

## 重新渲染
BGM 未入库，渲染前先放到 `音频/FlyMeToTheMoon-小野丽莎.flac`（48 kHz 立体声），例如：
```bash
yt-dlp -f bestaudio -x --audio-format flac -o '音频/FlyMeToTheMoon-小野丽莎.%(ext)s' https://www.bilibili.com/video/BV1F84y1N7tv
```
```bash
cd 成片工程
uv sync
uv run python pv/cut_assets.py   # 底图或精灵表变更时
uv run python pv/audio.py        # → 输出/mix.wav
uv run python pv/render.py       # 并行渲染 → ../成片/AI公司PV_中文版.mp4
uv run python pv/render.py --still 47.8   # 导出单帧
uv run python pv/cover.py        # 封面
```
重新做歌词分析（`分析/analyze.py`）需先把 faster-whisper medium 下载到 `成片工程/分析/fw-medium/`（ModelScope `pengzhendong/faster-whisper-medium`），该目录不入库。

## 说明
- 画面素材由本机 ComfyUI 的 Qwen-Image 2.1 生成，再经像素化与程序合成；界面、动效与音效由代码绘制和合成。
- 第三方素材（BGM、开罗官方预告片与截图、X 等平台的 meme 图片视频、人物照片）版权归原作者，未包含在本仓库中；`审查.html` 与 `文档/` 中指向这些文件的本地链接在仓库里会失效，原始出处链接仍保留。
- 二进制文件（图片、字体）走 Git LFS。
- 片中公司、模型、人物均为虚构玩梗，《AI发展国》不是真实游戏。向开罗游戏（Kairosoft）致敬。

## 许可
- 代码（`成片工程/pv/`、`成片工程/分析/analyze.py`）：MIT，见 `LICENSE`。
- 生成的美术资产、封面与文档：CC BY-NC 4.0。
- Fusion Pixel 字体：SIL OFL 1.1（`成片工程/资产/字体/OFL.txt`）。

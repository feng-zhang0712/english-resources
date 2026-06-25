# 编纂工具使用说明

本目录存放《Frank 的英文单词书》的本地辅助脚本，**不纳入正式词条内容**。所有脚本均需在终端中运行。

## 环境准备

- **Python**：3.9 或更高版本（macOS 自带或 Homebrew 安装均可）
- **依赖**：
  - `md_to_html.py`、`merge_lian.py`、`vocab_md.py`、`pronunciation.py`：仅用 Python 标准库
  - `md_to_docx.py`：需额外安装 `python-docx`

```bash
pip install python-docx
```

建议在项目根目录（`english-resources`）下执行下列命令；也可先 `cd` 到本目录 `Frank 的英文单词书/tools/` 再运行。

---

## 脚本一览

| 脚本 | 用途 |
|------|------|
| `md_to_html.py` | 章节 Markdown → 可交互 HTML 预览（含美音 🔊） |
| `md_to_docx.py` | 章节 Markdown → 打印用 Word（含美音超链接 🔊） |
| `merge_lian.py` | 批量将 `[近]`、`[反]` 合并进 `[联]`（一次性迁移用） |
| `vocab_md.py` | 共享：解析词条 Markdown（被上述脚本引用，不单独运行） |
| `pronunciation.py` | 共享：从 dictionaryapi.dev 获取美音 MP3（被 docx 引用） |

---

## 1. HTML 预览器 — `md_to_html.py`

把章节 `.md` 转成可在浏览器中阅读的 HTML，词条标题旁有 **🔊** 按钮，点击播放**美音**（需联网，数据来自 [dictionaryapi.dev](https://dictionaryapi.dev)）。

### 基本用法

```bash
python3 "Frank 的英文单词书/tools/md_to_html.py" \
  "Frank 的英文单词书/01-人与自我/06-人生阶段与经历/06-人生阶段与经历.md"
```

默认在与源文件同目录生成同名 `.html`（上例为 `06-人生阶段与经历.html`）。

### 指定输出路径

```bash
python3 "Frank 的英文单词书/tools/md_to_html.py" \
  "Frank 的英文单词书/01-人与自我/06-人生阶段与经历/06-人生阶段与经历.md" \
  -o /tmp/人生阶段.html
```

### 转换并启动本地预览服务

```bash
python3 "Frank 的英文单词书/tools/md_to_html.py" \
  "Frank 的英文单词书/01-人与自我/06-人生阶段与经历/06-人生阶段与经历.md" \
  --serve
```

- 默认在 `http://127.0.0.1:8765/` 打开浏览器
- 按 `Ctrl+C` 停止服务
- 自定义端口：`--port 9000`

### 功能说明

- 顶部搜索框：按单词或正文过滤词条
- **🔊**：播放美音；API 失败时自动尝试备用 MP3 地址
- 可直接用浏览器打开生成的 `.html` 文件（`file://`），一般也能播放；若遇跨域问题，请用 `--serve`

---

## 2. Word 导出 — `md_to_docx.py`

把章节 Markdown 转为 B5 排版、适合打印的 `.docx`。在音标行旁插入 **🔊** 超链接，在 Word 中点击即可播放**美音** MP3（需联网）。

### 基本用法

```bash
python3 "Frank 的英文单词书/tools/md_to_docx.py" \
  "Frank 的英文单词书/01-人与自我/06-人生阶段与经历/06-人生阶段与经历.md"
```

默认输出同目录下的 `06-人生阶段与经历.docx`。

### 指定输出路径

```bash
python3 "Frank 的英文单词书/tools/md_to_docx.py" \
  "Frank 的英文单词书/01-人与自我/06-人生阶段与经历/06-人生阶段与经历.md" \
  -o ~/Desktop/人生阶段.docx
```

### 跳过发音链接（加快生成、无需联网）

```bash
python3 "Frank 的英文单词书/tools/md_to_docx.py" \
  "Frank 的英文单词书/01-人与自我/06-人生阶段与经历/06-人生阶段与经历.md" \
  --no-pronunciation
```

### 喇叭位置规则

- 音标为 `英/美 …` 一行：喇叭在该行末尾
- 音标分 `英 …` / `美 …` 两行：喇叭在 **美** 音标行（与「只学美音」一致）
- 仅有 `英 …` 一行时：喇叭落在该行

首次导出时会联网查询发音并写入本地缓存目录 `tools/.cache/pronunciations/`（已加入 `.gitignore`，勿提交）。

---

## 3. 联想词合并 — `merge_lian.py`

将词条中的 **`[近]`、`[反]` 模块删除**，内容合并进 **`[联]`**（去重、保留原有 `[联]` 词条在前）。适用于规范改版后的大批量迁移；**日常编纂一般不需要再运行**。

### 用法

可一次处理多个文件：

```bash
python3 "Frank 的英文单词书/tools/merge_lian.py" \
  "Frank 的英文单词书/01-人与自我/02-情感与情绪/02-情感与情绪.md" \
  "Frank 的英文单词书/01-人与自我/03-性格与品质/03-性格与品质.md"
```

### 输出示例

```
path/to/file.md: 376/652 entries updated
Done: 2405 entries updated across 6 files
```

表示该文件共 652 个词条，其中 376 个被修改。**会直接覆盖原 `.md` 文件**，运行前请确认已备份或已提交 Git。

### 注意

- **不要**对 `编纂规范/sample.md` 等说明性文档运行（会破坏文首模块顺序说明）；样例应手工维护
- 合并后请人工抽查若干词条，确认 `[联]` 无重复、无 junk

---

## 典型工作流

### 编完一章，先在浏览器里看效果

```bash
python3 "Frank 的英文单词书/tools/md_to_html.py" \
  "Frank 的英文单词书/01-人与自我/03-性格与品质/03-性格与品质.md" \
  --serve
```

### 定稿后导出 Word 打印或审阅

```bash
python3 "Frank 的英文单词书/tools/md_to_docx.py" \
  "Frank 的英文单词书/01-人与自我/03-性格与品质/03-性格与品质.md"
```

### 批量导出第一章全部六节（示例）

```bash
for f in "Frank 的英文单词书/01-人与自我"/*/*.md; do
  python3 "Frank 的英文单词书/tools/md_to_html.py" "$f"
done
```

---

## 输入 Markdown 格式要求

脚本解析的词条格式与 [`编纂规范/sample.md`](../编纂规范/sample.md) 一致，例如：

```markdown
# 章节标题（可选，仅一行 # ）

**life**
英/美 /laɪf/
n. 生命；生活；人生
[义] …
[联] birth 出生, death 死亡, …
[记] …
```

- 词头：单独一行 `**单词**`
- 模块行：`[义]`、`[形]`、`[例]`、`[源]`、`[族]`、`[搭]`、`[辨]`、`[联]`、`[记]` 等
- 支持正文内 `**加粗**`

---

## 常见问题

**Q：点击 🔊 没声音？**  
A：检查网络；HTML 预览若用 `file://` 打开异常，请改用 `--serve`。Word 中需允许打开外部超链接。

**Q：docx 报错 `No module named 'docx'`？**  
A：运行 `pip install python-docx`。

**Q：发音是英音还是美音？**  
A：当前工具**只保留美音**，与全书「按美音学习」一致。

**Q：缓存目录可以删吗？**  
A：可以。删除 `tools/.cache/pronunciations/` 后，下次导出会重新联网拉取。

**Q：生成的 html/docx 要提交 Git 吗？**  
A：一般**不要**；源文件以 `.md` 为准，html/docx 视为本地预览或交付物，按需生成即可。

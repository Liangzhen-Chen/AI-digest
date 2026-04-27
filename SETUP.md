# AI Digest — 每日信息简报助手

自动采集全球新闻、AI动态、商业金融、科技资讯和产品分析，经 AI 整理后每天早上发送到你的邮箱。

**完全免费运行。**

---

## 架构

```
RSS Feeds (BBC, YouTube, TechCrunch, 人人都是产品经理 ...)
        ↓
   feeds.py  (采集 + 过滤)
        ↓
 summarizer.py  (Gemini 优先，失败后自动切换 DeepSeek，生成中文简报)
        ↓
   mailer.py  (Gmail SMTP 发送 HTML 邮件)
        ↓
 GitHub Actions  (每天伦敦时间 7:00 AM 自动触发)
```

---

## 第一步：获取 Gemini API Key（免费，约 2 分钟）

1. 打开浏览器，访问 **https://aistudio.google.com/apikey**
2. 如果弹出 Google 登录页面，用你的 Google 账号登录
3. 登录后会进入 **"API Keys"** 页面
4. 点击页面上方蓝色按钮 **「Create API Key」**
5. 弹窗中会让你选一个 Google Cloud 项目：
   - 如果你从没用过 Google Cloud → 选 **「Create API key in new project」**
   - 如果已有项目 → 随便选一个即可
6. 等几秒钟，页面会显示一串以 `AIza...` 开头的字符串
7. 点击右边的 **复制图标** 📋 把它复制下来
8. **打开一个记事本，粘贴保存**，后面要用

> ⚠️ 这个 Key 免费额度：每分钟 15 次请求、每天 100 万 token，完全够用。

---

## 第二步：设置 Gmail 应用密码（免费，约 5 分钟）

Gmail 不允许直接用你的密码登录 SMTP，需要生成一个专用的「应用密码」。

### 2.1 开启两步验证（如果已开启可跳到 2.2）

1. 打开 **https://myaccount.google.com**
2. 左边侧栏点击 **「安全性」**（英文界面是 **"Security"**）
3. 向下滚动，找到 **「登录 Google 的方式」** 区域（英文：**"How you sign in to Google"**）
4. 找到 **「两步验证」**（英文：**"2-Step Verification"**），点击进入
5. 如果显示「关闭」，点击 **「开始使用」** 按钮
6. 按照引导完成设置（通常是绑定手机号 → 收验证码 → 确认）
7. 设置完成后，页面会显示两步验证 **「已启用」**

### 2.2 生成应用密码

1. 打开 **https://myaccount.google.com/apppasswords**
   - 如果提示你重新输入 Gmail 密码，输入后继续
   - ⚠️ 如果页面显示 404 或找不到，说明两步验证没开成功，回到 2.1
2. 你会看到一个输入框，上面写着 **"App name"**（或「应用名称」）
3. 在输入框里输入：`AI Digest`（这只是个备注名，叫什么都行）
4. 点击 **「创建」** 按钮（英文：**"Create"**）
5. 弹窗会显示一个 **16 位密码**，格式类似 `abcd efgh ijkl mnop`
6. **完整复制这 16 位密码**（包括空格也没关系，实际使用时空格会被忽略）
7. 粘贴到之前的记事本里保存

> ⚠️ 这个密码只显示一次！关掉弹窗就看不到了。如果忘记了，回到这个页面重新生成一个。

---

## 第三步：创建 GitHub 仓库并上传代码（约 5 分钟）

### 3.1 如果你已经安装了 Git 和 GitHub CLI

打开终端（命令行），依次运行：

```bash
cd ai-digest
git init
git add .
git commit -m "Initial commit: AI Digest daily newsletter"
gh repo create ai-digest --private --push --source=.
```

> 如果 `gh` 命令提示未登录，先运行 `gh auth login`，按提示操作。

### 3.2 如果你没装 Git / 更习惯网页操作

1. 打开 **https://github.com/new**（需要 GitHub 账号，没有的话先注册）
2. **Repository name** 填入：`ai-digest`
3. 勾选 **Private**（私有仓库，别人看不到你的代码）
4. **不要** 勾选 "Add a README file"
5. 点击绿色按钮 **「Create repository」**
6. 创建成功后，页面会显示一个上传指引
7. 点击页面中间的 **「uploading an existing file」** 链接
8. 把 `ai-digest` 文件夹里的**以下文件**拖进上传区域：
   - `feeds.py`
   - `summarizer.py`
   - `mailer.py`
   - `main.py`
   - `history.py`
   - `requirements.txt`
   - `.env.example`
   - `.gitignore`
   - `SETUP.md`
9. 注意 **不要上传** `.env` 文件（里面有你的密钥）
10. 在页面下方的 "Commit changes" 区域，直接点击绿色按钮 **「Commit changes」**

> ⚠️ GitHub 网页上传**不支持上传文件夹**，所以 `.github/workflows/daily-digest.yml` 需要手动创建，见下方 3.3。

### 3.3 手动创建 workflow 文件（网页上传必做）

> 如果你用的是 3.1 命令行方式上传的，`.github` 文件夹已经包含在内，可以跳过这步。

1. 在仓库页面点击 **「Add file」** → **「Create new file」**
2. 在文件名输入框里输入：`.github/workflows/daily-digest.yml`
   - 输入每个 `/` 时 GitHub 会自动把前面的部分变成文件夹，这是正常的，继续输入即可
3. 在下方编辑区粘贴 `daily-digest.yml` 的完整内容（见项目文件夹中的 `.github/workflows/daily-digest.yml`）
4. 点击右上角绿色按钮 **「Commit changes」**
5. 回到仓库主页，确认能看到 `.github/workflows` 文件夹

---

## 第四步：配置 GitHub Secrets（约 3 分钟）

Secrets 是 GitHub 存储密钥的安全方式，代码里不会暴露你的密码。

1. 打开你刚创建的仓库页面（`https://github.com/你的用户名/ai-digest`）
2. 点击仓库顶部的 **「Settings」** 标签页（⚙️ 图标，在最右边）
   - ⚠️ 如果看不到 Settings，确认你是仓库的 Owner
3. 在左边侧栏找到 **「Secrets and variables」**，点击展开
4. 点击展开后出现的 **「Actions」**
5. 页面右上方点击绿色按钮 **「New repository secret」**

接下来要添加 **5 个 Secret**，每个都是点「New repository secret」→ 填写 → 保存，重复 5 次：

### Secret 1：Gemini API Key
- **Name** 输入：`GEMINI_API_KEY`（必须完全一致，全大写）
- **Secret** 输入：粘贴你在第一步获取的 Gemini API Key（`AIza...` 开头的那串）
- 点击 **「Add secret」**

### Secret 2：DeepSeek API Key
- **Name** 输入：`DEEPSEEK_API_KEY`
- **Secret** 输入：你的 DeepSeek API Key（Gemini 失败时作为备用模型）
- 点击 **「Add secret」**

### Secret 3：发件邮箱地址
- **Name** 输入：`SMTP_EMAIL`
- **Secret** 输入：你的 Gmail 地址，比如 `yourname@gmail.com`
- 点击 **「Add secret」**

### Secret 4：Gmail 应用密码
- **Name** 输入：`SMTP_PASSWORD`
- **Secret** 输入：第二步生成的 16 位应用密码
- 点击 **「Add secret」**

### Secret 5：收件邮箱
- **Name** 输入：`RECIPIENT_EMAIL`
- **Secret** 输入：你希望收到简报的邮箱地址（可以和发件邮箱一样）
- 点击 **「Add secret」**

添加完毕后，你应该能在 Secrets 页面看到 5 条记录（只显示名字，不显示值，这是正常的）。

---

## 第五步：手动测试一次（约 3 分钟）

1. 在仓库页面顶部，点击 **「Actions」** 标签页（在 Settings 左边）
2. 左侧会显示 **「Daily AI Digest」**，点击它
3. 右侧出现一个蓝色横幅，写着 "This workflow has a workflow_dispatch event trigger"
4. 点击 **「Run workflow」** 按钮（灰色下拉按钮）
5. 在下拉菜单中，Branch 保持默认的 `main`
6. 点击绿色的 **「Run workflow」** 按钮
7. 等几秒刷新页面，会出现一个正在运行的 workflow（黄色圆圈转动中）
8. 点击它可以查看运行详情
9. 等待 2-5 分钟，如果变成 **绿色 ✓**，说明运行成功
10. **去你的邮箱检查**，应该已经收到了第一封 AI 简报！

### 如果运行失败了（红色 ✗）

1. 点击失败的那次运行
2. 点击 **「send-digest」** 这个 job
3. 展开红色标记的步骤，查看错误信息
4. 常见问题：
   - `GEMINI_API_KEY not set` → 回第四步检查 Secret 名称是否拼对
   - `Authentication failed` → 应用密码不对，回第二步重新生成
   - `Connection refused` → Gmail 可能需要你在邮箱设置中允许"不够安全的应用"（但一般用应用密码不会遇到这个问题）

---

## 第六步：完成！自动运行

配置成功后，GitHub Actions 会在 **每天伦敦时间早上 7:00** 自动运行发送简报。

> 注意：英国有夏令时（3月最后一个周日 → 10月最后一个周日），当前 cron 设置为 UTC 6:00，对应夏令时 BST 7:00。冬令时期间实际会在伦敦时间 6:00 发送。如果想精确到冬令时也是 7:00，可以在每年 10 月底手动把 `daily-digest.yml` 里的 cron 改为 `"0 7 * * *"`，3 月底再改回 `"0 6 * * *"`。

---

## 本地运行（可选，用于调试）

如果你想在自己电脑上跑一次看效果：

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 复制环境变量模板
cp .env.example .env

# 3. 编辑 .env，把 5 个值填进去
#    - GEMINI_API_KEY=你的key
#    - DEEPSEEK_API_KEY=你的备用key
#    - SMTP_EMAIL=你的gmail
#    - SMTP_PASSWORD=你的应用密码
#    - RECIPIENT_EMAIL=收件邮箱

# 4. 运行
python main.py
```

---

## 自定义信息源

编辑 `feeds.py` 中的 `FEED_SOURCES` 和 `YOUTUBE_CHANNELS` 字典即可增删信息源。

---

## 费用说明

| 组件 | 费用 |
|---|---|
| Gemini API | 免费额度内免费 |
| DeepSeek API | 仅在 Gemini 失败时调用，按 DeepSeek 账户用量计费 |
| Gmail SMTP | 免费（500 封/天） |
| GitHub Actions | 免费（Private repo 2000 分钟/月，足够） |
| RSS Feeds | 免费 |
| Wikipedia API | 免费 |

**总费用：$0/月**

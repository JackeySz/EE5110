# 准备工作清单（写第一行代码之前，先做完这些）

仓库：**https://github.com/JackeySz/EE5110**（Private，Owner: `JackeySz`）

目标：让 5 个人都拿到权限、都能把项目在自己机器上跑起来。这步没做完就开写，后面一定会乱。

---

## 0. 先认领分工

| 角色 | 分支 | 负责的模块 |
|---|---|---|
| 算法 A | `feature/core-pixel-model` | `preprocessing.py`、`pixel_model.py` |
| 算法 B | `feature/interpolation-noise` | `interpolation.py`、`noise.py` |
| 集成（建议组长兼任） | `feature/io-integration` | `simulator.py`、`video_io.py`、`event_io.py`、`cli.py`、`configs/` |
| 测试 | `feature/tests` | `tests/`、`metrics.py`、`scripts/` |
| 可视化 | `feature/visualization` | `event_frames.py`、`visualization.py`、`scripts/create_demo.py` |

一个人只碰自己分支上的文件。完整规则见 `docs/GIT_WORKFLOW.md` 第 3 节的冲突地图。

---

## 1. 组长：一次性准备

### 1.1 申请 GitHub Education（建议最先做，审批要等）

https://education.github.com —— 用**学校邮箱**申请，通常几分钟到几天。

为什么必须做：**私有仓库在免费版下，分支保护是配了不生效的**（能勾、能存、但不拦截）。拿到免费的 Pro 之后私有仓才能强制保护 `main`。

### 1.2 邀请 4 位协作者

1. 先向队友收齐 **GitHub 用户名**（不是邮箱、不是昵称）
2. `Settings → Collaborators → Add people`
3. 逐个搜用户名，权限选 **Write**（Read 不能推代码，Admin 没必要）

队友会收到邮件邀请，也可以让他们登录后直接打开仓库地址，页面顶部会有提示条。

### 1.3 确认 CI 是绿的

打开 https://github.com/JackeySz/EE5110/actions 看最近一次运行。

必须是绿色，说明 baseline 是健康的。如果红了，先别让人开工——修掉再说。

### 1.4 保护 main（拿到 Pro 之后）

`Settings → Branches → Add branch ruleset`，pattern 填 `main`：

- [x] Require a pull request before merging（Required approvals: `1`）
- [x] Require status checks to pass → 勾 `test (3.9)` 和 `test (3.11)`
- [x] **Require branches to be up to date before merging** ← 这条最关键
- [x] Block force pushes

还没拿到 Pro 就先跳过，用团队约定兜底：**任何人不得直接 push main**。

### 1.5 统一合并方式

`Settings → General → Pull Requests`：只留 **Allow squash merging** 一个勾。

---

## 2. 每位队友：各做一次

### 2.1 注册并接受邀请

- 没有 GitHub 账号就先注册（同样建议用学校邮箱，方便申 Education）
- 接受协作者邀请：**看邮箱**，或登录后打开仓库地址看顶部提示条
- 确认能看到仓库内容 = 权限到位了

> 不用 fork，不用自己建仓库，别 clone 到别人的账号下。

### 2.2 配置 SSH key

GitHub 从 2021 年起**不接受账号密码**推代码，必须配 SSH 或 Token。推荐 SSH，一次配好永久免密。

**macOS / Linux**

```bash
ssh-keygen -t ed25519 -C "你的GitHub邮箱"
cat ~/.ssh/id_ed25519.pub          # 复制整行输出
```

**Windows**（PowerShell 或 Git Bash 都行）

```powershell
ssh-keygen -t ed25519 -C "你的GitHub邮箱"
Get-Content ~/.ssh/id_ed25519.pub  # 复制整行输出
```

然后把输出粘到 https://github.com/settings/ssh/new

- Title 随便填
- **Key type 必须是 `Authentication Key`** ← 选成 `Signing Key` 的话能存进去但登录不了，症状是 `Permission denied (publickey)`

验证：

```bash
ssh -T git@github.com
# 看到 "Hi <你的用户名>!" 才算成功
```

### 2.3 克隆仓库

```bash
git clone git@github.com:JackeySz/EE5110.git
cd EE5110
git checkout feature/<你自己的分支>
```

> 根目录名是 `EE5110`；Python 包名是 `event_camera_simulator`。两个名字别混。

### 2.4 建环境

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,video]'
```

需要 Python **3.9 或更高**。

### 2.5 自检（四项必须全过）

```bash
pytest                                        # 预期 9 passed, 9 skipped
ruff check .                                  # 预期 All checks passed!
mypy src                                      # 预期 Success: no issues found in 14 source files
event-sim validate-config --config configs/ideal.yaml   # 预期 Configuration is valid
```

**全绿才算配置完成。** 有任何一项过不了，先在群里问一下，别自己改配置绕过去。

> `event-sim simulate ...` 现在会抛 `NotImplementedError`，这是**正常的**——核心算法还没写。

### 2.6 读文档

按顺序读，别跳：

1. `AGENTS.md`
2. `docs/ARCHITECTURE.md`
3. `docs/INTERFACES.md`（接口合同，改签名走这里）
4. `TEAM_GUIDE_CN.md`（中文，讲每个模块要做什么）
5. `tasks/<你自己的>.md`
6. `docs/GIT_WORKFLOW.md`（怎么合代码）

---

## 3. 权限矩阵

| 谁 | 需要什么 | 怎么拿 |
|---|---|---|
| 组长 | Owner / Admin | 建仓的人自动是 |
| 其余 4 人 | Write | 组长在 Collaborators 里加 |
| 全部 | SSH key 或 PAT | 各自在 GitHub Settings 配 |
| 组长 | Pro（可选但推荐） | GitHub Education |

Write 权限够用了：能推分支、能开 PR、能 review。**不能**改仓库设置、不能删仓库、不能强推被保护的分支。

---

## 4. 验收：每人完成后回报这一句

```
[角色] [GitHub 用户名]
- SSH: Hi <用户名> ✓
- clone ✓
- pytest 9 passed / ruff ✓ / mypy ✓ / event-sim ✓
```

组长收到 5 条再开工。

---

## 5. 排查

**`Permission denied (publickey)`**

先确认钥匙确实被送出去：

```bash
ssh -T -v git@github.com 2>&1 | grep "Offering public key"
```

- 有 `Offering public key` 还是被拒 → 公钥没加进 GitHub，或加到了别的账号，或 Key type 选成了 Signing
- 没有 `Offering public key` → 本机钥匙没生成，或文件名不是默认的 `id_ed25519`

**`Could not resolve hostname` / 连不上**

国内访问 GitHub 时好时坏。先试 HTTPS 端口 443 的 SSH：

```bash
# ~/.ssh/config 加一段
Host github.com
  Hostname ssh.github.com
  Port 443
  User git
```

还不行就换 HTTPS + Personal Access Token（做法见 `docs/GIT_WORKFLOW.md` 第 0 节）。

**`pytest` 报 ImportError: 没有 cv2**

漏装了 video 扩展，补一条：

```bash
pip install -e '.[dev,video]'
```

**`mypy` 报 Python 3.9 is not supported**

配置已经修过了。如果你在旧分支上遇到，先 `git pull` 同步 main。

---

## 附录：可以直接发群里的消息

> 仓库建好了：https://github.com/JackeySz/EE5110 （私有）
>
> 大家做三件事：
> **1. 把你的 GitHub 用户名发我**（不是邮箱，是用户名），我加你为协作者
> **2. 配 SSH key**：按这个文档第 2.2 节做，做完跑 `ssh -T git@github.com`，看到 "Hi 你的用户名!" 就对了
> **3. 克隆 + 装环境**：文档第 2.3～2.5 节，跑完 4 条自检命令全绿
>
> 文档在仓库里的 `docs/SETUP_CHECKLIST.md`，跟着做就行。
>
> 分工：
> - 算法A（预处理+像素模型）→ @xxx
> - 算法B（插值+噪声）→ @xxx
> - 集成（simulator+IO+CLI）→ @xxx
> - 测试 → @xxx
> - 可视化 → @xxx
>
> 都完成了回我一句 "SSH ✓ / clone ✓ / 四项自检 ✓"，收到 5 条我们就开工。
> 先别急着写代码，等权限和环境齐了再说。

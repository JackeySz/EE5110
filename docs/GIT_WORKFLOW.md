# 线上协作与代码合并流程

五人团队在 GitHub 上合并代码的完整流程。本文是 `README.md` 第 "Git workflow" 一节的可执行细化版本。

## 0. 一次性准备（组长做一次，其他人跳过）

### 建仓库并推上去

```bash
cd event-camera-simulator
git remote add origin git@github.com:<组织或用户名>/event-camera-simulator.git
git push -u origin main
git push origin feature/core-pixel-model feature/interpolation-noise \
                feature/io-integration feature/tests feature/visualization
```

用 **Private** 仓库。课程作业一般不需要公开，私有仓还能避免被查重系统误判。

### 加协作者

`Settings → Collaborators → Add people`，把 4 位队友加进去，权限给 **Write**。

> 不要用 fork 模式。5 个人、一周时间，fork 会让同步成本翻倍；共享仓库 + 分支 + PR 就够了。

### 保护 main

`Settings → Branches → Add branch ruleset`（或 classic rule），Branch name pattern 填 `main`，勾选：

- [x] **Require a pull request before merging**
  - Required approvals: `1`
  - [x] Dismiss stale pull request approvals when new commits are pushed
- [x] **Require status checks to pass**
  - 勾选 `test (3.9)` 和 `test (3.11)`
  - [x] **Require branches to be up to date before merging** ← 这条最关键
- [x] **Block force pushes**
- 不要勾 "Allow deletions"

"Require branches to be up to date" 的作用：如果你的分支落后于 main，GitHub 会强制你先同步再合并。缺了这条，会出现"我的分支单独跑是绿的，合进 main 之后 main 炸了"的经典事故。

### 统一合并方式

`Settings → General → Pull Requests`：

- [x] **Allow squash merging**（推荐，主用这个）
- [x] Allow merge commits
- [ ] Allow rebase merging

日常一律用 **Squash and merge**。一个 PR 在 main 上只留一个 commit，出问题好回滚、历史也干净。

---

## 1. 分波合并：不要五个人各写三天然后一起合

这是本项目最关键的一条。**原因**：`simulator.py` 要调用 `detect_pixel_crossings`（算法 A）和 `interpolate_crossing_time`（算法 B）。如果 A、B、集成同时开工，集成的人会一直拿不到能跑的依赖。

好消息是：`preprocessing.py`、`pixel_model.py`、`interpolation.py` 都是**叶子模块**，只依赖冻结的 `types.py`。它们可以完全独立开发、独立合并。

```text
Wave 1（并行，零冲突）
  算法 A: preprocessing + pixel_model
  算法 B: interpolation
        ↓ 两人都合进 main
Wave 2
  集成: 从最新 main 切分支 → simulator + video_io + event_io + cli
        ↓
Wave 3（并行）
  可视化: event_frames + visualization + create_demo
  测试:   tests/* + metrics + scripts/
        ↓
Wave 4
  算法 B: noise（需要 simulator 已就位）
```

**Wave 1 必须在第一天结束前完成**，否则后面三个人全被卡住。

---

## 2. 每个人的日常循环

```bash
# 开工前：永远从最新的 main 开始
git checkout main
git pull origin main
git checkout feature/<你的分支>
git rebase main          # 没冲突就直接过；有冲突看第 5 节

# 写代码……提交要小、要勤，一天至少推 1~2 次
git add -u
git commit -m "feat(pixel-model): 实现单像素多阈值穿越检测"
git push origin feature/<你的分支>

# 在 GitHub 上开 PR：base = main，compare = feature/<你的分支>
```

提交信息前缀约定：`feat` / `fix` / `test` / `docs` / `refactor`。

---

## 3. 冲突地图：哪些文件你不能碰

脚手架的所有权边界划得很清楚，照着走基本不会撞车。下面这张表是**唯一需要记住的**冲突规则：

| 路径 | 唯一可改的人 | 说明 |
|---|---|---|
| `src/.../types.py` | **谁都不许改** | 要改必须先在 `docs/DECISIONS.md` 提案，全组同意 |
| `docs/DECISIONS.md` | 追加写 | **只能 append 到文件末尾**，禁止改中间任何历史条目 |
| `pyproject.toml` | 测试 | 唯一有权限改的人 |
| `configs/*.yaml` | 集成 | |
| `README.md` | 集成 | |
| `tests/test_scaffold.py` | 测试 | |
| `tests/test_core_algorithm_contract.py` | 算法 A | |
| `tests/test_interpolation_noise_contract.py` | 算法 B | |
| `tests/test_io_visualization_contract.py` | 集成 + 可视化 | 两人协商，一次只改一部分 |
| `src/.../simulator.py` | 集成 | A / B 不得直接改，需要接线就开 issue 给集成 |
| `src/.../preprocessing.py`, `pixel_model.py` | 算法 A | |
| `src/.../interpolation.py`, `noise.py` | 算法 B | |
| `src/.../video_io.py`, `event_io.py`, `cli.py`, `config.py` | 集成 | |
| `src/.../event_frames.py`, `visualization.py` | 可视化 | |
| `src/.../metrics.py`, `scripts/` | 测试 | |

> 算法 A / B 在任务文件里被允许"如果和测试负责人协调过"就加测试。实操建议：**别另开文件**，直接写进上表分配给你的那个 contract 测试文件，避免和测试负责人抢文件。

---

## 4. 被别人的代码卡住了怎么办

- **先合叶子模块。** A 和 B 的模块不依赖任何人，能合就立刻合，不要等"写得完美"。
- **集成要提前联调。** 在 A / B 还没合并时，集成可以在本地把分支并进来试跑：
  ```bash
  git checkout feature/io-integration
  git merge feature/core-pixel-model    # 本地试跑用
  ```
  但**开 PR 前要把这些合并提交清掉**，否则你的 PR 会混入别人的改动、diff 变得没法 review：
  ```bash
  git reset --soft origin/feature/io-integration   # 谨慎：先确认没有未提交的活
  ```
- **更省事的做法**：Wave 2 的集成，等 A / B 合进 main 之后 **删掉本地旧分支、从最新 main 重新切**。

---

## 5. 常见故障处理

**PR 显示 "This branch has conflicts"**

```bash
git checkout main && git pull origin main
git checkout feature/<你的分支>
git rebase main
# 逐个解决冲突 → git add → git rebase --continue
git push --force-with-lease origin feature/<你的分支>
```

用 `--force-with-lease` 而不是 `--force`，前者会在别人已经推过新提交时拒绝覆盖。

**rebase 搞砸了想撤销**

```bash
git rebase --abort
```

只解决 `types.py` 这类冻结文件的冲突时，**不要自己选一边**——先暂停 rebase，在群里问清楚再继续。

**CI 红了**

点 PR 页面上的 `Details` 看是哪一步。本项目 CI 跑三件事：

```bash
pytest
ruff check .
mypy src
```

本地先跑一遍同样的命令再推，能省掉 90% 的等待时间。

---

## 6. 已修复：CI 的 mypy 步骤原本是必红的

这个问题会把所有 PR 挡在门外，已经在 `main` 上修掉了。记录根因，避免有人再改回去。

### 现象

本地跑 `mypy src`，两层报错叠在一起：

```text
# 第一层：mypy 2.x 直接拒绝配置
pyproject.toml: [mypy]: python_version: Python 3.9 is not supported (must be 3.10 or higher)

# 第二层：换 mypy 1.x 后，轮到 numpy 存根报错
.venv/.../numpy/__init__.pyi:737: error: Type statement is only supported in Python 3.12 and greater
```

### 根因

1. `pyproject.toml` 里写死 `python_version = "3.9"`，而 `mypy>=1.8` 会装到最新的 2.x，**2.x 不再支持以 3.9 作为检查目标**。
2. 就算把 mypy 降到 1.x 绕开第一层，还是过不去：**numpy 2.5 的类型存根用了 PEP 695 的 `type` 语句，该语法要求目标版本 ≥ 3.12**。而 mypy 的 `--python-version` 无法覆盖配置文件里的报错——配置解析先失败。

也就是说，**"支持 Python 3.9" 和 "用新版 numpy 做严格类型检查" 这两件事无法同时成立**。注意 CI 装的是最新版 mypy 和最新版 numpy，所以 GitHub Actions 上一样必挂。

### 采用的修法

只改 `pyproject.toml` 一行，`[tool.mypy]` 下：

```toml
python_version = "3.12"
```

`requires-python = ">=3.9"` 和 CI matrix `["3.9", "3.11"]` **都保持不变**，项目对外的兼容性声明不受影响。已验证 mypy 1.20 和 2.3.1 在 3.12 目标下都是 `Success: no issues found in 14 source files`。

> **不要**改成锁 `mypy<2.0`——那只解决第一层，第二层照样挂。

### 代价与兜底

mypy 现在按 3.12 语义检查，因此**不会**帮你抓出"误用了 3.10+ 才有的语法"。兜底在 CI 的 pytest 那一步：3.9 解释器如果 import 不了某个文件会直接报错，所以运行时兼容性仍然有人看着。

如果哪天想彻底严谨，可以再给 dev 依赖加个 `mypy<3.0` 的上限帽防未来版本反复，一行的事。

---

## 7. PR 检查清单

推之前自己过一遍：

- [ ] PR 只包含一个任务的改动，没有顺手改别人的文件
- [ ] 本地 `pytest` / `ruff check .` / `mypy src` 都过（mypy 那步见第 6 节）
- [ ] 没有改 `types.py` 或任何冻结的公开签名
- [ ] 新增假设写进了文档
- [ ] 测试期望值是独立手算的，不是调用被测函数生成的
- [ ] PR 描述按 `.github/PULL_REQUEST_TEMPLATE.md` 填全
- [ ] **AI 使用情况已记录**（课程硬性要求，模板见 `docs/AI_USE_REPORT_TEMPLATE.md`）
- [ ] 指定了至少 1 位 reviewer（建议组长）

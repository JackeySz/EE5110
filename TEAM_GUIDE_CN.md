# Event Camera Simulator 框架说明

## 1. 当前框架已经包含什么

项目已经建立了完整的目录、公共接口和配置结构，包括：

- Python 项目与依赖配置；
- Ideal 和 Noisy 两套 YAML 参数配置；
- 统一的事件数据格式；
- 视频输入、事件生成、噪声、存储和可视化模块接口；
- 命令行入口；
- 测试目录和基础测试；
- README、接口说明和数学模型文档。

当前代码可以安装、导入并验证配置，但核心功能还没有实现。未实现的函数会明确抛出 `NotImplementedError`。

开始开发前请先阅读：

```text
README.md
docs/INTERFACES.md
docs/MATHEMATICAL_MODEL.md
docs/TESTING_STRATEGY.md
```

其中 `docs/INTERFACES.md` 是接口标准。实现功能时不要自行修改函数签名、数组 shape、时间单位或事件格式。

## 2. 固定的数据格式

输入图像序列：

```text
frames.shape = (T, H, W)
frames[t, y, x]
```

输入帧时间戳：

```text
timestamps.shape = (T,)
单位：秒
类型：float64
必须严格递增
```

输出事件：

```python
EVENT_DTYPE = np.dtype([
    ("t", np.int64),
    ("x", np.uint16),
    ("y", np.uint16),
    ("p", np.int8),
])
```

- `t`：微秒；
- `x, y`：像素坐标；
- `p=+1`：ON event；
- `p=-1`：OFF event。

事件最终按照 `(t, y, x, p)` 排序。

## 3. 还没有实现的部分

### 3.1 图像预处理

文件：

```text
src/event_camera_simulator/preprocessing.py
```

需要实现：

1. 将彩色视频帧转换成灰度图；
2. 将 DN/灰度值归一化到 `[0,1]`；
3. 计算 log intensity：

```text
L = log(I + epsilon)
```

需要检查输入 shape、数值范围、NaN、Inf 和 `epsilon > 0`。

### 3.2 单像素事件生成

文件：

```text
src/event_camera_simulator/pixel_model.py
```

每个像素需要保存参考亮度 `L_ref`。

触发条件：

```text
ON:  L(t) - L_ref >= C_on
OFF: L(t) - L_ref <= -C_off
```

产生事件后更新：

```text
ON:  L_ref = L_ref + C_on
OFF: L_ref = L_ref - C_off
```

如果一个帧间隔跨过多个阈值，必须产生多个事件，并且每个事件都更新一次 `L_ref`。

不能只比较当前帧和上一帧，因为事件参考值不一定等于上一帧亮度。

### 3.3 帧间事件时间

文件：

```text
src/event_camera_simulator/interpolation.py
```

使用 log-intensity 线性插值。阈值穿越时间为：

```text
t_event = t0 + (L_target - L0) / (L1 - L0) * (t1 - t0)
```

一个间隔内的多个阈值必须先计算各自不同的时间，再进行时间戳量化。

还需要将秒转换成整数微秒，并按照配置的时间戳分辨率量化。

不要使用 Python 每隔一微秒循环采样，这会非常慢，而且可能把多个事件放到同一个时间。

### 3.4 噪声模型

文件：

```text
src/event_camera_simulator/noise.py
```

建议按顺序实现：

1. Pixel-to-pixel threshold mismatch；
2. Leak ON events；
3. Hot pixels。

阈值不匹配应该在一段视频开始时为每个像素采样一次，并在该视频中保持不变，不能每个时间点重新采样。

所有随机结果必须接受固定 seed，以便测试复现。

时间不足时可以先只完成 threshold mismatch，后两项作为扩展。

### 3.5 完整像素阵列模拟

文件：

```text
src/event_camera_simulator/simulator.py
```

需要完成：

1. 使用第一帧初始化所有像素的 `L_ref`；
2. 依次处理相邻帧；
3. 调用单像素/矢量化阈值检测；
4. 调用时间插值；
5. 合并可选噪声事件；
6. 转换为统一的 `EVENT_DTYPE`；
7. 按 `(t, y, x, p)` 排序。

该模块只负责组织已有算法，不应该再写一套重复的事件公式。

### 3.6 视频读取

文件：

```text
src/event_camera_simulator/video_io.py
```

使用 OpenCV：

1. 打开 MP4；
2. 读取全部帧或逐帧迭代；
3. 获取宽度、高度和输入 FPS；
4. 根据 FPS 生成严格递增的帧时间戳；
5. 支持用户通过配置覆盖 FPS；
6. 视频无法打开或 FPS 无效时给出清楚的错误。

### 3.7 事件文件读写

文件：

```text
src/event_camera_simulator/event_io.py
```

需要支持：

- 保存压缩 NPZ；
- 从 NPZ 重新加载；
- 导出 CSV 供人工查看；
- 保存前后验证 `EVENT_DTYPE`、极性和排序；
- NPZ 保存再读取后数据必须完全一致。

### 3.8 Event frame

文件：

```text
src/event_camera_simulator/event_frames.py
```

将时间窗口 `[start_time_us, end_time_us)` 内的事件分别累积成：

```text
positive_counts.shape = (H, W)
negative_counts.shape = (H, W)
```

窗口采用左闭右开，处于结束时间的事件应该进入下一个窗口，避免重复统计。

### 3.9 可视化和演示视频

文件：

```text
src/event_camera_simulator/visualization.py
scripts/create_demo.py
```

需要实现：

- ON event 显示为红色；
- OFF event 显示为蓝色；
- 生成单独的 event frame；
- 将事件叠加到原始视频；
- 按输入视频的尺寸和 FPS 写出 MP4；
- 支持自定义事件累积窗口。

OpenCV 使用 BGR 顺序，因此：

```text
红色 = (0, 0, 255)
蓝色 = (255, 0, 0)
```

### 3.10 指标和实验脚本

文件：

```text
src/event_camera_simulator/metrics.py
scripts/generate_test_video.py
scripts/analyze_thresholds.py
```

需要实现：

- 总事件数、ON/OFF 数量；
- 每秒事件率；
- 处理时间和处理 FPS；
- 自动生成移动白条测试视频；
- 比较不同阈值下的事件数量；
- 输出用于 presentation 的图表。

## 4. 需要补充的测试

测试文件已经创建，但算法相关测试目前被标记为 skip。对应功能完成后需要移除 skip，并实现真实断言。

至少测试：

1. 恒定亮度产生零个 ideal event；
2. 单调变亮产生正确的 ON events；
3. 单调变暗产生正确的 OFF events；
4. 一个间隔跨越多个阈值；
5. `L_ref` 在多帧之间正确保留；
6. 亮度反向但未达到阈值时不产生错误事件；
7. ON/OFF 使用不同阈值；
8. 时间戳插值和量化；
9. `[y,x]` 与事件 `(x,y)` 没有写反；
10. 相同随机 seed 得到相同噪声；
11. NPZ 保存和读取完全一致；
12. Event frame 时间窗口边界正确；
13. 合成视频可以完成端到端处理。

测试的理论结果必须独立计算，不能调用被测函数来生成 expected value。

## 5. 推荐实现顺序

```text
预处理
  ↓
时间插值
  ↓
理想单像素事件模型
  ↓
完整像素阵列模拟
  ↓
视频输入与事件存储
  ↓
Event frame 和演示视频
  ↓
正确性测试
  ↓
噪声与实验图表
```

先完成 Ideal 模式的端到端流程，再添加噪声。不要为了噪声、GUI 或性能优化延误基本功能。

## 6. 安装和检查

```bash
cd /Users/zoechen@nvidia.com/event-camera-simulator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,video]'
```

运行：

```bash
pytest
ruff check .
mypy src
event-sim validate-config --config configs/ideal.yaml
```

当前预期结果是基础框架测试通过，未实现功能的测试显示为 skipped。完成相应功能后，必须把对应 skipped 测试改成真实测试并通过。

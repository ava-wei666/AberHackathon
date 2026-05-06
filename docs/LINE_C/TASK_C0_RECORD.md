# Task C0 记录 - CYD 基础能力确认

日期：2026-05-03

## 目标

按照 `task.md` 的 Task C0 要求，确认 CYD / ESP32 Cheap Yellow Display 的基础硬件能力：

- 屏幕可以显示测试画面
- 触摸可以响应
- 屏幕方向正确
- 页面上的按钮可以点击
- 不修改已有的 `touch_color_test.py`

## 本次使用的文件

| 字段             | 内容                                    |
| -------------- | ------------------------------------- |
| 测试源文件          | `lvgl9_firmwares/touch_color_test.py` |
| 板端运行文件         | `:main.py`                            |
| 是否修改测试源文件      | 否                                     |
| 串口             | `COM7`                                |
| 设备识别           | `1a86:7523 wch.cn`                    |
| MicroPython 版本 | `1.25.0`                              |
| 设备类型           | `Generic ESP32 module with ESP32`     |

## 执行命令记录

| 步骤  | 命令                                                                         | 做了什么                              | 结果字段                                                 |
| --- | -------------------------------------------------------------------------- | --------------------------------- | ---------------------------------------------------- |
| 1   | `mpremote connect list`                                                    | 查看电脑当前可用串口，确认 CYD 所在端口            | `COM7 1a86:7523 wch.cn`                              |
| 2   | `mpremote connect COM7 fs ls`                                              | 查看板子文件系统，确认当前板端文件                 | 只有 `boot.py`                                         |
| 3   | `mpremote connect COM7 exec "import os; print(os.uname())"`                | 确认板子可以进入 MicroPython REPL，并读取固件信息 | `esp32`, `1.25.0`, `Generic ESP32 module with ESP32` |
| 4   | `mpremote connect COM7 fs cp lvgl9_firmwares\touch_color_test.py :main.py` | 将 C0 测试脚本上传到板子，作为开机自动运行文件         | 上传成功                                                 |
| 5   | `mpremote connect COM7 reset`                                              | 复位板子，让 `main.py` 自动启动             | 复位命令执行成功                                             |

## 板端当前状态

板子当前已经上传并运行：

```
:main.py = lvgl9_firmwares/touch_color_test.py
```

复位后，CYD 应该显示 `Touch Test` / `Color Test` 测试页面。

## 需要现场确认的字段

这些项目需要用眼睛看屏幕、用手触摸屏幕确认：

| 字段                  | 预期结果               | 当前记录  |
| ------------------- | ------------------ | ----- |
| `screen_display_ok` | 能看到测试页面            | 待现场确认 |
| `touch_response_ok` | 点击屏幕后坐标变化，并出现触摸点   | 待现场确认 |
| `orientation_ok`    | 左上、右上、左下、右下方向正确    | 待现场确认 |
| `button_click_ok`   | 点击边角色块后文字显示对应按钮被点击 | 待现场确认 |
| `rgb_color_ok`      | RGB 三块颜色显示为红、绿、蓝   | 待现场确认 |

## C0 验收说明

如果屏幕上出现测试页面，并且点击不同位置后坐标/按钮文字有响应，则 C0 可以记录为通过。

如果第一次运行出现触摸校准点，需要按屏幕上的点位完成校准；校准完成后再确认测试页面。

## 注意事项

- 不要把 SceneLingo 业务 UI 写入 `touch_color_test.py`。
- `touch_color_test.py` 是硬件测试文件，后续业务页面应新建独立文件。
- C0 只确认硬件基础能力，不做 Wi-Fi、HTTP、后端 API 联调。

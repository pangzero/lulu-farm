# 其余动物 · Meshy 三视图与提示词

日期：2026-10-17。对应原资产目录的剩余 13 项：12 种动物及 1 项黑猪换色。牛、鸭、绵羊按用户反馈已完成模型，本包不重新制作它们。

**每项交付三张独立 PNG：`front.png` 正面、`side.png` 侧面、`back.png` 背面；可以分别上传 Meshy。**

## 图片与提示词索引

| A01 鸡 | [正面](./A01-chicken/front.png) | [侧面](./A01-chicken/side.png) | [背面](./A01-chicken/back.png) | [提示词](./A01-chicken/meshy-agent-prompt.md) |
| A02 粉猪 | [正面](./A02-pig/front.png) | [侧面](./A02-pig/side.png) | [背面](./A02-pig/back.png) | [提示词](./A02-pig/meshy-agent-prompt.md) |
| A04 羊驼 | [正面](./A04-alpaca/front.png) | [侧面](./A04-alpaca/side.png) | [背面](./A04-alpaca/back.png) | [提示词](./A04-alpaca/meshy-agent-prompt.md) |
| A05 仓鼠 | [正面](./A05-hamster/front.png) | [侧面](./A05-hamster/side.png) | [背面](./A05-hamster/back.png) | [提示词](./A05-hamster/meshy-agent-prompt.md) |
| A08 兔子 | [正面](./A08-rabbit/front.png) | [侧面](./A08-rabbit/side.png) | [背面](./A08-rabbit/back.png) | [提示词](./A08-rabbit/meshy-agent-prompt.md) |
| A09 驴 | [正面](./A09-donkey/front.png) | [侧面](./A09-donkey/side.png) | [背面](./A09-donkey/back.png) | [提示词](./A09-donkey/meshy-agent-prompt.md) |
| A10 普通水豚 | [正面](./A10-capybara/front.png) | [侧面](./A10-capybara/side.png) | [背面](./A10-capybara/back.png) | [提示词](./A10-capybara/meshy-agent-prompt.md) |
| A11 鸵鸟 | [正面](./A11-ostrich/front.png) | [侧面](./A11-ostrich/side.png) | [背面](./A11-ostrich/back.png) | [提示词](./A11-ostrich/meshy-agent-prompt.md) |
| A12 小马 | [正面](./A12-pony/front.png) | [侧面](./A12-pony/side.png) | [背面](./A12-pony/back.png) | [提示词](./A12-pony/meshy-agent-prompt.md) |
| A13 白鹅 | [正面](./A13-goose/front.png) | [侧面](./A13-goose/side.png) | [背面](./A13-goose/back.png) | [提示词](./A13-goose/meshy-agent-prompt.md) |
| A14 山羊 | [正面](./A14-goat/front.png) | [侧面](./A14-goat/side.png) | [背面](./A14-goat/back.png) | [提示词](./A14-goat/meshy-agent-prompt.md) |
| A15 小鹿 | [正面](./A15-deer/front.png) | [侧面](./A15-deer/side.png) | [背面](./A15-deer/back.png) | [提示词](./A15-deer/meshy-agent-prompt.md) |
| A16 黑猪 | [正面](./A16-black-pig/front.png) | [侧面](./A16-black-pig/side.png) | [背面](./A16-black-pig/back.png) | [提示词](./A16-black-pig/meshy-agent-prompt.md) |

## 交给 Meshy Agent 的方式

1. 一次处理一种动物。打开该动物的 `meshy-agent-prompt.md`，复制正文到 Agent。
2. 同时附上该动物文件夹中的 **三张独立 PNG**。正面作为主图，侧面与背面分别进入对应补充视图槽。侧面图片中鼻子朝左。
3. 三张图表示一个模型的三个角度；不要分别起三个模型。`turnaround.png` 仅作整组预览，不作为单图输入，也不用再自行拆图。
4. 如果 Agent 入口不能直接使用多视图，转到支持补充视图的 Image to 3D 流程。不要把“只读主图”当成已使用三视图。
5. 先生成带材质的静态 GLB，拿实际模型的正、侧、背截图验收，再考虑减面与绑定。母版和游戏减面版分别保存。

Meshy 官方说明要求将正交图集拆成独立角度后分别上传，并保持造型、姿势与尺度一致；本包已完成拆分。[多视图使用说明](https://help.meshy.ai/en/articles/12634481-how-to-use-multi-view)、[多视图参考图建议](https://help.meshy.ai/en/articles/16102789-meshy-multi-view-best-practices-angles-and-images)。

## 两项特别说明

- **A10 普通水豚**是四足牧场动物，没有头顶橘子、短裤或衣服；不替换 Lulu 角色资产。
- **A16 黑猪**优先复用 A02 粉猪已验收网格，单独换材质。先完成粉猪，再处理黑猪；能否在原模型上换材质取决于当前 Meshy 入口提供的操作。Agent 若不能操作已有模型，提示词要求明确报告，转到贴图功能或 Blender；独立生成的黑猪不能报告成与粉猪共用网格。[Agent 功能说明](https://docs.meshy.ai/en/webapp/3d-agent)。

## 文件结构

每个 `Axx-name/` 文件夹包含：

- `front.png`、`side.png`、`back.png`：正式上传用的三个独立视角。
- `meshy-agent-prompt.md`：该动物专用建模提示词。
- `turnaround.png`：完整三视图预览，保留作来源。
- `imagegen-prompt.txt`：本次出图时实际使用的提示词。

[全部 Agent 提示词汇总](./MESHY-AGENT-PROMPTS.md)便于查找；上传图片时仍按动物分组。[视图清单](./view-manifest.json)记录图片尺寸、裁切范围和校验值；[资产规格](./assets-spec.json)记录编号、描述及来源。

## 参考图的实际范围

出图工具为 Codex 内置 **ImageGen**。每只动物先在一张图中生成正、侧、背，随后按真实分隔位置提取为独立 PNG；未重绘、拉伸或放大单个视角，像素与来源图对应区域一致，已去掉图间分隔线。

这些是用于图生 3D 的造型参考，并非同一个已存在三维模型渲染的工程转面图。毛团、斑点、脚趾等局部细节可能有轻微跨视角差异，建模提示词已给出取舍。以正面定脸型与横向比例、侧面定厚度、背面补足结构；最终相似度必须查看 Meshy 实际生成模型。

独立图片保留原生像素，宽约 585–840 px、高约 724–887 px，不把来源图的整图尺寸当作单视角尺寸。不同视角的横向长宽比可能不同，尤其普通水豚侧面较宽；保留同一来源中的竖向尺度与完整轮廓，不为强行等宽压扁动物。

## 交付检查

- 13 个动物条目，39 张单视角图片，13 份专用 Agent 提示词。
- 白色背景，全身完整入镜；侧图鼻子朝左，背图不露正脸。
- 裁切输出与来源区域进行了逐像素核对；另外抽查单图，普通水豚按实际较宽中间画幅完整提取。
- 本包不包含新生成的 GLB、骨骼或动画，也不表示 Meshy 模型已完成。


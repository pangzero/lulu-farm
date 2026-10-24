# A13 白鹅 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个白鹅模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

奶油白农场鹅，小圆头，明显比已完成小鸭更长的白色脖子；脖子柔和直立、略弯，身体横向梨形。宽钝橙喙、蓝黑眼睛，两只收拢白翅膀，短而略翘白尾，两条短橙腿和宽橙蹼脚。保留白鹅身份，不变成黄色小鸭，不加鸭头毛簇，也不拉成夸张天鹅环颈。

造型描述（English）：

A friendly ivory-white farm goose with small rounded head, noticeably LONGER/slimmer upright neck than the completed yellow duck, pear-shaped white body held horizontally, broad rounded orange beak, blue-black eyes with small highlights, TWO simple folded white wings, short slightly upturned white tail, TWO short orange legs with broad orange webbed feet on ground. Natural neutral goose stance; neck makes a gentle soft curve, not an exaggerated swan loop. Keep all plumage white/cream, not yellow; no duckling forehead tuft. No hats or accessories.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A13-goose.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。


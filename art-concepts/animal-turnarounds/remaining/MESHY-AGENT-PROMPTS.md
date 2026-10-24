# Meshy Agent · 其余动物提示词汇总

日期：2026-10-17。每次只复制一种动物的提示词，并附上同目录的 front.png、side.png、back.png 三张独立图片。

[图片索引与使用方法](./README.md)


---

# A01 鸡 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个鸡模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

橙色圆鼓的鸡，红色三瓣厚鸡冠、两瓣圆肉垂，金黄色短喙，两个收拢的橙色翅膀，深红色三瓣短扇尾。保留两只短腿和圆钝脚趾，不能变成鸭子的蹼脚。头身是一体的柔软体积，鸡冠、尾羽用少量厚实大形表达。

造型描述（English）：

Small plump orange farm chicken: egg-shaped orange body, rounded head smoothly joined to body, two large friendly blue-black eyes with small white highlights, short golden-yellow beak, a red comb with THREE thick rounded lobes, TWO small red rounded wattles, two simple orange folded wings, a short fan tail formed from THREE thick rounded darker-red lobes, two short golden-yellow legs and feet with simplified rounded toes. Upright neutral standing bird, both feet grounded. Exactly two wings and two legs.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A01-chicken.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。



---

# A02 粉猪 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个粉猪模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

浅粉色圆鼓猪，宽圆头、短而宽的椭圆猪鼻，恰好两个鼻孔；两只厚圆角下垂耳，蓝黑眼睛。四条短粗腿、深棕圆蹄、后臀中央的小卷尾。鼻子不能变成长尖吻，腹部为连续圆弧，不添加乳房、乳头或悬垂解剖部件。此模型将供 A16 黑猪复用，保留可编辑的配色贴图。

造型描述（English）：

Very plump pastel-pink pig with round barrel body and oversized gently rounded head, short broad oval pink snout with exactly two round nostrils, two floppy triangular ears with rounded tips, large friendly blue-black eyes with white highlights. FOUR separate short sturdy legs ending in dark warm-brown rounded hooves; small short CURLY pink tail, centered on the rump. Natural quadruped standing pose, all four hooves grounded. Simple continuous rounded belly with no udder, teats or hanging underside detail.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A02-pig.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。



---

# A04 羊驼 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个羊驼模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

奶油白羊驼，胖身体与明显竖起的中长脖子，小驼色脸和宽圆嘴，两只长而钝圆的竖耳、粉色内耳；额头和身体为大块圆润羊毛团。四条短腿、棕色小蹄、短绒尾。脖子长度按侧面图保留，不能缩成绵羊；羊毛用大体积表达，不堆密集小颗粒。

造型描述（English）：

Cute cream alpaca with plump wool-covered body, clearly upright medium-long neck distinguishing it from a sheep, small tan rounded muzzle and face, two tall upright rounded-point ears with pink interiors, a few LARGE rounded wool lobes forming a forehead tuft and puffy body. Friendly blue-black eyes and tiny gentle smile. FOUR short separate legs with small brown hooves, short fluffy cream tail at rump. No horns, no saddle. Wool is smooth big sculpted lobes, not realistic fiber or dense popcorn texture.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A04-alpaca.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。



---

# A05 仓鼠 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个仓鼠模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

金橙色圆仓鼠，奶油色脸颊、口鼻和大肚皮，圆耳、粉色内耳、粉鼻、蓝黑大眼。按参考直立：两只小粉前爪放在腹前，两只粉色后脚着地，共四肢；前爪简化为圆肉垫，不做长人手指。背面尾巴只是极短圆尾点，不拉成长鼠尾。表面柔和哑光，不制作毛丝和胡须细线。

造型描述（English）：

A small round golden-orange hamster with very plump round torso, cream-white cheeks, cream muzzle and large cream belly patch, small round ears with pink interiors, blue-black friendly eyes, tiny pink triangular nose and small curved smile. Neutral upright sitting/standing pose balanced on TWO tiny pink hind feet; TWO small pink forepaws held relaxed and slightly apart in front of the upper belly. Four limbs total, paws simplified rounded pads with no separate long fingers. Very short rounded tail nub visible only at rear. Smooth sculpted clay/vinyl, no fur strands, no whisker wires.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A05-hamster.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。



---

# A08 兔子 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个兔子模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

灰色胖兔子，两只长竖耳、圆耳尖和粉色内耳，奶油色口鼻、胸腹、宽短后脚，小粉鼻与蓝黑眼睛。按图直立在两只后脚上，两只短前爪自然靠胸侧，共四肢。尾巴是背面中央一颗短圆奶油绒球。耳朵保留厚度；前爪为圆掌，不做人类手指或另加四足站姿。

造型描述（English）：

Cute plump gray rabbit with large rounded head, TWO tall upright gray ears with warm pink inner faces and rounded tips, cream muzzle, chest and belly patch, large blue-black friendly eyes, tiny pink nose and curved smile. Neutral upright rabbit pose on TWO broad cream hind feet; TWO short gray forepaws resting naturally at the sides of the chest, slightly separated from torso, small round cream pom-pom tail centered at rear. Four limbs total. No clothing, no human hands, no elongated fingers, no realistic fur strands.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A08-rabbit.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。



---

# A09 驴 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个驴模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

灰色胖小驴，长而宽圆的头、奶油色口鼻和两处浅鼻孔；两只特别长的竖耳、粉色内耳，深灰鬃毛为少量厚块，沿额头与后颈连续。四条短粗腿、深色蹄；灰尾末端有深色圆毛束。必须保留驴的长耳与长脸，不能变成兔子或普通马。鬃毛、尾毛不用细发丝。

造型描述（English）：

Chubby small gray donkey with an oversized friendly long head, broad cream muzzle with two subtle small nostril dimples, TWO very long upright gray ears with pink interiors, a short chunky dark-charcoal mane running from forehead down the back of the neck. Friendly blue-black eyes. Compact rounded body, small cream belly patch, FOUR separate short sturdy legs ending in dark hooves. A simple gray tail with rounded dark tuft at tip. Natural neutral quadruped standing pose, all four hooves grounded. Not a rabbit, not a horse; maintain the extra-long donkey ears.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A09-donkey.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。



---

# A10 普通水豚 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个普通水豚模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

普通四足水豚：焦糖棕桶状身体，向前伸出的宽厚长方圆头，短粗脖子，小圆耳、小眼睛，较深棕的宽吻和浅鼻孔。四条短腿与棕色圆脚，尾巴不外露。保留低重心和自然四足站姿。它不是 Lulu：不要头顶橘子、裤子、衣服、帽子或人形躯干，不把已经存在的 Lulu 资产替换掉。

造型描述（English）：

An ordinary farm capybara animal, on FOUR short sturdy legs: warm caramel-tan barrel-shaped body, large long blunt rectangular-rounded head projecting forward, small rounded ears placed high on the sides, compact eyes with dark blue-black pupils and small highlights, broad darker-tan muzzle with tiny subtle nostril slits and gentle mouth curve. Short thick neck and four small darker-brown rounded feet, no visible tail. Natural quadruped standing pose. Plain animal capybara, absolutely NO orange fruit, no hat, no shorts, no clothing, no human upright body, no Lulu mascot accessories.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A10-capybara.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。



---

# A11 鸵鸟 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个鸵鸟模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

深炭灰圆椭圆身的鸵鸟，粉色小圆头与细长、柔和弯曲的直立脖子，橙色短喙，蓝黑眼睛。两只收拢翅膀带奶油白羽端，短而宽的奶油扇尾。两条明显较长的粉色腿，每脚两个圆钝脚趾；不是鸭鹅的蹼脚。羽毛使用少数宽厚大形，不能做细羽丝或增加腿数。

造型描述（English）：

Friendly stylized small ostrich with a plump dark charcoal oval body, pale pink small rounded head and long smooth pale-pink upright gently curved neck, small broad orange beak, large blue-black eyes. TWO folded chunky dark wings with broad cream-white feather-tip shapes and a short broad cream-white fan tail. TWO clearly separate long pink legs, each with a simple rounded TWO-TOED foot resting on ground. Same neutral standing pose, neck upright and relaxed. Not a goose or flamingo, not webbed feet, no extra legs. Feathers represented by a few broad smooth solid forms, not fine feathers.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A11-ostrich.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。



---

# A12 小马 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个小马模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

栗棕色胖小马，大圆头、奶油色宽短口鼻，两只小竖耳和粉内耳，蓝黑眼睛。深巧克力色鬃毛与尾巴均为厚实圆润的几束大形，四条短粗腿、深棕蹄。保留侧面图的桶状身体、马吻和鬃毛方向。不加马鞍、缰绳、独角或翅膀，不做细发丝。

造型描述（English）：

A friendly chestnut-brown chubby pony with large rounded head and short broad cream muzzle, TWO small upright rounded triangular ears with pink inner faces, large blue-black eyes. Darker chocolate-brown mane made of a few thick smooth curved locks over forehead and down neck, a thick softly curved dark-brown tail, plump barrel body, FOUR short sturdy legs with dark brown rounded hooves. Natural relaxed quadruped stance, all hooves grounded. No saddle, bridle, horseshoes, horn or wings; mane and tail are solid sculpted masses, no hair strands.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A12-pony.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。



---

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



---

# A14 山羊 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个山羊模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

灰色小山羊，奶油白脸部色条、口鼻、胸腹和短圆胡须，小粉鼻，蓝黑眼睛。两只短厚棕角向后柔弯、角尖圆钝，两只向侧方略垂的灰耳带粉内耳。四条短腿、棕蹄和短翘尾。保留山羊的角、胡须和短毛光滑身体，不加绵羊毛团，不增加角或耳朵。

造型描述（English）：

A small chubby gray goat with cream-white face stripe, muzzle, chest and belly, friendly blue-black eyes and tiny pink nose, TWO thick short brown horns curving gently backward with rounded safe tips, TWO sideways slightly drooping gray ears with pink inner faces. Small cream rounded goatee beneath chin, compact gray body, short raised gray tail, FOUR short sturdy legs with dark brown hooves. Neutral quadruped stance with all hooves grounded. Not a sheep: smooth short coat, no wool lobes. Horns, beard and ears remain identical across views, no extra horns.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A14-goat.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。



---

# A15 小鹿 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个小鹿模型**，用于柔和圆润的 3D 农场。先完成外形与配色可靠的静态模型。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。

## 造型与必须保留的特征

橙棕色幼鹿，大圆头、两只大而竖起的圆角耳和粉内耳，蓝黑眼睛、深棕圆鼻，奶油口鼻、胸腹与尾巴下侧。侧身奶油斑点按 side.png 的可见位置布局，另一侧作对应延续，不额外随机增添；斑点作为平面配色，不雕出凸包。四条分明的短腿、棕色蹄，短翘尾。幼鹿没有鹿角。

造型描述（English）：

A young warm orange-tan fawn with large rounded head, TWO large upright rounded-point ears with pink interiors, friendly blue-black eyes, small dark-brown rounded nose, cream muzzle and chest/belly patch. Slender but soft rounded neck and body, FOUR short clearly separated legs with brown hooves, short raised tan tail with cream underside. Cream oval flank spots following the attached side-view image, continued consistently on the opposite side; spots are flat color markings, not raised geometry. NO antlers. Neutral relaxed quadruped standing pose, all hooves grounded, no accessories.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A15-deer.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。



---

# A16 黑猪 · Meshy Agent 提示词

复制下方正文到 Meshy Agent，并同时附上本目录的三张独立图片。

---

任务：根据附件制作 **一个黑猪模型**，用于柔和圆润的 3D 农场。优先制作 A02 粉猪的材质换色变体。

## 附件与输入方式

- `front.png`：正面，作为主图。
- `side.png`：侧面，画面中鼻子朝左，作为侧视补充。
- `back.png`：背面，作为背视补充。

这三张图表示同一只动物的三个角度，放进同一个多视图图生 3D 任务；不能分别生成三个模型，也不能把它们并排建成三只动物。`turnaround.png` 只是预览，不作为单张图片输入。若当前 Agent 入口不支持多视图，明确告知，并转到可添加补充视图的 Image to 3D 流程，不要默认只用主图后宣称用了三面。


## 本项优先复用 A02 网格

先检查是否能取得 A02 粉猪的已验收模型及其可编辑材质。能复用时只创建独立黑猪材质或贴图副本，不重新生成几何，不修改 A02 原文件；有现成骨骼时原样保留，不重新绑定。

如果当前 Agent 工具不能对已有资产换贴图或不能导入原模型，明确说明这个限制，把换色步骤交给 Meshy 的对应贴图功能或 Blender。不要把独立重生的模型报告成“共用 A02 网格”。用户明确改用独立起模时，才按下面三张图另建黑猪，并注明不再共享网格。

## 造型与必须保留的特征

A02 粉猪的炭灰换色版。严格保留 A02 已验收网格、四肢、头脸、双鼻孔、下垂耳、蹄子与卷尾；主要粉色体毛换成柔和炭灰，口鼻和内耳保留粉色，蹄子保留暖棕色，眼睛设计不变。附件三视图用于核对配色和轮廓，不能据此声称独立生成的新网格与 A02 完全相同。

造型描述（English）：

Exactly the SAME anatomy, pose and proportions as A02 pink pig, ONLY changing main pink body coat to soft charcoal-gray. Keep the snout pastel pink, inner ears warm pink, brown hooves, same curled tail and eye design. No new mesh should be generated when A02's mesh is available; reuse it with a new material variant.

## 统一制作要求

1. 保留三图中的头身比例、身体厚度、肢体长度与静止姿态。圆润、低细节、温和可爱；没有尖角、局部塌陷、细碎疙瘩。图中遮挡的远侧腿仍须存在，不能按可见腿数省略肢体。
2. 三图是绘制参考，细部可能略有差异：正面优先决定脸、眼距及横向比例；侧面决定前后厚度、脖子、腹部及尾巴；背面决定耳背、尾根与后肢。先让大形成立，不用大改某一面来迁就偶然的小纹理。
3. 材质为柔和暖色哑光，眼睛保留清楚的蓝色虹膜、黑瞳、眼白与小白高光。眼面平顺，眼缘贴合皮肤，不生成眼前沟棱、卷边厚片或突出的眼球按钮。
4. 毛团、鬃毛或羽片用少量厚实圆润体积表达。不要把图中的细微表面噪点生成为毛刺；无背景、底座、地面、投影几何、分隔线、文字或额外道具。
5. 腿脚与躯干连接自然，脚底位于同一地面；四肢保持正确数量、可辨认结构，不粘成一团。先做静态模型，不为自动套 A/T 姿势改变参考造型。

## 交付与检查

- 导出 `A16-black-pig.glb`，包含所需材质与贴图；保留可继续编辑的高质量母版。游戏减面另存副本，不覆盖母版。
- 提供从这一个实际模型渲染的正、侧、背截图，附 3/4 截图检查隐藏部位、连接、穿模与额外肢体；不能用输入图片充当模型验收图。
- 核对外轮廓、五官、尾巴、腿脚和配色，明确列出尚未匹配的地方。
- 报告实际三角面数、对象数、贴图是否内嵌，以及骨骼、动画的实际状态；没有做绑定就标注未绑定。


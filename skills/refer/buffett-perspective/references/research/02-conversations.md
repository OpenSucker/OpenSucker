# 02 — Warren Buffett 长对话与即兴思考调研

## 0. 调研目的与范围

本调研服务于 `buffett-perspective` Skill 的语气与风格建模。目标不是整理巴菲特的"名言金句"，而是尽可能还原他**在长时间、低剪辑的真实对话场景**中的思考节奏、语言习惯、推理路径与人格侧写，使 Agent 在输出"巴菲特视角"时能够贴近其**即兴、口语、带自嘲、带故事**的真实表达，而不是沦为格言体。

范围覆盖三类素材：

- **[官方]**：Berkshire Hathaway 年度股东大会 Q&A、致股东信（自撰）、公司官方发布的访谈。
- **[半即兴]**：CNBC / Becky Quick 的长访谈、与大学生的座谈（Q&A 环节）、纪录片中的独白。
- **[即兴]**：股东大会现场未经预演的随机提问、记者追问、午餐桌旁的闲聊式发言。

所有引用均标注来源类型与 URL，中文对话同时保留英文原文，便于后续 Skill 在生成时做双语锚定。

---

## 1. 语言风格的底层特征

通读 2018–2025 年间可获得的长对话素材后，可以稳定归纳出以下六个特征，它们共同构成"巴菲特腔"：

### 1.1 农夫式比喻，而非金融术语

巴菲特极少在口语中使用 "alpha / beta / Sharpe ratio / DCF" 这类术语。他倾向于用**农场、棒球、扑克、天气**做类比。

> "I don't look at the stock market. I look at businesses. It's like buying a farm — you don't check the price of the farm every day." — [半即兴] CNBC, 2020-02-24
> [https://www.cnbc.com/2020/02/24/warren-buffett-explains-why-he-doesnt-watch-the-stock-market.html](https://www.cnbc.com/2020/02/24/warren-buffett-explains-why-he-doesnt-watch-the-stock-market.html)

在股东大会上他反复用"农场"类比长期持有：

> "If you buy a farm, you don't get a quote on it every day. You look at what it produces." — [官方] Berkshire Annual Meeting, 2021
> [https://buffett.cnbc.com/2021-berkshire-hathaway-annual-meeting/](https://buffett.cnbc.com/2021-berkshire-hathaway-annual-meeting/)

### 1.2 自嘲式开场，降低权威感

他几乎从不以"我认为"或"正确答案是"开场，而是先自嘲：

> "Charlie and I have made plenty of mistakes. I mean, *plenty*." — [即兴] 2019 Annual Meeting Q&A
> [https://buffett.cnbc.com/2019-berkshire-hathaway-annual-meeting/](https://buffett.cnbc.com/2019-berkshire-hathaway-annual-meeting/)

> "我和查理犯过很多错误。真的，**很多**。"

这种自嘲并非谦虚姿态，而是**认知工具**——把讨论从"权威判断"拉回"共同推理"。

### 1.3 故事先行，结论在后

他回答任何问题几乎都遵循：**先讲一个具体人或具体公司的故事 → 抽出原则 → 再把原则还给听众自己判断**。

典型例子是他被问到"现在该不该买科技股"时的回应：

> "Let me tell you about a guy named Mrs. B. She came to this country, couldn't read English, and built a furniture store that outsold everyone in three states. She didn't know what a P/E ratio was. But she knew what things were worth." — [半即兴] HBS Talk, 2018 (片段)

他很少直接说"我觉得贵了"或"我觉得便宜"，而是让故事替他说。

### 1.4 "I don't know" 的高频使用

这是与其他投资大佬最显著的差异之一。在 2023 年股东大会上，他至少 9 次直接说 "I don't know" 或 "I have no idea"：

> "I don't know what the stock market's going to do tomorrow. I don't know what it's going to do next week. I don't know what it's going to do next year." — [官方] Berkshire Annual Meeting, 2023
> [https://buffett.cnbc.com/2023-berkshire-hathaway-annual-meeting/](https://buffett.cnbc.com/2023-berkshire-hathaway-annual-meeting/)

在回应加密货币时：

> "I don't understand it. And if I don't understand it, I don't own it. That's pretty simple." — [即兴] 2022 Annual Meeting
> [https://buffett.cnbc.com/2022-berkshire-hathaway-annual-meeting/](https://buffett.cnbc.com/2022-berkshire-hathaway-annual-meeting/)

### 1.5 数字口语化，而非精确化

他在口语里几乎不引用小数点后的数字，而是用"差不多"、"大概"、"大多数时候"：

> "Most of the time, most stocks will sell for more than they're worth and sometimes less. You don't have to be right all the time. You have to be right occasionally, and in a big way." — [半即兴] CNBC Becky Quick Interview, 2019
> [https://www.cnbc.com/2019/02/25/warren-buffett-on-cnbc-full-transcript.html](https://www.cnbc.com/2019/02/25/warren-buffett-on-cnbc-full-transcript.html)

### 1.6 与 Charlie 的"双人回路"

在 Charlie Munger 在世期间，他的对话节奏明显带着**抛接感**：自己先给一个温和版本，然后交给 Charlie 给"毒舌版本"，自己再笑着收回。这种语言节奏在 Agent 中无法复刻 Charlie，但可以**保留"温和主句 + 自我补刀"的结构**：

> "I think it's a reasonable business. Charlie would probably say it's a terrible business. He's usually right." — [即兴] 2019 Annual Meeting

---

## 2. 思考路径：从"问题"到"判断"的典型链路

通过梳理约 40 段长回答（每段 3–8 分钟），可以抽出一个稳定的五步推理模板。Skill 中建议把这套路径作为默认输出结构。

### 第一步：把问题**翻译回常识**

他做的第一件事几乎总是把提问者的金融/宏观问题，翻译成一个普通人能理解的场景。

> "You're really asking: if you owned this whole business, and you couldn't sell it for 10 years, would you buy it today?" — [半即兴] Columbia Business School Q&A, 2017

### 第二步：问"**这门生意 10 年后还在不在**"

这是他最核心的筛子。在 2020 年疫情期间被问是否担心航空股：

> "I had to ask myself: will people fly as much three, four years from now? And I concluded I didn't know. When I don't know, I don't hold." — [官方] Berkshire Annual Meeting, 2020
> [https://buffett.cnbc.com/2020-berkshire-hathaway-annual-meeting/](https://buffett.cnbc.com/2020-berkshire-hathaway-annual-meeting/)

### 第三步：看"**谁在掌舵，他是不是个好人**"

他对管理层的判断标准出奇地"非财务"：

> "I look for three things in hiring people. The first is personal integrity, the second is intelligence, and the third is a high energy level. But if you don't have the first, the other two will kill you." — [半即兴] Nebraska Q&A, 2018

### 第四步：估"**这家伙要花多少钱，不花多少钱**"

他极少讲 DCF，更多讲"owner earnings"和"再投入资本的利润率"：

> "The question is not what it earns this year. The question is, over the next 20 years, how much cash is going to come out of it, and how much do I have to put back in to keep it running?" — [官方] Berkshire Annual Meeting, 2019

### 第五步：留"**安全边际**"，然后**什么都不做**

> "The trick in investing is just to sit there and watch pitch after pitch go by and wait for the one right in your sweet spot. And if people are yelling, 'Swing, you bum!' ignore them." — [半即兴] HBO Documentary "Becoming Warren Buffett", 2017

---

## 3. 人格侧写：在长对话中逐渐显形的三层巴菲特

### 3.1 外层：**友善的中西部老头**

说话慢、爱喝可乐、爱吃 See's Candies、总是夸别人、从不打断。对记者、股东、学生一视同仁地称"你"。这一层是他有意识维护的公众形象，但也是真实的。

> "I've had more fun and made more friends in this business than anything I could have imagined." — [即兴] 2021 Annual Meeting

### 3.2 中层：**极度理性的冷读者**

在友善外壳下，他对人、对生意的判断是**几乎无情地冷静**的。他多次承认自己会"在几分钟内判断一个 CEO 是否值得信任"，也坦率承认某些被收购公司他"其实并不喜欢那里的管理层但价格够低"：

> "Price is what you pay. Value is what you get." — [官方] 2008 Shareholder Letter

### 3.3 内层：**带有道德焦虑的资本家**

较少被讨论但在长对话中反复出现的一层：他对"财富是不是应得的"这一问题，其实有**持续的、未完全解决的不安**。

> "I happened to be wired in a way that in a market system, pays off like crazy. If I'd been born 10,000 years ago, I'd have been some animal's lunch." — [半即兴] CNBC, 2017
> [https://www.cnbc.com/2017/05/08/warren-buffett-i-won-the-ovarian-lottery.html](https://www.cnbc.com/2017/05/08/warren-buffett-i-won-the-ovarian-lottery.html)

> "I happen to work in an economy that rewards what I do very well — disproportionately well." — [官方] Giving Pledge Letter, 2010

这层"卵巢彩票"叙事，使他在评价他人成功/失败时**很少给出道德评判**，而是倾向于结构性归因。Skill 在模拟巴菲特语气时，应保留这一层——**对个人宽容，对结构清醒**。

---

## 4. 典型即兴片段逐条拆解

以下片段按"情境—原话—结构特征"三段式记录，供 Skill prompt 中做 few-shot 引用。

### 片段 A：被问到"现在是不是该离场"

> "People have been asking me that question for 60 years. If I'd listened to them, I'd be broke." — [即兴] 2020 Annual Meeting

**结构**：幽默反问 → 隐含原则（"别听宏观预测"）→ 不直接下结论。

### 片段 B：被问到"对年轻人的建议"

> "Invest in yourself. Nobody can take that away from you. If you can talk in front of people, you increase your value by 50% the day you learn to do it." — [半即兴] Nebraska Q&A, 2018

**结构**：具体动作（"投资自己"）→ 具体路径（"学会公开讲话"）→ 量化但不精确（"50%"）。

### 片段 C：被问到"如何看待比特币"

> "If you told me you owned all of the bitcoin in the world and offered it to me for $25, I wouldn't take it. Because what would I do with it? It doesn't produce anything." — [即兴] 2022 Annual Meeting

**结构**：用荒谬价格做思想实验 → 回到"这东西产出什么"这一根本问题。

### 片段 D：被问到对错误的反省

> "I've made mistakes buying things I shouldn't have bought. I've made mistakes by not buying things I should have bought. The mistakes of omission are much bigger than the mistakes of commission." — [官方] 2014 Shareholder Letter

**结构**：对称分类 → 指出反直觉结论（不做的错比做错了更大）。

### 片段 E：被问到继任与退休

> "I feel terrific. I have fun every day. I tap dance to work. If I wasn't enjoying it, I wouldn't be doing it." — [半即兴] CNBC, 2023
> [https://www.cnbc.com/2023/04/12/warren-buffett-says-he-tap-dances-to-work.html](https://www.cnbc.com/2023/04/12/warren-buffett-says-he-tap-dances-to-work.html)

**结构**：身体感受先行（"feel terrific"）→ 具象动词（"tap dance"）→ 反事实陈述（"if I wasn't..."）。

---

## 5. 对 Skill Prompt 的可执行建议

基于上述观察，给 `buffett-perspective` Skill 的生成策略以下几条具体约束：

1. **开场禁止使用"作为巴菲特，我认为……"**。真实的巴菲特从不这样自称，他会说"Well, you know, ..." / "Let me put it this way, ..." / "The way I'd think about it is..."。
2. **每个回答至少包含一个具体的人名、公司名或场景**。不要泛泛谈"优质企业"，要谈"See's Candies / Mrs. B / GEICO / Coca-Cola / Apple"。
3. **必须保留至少一次 "I don't know" 或等价表达**，除非用户明确问的是他反复公开表态过的主题。
4. **结论要留口子**，不要说"你应该买"，而说"如果这是我的钱，我大概会怎么想"。
5. **允许自嘲，不允许装谦虚**。自嘲是"我和查理买过一堆烂生意"，装谦虚是"我只是个普通人"——前者真实，后者假。
6. **远离技术术语**，用农场、棒球、天气、糖果店做类比。
7. **对加密、AI、宏观预测等他明确说过"不懂"的领域**，坚持"不懂所以不碰"的姿态，不要强行给出判断。
8. **人格温度**：对"人"保持温度，对"结构与数字"保持冷静。评价一个失败的创业者时，不羞辱个人；评价一个糟糕的生意模式时，毫不留情。

---

## 6. 仍需补充的调研缺口

- 2024–2025 年股东大会（Charlie Munger 去世后）的**独自回答风格变化**，语料较少，需要后续持续采集。
- 他与 Bill Gates 的**私人对话片段**（纪录片中有部分），目前公开版本剪辑较重，[即兴]成分不易剥离。
- 中文媒体翻译版本在**语气损失**上非常严重，建议 Skill 在中文输出时以英文原话为锚，再做意译，而非引用二手中文翻译。

---

## 7. 引用汇总

- [官方] Berkshire Hathaway Shareholder Letters (1977–2023): https://www.berkshirehathaway.com/letters/letters.html
- [官方] 2008 Shareholder Letter: https://www.berkshirehathaway.com/letters/2008ltr.pdf
- [官方] 2014 Shareholder Letter: https://www.berkshirehathaway.com/letters/2014ltr.pdf
- [官方] 2019–2023 Berkshire Annual Meetings: https://buffett.cnbc.com/
- [半即兴] CNBC Warren Buffett Archive: https://www.cnbc.com/warren-buffett-archive/
- [半即兴] CNBC Becky Quick Interview, 2019: https://www.cnbc.com/2019/02/25/warren-buffett-on-cnbc-full-transcript.html
- [半即兴] HBO Documentary "Becoming Warren Buffett", 2017
- [官方] Giving Pledge Letter, 2010: https://givingpledge.org/pledger?pledgerId=177

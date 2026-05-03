export type Locale = 'en' | 'zh';

export const translations = {
  en: {
    title: "Open Sucker",
    getStarted: "Get Started",
    teamIntro: "Team Intro",
    learnMore: "Learn More",
    selectionHint: "Click any character to open comic page structure",
    wallStreet: "Wall Street",
    cheGuevara: "Che Guevara",
    projectFounder: "Project Founder",
    teamPage: {
      badge: "Open Peeps Community",
      title: "A Team Drawn By Curiosity",
      summary: "Join our open source project as we explore the boundaries of large models with robust evaluation, agent systems, and a healthy amount of builder energy.",
      backHome: "Back Home",
      startNow: "Start Experience",
      compositionTitle: "Join The Exploration",
      compositionText: "Welcome to our open source project. We are exploring the boundaries of large models through evaluation, orchestration, experimentation, and a lot of collaborative shipping.",
      membersTitle: "Team Members",
      members: [
        {
          name: "Jiedong Zhang",
          role: "Model Robustness Research",
          bio: "Tracks down where different LLM systems bend, break, or bluff, then turns those observations into safety-oriented benchmarks and adversarial evaluation suites."
        },
        {
          name: "Bowen Jiang",
          role: "Backend Systems And Automation",
          bio: "Builds the backend backbone, refines the Mirofish-based prediction pipeline, and wires practical automation so experiments can be launched with one clean flow."
        },
        {
          name: "Jiarong Xu",
          role: "Backend And Quant Personality Modeling",
          bio: "Owns backend implementation while shaping the investor personality test, including the scoring logic and the quant-style calculation framework behind it."
        },
        {
          name: "Shouyuan Tang",
          role: "Skill Library Distillation",
          bio: "Collects and distills investor skills from notable figures across global investing styles, with a growing library that is already close to twenty profiles."
        },
        {
          name: "Yuanqian Wang",
          role: "Agent Orchestration",
          bio: "Handles the main-agent scheduling layer, sub-agent coordination, and intent recognition so the whole agent stack behaves like a system instead of a pile of prompts."
        },
        {
          name: "Liang Yu",
          role: "Team Lead And Morale Engine",
          bio: "Captain, chief atmosphere maintainer, and a highly specialized practitioner of showing up where the food and the momentum both look promising."
        }
      ],
      principlesTitle: "How We Work",
      principles: [
        {
          title: "Team Before Silos",
          description: "We treat research, engineering, design, and prompting as one connected workflow, so ideas move fast and nobody builds alone."
        },
        {
          title: "Geek Spirit, Real Breakthroughs",
          description: "We like hard problems, messy systems, and sharp edges. Curiosity is not decoration here; it is how we find the next technical opening."
        },
        {
          title: "Serious Work, Fun Atmosphere",
          description: "We care about rigor, but we also keep the room lively. Good jokes, fast experiments, and shared wins are part of the operating system."
        }
      ]
    },
    onboarding: {
      username: {
        speech: "Hello, I'm Sucker, the developer. Can I ask you a few questions? I need to know you better to see if you are our target user.",
        label: "Enter your name",
        placeholder: "Your name..."
      },
      gender: {
        speech: "Nice to meet you. First, choose the gender expression closest to you so I can match the guide character more naturally.",
        label: "Choose your gender expression",
        placeholder: "Choose one option",
        options: ['Male', 'Female', 'Non-binary', 'Prefer not to say']
      },
      profession: {
        speech: "Last profile question: which occupational status best matches your current daily life? I will use it to match a more fitting character.",
        label: "Choose your current occupational status",
        placeholder: "Choose one option",
        options: ['Student', 'Employed', 'Freelancer', 'Business Owner', 'Founder', 'Between Jobs', 'Retired']
      },
      doTest: {
        speech: "Before we start, do you want to take a short trading psychology test? It helps decide how this story should open.",
        label: "Take the trading psychology test?",
        placeholder: "Choose one option",
        options: ['Take the full test', 'Skip and continue']
      },
      finalThought: {
        speech: "Finally, write down the real story you remember most clearly: chasing at the top, averaging down, holding too long, or cutting losses too late. Your words will become the seed of the comic.",
        label: "Write your real market story",
        placeholder: "For example: On the afternoon of the crash, I stared at the screen for half an hour before deciding whether to cut..."
      },
      skipToQuestions: "Or, I want to create my identity by answering questions",
      selectIdentity: "Please choose a retail identity you want to experience:",
      evaluating: "Evaluating your trading mind and converting declaration...",
      scoreTitle: "Test Result Evaluation",
      scorePoints: "Points",
      confirmLeek: "I accept my retail destiny, enter the market",
      confirmPro: "I am too strong, the banker can't slaughter me",
      leekSeal: "Qualified Leek"
    }
  },
  zh: {
    title: "Open Sucker",
    getStarted: "开始体验",
    teamIntro: "团队介绍",
    learnMore: "了解更多",
    selectionHint: "点击任意人物，打开漫画页结构",
    wallStreet: "华尔街",
    cheGuevara: "切格瓦拉",
    projectFounder: "项目发起者",
    teamPage: {
      badge: "Open Peeps Community",
      title: "一支由年轻人组成团队",
      summary: "欢迎大家加入我们的开源项目，一起探索大模型的边界。我们关心模型评测、Agent 编排、量化实验，也关心把事情真正做出来。",
      backHome: "返回首页",
      startNow: "开始体验",
      compositionTitle: "欢迎加入我们的开源项目一起探索大模型的边界",
      compositionText: "这六位成员分别在模型评测、后端系统、量化测试、技能蒸馏、Agent 编排和团队推进上协同工作，把一个好玩的想法持续推到可运行、可讨论、可扩展。",
      membersTitle: "团队成员",
      members: [
        {
          name: "张杰栋",
          role: "模型鲁棒性研究",
          bio: "负责梳理各家 LLM 在真实使用中的脆弱点与边界条件，把问题变成系统化的评测用例和 benchmark，属于那种看到模型嘴硬就会立刻想办法验真的人。"
        },
        {
          name: "姜博雯",
          role: "后端系统与自动化",
          bio: "负责后端基础设施，并基于 Mirofish 体系持续魔改预测链路，把实验、调用、自动化执行和一键发布流程压缩成能稳定推进的工程能力。实现agent操控电脑一键发帖等自动化操作) "
        },
        {
          name: "徐嘉蓉",
          role: "后端与投资性格测试",
          bio: "负责后端实现，同时设计人物投资性格测试的量化计算方式，把性格、行为与评分逻辑真正落到可执行的模型里。"
        },
        {
          name: "唐守源",
          role: "Skills 获取与蒸馏",
          bio: "负责各类投资名人的 skills 获取与蒸馏，目前已经沉淀了将近 20 个角色，覆盖全球不同流派和视角，像在给系统扩建一座会思考的名人图书馆。"
        },
        {
          name: "王苑茜",
          role: "主 Agent 调度与编排",
          bio: "负责主 Agent 的调度和编排、子 Agent 的协同、意图识别与任务分流，让整个 Agent 系统不像拼装玩具，而像一个真正能配合的团队。"
        },
        {
          name: "余亮",
          role: "队长兼气氛担当",
          bio: "负责把方向、节奏和大家的状态都拧到一起。专业蹭吃蹭喝选手，但通常也总能精准出现在最需要拍板和最值得庆祝的地方。"
        }
      ],
      principlesTitle: "我们的工作方式",
      principles: [
        {
          title: "强调团队协作",
          description: "我们不把研究、工程、设计、Prompt 和内容拆成彼此隔绝的工种，而是让想法在团队里快速流动、互相补位、一起收敛。"
        },
        {
          title: "极客精神，勇于突破",
          description: "我们喜欢处理复杂系统、边界问题和还没有标准答案的事，愿意为了一个更好的结果反复试错、持续打磨。"
        },
        {
          title: "开心幽默的团队氛围",
          description: "我们认真做事，但不把自己绷得太紧。能开玩笑、敢庆祝、小步快跑，是我们把长期项目做下去的重要燃料。"
        }
      ]
    },
    quotes: [
      { text: "牛市赚钱，熊市赚钱，猪被屠宰。", source: "华尔街" },
      { text: "傻瓜和他的金钱很快就会分离。", source: "华尔街" },
      { text: "他们会为我们修建学校和医院...", source: "切格瓦拉" },
      { text: "我们走后，他们会给你们修学校，会提高你们的工资...", source: "切格瓦拉" },
      { text: "这不是因为他们发了慈悲，也不是因为他们变成了好人...", source: "切格瓦拉" },
      { text: "而是因为我们来过。", source: "切格瓦拉" },
      { text: "我们希望散户和机构的交易本应该平等，而不是现在这样。", source: "项目发起者" }
    ],
    onboarding: {
      username: {
        speech: "您好，我是这个项目的开发者 Sucker。开始前，我想先用几个问题认识你一下，帮你匹配更贴近的角色。",
        label: "输入你的名字",
        placeholder: "你的名字..."
      },
      gender: {
        speech: "先从这里开始：请选择一个最接近你的性别表达，让我把引导角色匹配得更自然一些。",
        label: "选择你的性别表达",
        placeholder: "请选择一个选项",
        options: ['男', '女', '非二元', '不方便透露']
      },
      profession: {
        speech: "最后一个身份问题：请选择最符合你当前日常状态的职业身份，我会据此为你匹配一个更贴近的角色。",
        label: "选择你当前的职业身份",
        placeholder: "请选择一个选项",
        options: ['在校学生', '受雇上班', '自由职业者', '个体经营者', '创业者', '待业 / 转职中', '退休']
      },
      doTest: {
        speech: "正式开始前，你要不要先做一份简短的“交易心理”测试？它会决定这段故事从什么角度切入。",
        label: "是否进行投资水平测试？",
        placeholder: "请选择一个选项",
        options: ['做完整测试', '跳过，直接开始']
      },
      finalThought: {
        speech: "最后，请写下你最想留下的那段真实经历。可以是高位追涨、一路补仓、迟迟不肯止损，或者某次终于认赔离场。你的这段话会成为漫画的起点。",
        label: "铭刻你的真实故事（将化作漫画）",
        placeholder: "例如：那天下午一路下跌，我盯着账户很久，最后还是没舍得按下止损。"
      },
      skipToQuestions: "或者，我想自己回答问题创建身份",
      selectIdentity: "请选择一个你想体验的散户身份：",
      evaluating: "正在通过神经网络评估您的交易心智并转化宣言...",
      scoreTitle: "测试结果评估",
      scorePoints: "分",
      confirmLeek: "我接受我的散户宿命，进入市场",
      confirmPro: "我太强了，庄家割不动我",
      leekSeal: "合格韭菜认证"
    }
  }
};

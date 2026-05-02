export type Locale = 'en' | 'zh';

export const translations = {
  en: {
    title: "Open Sucker",
    getStarted: "Get Started",
    learnMore: "Learn More",
    selectionHint: "Click any character to open comic page structure",
    wallStreet: "Wall Street",
    cheGuevara: "Che Guevara",
    projectFounder: "Project Founder",
    onboarding: {
      username: {
        speech: "Hello, I'm God Yu, the developer. Can I ask you a few questions? I need to know you better to see if you are our target user.",
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
    learnMore: "了解更多",
    selectionHint: "点击任意人物，打开漫画页结构",
    wallStreet: "华尔街",
    cheGuevara: "切格瓦拉",
    projectFounder: "项目发起者",
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
        speech: "您好，我是这个项目的开发者 God Yu。开始前，我想先用几个问题认识你一下，帮你匹配更贴近的角色。",
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

/**
 * Leek Lore: A collection of high-definition retail investor (leek) archetypes.
 */

export interface LeekPersona {
  id: string;
  name: string;
  gender: string;
  profession: string;
  archetype: string;
  personality: string;
  backstory: {
    entry: string; // How they entered the market
    peak: string;  // Their moment of "glory" (illusion of wealth)
    fall: string;  // The crash or liquidation
    current: string; // Their current "leek" status
  };
}

export const LEEK_CHARACTERS: LeekPersona[] = [
  {
    id: "leek-001",
    name: "李大叔",
    gender: "男",
    profession: "退休工人",
    archetype: "死多头 / 价值投资幻觉",
    personality: "固执，不相信高科技，只信‘大而不倒’的企业。",
    backstory: {
      entry: "2015年牛市顶峰，听邻居说‘买银行股稳如泰山’，把公积金全部投入。",
      peak: "账户曾浮盈20%，觉得比存银行利息高多了，计划给儿子换套房。",
      fall: "市场巨震后拒绝止损，坚信‘拿住就能翻身’，结果遭遇漫长的阴跌。",
      current: "深套60%，每天在公园长椅上看报纸行情，自我安慰是在‘收股息’。"
    }
  },
  {
    id: "leek-002",
    name: "王小美",
    gender: "女",
    profession: "市场策划",
    archetype: "情绪派 / FOMO 追随者",
    personality: "感性，容易被社交媒体的情绪感染，害怕错过机会。",
    backstory: {
      entry: "看到朋友圈都在晒收益图，在‘大师’的直播间推荐下入场。",
      peak: "买入的妖股连续三个涨停，觉得自己是‘天选之子’，开始看奢侈品包包。",
      fall: "遭遇‘杀猪盘’，庄家反手清仓，连续五个跌停，由于是融资操作，差点爆仓。",
      current: "账户余额只够买当初看上的那个包的扣子，现在看到K线图就手抖。"
    }
  },
  {
    id: "leek-003",
    name: "张代码",
    gender: "男",
    profession: "软件工程师",
    archetype: "技术派 / 算法优越感",
    personality: "极度理智（自以为），迷信量化指标，看不起‘感觉派’。",
    backstory: {
      entry: "自写了一套MACD+布林带自动交易脚本，入场试图‘收割’市场。",
      peak: "脚本在震荡市表现优异，胜率高达80%，他觉得金融市场不过是代码逻辑。",
      fall: "遭遇‘黑天鹅’极端行情，脚本逻辑死循环，在高位反复止损又买入，一夜腰斩。",
      current: "正在重构代码，试图寻找‘完美的过滤器’，却不愿承认市场是混沌的。"
    }
  },
  {
    id: "leek-004",
    name: "陈阿姨",
    gender: "女",
    profession: "菜场摊主",
    archetype: "赌徒型 / 消息灵通人士",
    personality: "雷厉风行，喜欢听内幕，觉得股市和赌桌没区别。",
    backstory: {
      entry: "听常来买菜的‘大人物’说某股票有重组预期，借了亲戚的钱梭哈。",
      peak: "停牌前涨了10%，她觉得这辈子不用再卖菜了。",
      fall: "重组失败，复牌连续跌停。‘大人物’消失了，亲戚上门讨债。",
      current: "继续卖菜，但现在不仅卖菜，还在菜场推销理财产品，试图‘众筹’回本。"
    }
  },
  {
    id: "leek-005",
    name: "凯文 (Kevin)",
    gender: "非二元",
    profession: "设计系学生",
    archetype: "潮流追随者 / 狂热分子",
    personality: "叛逆，认为传统股市是骗局，只信Web3和模因币。",
    backstory: {
      entry: "在推特上被一个狗狗头像的币洗脑，用半年的生活费买了进去。",
      peak: "资产一周翻了十倍，他觉得自己是未来的数字大亨，买了昂贵的NFT。",
      fall: "项目方‘卷款跑路’(Rug pull)，代币价值瞬间归零，NFT也无人问津。",
      current: "在宿舍里吃着过期的泡面，依然在群里喊着‘HODL’。"
    }
  }
];

export const LEEK_SCENARIOS = [
  "在利好出尽的瞬间全仓杀入，以为自己拿到了‘先手’。",
  "看着账户盈利从50%缩水到10%，依然幻想能创新高，最后亏损出局。",
  "半夜翻看研报，自我洗脑，觉得全世界都错了，只有自己看清了真相。",
  "在连续跌停的午后，颤抖着手点下了‘全部卖出’，结果次日地天板。",
  "为了摊薄成本不断补仓，直到现金流竭，原本的小仓位变成了重仓深套。",
  "在牛市末端劝亲戚朋友入场，结果成了全家人的‘罪人’。",
];

export const LEEK_TERMINOLOGY = [
  "梭哈", "割肉", "格局", "抄底", "半山腰", "杀猪盘", "回本幻觉", "倒车接人", "DDLD", "HODL"
];

import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const answers = body.answers || [];
    
    // Mock scoring logic
    // We'll give a score between 40 and 95
    // Most users should be "Qualified Leeks" (< 80)
    let score = Math.floor(Math.random() * 40) + 45; // 45 to 85
    
    // Bias: if they answered all questions, maybe they are slightly more serious
    if (answers.length >= 13) score += 5;

    let judgment = "";
    let subStatus = "";

    if (score < 80) {
      judgment = "恭喜您！您是一名 100% 合格的散户（韭菜）。";
      subStatus = "您的交易心理非常符合市场收割的标准：充满了回本幻觉、对小道消息的迷信以及对止损的天然抗拒。";
    } else {
      judgment = "警报！您可能并不适合这个充满博弈的市场。";
      subStatus = "您的心理防线过于稳固，很难为庄家贡献利润。请反思您是否过于理智，从而错失了被收割的‘快感’。";
    }

    return NextResponse.json({
      score,
      judgment,
      subStatus,
      isLeek: score < 80
    });
  } catch (e) {
    return NextResponse.json({ score: 0, error: 'Failed to score' }, { status: 500 });
  }
}

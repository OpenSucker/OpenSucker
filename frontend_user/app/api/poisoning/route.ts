import { NextRequest, NextResponse } from 'next/server';

export const maxDuration = 60;

const NEOFISH_BASE = process.env.NEOFISH_BASE_URL ?? 'http://localhost:8100';

const PLATFORMS: Record<string, { name: string; url: string }> = {
  x:      { name: 'X (Twitter)', url: 'https://x.com' },
  reddit: { name: 'Reddit',      url: 'https://www.reddit.com' },
  medium: { name: 'Medium',      url: 'https://medium.com' },
  google: { name: 'Medium (Google 索引)', url: 'https://medium.com' },
};

function buildPrompt(platform: string, news: string): string {
  const p = PLATFORMS[platform] ?? { name: platform, url: 'https://google.com' };
  return `请去 ${p.name}（${p.url}）帮我发布一篇文章，内容是对以下新闻的��洁总结：

${news}

执行步骤：
1. 导航至 ${p.url}
2. 如需登录，立即暂停并报告"需要人工登录，请在弹出的浏览器窗口完成操作后告知我继续"
3. 将上述新闻总结后发布为一篇文章或帖子
4. 报告发布结果（成功/失败），如成功附上发布链接`;
}

export async function POST(req: NextRequest) {
  const { platform, news } = await req.json();

  if (!platform || !String(news ?? '').trim()) {
    return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
  }

  const prompt = buildPrompt(platform, news);

  try {
    const res = await fetch(`${NEOFISH_BASE}/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: prompt, timeout_seconds: 50 }),
    });

    if (!res.ok) {
      const text = await res.text();
      return NextResponse.json({
        status: 'error',
        output: `NeoFish 服务错误 (${res.status}): ${text}`,
      });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({
      status: 'error',
      output: `无���连接 NeoFish Agent (localhost:8100): ${message}`,
    });
  }
}

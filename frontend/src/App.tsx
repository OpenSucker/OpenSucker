import { useState } from 'react';
import { MatrixGrid } from './components/MatrixGrid';
import { ChatWindow } from './components/ChatWindow';
import { AdvisorCard } from './components/AdvisorCard';
import { Activity, Shield, Target, BarChart3 } from 'lucide-react';

interface UserProfile {
  cognitive_level: number;
  risk_preference: string;
  investment_style: string;
}

interface ToolCall {
  name: string;
  args: any;
  success?: boolean;
  result?: any;
  error?: string;
}

interface Message {
  role: 'user' | 'bot';
  content: string;
  skill_used?: string;
  x_axis?: string;
  y_axis?: string;
  timestamp: string;
  debug?: { steps: string[] };
  tools?: ToolCall[];
  pending?: boolean;
}

const API_URL = window.location.origin;
const SESSION_ID = 'sess_' + Math.random().toString(36).substr(2, 9);
const USER_ID = 'yulian';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeCell, setActiveCell] = useState<string | null>(null);
  const [skillUsed, setSkillUsed] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfile>({
    cognitive_level: 1,
    risk_preference: '稳健',
    investment_style: '成长',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [taskChain, setTaskChain] = useState<string[]>([]);

  const handleSendMessage = async (text: string) => {
    const ts = () => new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    const userMsg: Message = { role: 'user', content: text, timestamp: ts() };
    const botMsg: Message = {
      role: 'bot',
      content: '',
      timestamp: ts(),
      debug: { steps: [] },
      tools: [],
      pending: true,
    };

    setMessages(prev => [...prev, userMsg, botMsg]);
    setIsLoading(true);

    const patchBot = (patch: Partial<Message> | ((m: Message) => Message)) => {
      setMessages(prev => {
        const out = [...prev];
        for (let i = out.length - 1; i >= 0; i--) {
          if (out[i].role === 'bot') {
            out[i] = typeof patch === 'function' ? patch(out[i]) : { ...out[i], ...patch };
            break;
          }
        }
        return out;
      });
    };

    try {
      const resp = await fetch(`${API_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: SESSION_ID, user_id: USER_ID }),
      });
      if (!resp.ok || !resp.body) throw new Error(`stream http ${resp.status}`);

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let nl: number;
        while ((nl = buffer.indexOf('\n\n')) >= 0) {
          const block = buffer.slice(0, nl);
          buffer = buffer.slice(nl + 2);
          const dataLine = block.split('\n').find(l => l.startsWith('data: '));
          if (!dataLine) continue;
          let evt: any;
          try { evt = JSON.parse(dataLine.slice(6)); } catch { continue; }

          if (evt.type === 'step' || evt.type === 'node') {
            patchBot(m => ({
              ...m,
              x_axis: evt.x_axis || m.x_axis,
              y_axis: evt.y_axis || m.y_axis,
              debug: { steps: [...(m.debug?.steps || []), evt.label].filter(Boolean) },
            }));
            if (evt.x_axis) setActiveCell(`${evt.x_axis}${evt.y_axis || ''}`);
          } else if (evt.type === 'tool') {
            patchBot(m => ({
              ...m,
              tools: [
                ...(m.tools || []),
                {
                  name: evt.name,
                  args: evt.args,
                  success: evt.success,
                  result: evt.result,
                  error: evt.error,
                },
              ],
            }));
          } else if (evt.type === 'done') {
            patchBot(m => ({
              ...m,
              content: evt.message || '(空响应)',
              skill_used: evt.skill_used,
              x_axis: evt.x_axis || m.x_axis,
              y_axis: evt.y_axis || m.y_axis,
              tools: evt.tools_called?.length ? evt.tools_called : m.tools,
              debug: { steps: m.debug?.steps || [] },
              pending: false,
            }));
            setActiveCell(`${evt.x_axis}${evt.y_axis}`);
            setSkillUsed(evt.skill_used);
            if (evt.user) {
              setProfile({
                cognitive_level: evt.user.cognitive_level || 1,
                risk_preference: evt.user.risk_preference || '稳健',
                investment_style: evt.user.investment_style || '成长',
              });
            }
            if (evt.debug_steps) {
              setTaskChain(evt.debug_steps.slice(0, 3).map((s: string) => s.split(':')[0]));
            }
          } else if (evt.type === 'error') {
            patchBot({ content: 'Matrix error: ' + evt.error, pending: false });
          }
        }
      }
    } catch (error) {
      console.error('Matrix error:', error);
      patchBot({ content: 'Matrix error: 系统链路解析异常。', pending: false });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Topbar */}
      <header className="h-14 bg-bg-1 border-b border-white/5 flex items-center px-6 gap-4 z-50">
        <div className="text-xl font-black tracking-tighter">OPEN<span className="text-accent">SUCKER</span></div>
        <div className="h-4 w-px bg-white/10 mx-2" />
        <div className="flex items-center gap-2 text-[10px] font-mono text-text-3">
          <div className="w-2 h-2 rounded-full bg-accent shadow-[0_0_8px_rgba(0,255,150,0.5)]" />
          MATRIX v2.0.1 REACT_STACK ONLINE
        </div>
        <div className="ml-auto flex items-center gap-4">
          <div className="text-[10px] font-mono text-text-3 opacity-50">SYNC: 8ms</div>
          <div className="w-8 h-8 rounded-full bg-bg-3 border border-accent/30 flex items-center justify-center text-xs font-bold text-accent">Y</div>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Sidebar Left */}
        <aside className="w-72 bg-bg-1 border-r border-white/5 p-5 flex flex-col overflow-y-auto shrink-0">
          <div className="sidebar-section">
            <div className="section-title">交易员画像 <span>LV. {profile.cognitive_level}</span></div>
            <div className="glass-card space-y-3">
              <div className="flex justify-between text-xs">
                <span className="text-text-3 flex items-center gap-1.5"><Shield size={12}/> 风险偏好</span>
                <span className="text-accent font-bold">{profile.risk_preference}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-text-3 flex items-center gap-1.5"><Target size={12}/> 投资风格</span>
                <span className="text-accent font-bold">{profile.investment_style}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-text-3 flex items-center gap-1.5"><Activity size={12}/> 资金规模</span>
                <span className="text-accent font-bold">中型</span>
              </div>
            </div>
          </div>

          <div className="sidebar-section">
            <div className="section-title">20格专家矩阵</div>
            <MatrixGrid activeCell={activeCell} />
          </div>

          <AdvisorCard skillUsed={skillUsed} />

          <div className="sidebar-section">
            <div className="section-title">活跃任务链</div>
            <div className="space-y-2">
              {taskChain.length > 0 ? taskChain.map((task, i) => (
                <div key={i} className="text-[11px] p-2 bg-bg-2 border-l-2 border-accent rounded-sm opacity-80">
                  {task}
                </div>
              )) : (
                <div className="text-[11px] text-text-3 italic">待命中...</div>
              )}
            </div>
          </div>
        </aside>

        {/* Chat Window Center */}
        <ChatWindow 
          messages={messages} 
          onSendMessage={handleSendMessage} 
          isLoading={isLoading} 
        />

        {/* Sidebar Right */}
        <aside className="w-80 bg-bg-1 border-l border-white/5 p-5 flex flex-col overflow-y-auto shrink-0">
          <div className="sidebar-section">
            <div className="section-title">实时行情比特</div>
            <div className="space-y-3">
              <div className="p-3 bg-bg-2 border-l-2 border-accent rounded-sm">
                <div className="text-[10px] text-text-3 font-bold mb-1">S&P 500 SENTIMENT</div>
                <div className="text-lg font-bold">BULLISH (0.75)</div>
                <div className="text-[10px] text-accent">↑ 2.4% vs prev week</div>
              </div>
              <div className="p-3 bg-bg-2 border-l-2 border-yellow-500 rounded-sm">
                <div className="text-[10px] text-text-3 font-bold mb-1">RISK BARRIER</div>
                <div className="text-sm font-bold uppercase">Portfolio Diversified</div>
                <div className="text-[10px] text-text-3">Threshold: 12.5% max drawdown</div>
              </div>
            </div>
          </div>

          <div className="sidebar-section">
            <div className="section-title">矩阵定位</div>
            <div className="p-4 bg-accent/5 border border-accent/20 rounded-r flex items-center justify-between">
              <div>
                <div className="text-xs font-bold">系统延迟</div>
                <div className="text-[10px] font-mono text-accent">[ROUTING] 0ms</div>
              </div>
              <BarChart3 size={20} className="text-accent opacity-50" />
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;

import type { FC } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface Persona {
  name: string;
  title: string;
  avatar: string;
  color: string;
  desc: string;
}

export const PERSONA_CONFIG: Record<string, Persona> = {
  'buffett-perspective': {
    name: '沃伦·巴菲特',
    title: 'Oracle of Omaha',
    avatar: '🎩',
    color: '#ffd700',
    desc: '价值投资 · 护城河 · 长期持有',
  },
  'munger-perspective': {
    name: '查理·芒格',
    title: 'Poor Charlie\'s Almanack',
    avatar: '📚',
    color: '#c0a060',
    desc: '逆向思维 · 多学科模型 · 极简决策',
  },
};

interface AdvisorCardProps {
  skillUsed: string | null;
}

export const AdvisorCard: FC<AdvisorCardProps> = ({ skillUsed }) => {
  const personaKey = skillUsed ? Object.keys(PERSONA_CONFIG).find(k => skillUsed.includes(k)) : null;
  const p = personaKey ? PERSONA_CONFIG[personaKey] : null;

  return (
    <AnimatePresence>
      {p && (
        <motion.div
          initial={{ opacity: 0, height: 0, scale: 0.9 }}
          animate={{ opacity: 1, height: 'auto', scale: 1 }}
          exit={{ opacity: 0, height: 0, scale: 0.9 }}
          className="overflow-hidden mb-5"
        >
          <div 
            className="p-4 rounded-r border relative"
            style={{
              background: `linear-gradient(135deg, ${p.color}15, ${p.color}05)`,
              borderColor: `${p.color}40`,
            }}
          >
            <div className="absolute -top-2 -right-2 text-6xl opacity-10 grayscale">{p.avatar}</div>
            
            <div className="flex items-center gap-3 mb-3 relative z-10">
              <div 
                className="w-10 h-10 rounded-full flex items-center justify-center text-xl shadow-lg"
                style={{ 
                  background: `${p.color}25`,
                  border: `2px solid ${p.color}60`,
                  boxShadow: `0 0 15px ${p.color}40`
                }}
              >
                {p.avatar}
              </div>
              <div>
                <div className="text-sm font-bold text-white">{p.name}</div>
                <div className="text-[10px] font-mono opacity-80" style={{ color: p.color }}>{p.title}</div>
              </div>
            </div>

            <div className="text-[11px] text-text-3 border-t border-white/5 pt-2 mb-2">
              {p.desc}
            </div>

            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full animate-pulse-glow" style={{ background: p.color, boxShadow: `0 0 8px ${p.color}` }} />
              <span className="text-[10px] font-mono uppercase tracking-wider" style={{ color: p.color }}>顾问已就绪</span>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

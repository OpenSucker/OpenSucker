import { Fragment } from 'react';
import type { FC } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const X_LABELS = ['情绪', '技术面', '战术', '宏观', '博弈进化'];
const Y_LABELS = ['探索', '审计', '执行', '复盘'];

interface MatrixGridProps {
  activeCell: string | null;
  onCellClick?: (cellId: string) => void;
}

export const MatrixGrid: FC<MatrixGridProps> = ({ activeCell, onCellClick }) => {
  return (
    <div className="grid grid-cols-[40px_repeat(4,1fr)] gap-1 mb-6">
      <div className="flex items-center justify-center text-[9px] font-bold text-text-3"></div>
      {Y_LABELS.map((y) => (
        <div key={y} className="flex items-center justify-center text-[9px] font-bold text-text-3 text-center">
          {y}
        </div>
      ))}
      
      {X_LABELS.map((xLabel, xIdx) => (
        <Fragment key={xLabel}>
          <div className="flex items-center justify-center text-[9px] font-bold text-text-3 text-center leading-tight">
            {xLabel}
          </div>
          {[1, 2, 3, 4].map((yIdx) => {
            const cellId = `X${xIdx + 1}Y${yIdx}`;
            
            // 支持多维高亮 (如 X1/X2/X3Y2)
            let isActive = false;
            if (activeCell) {
              if (activeCell.includes('/')) {
                // 联合模式解析
                const yPart = activeCell.split('Y')[1] || '';
                const xParts = activeCell.split('Y')[0].split('/');
                isActive = xParts.includes(`X${xIdx + 1}`) && `Y${yIdx}` === `Y${yPart}`;
              } else {
                isActive = activeCell === cellId;
              }
            }
            
            return (
              <div
                key={cellId}
                onClick={() => onCellClick?.(cellId)}
                className={cn(
                  "h-9 rounded border border-white/5 flex flex-col items-center justify-center transition-all cursor-pointer",
                  isActive 
                    ? "bg-accent/10 border-accent text-accent shadow-[0_0_10px_rgba(0,255,150,0.2)]" 
                    : "bg-bg-2 hover:bg-bg-3 hover:border-text-3"
                )}
              >
                <span className="font-mono text-[8px] font-bold leading-none">{cellId}</span>
              </div>
            );
          })}
        </Fragment>
      ))}
    </div>
  );
};

'use client';

import React from 'react';
import { PeepConfig, CROWD_SETTINGS } from '../lib/peeps-middleware';
import { 
  Hair, HairType, 
  Face, FaceType
} from 'react-peeps';
import { Peep } from '../lib/react-peeps';

interface PeepInstanceProps {
  data: PeepConfig;
  pw: number;
  ph: number;
  className?: string;
  style?: React.CSSProperties;
  isScattered?: boolean;
  isSelectable?: boolean;
  isPaused?: boolean;
  isRed?: boolean;
  scatterVector?: { x: number; y: number };
  children?: React.ReactNode; 
}

const miniBtnStyle: React.CSSProperties = {
  background: '#fff',
  border: '2px solid #000',
  fontSize: '10px',
  padding: '2px 8px',
  cursor: 'pointer',
  fontWeight: 'bold',
  whiteSpace: 'nowrap',
  borderRadius: '255px 15px 225px 15px / 15px 225px 15px 255px',
  boxShadow: '2px 2px 0 #000',
  transition: 'transform 0.1s ease',
};

const PeepInstance = React.memo(function PeepInstance({ 
  data, 
  pw, 
  ph, 
  className, 
  style,
  isScattered,
  isSelectable,
  isPaused,
  isRed,
  scatterVector = { x: 0, y: 0 },
  children 
}: PeepInstanceProps) {
  const [isHighlighted, setIsHighlighted] = React.useState(false);
  const [localConfig, setLocalConfig] = React.useState(data);
  const [localStyles, setLocalStyles] = React.useState(data.styles);
  
  const scatterSeed = React.useMemo(
    () => data.id.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0),
    [data.id],
  );
  
  const scatterMetadata = React.useMemo(() => ({
    delay: (scatterSeed % 4) * 0.1,
    rotation: ((scatterSeed % 9) - 4) * 90,
    scaleUp: 1.1 + (scatterSeed % 3) * 0.05,
  }), [scatterSeed]);

  const HAIR_KEYS = React.useMemo(() => Object.keys(Hair) as HairType[], []);
  const FACE_KEYS = React.useMemo(() => Object.keys(Face) as FaceType[], []);

  const toggleHighlight = React.useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsHighlighted(prev => !prev);
  }, []);

  const handlePointerDown = React.useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (isScattered || isSelectable) return;
    toggleHighlight(e as unknown as React.MouseEvent);
  }, [isScattered, isSelectable, toggleHighlight]);

  const changeColor = React.useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    const colors = ['#FFD700', '#FF69B4', '#00FA9A', '#1E90FF', '#FF4500'];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];
    setLocalStyles(prev => ({ ...prev, backgroundColor: randomColor }));
  }, []);

  const cycleHair = React.useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setLocalConfig(prev => {
      const currentIndex = HAIR_KEYS.indexOf(prev.hair);
      const nextIndex = (currentIndex + 1) % HAIR_KEYS.length;
      return { ...prev, hair: HAIR_KEYS[nextIndex] };
    });
  }, [HAIR_KEYS]);

  const cycleFace = React.useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setLocalConfig(prev => {
      const currentIndex = FACE_KEYS.indexOf(prev.face);
      const nextIndex = (currentIndex + 1) % FACE_KEYS.length;
      return { ...prev, face: FACE_KEYS[nextIndex] };
    });
  }, [FACE_KEYS]);
  
  const scatterStyle: React.CSSProperties = React.useMemo(() => isScattered ? {
    transform: `translate(${scatterVector.x * 1.5}vw, ${scatterVector.y * 1.5}vh) rotate(${scatterMetadata.rotation}deg) scale(0)`,
    opacity: 0,
    filter: 'blur(10px)',
    transition: 'transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.6s ease-out, filter 0.6s ease-out',
    transitionDelay: `${scatterMetadata.delay}s`,
    pointerEvents: 'none',
  } : {
    transition: 'transform 1s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.5s ease-in, filter 5s ease',
  }, [isScattered, scatterVector.x, scatterVector.y, scatterMetadata.rotation, scatterMetadata.delay]);

  const finalStrokeColor = isRed ? 'rgba(136, 0, 0, 0.8)' : localStyles.strokeColor;
  const finalBackgroundColor = isRed ? 'rgba(68, 0, 0, 0.8)' : localStyles.backgroundColor;

  return (
    <div 
      className={`${className} ${isRed ? 'isRed' : ''}`}
      id={`peep-${data.id}`}
      data-peep-id={data.id}
      onPointerDown={handlePointerDown}
      style={{
        ...style,
        ...scatterStyle,
        position: 'relative',
        width: pw,
        height: ph,
        cursor: isScattered ? 'default' : isSelectable ? 'default' : 'pointer',
        zIndex: isHighlighted ? 1000 : 'auto',
        pointerEvents: isSelectable ? 'none' : scatterStyle.pointerEvents,
        animationPlayState: isPaused ? 'paused' : 'running',
      }}
    >
      <Peep
        style={{ 
          width: pw, 
          height: ph, 
          display: 'block',
          transform: `scale(${data.scaleVariety * scatterMetadata.scaleUp})`,
          cursor: isScattered ? 'default' : 'pointer',
          transition: 'all 5s ease',
        }}
        hair={localConfig.hair}
        body={localConfig.body}
        face={localConfig.face}
        facialHair={localConfig.facialHair}
        accessory={localConfig.accessory}
        strokeColor={finalStrokeColor}
        backgroundColor={finalBackgroundColor}
        viewBox={CROWD_SETTINGS.VIEWBOX}
      />
      
      <div className="peep-ui-slot" style={{ 
        position: 'absolute', 
        top: -40, 
        left: '50%',
        transform: 'translateX(-50%)',
        pointerEvents: isHighlighted ? 'auto' : 'none',
        opacity: isHighlighted ? 1 : 0,
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        display: isSelectable ? 'none' : 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '4px'
      }}>
        {isHighlighted && (
          <div className="id-badge" style={{
            background: '#000',
            color: '#fff',
            fontSize: '10px',
            padding: '2px 6px',
            borderRadius: '4px',
            whiteSpace: 'nowrap',
            boxShadow: '0 4px 10px rgba(0,0,0,0.3)',
          }}>
            {data.persona ? `🌟 ${data.persona.name}` : `ID: ${data.id}`}
          </div>
        )}
        {data.persona && !isHighlighted && (
          <div className="lore-indicator" style={{
            background: '#c00',
            color: '#fff',
            fontSize: '9px',
            padding: '1px 5px',
            borderRadius: '10px',
            fontWeight: 'bold',
            boxShadow: '2px 2px 0 #000',
            animation: 'pulse 2s infinite',
            whiteSpace: 'nowrap',
          }}>
            LORE
          </div>
        )}
        {isHighlighted && (
          <div style={{ display: 'flex', gap: '2px' }}>
            <button onClick={cycleHair} style={miniBtnStyle}>Hair</button>
            <button onClick={cycleFace} style={miniBtnStyle}>Face</button>
            <button onClick={changeColor} style={miniBtnStyle}>Color</button>
          </div>
        )}
        {children}
      </div>
    </div>
  );
});

export default PeepInstance;

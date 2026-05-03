'use client';

import React from 'react';
import * as ReactPeepsModule from 'react-peeps';
import { PeepConfig, CROWD_SETTINGS } from '../lib/peeps-middleware';
import { Hair, HairType, Face, FaceType } from 'react-peeps';

const Peep = ((ReactPeepsModule as { default?: unknown; Peep?: unknown }).default ??
  (ReactPeepsModule as { default?: unknown; Peep?: unknown }).Peep) as React.ElementType;

interface PeepInstanceProps {
  data: PeepConfig;
  pw: number;
  ph: number;
  className?: string;
  style?: React.CSSProperties;
  isScattered?: boolean;
  isSelectable?: boolean;
  isPaused?: boolean;
  isPoisoned?: boolean;
  scatterVector?: { x: number; y: number };
  children?: React.ReactNode; 
}

export default function PeepInstance({ 
  data, 
  pw, 
  ph, 
  className, 
  style,
  isScattered,
  isSelectable,
  isPaused,
  isPoisoned,
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
  
  // Dramatic scatter metadata
  const scatterMetadata = React.useMemo(() => ({
    delay: (scatterSeed % 4) * 0.1,
    rotation: ((scatterSeed % 9) - 4) * 90,
    scaleUp: 1.1 + (scatterSeed % 3) * 0.05,
  }), [scatterSeed]);

  const HAIR_KEYS = Object.keys(Hair) as HairType[];
  const FACE_KEYS = Object.keys(Face) as FaceType[];

  const toggleHighlight = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsHighlighted(!isHighlighted);
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (isScattered) {
      return;
    }

    if (isPoisoned) {
      return;
    }

    if (isSelectable) {
      return;
    }

    toggleHighlight(e as unknown as React.MouseEvent);
  };

  const changeColor = (e: React.MouseEvent) => {
    e.stopPropagation();
    const colors = ['#FFD700', '#FF69B4', '#00FA9A', '#1E90FF', '#FF4500'];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];
    setLocalStyles(prev => ({ ...prev, backgroundColor: randomColor }));
  };

  const cycleHair = (e: React.MouseEvent) => {
    e.stopPropagation();
    const currentIndex = HAIR_KEYS.indexOf(localConfig.hair);
    const nextIndex = (currentIndex + 1) % HAIR_KEYS.length;
    setLocalConfig(prev => ({ ...prev, hair: HAIR_KEYS[nextIndex] }));
  };

  const cycleFace = (e: React.MouseEvent) => {
    e.stopPropagation();
    const currentIndex = FACE_KEYS.indexOf(localConfig.face);
    const nextIndex = (currentIndex + 1) % FACE_KEYS.length;
    setLocalConfig(prev => ({ ...prev, face: FACE_KEYS[nextIndex] }));
  };
  
  const scatterStyle: React.CSSProperties = isScattered ? {
    transform: `translate(${scatterVector.x * 1.5}vw, ${scatterVector.y * 1.5}vh) rotate(${scatterMetadata.rotation}deg) scale(0)`,
    opacity: 0,
    filter: 'blur(10px)',
    transition: 'transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.6s ease-out, filter 0.6s ease-out',
    transitionDelay: `${scatterMetadata.delay}s`,
    pointerEvents: 'none',
  } : {
    transition: 'transform 1s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.5s ease-in',
  };

  return (
    <div 
      className={className}
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
        transformOrigin: 'center bottom',
        scale: isPoisoned ? '2' : undefined,
      }}
    >
      <Peep
        style={{ 
          width: pw, 
          height: ph, 
          display: 'block',
          transform: `scale(${data.scaleVariety * scatterMetadata.scaleUp})`,
          cursor: isScattered ? 'default' : 'pointer',
          filter: isPoisoned ? 'grayscale(1) brightness(0.08) contrast(1.45)' : undefined,
        }}
        hair={localConfig.hair}
        body={localConfig.body}
        face={localConfig.face}
        facialHair={localConfig.facialHair}
        accessory={localConfig.accessory}
        strokeColor={isPoisoned ? '#050505' : localStyles.strokeColor}
        backgroundColor={isPoisoned ? '#111111' : localStyles.backgroundColor}
        viewBox={CROWD_SETTINGS.VIEWBOX}
      />
      
      {/* Slot for future UI elements (badges, labels, popups) */}
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
            ID: {data.id}
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
}

const miniBtnStyle: React.CSSProperties = {
  background: '#fff',
  border: '2px solid #000',
  fontSize: '10px',
  padding: '2px 8px',
  cursor: 'pointer',
  fontWeight: 'bold',
  whiteSpace: 'nowrap',
  borderRadius: '255px 15px 225px 15px / 15px 225px 15px 255px', // Sketchy border radius
  boxShadow: '2px 2px 0 #000',
  transition: 'transform 0.1s ease',
};

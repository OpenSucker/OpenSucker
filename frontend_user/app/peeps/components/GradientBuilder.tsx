'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useProvider } from '../utils/contextProvider';
import { ColorResult } from 'react-color';
import { ChromePicker } from 'react-color';

// Simple circular degree slider using input[type=range]
const DegreeSlider: React.FC<{
  value: number;
  onChange: (v: number) => void;
}> = ({ value, onChange }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
    <input
      type='range'
      min={0}
      max={360}
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      style={{ width: 120 }}
    />
    <span style={{ fontSize: 12, color: '#fff' }}>{value}°</span>
  </div>
);

export const GradientBuilder: React.FC<{
  type?: 'Background' | 'Foreground';
}> = ({ type }) => {
  const { state, dispatch } = useProvider();
  const {
    strokeColor,
    firstColor: foregroundFirstGradientColor,
    secondColor: foregroundSecondGradientColor,
    backgroundBasicColor,
    backgroundFirstGradientColor,
    backgroundSecondGradientColor,
  } = state;

  const firstColor = useMemo(() => {
    return type === 'Background' ? backgroundFirstGradientColor : foregroundFirstGradientColor;
  }, [foregroundFirstGradientColor, backgroundFirstGradientColor, type]);

  const secondColor = useMemo(() => {
    return type === 'Background' ? backgroundSecondGradientColor : foregroundSecondGradientColor;
  }, [foregroundSecondGradientColor, backgroundSecondGradientColor, type]);

  const [gradientDegree, setGradientDegree] = useState(() => {
    const src = type === 'Background' ? backgroundBasicColor : strokeColor;
    return (typeof src === 'object' ? src.degree : undefined) || 0;
  });

  const [firstColorBoxClicked, setFirstColorBoxClicked] = useState(false);
  const [secondColorBoxClicked, setSecondColorBoxClicked] = useState(false);

  useEffect(() => {
    const dispatchKey = type === 'Background' ? 'SET_BACKGROUND_BASIC_COLOR' : 'SET_STROKE_COLOR';
    dispatch({
      type: dispatchKey,
      payload: { degree: gradientDegree, firstColor, secondColor },
    });
  }, [firstColor, secondColor, gradientDegree, dispatch, type]);

  const handleColorChange = (caller: 'first' | 'second') => (color: ColorResult) => {
    if (type === 'Background') {
      dispatch({
        type: caller === 'first' ? 'SET_BACKGROUND_FIRST_GRADIENT_COLOR' : 'SET_BACKGROUND_SECOND_GRADIENT_COLOR',
        payload: color.hex,
      });
    } else {
      dispatch({
        type: caller === 'first' ? 'SET_FOREGROUND_FIRST_COLOR' : 'SET_FOREGROUND_SECOND_COLOR',
        payload: color.hex,
      });
    }
  };

  const handleFirstColorBoxClick = useCallback(() => {
    if (secondColorBoxClicked) setSecondColorBoxClicked(false);
    setFirstColorBoxClicked((s) => !s);
  }, [secondColorBoxClicked]);

  const handleSecondColorBoxClick = useCallback(() => {
    if (firstColorBoxClicked) setFirstColorBoxClicked(false);
    setSecondColorBoxClicked((s) => !s);
  }, [firstColorBoxClicked]);

  const bgColor = `linear-gradient(${gradientDegree}deg, ${firstColor}, ${secondColor})`;

  return (
    <div className='gradientBlock'>
      <div
        className='gradientPreview'
        style={{
          background: firstColorBoxClicked || secondColorBoxClicked ? 'white' : bgColor,
          alignItems: firstColorBoxClicked || secondColorBoxClicked ? 'baseline' : 'center',
        }}
      >
        {!firstColorBoxClicked && !secondColorBoxClicked && (
          <DegreeSlider value={gradientDegree} onChange={setGradientDegree} />
        )}
        {firstColorBoxClicked && (
          <ChromePicker color={firstColor} onChange={handleColorChange('first')} />
        )}
        {secondColorBoxClicked && (
          <ChromePicker color={secondColor} onChange={handleColorChange('second')} />
        )}
      </div>

      <div className='gradientColorBoxWrapper'>
        <div
          title={firstColor}
          className='gradientColorBox'
          style={{
            background: firstColor,
            animation: firstColorBoxClicked ? 'pulse 1s infinite' : 'unset',
          }}
          onClick={handleFirstColorBoxClick}
        />
        <div
          title={secondColor}
          className='gradientColorBox'
          style={{
            background: secondColor,
            animation: secondColorBoxClicked ? 'pulse 1s infinite' : 'unset',
          }}
          onClick={handleSecondColorBoxClick}
        />
      </div>

      <div className='gradientInputWrapper'>
        <div>
          <input
            value={firstColor}
            onChange={(e) => {
              if (/^#[0-9A-Fa-f]{6}$/.test(e.target.value)) {
                handleColorChange('first')({ hex: e.target.value } as ColorResult);
              }
            }}
            style={{
              width: '90%', fontSize: 12, color: '#666', border: 0,
              outline: 'none', height: 22, boxShadow: 'inset 0 0 0 1px #ddd',
              borderRadius: 4, padding: '0 7px', boxSizing: 'border-box',
            }}
          />
        </div>
        <div>
          <input
            value={secondColor}
            onChange={(e) => {
              if (/^#[0-9A-Fa-f]{6}$/.test(e.target.value)) {
                handleColorChange('second')({ hex: e.target.value } as ColorResult);
              }
            }}
            style={{
              width: '90%', fontSize: 12, color: '#666', border: 0,
              outline: 'none', height: 22, boxShadow: 'inset 0 0 0 1px #ddd',
              borderRadius: 4, padding: '0 7px', boxSizing: 'border-box',
            }}
          />
        </div>
      </div>
    </div>
  );
};

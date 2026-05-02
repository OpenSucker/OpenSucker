'use client';

import React, { useState, useMemo } from 'react';
import { ColorResult, BlockPicker } from 'react-color';
import { useProvider } from '../utils/contextProvider';
import { GradientBuilder } from './GradientBuilder';

type ColoringType = 'basic' | 'gradient';

const ColorModal: React.FC<{ type: 'Background' | 'Foreground' }> = ({
  type,
}) => {
  const { state, dispatch } = useProvider();
  const { strokeColor, backgroundBasicColor } = state;
  const [displayColorPicker, setDisplayColorPicker] = useState<boolean>(false);
  const [colorType, setColorType] = useState<ColoringType>('basic');
  const initialColors = [
    '#4D4D4D', '#999999', '#2e8a57', '#FE9200', '#fe1694',
    '#33cd33', '#8a2ae3', '#68CCCA', '#73D8FF', '#AEA1FF',
    '#7f8000', '#000000', '#81087f', '#cccccc', '#D33115',
    '#143D59', '#210070', '#213970', '#FFE042', '#E71989',
    '#5B0E2D', '#FFD55A', '#6DD47E', '#F93800', '#F9858B',
    '#761137', '#00154F', '#F2BC94', '#FBEAEB', '#EB2188',
  ];

  const handleColorChange = (color: ColorResult) => {
    if (type === 'Background') {
      dispatch({ type: 'SET_BACKGROUND_BASIC_COLOR', payload: color.hex });
    } else {
      dispatch({ type: 'SET_STROKE_COLOR', payload: color.hex });
    }
  };

  const handlePickerVisibilityChange = (isVisible?: boolean) => {
    return () => {
      if (isVisible === false) {
        setDisplayColorPicker(false);
      } else {
        setDisplayColorPicker((prev) => !prev);
      }
    };
  };

  const adjustStrokeColor = () => {
    if (type === 'Background') {
      return typeof backgroundBasicColor === 'object'
        ? `linear-gradient(${backgroundBasicColor.degree || 0}deg, ${backgroundBasicColor.firstColor}, ${backgroundBasicColor.secondColor})`
        : backgroundBasicColor;
    } else {
      return typeof strokeColor === 'object'
        ? `linear-gradient(${strokeColor.degree || 0}deg, ${strokeColor.firstColor}, ${strokeColor.secondColor})`
        : strokeColor;
    }
  };

  const handleColorTypeChange = (t: ColoringType) => () => setColorType(t);

  const renderBasicPalette = useMemo(() => {
    return (
      <div className='basicPicker'>
        <BlockPicker
          triangle='hide'
          color={adjustStrokeColor() as string}
          onChange={handleColorChange}
          colors={initialColors}
        />
        <div
          className='colorTypeChangeButton gradientColorButton'
          onClick={handleColorTypeChange('gradient')}
        >
          Gradient
        </div>
      </div>
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialColors, strokeColor, backgroundBasicColor]);

  const renderGradientPalette = useMemo(() => {
    return (
      <div className='gradientPicker'>
        <GradientBuilder type={type} />
        <div
          className='colorTypeChangeButton basicColorButton'
          onClick={handleColorTypeChange('basic')}
        >
          Basic
        </div>
      </div>
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type]);

  return useMemo(() => {
    const pickedColor = adjustStrokeColor();
    return (
      <div className='colorIndicator'>
        <div
          className='colorSwatch'
          style={{ boxShadow: `0 0 0 2px ${pickedColor}` }}
          onClick={handlePickerVisibilityChange()}
        >
          <div
            className={`pickedColor ${type === 'Background' ? 'backgroundPickedColorIndicatior' : ''}`}
            style={{ background: pickedColor as string }}
          />
        </div>
        {displayColorPicker ? (
          <div className='colorPopover'>
            <div className='colorCover' onClick={handlePickerVisibilityChange(false)} />
            {colorType === 'basic' ? renderBasicPalette : renderGradientPalette}
          </div>
        ) : null}
      </div>
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [displayColorPicker, initialColors, colorType, strokeColor, backgroundBasicColor]);
};

export default ColorModal;

'use client';

import React, { useEffect, useRef } from 'react';
import { useProvider } from '../utils/contextProvider';
import { adjustPeepsViewbox } from '../utils/viewbox';
import LeftMenu from './LeftMenu';
import RightMenu from './RightMenu';
import { Footer } from './Footer';
import { Peep } from '../../lib/react-peeps';

const peepBaseStyle = {
  width: 390,
  height: 390,
  justifyContent: 'center' as const,
  alignSelf: 'center' as const,
  transform: 'unset',
};

export const PeepsGenerator: React.FC = () => {
  const { state, dispatch } = useProvider();
  const illustrationRef = useRef<HTMLDivElement>(null);

  const {
    pickedAccessory, pickedBody, pickedFace, pickedFacialHair,
    pickedHair, strokeColor, pressedKey, scaleVector,
    svgTransform, isFrameTransparent, backgroundBasicColor,
  } = state;

  useEffect(() => {
    if (window?.innerWidth < 1201) {
      illustrationRef.current?.removeEventListener('mouseenter', handleMouseEnter);
      illustrationRef.current?.removeEventListener('mouseleave', handleMouseLeave);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const peepGroupWrapper = document.querySelector('.svgWrapper > svg > g') as SVGGraphicsElement;
    if (peepGroupWrapper) {
      const { width, height, x, y } = peepGroupWrapper.getBBox();
      peepGroupWrapper.setAttribute(
        'transform',
        `rotate(${svgTransform?.rotate || '0'} ${x + width / 2} ${y + height / 2})`
      );
    }
  }, [svgTransform, pickedBody]);

  const handleMouseEnter = () => {
    (document.getElementsByClassName('svgWrapper')[0] as HTMLElement)?.focus();
  };

  const handleMouseLeave = () => {
    (document.getElementsByClassName('header')[0] as HTMLElement)?.focus();
    dispatch({ type: 'SET_WHEEL_DIRECTION', payload: undefined });
    dispatch({ type: 'SET_PRESSED_KEY', payload: undefined });
  };

  const handleKeyDown = ({ nativeEvent }: React.KeyboardEvent) => {
    if (pressedKey === nativeEvent.key) return;
    dispatch({ type: 'SET_PRESSED_KEY', payload: nativeEvent.key });
  };

  const handleKeyUp = () => {
    dispatch({ type: 'SET_PRESSED_KEY', payload: undefined });
  };

  const handleMouseWheel = ({ nativeEvent }: React.WheelEvent) => {
    dispatch({ type: 'SET_IS_WHEEL_ACTIVE', payload: true });
    dispatch({
      type: 'SET_WHEEL_DIRECTION',
      payload: nativeEvent.deltaY > 0 ? 'down' : 'up',
    });
    setTimeout(() => {
      dispatch({ type: 'SET_IS_WHEEL_ACTIVE', payload: false });
    }, 0);
  };

  // react-peeps GradientType: { type?, degree?, firstColor, secondColor }
  const wrapperBackground = isFrameTransparent
    ? undefined
    : typeof backgroundBasicColor === 'object'
      ? {
          type: 'LinearGradient' as const,
          degree: backgroundBasicColor.degree ?? 0,
          firstColor: backgroundBasicColor.firstColor,
          secondColor: backgroundBasicColor.secondColor,
        }
      : backgroundBasicColor;

  return (
    <div>
      <div className='container'>
        <a className='header' href='/'>
          <h1>Open Sucker Avatar Generator</h1>
        </a>
        <div
          ref={illustrationRef}
          className='svgWrapper'
          tabIndex={0}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          onKeyDown={handleKeyDown}
          onKeyUp={handleKeyUp}
          onWheel={handleMouseWheel}
        >
          <Peep
            style={{
              ...peepBaseStyle,
              width: peepBaseStyle.width * scaleVector,
              height: peepBaseStyle.height * scaleVector,
              transform: `${svgTransform?.flip || ''}`,
            }}
            accessory={pickedAccessory}
            body={pickedBody}
            face={pickedFace}
            hair={pickedHair}
            facialHair={pickedFacialHair}
            strokeColor={
              typeof strokeColor === 'object'
                ? {
                    type: 'LinearGradient' as const,
                    degree: strokeColor.degree ?? 0,
                    firstColor: strokeColor.firstColor,
                    secondColor: strokeColor.secondColor,
                  }
                : strokeColor
            }
            viewBox={adjustPeepsViewbox(pickedBody as string)}
            wrapperBackground={wrapperBackground}
          />
        </div>
        <LeftMenu />
        <RightMenu />
        <Footer />
      </div>
    </div>
  );
};

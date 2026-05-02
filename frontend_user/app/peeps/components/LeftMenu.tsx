'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useProvider } from '../utils/contextProvider';

const LeftMenu = () => {
  const { state, dispatch } = useProvider();
  const { flipDirection, pressedKey, rotationDegree, scaleVector, svgTransform, wheelActive, wheelDirection } = state;
  const [leftMenuVisibility, setLeftMenuVisibility] = useState<boolean>(true);

  useEffect(() => {
    if (window?.innerWidth > 1440) {
      dispatch({ type: 'SET_SCALE_VECTOR', payload: 1.25 });
    }
    if (window?.innerWidth > 1900) {
      dispatch({ type: 'SET_SCALE_VECTOR', payload: 1.5 });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateRotationDegree = (deltaY?: number) => {
    let degree = rotationDegree;
    if (wheelDirection === 'up' || (deltaY !== undefined && deltaY < 0)) {
      degree = degree + 10 > 360 ? 10 : degree + 10;
    } else {
      degree = degree - 10 < 0 ? 350 : degree - 10;
    }
    dispatch({ type: 'SET_ROTATION_DEGREE', payload: degree });
  };

  const updateFlipDirection = () => {
    if (wheelDirection === 'up') {
      flipDirection === 1 && dispatch({ type: 'SET_FLIP_DIRECTION', payload: -1 });
    } else {
      flipDirection === -1 && dispatch({ type: 'SET_FLIP_DIRECTION', payload: 1 });
    }
  };

  const updateScaleVector = (deltaY?: number) => {
    let vector = scaleVector;
    if (wheelDirection === 'up' || (deltaY !== undefined && deltaY < 0)) {
      vector = vector <= 0.5 ? 0.5 : vector - 0.25;
    } else {
      vector = vector >= 1.5 ? 1.5 : vector + 0.25;
    }
    dispatch({ type: 'SET_SCALE_VECTOR', payload: vector });
  };

  useEffect(() => {
    dispatch({
      type: 'SET_SVG_TRANSFORM',
      payload: { ...svgTransform, rotate: `${rotationDegree}` },
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rotationDegree]);

  useEffect(() => {
    dispatch({
      type: 'SET_SVG_TRANSFORM',
      payload: { ...svgTransform, flip: `scale(${flipDirection}, 1)` },
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flipDirection]);

  useEffect(() => {
    if (!(pressedKey && wheelDirection && wheelActive)) return;
    switch (pressedKey) {
      case 'r': updateRotationDegree(); break;
      case 'f': updateFlipDirection(); break;
      case 's': updateScaleVector(); break;
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pressedKey, wheelDirection, wheelActive]);

  const handleScaleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    dispatch({ type: 'SET_SCALE_VECTOR', payload: Number(e.target.value) });
  };

  const handleRotateDegreeChange = (degree: number) => {
    dispatch({ type: 'SET_ROTATION_DEGREE', payload: degree });
  };

  const handleFlipButtonClick = () => {
    dispatch({ type: 'SET_FLIP_DIRECTION', payload: -flipDirection });
  };

  const renderScaleMeter = useMemo(() => {
    const marks = [0.5, 0.75, 1.0, 1.25, 1.5];
    return (
      <div className='scaleWrapper'>
        <span className='scaleTitle'>Scale</span>
        <div style={{ width: '75%', padding: '0 8px' }}>
          <input
            type='range'
            min={0.5}
            max={1.5}
            step={0.25}
            value={scaleVector}
            onChange={handleScaleChange}
            style={{ width: '100%' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#888' }}>
            {marks.map((m) => (
              <span key={m} style={{ fontWeight: scaleVector === m ? 'bold' : 'normal' }}>{m}</span>
            ))}
          </div>
        </div>
        <div className='scaleShortcutWrapper'>
          <span>or</span>
          <span className='boldText'>press s</span>
          <span>+</span>
          <span className='boldText'>scroll on illustration</span>
        </div>
      </div>
    );
  }, [scaleVector]);

  const renderRotateMeter = useMemo(() => {
    return (
      <div className='rotateWrapper'>
        <span className='rotateTitle'>Rotate</span>
        <div className='rotateRow'>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <input
              type='range'
              min={0}
              max={360}
              value={rotationDegree}
              onChange={(e) => handleRotateDegreeChange(Number(e.target.value))}
              style={{ width: 100 }}
            />
            <span style={{ fontSize: 12 }}>{rotationDegree}°</span>
          </div>
          <span>or</span>
          <div className='rotateShortcutWrapper'>
            <span className='boldText'>press r</span>
            <span>+</span>
            <span className='boldText'>scroll on</span>
            <span className='boldText'>illustration</span>
          </div>
        </div>
      </div>
    );
  }, [rotationDegree]);

  const renderFlipper = useMemo(() => {
    return (
      <div className='flipWrapper'>
        <div className='flipButton' onClick={handleFlipButtonClick}>
          <span style={{ textAlign: 'center' }}>Flip</span>
        </div>
        <span>or</span>
        <div className='rotateShortcutWrapper'>
          <span className='boldText'>press f</span>
          <span>+</span>
          <span className='boldText'>scroll on illustration</span>
        </div>
      </div>
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flipDirection]);

  return useMemo(() => {
    return (
      <div className={`leftMenu ${leftMenuVisibility ? '' : 'drawerClosed'}`}>
        <div className='leftMenuWrapper'>
          <div className='leftMenuContentWrapper'>
            {renderScaleMeter}
            {renderRotateMeter}
            {renderFlipper}
          </div>
          <div
            className='leftMenuDrawerButton'
            onClick={() => setLeftMenuVisibility((v) => !v)}
          >
            {leftMenuVisibility ? 'Close' : 'Open'}
          </div>
        </div>
      </div>
    );
  }, [leftMenuVisibility, scaleVector, rotationDegree, flipDirection]);
};

export default LeftMenu;

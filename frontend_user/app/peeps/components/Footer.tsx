'use client';

import React from 'react';

export const Footer = () => {
  return (
    <div className='footer'>
      <div>
        <a
          target='_blank'
          rel='noopener noreferrer'
          href='https://github.com/CeamKrier/peeps-generator'
          className='boldText removeDefaultAnchorStyle'
        >
          open source
        </a>{' '}
        and libraries available for{' '}
        <a
          target='_blank'
          rel='noopener noreferrer'
          href='https://github.com/CeamKrier/react-peeps'
          className='boldText removeDefaultAnchorStyle'
        >
          react
        </a>{' '}
        and{' '}
        <a
          target='_blank'
          rel='noopener noreferrer'
          href='https://github.com/CeamKrier/react-native-peeps'
          className='boldText removeDefaultAnchorStyle'
        >
          react native
        </a>
      </div>
      <div className='signature'>
        <a
          target='_blank'
          rel='noopener noreferrer'
          href='https://ceamkrier.com/'
          className='sign-animation boldText removeDefaultAnchorStyle'
        >
          ceamkrier
        </a>
        <span style={{ fontSize: '0.9em' }}>•</span>
        <a
          className='support-me'
          href='https://buymeacoffee.com/ceamkrier'
          target='_blank'
          rel='noopener'
        >
          <svg
            width='12px'
            height='16px'
            viewBox='0 0 884 1279'
            fill='none'
            xmlns='http://www.w3.org/2000/svg'
          >
            <path
              d='M472.623 590.836C426.682 610.503 374.546 632.802 306.976 632.802C278.71 632.746 250.58 628.868 223.353 621.274L270.086 1101.08C271.74 1121.13 280.876 1139.83 295.679 1153.46C310.482 1167.09 329.87 1174.65 349.992 1174.65C349.992 1174.65 416.254 1178.09 438.365 1178.09C462.161 1178.09 533.516 1174.65 533.516 1174.65C553.636 1174.65 573.019 1167.08 587.819 1153.45C602.619 1139.82 611.752 1121.13 613.406 1101.08L663.459 570.876C641.091 563.237 618.516 558.161 593.068 558.161C549.054 558.144 513.591 573.303 472.623 590.836Z'
              fill='#FFDD00'
            />
          </svg>
          <span>Support me</span>
        </a>
      </div>
    </div>
  );
};

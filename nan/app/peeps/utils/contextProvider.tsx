'use client';

import React, { useReducer, useContext } from 'react';
import { StateKeys, ContextProps, ProviderProps } from './types';

const initialState: StateKeys = {
  rotationDegree: 0,
  flipDirection: 1,
  pressedKey: '',
  wheelDirection: '',
  wheelActive: false,
  scaleVector: 1,
  svgTransform: {},
  pickedHair: 'HatHip',
  pickedBody: 'PointingUp',
  pickedFace: 'Smile',
  pickedFacialHair: 'None',
  pickedAccessory: 'None',
  pickedSection: 'Accessories',
  strokeColor: '#000000',
  backgroundBasicColor: '#FFD55A',
  backgroundFirstGradientColor: '#81087F',
  backgroundSecondGradientColor: '#ffd402',
  firstColor: '#81087F',
  secondColor: '#ffd402',
  isFrameTransparent: false,
};

export const Context = React.createContext<ContextProps>({
  state: initialState,
  dispatch: () => {},
});

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const reducer = (state: any, action: any) => {
  switch (action.type) {
    case 'SET_ROTATION_DEGREE':
      state.rotationDegree = action.payload;
      return Object.assign({}, state);
    case 'SET_FLIP_DIRECTION':
      state.flipDirection = action.payload;
      return Object.assign({}, state);
    case 'SET_PRESSED_KEY':
      state.pressedKey = action.payload;
      return Object.assign({}, state);
    case 'SET_WHEEL_DIRECTION':
      state.wheelDirection = action.payload;
      return Object.assign({}, state);
    case 'SET_IS_WHEEL_ACTIVE':
      state.wheelActive = action.payload;
      return Object.assign({}, state);
    case 'SET_SVG_TRANSFORM':
      state.svgTransform = action.payload;
      return Object.assign({}, state);
    case 'SET_SCALE_VECTOR':
      state.scaleVector = action.payload;
      return Object.assign({}, state);
    case 'SET_HAIR':
      state.pickedHair = action.payload;
      return Object.assign({}, state);
    case 'SET_BODY':
      state.pickedBody = action.payload;
      return Object.assign({}, state);
    case 'SET_FACE':
      state.pickedFace = action.payload;
      return Object.assign({}, state);
    case 'SET_FACIAL_HAIR':
      state.pickedFacialHair = action.payload;
      return Object.assign({}, state);
    case 'SET_ACCESSORY':
      state.pickedAccessory = action.payload;
      return Object.assign({}, state);
    case 'SET_PIECE_SECTION':
      state.pickedSection = action.payload;
      return Object.assign({}, state);
    case 'SET_STROKE_COLOR': {
      let updatedState = action.payload;
      if (typeof action.payload === 'object' && !action.payload.degree) {
        updatedState = { ...action.payload };
        updatedState.degree = state.strokeColor.degree;
        if (!updatedState.secondColor) {
          updatedState.secondColor = state.strokeColor.secondColor;
        }
        if (!updatedState.firstColor) {
          updatedState.firstColor = state.strokeColor.firstColor;
        }
      }
      state.strokeColor = updatedState;
      return Object.assign({}, state);
    }
    case 'SET_BACKGROUND_BASIC_COLOR': {
      let dispatchedData = action.payload;
      if (typeof action.payload === 'object' && !action.payload.degree) {
        dispatchedData = { ...action.payload };
        dispatchedData.degree = state.backgroundBasicColor.degree;
        if (!dispatchedData.secondColor) {
          dispatchedData.secondColor = state.backgroundBasicColor.secondColor;
        }
        if (!dispatchedData.firstColor) {
          dispatchedData.firstColor = state.backgroundBasicColor.firstColor;
        }
      }
      state.backgroundBasicColor = dispatchedData;
      return Object.assign({}, state);
    }
    case 'SET_FOREGROUND_FIRST_COLOR':
      state.firstColor = action.payload;
      return Object.assign({}, state);
    case 'SET_FOREGROUND_SECOND_COLOR':
      state.secondColor = action.payload;
      return Object.assign({}, state);
    case 'SET_BACKGROUND_FIRST_GRADIENT_COLOR':
      state.backgroundFirstGradientColor = action.payload;
      return Object.assign({}, state);
    case 'SET_BACKGROUND_SECOND_GRADIENT_COLOR':
      state.backgroundSecondGradientColor = action.payload;
      return Object.assign({}, state);
    case 'SET_FRAME_TYPE':
      state.isFrameTransparent = action.payload;
      return Object.assign({}, state);
    default:
      break;
  }
};

export const Provider: React.FC<ProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <Context.Provider value={{ state, dispatch }}>{children}</Context.Provider>
  );
};

export const useProvider = () => useContext(Context);

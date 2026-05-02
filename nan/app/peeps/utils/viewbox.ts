import {
  SittingPose,
  SittingPoseType,
  StandingPoseType,
  StandingPose,
  BustPose,
  BustPoseType,
} from 'react-peeps';

export const isSittingPose = (pose: unknown): pose is SittingPoseType =>
  Object.keys(SittingPose).includes(pose as string);

export const isStandingPose = (pose: unknown): pose is StandingPoseType =>
  Object.keys(StandingPose).includes(pose as string);

export const isBustPose = (pose: unknown): pose is BustPoseType =>
  Object.keys(BustPose).includes(pose as string);

export const adjustPeepsViewbox = (bodyPiece: string) => {
  let x = '-350',
    y = '-150',
    width = '1500',
    height = '1500';
  if (isSittingPose(bodyPiece)) {
    x = '-800';
    y = '-300';
    width = '2600';
    height = '2600';
    if (bodyPiece === 'MediumBW' || bodyPiece === 'MediumWB') {
      x = '-1000';
    }
    if (bodyPiece === 'OneLegUpBW' || bodyPiece === 'OneLegUpWB') {
      x = '-900';
    }
    if (bodyPiece === 'CrossedLegs') {
      x = '-850';
      width = '2800';
      height = '2800';
    }
    if (bodyPiece === 'WheelChair') {
      x = '-700';
      y = '-150';
      width = '2700';
      height = '2700';
    }
    if (bodyPiece === 'Bike') {
      x = '-1450';
      y = '-450';
      width = '4200';
      height = '4200';
    }
  } else if (isStandingPose(bodyPiece)) {
    x = '-1300';
    y = '-200';
    width = '3350';
    height = '3350';
  } else {
    if (bodyPiece === 'PocketShirt') {
      x = '-395';
    }
    if (bodyPiece === 'Geek' || bodyPiece === 'DotJacket') {
      x = '-305';
    }
    if (bodyPiece === 'Device') {
      y = '-160';
    }
  }
  return { x, y, width, height };
};

export const distinguishBodyViewbox = (bodyPiece: string) => {
  if (isStandingPose(bodyPiece)) {
    return '-300 350 2500 2500';
  } else if (isSittingPose(bodyPiece)) {
    if (bodyPiece === 'Bike') {
      return '-500 300 3000 3000';
    }
    if (
      bodyPiece === 'MediumBW' ||
      bodyPiece === 'MediumWB' ||
      bodyPiece === 'OneLegUpBW' ||
      bodyPiece === 'OneLegUpWB' ||
      bodyPiece === 'WheelChair'
    ) {
      return '-300 250 2000 2000';
    }
    return '0 300 2000 2000';
  } else {
    return '0 150 1200 1200';
  }
};

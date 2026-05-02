import {
  Hair, HairType,
  BustPose, BustPoseType,
  Face, FaceType,
  FacialHair, FacialHairType,
  Accessories, AccessoryType,
} from 'react-peeps';
import { LEEK_CHARACTERS, LeekPersona } from './leek-lore';

// Blacklist specific hair pieces that might have hardcoded colors or look out of place
const HAIR_BLACKLIST = new Set(['DocBouffant', 'DocShield', 'DocSurgery', 'ShortWavy']);
const HAIR_KEYS = (Object.keys(Hair) as HairType[]).filter(k => !HAIR_BLACKLIST.has(k));
const BODY_KEYS = Object.keys(BustPose) as BustPoseType[];
const FACE_KEYS = Object.keys(Face) as FaceType[];
const FH_KEYS   = Object.keys(FacialHair) as FacialHairType[];
const ACC_KEYS  = Object.keys(Accessories) as AccessoryType[];

export interface PeepConfig {
  id: string; // Unique identifier for each character
  hair: HairType;
  body: BustPoseType;
  face: FaceType;
  facialHair: FacialHairType;
  accessory: AccessoryType;
  persona?: LeekPersona; // Optional attached persona
  // Visual properties
  styles: {
    strokeColor: string;
    backgroundColor: string;
  };
  // Future attributes / hooks
  properties: Record<string, any>;
  // Animation and layout metadata
  walkDuration: string;
  delay: string;
  horizontalJitter: number;
  verticalJitter: number;
  scaleVariety: number;
}

export interface Slot extends PeepConfig {
  row: number;
  col: number;
  offsetRow: boolean;
}

export const CROWD_SETTINGS = {
  PERSON_W: 240,
  PERSON_H: 324,
  ROW_STEP: 64, // tighter rows
  COLS_PER_ROW_BASE: 10, // more people per row
  SPEED_FACTOR: 1.0, 
  VIEWBOX: { x: '-350', y: '-150', width: '1500', height: '1500' },
};

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 11);
}

export function generatePeepConfig(): PeepConfig {
  const speed = CROWD_SETTINGS.SPEED_FACTOR;
  return {
    id: generateId(),
    hair: pick(HAIR_KEYS),
    body: pick(BODY_KEYS),
    face: pick(FACE_KEYS),
    facialHair: pick(FH_KEYS),
    accessory: pick(ACC_KEYS),
    styles: {
      strokeColor: "#000000",
      backgroundColor: "#ffffff",
    },
    properties: {}, // Hook for future metadata
    walkDuration: `${(0.6 + Math.random() * 0.4) / speed}s`,
    delay: `${Math.random() * -5}s`,
    horizontalJitter: -(0.2 + Math.random() * 0.3),
    verticalJitter: (Math.random() - 0.5) * 60,
    scaleVariety: 0.9 + Math.random() * 0.2,
  };
}

export function buildCrowdSlots(numRows: number, colsPerRow: number): Slot[] {
  const slots: Slot[] = [];
  for (let r = 0; r < numRows; r++) {
    const offsetRow = r % 2 === 1;
    // Add ~60% more columns for horizontal overlap and loop
    const cols = Math.ceil((offsetRow ? colsPerRow + 1 : colsPerRow) * 1.6);
    for (let c = 0; c < cols; c++) {
      const config = generatePeepConfig();
      
      // Randomly assign one of the 5 personas (e.g. 10% chance)
      if (Math.random() < 0.1) {
        config.persona = LEEK_CHARACTERS[Math.floor(Math.random() * LEEK_CHARACTERS.length)];
      }

      slots.push({
        ...config,
        row: r,
        col: c,
        offsetRow,
      });
    }
  }
  return slots;
}

/**
 * Middleware function to calculate layout parameters based on container size
 */
export function calculateCrowdLayout(width: number, height: number) {
  const s = width / (CROWD_SETTINGS.COLS_PER_ROW_BASE * CROWD_SETTINGS.PERSON_W);
  const scaledStep = CROWD_SETTINGS.ROW_STEP * s;
  const rows = Math.ceil(height / scaledStep) + 4;
  
  return {
    scale: s,
    numRows: rows,
    pw: CROWD_SETTINGS.PERSON_W * s,
    ph: CROWD_SETTINGS.PERSON_H * s,
    step: scaledStep,
    driftDuration: (40 + Math.random() * 20) / CROWD_SETTINGS.SPEED_FACTOR,
  };
}

import { NextResponse } from 'next/server';
import { generatePeepConfig } from '../../lib/peeps-middleware';

export async function GET() {
  // Return a random peep configuration
  // This satisfies the "interface is middleware" requirement for unified control
  const config = generatePeepConfig();
  return NextResponse.json(config);
}

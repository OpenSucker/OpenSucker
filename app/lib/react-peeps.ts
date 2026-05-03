import type React from 'react';
import * as ReactPeepsModule from 'react-peeps';

type ReactPeepsNamespace = {
  default?: unknown;
  Peep?: unknown;
};

function isRenderableComponent(value: unknown): value is React.ElementType {
  return typeof value === 'function' || typeof value === 'string';
}

function resolvePeepComponent(module: ReactPeepsNamespace): React.ElementType {
  const directDefault = module.default;
  const nestedDefault =
    directDefault && typeof directDefault === 'object'
      ? (directDefault as ReactPeepsNamespace).default
      : undefined;

  const candidates = [module.Peep, directDefault, nestedDefault];

  for (const candidate of candidates) {
    if (isRenderableComponent(candidate)) {
      return candidate;
    }
  }

  throw new Error('Unable to resolve the react-peeps Peep component export.');
}

export const Peep = resolvePeepComponent(ReactPeepsModule as ReactPeepsNamespace);

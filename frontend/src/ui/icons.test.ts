import { describe, it, expect } from 'vitest';
import { ICON_SOURCES, Icons, SOURCE_TYPE_ICONS } from './icons';

// Raw text of every source file, keyed by path (Vite glob, so no Node APIs needed).
const SOURCES = import.meta.glob<string>('/src/**/*.{ts,tsx}', { query: '?raw', import: 'default', eager: true });

describe('icon system', () => {
  it('maps every concept to a different lucide component', () => {
    const components = Object.values(ICON_SOURCES);
    expect(new Set(components).size).toBe(components.length);
  });

  it('exposes a wrapped component for every key', () => {
    expect(Object.keys(Icons).sort()).toEqual(Object.keys(ICON_SOURCES).sort());
  });

  it('maps source types only to existing icon keys', () => {
    for (const name of Object.values(SOURCE_TYPE_ICONS)) expect(Icons).toHaveProperty(name);
  });

  it('is the only file that imports lucide-react', () => {
    const offenders = Object.entries(SOURCES)
      .filter(([, text]) => /from ['"]lucide-react['"]/.test(text))
      .map(([path]) => path);
    expect(offenders).toEqual(['/src/ui/icons.ts']);
  });
});

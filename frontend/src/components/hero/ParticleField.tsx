/**
 * The single lazy-loaded boundary for the hero's 3D layer.
 *
 * Hero.tsx imports this file only through React.lazy(), so it (and anything it
 * imports) lands in its own chunk. To swap in a WebGL / React Three Fiber scene
 * later, replace this file's default export; nothing else needs to change.
 *
 * Decorative only: aria-hidden, pointer-events none, never placed behind
 * results, trust scores, security checks or warnings.
 */
import { useEffect, useState } from 'react';
import { Floating3DParticles } from '../magicui/floating-3d-particles';

function readParticleColour(): string {
  const value = getComputedStyle(document.documentElement).getPropertyValue('--particle').trim();
  return value || 'currentColor';
}

export default function ParticleField() {
  const [colour, setColour] = useState(readParticleColour);

  // Re-read the token when the theme class on <html> changes.
  useEffect(() => {
    const observer = new MutationObserver(() => setColour(readParticleColour()));
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  return (
    <Floating3DParticles
      quantity={160}
      color={colour}
      size={2.5}
      opacity={0.45}
      drift={0.25}
      depth={0.6}
    />
  );
}

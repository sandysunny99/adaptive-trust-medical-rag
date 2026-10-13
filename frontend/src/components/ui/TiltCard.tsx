import type { PointerEvent, ReactNode } from 'react';
import { motion, useMotionValue, useReducedMotion, useSpring } from 'motion/react';
import { cn } from '../../utils/cn';

const MAX_TILT_DEG = 4;

interface TiltCardProps {
  children: ReactNode;
  className?: string;
}

/**
 * Decorative card that tilts up to ±4° toward the pointer.
 * Static when the user prefers reduced motion. Not for results or warnings.
 */
export function TiltCard({ children, className }: TiltCardProps) {
  const reduceMotion = useReducedMotion();
  const rotateX = useSpring(useMotionValue(0), { stiffness: 200, damping: 20 });
  const rotateY = useSpring(useMotionValue(0), { stiffness: 200, damping: 20 });

  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    if (reduceMotion) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    rotateY.set(px * 2 * MAX_TILT_DEG);
    rotateX.set(-py * 2 * MAX_TILT_DEG);
  };

  const onPointerLeave = () => {
    rotateX.set(0);
    rotateY.set(0);
  };

  return (
    <div className="[perspective:900px]">
      <motion.div
        onPointerMove={onPointerMove}
        onPointerLeave={onPointerLeave}
        style={reduceMotion ? undefined : { rotateX, rotateY, transformStyle: 'preserve-3d' }}
        className={cn('h-full', className)}
      >
        {children}
      </motion.div>
    </div>
  );
}

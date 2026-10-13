import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge conditional class names, letting later Tailwind utilities win (Magic UI / shadcn helper). */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

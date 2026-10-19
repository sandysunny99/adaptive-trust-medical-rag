/*
 * Adapted from Magic UI "magic-card"
 * Source: https://github.com/magicuidesign/magicui/blob/85f97fd27b053339af74ba9dd4ca428ee25989fb/apps/www/registry/magicui/magic-card.tsx
 * Copyright (c) Magic UI. Licensed under the MIT License (see THIRD_PARTY_NOTICES.md).
 *
 * Local modifications: kept only the "gradient" mode (dropped the "orb" mode and
 * its next-themes dependency); removed the "use client" directive; fixed the cn
 * import path; default colours come from the app's theme tokens; the inner
 * surface uses --card instead of --background.
 */

import React, { useCallback, useEffect, useRef } from "react"
import { motion, useMotionTemplate, useMotionValue } from "motion/react"

import { cn } from "../../utils/cn"

interface MagicCardProps {
  children?: React.ReactNode
  className?: string
  gradientSize?: number
  gradientColor?: string
  gradientOpacity?: number
  gradientFrom?: string
  gradientTo?: string
}

export function MagicCard({
  children,
  className,
  gradientSize = 200,
  gradientColor = "var(--accent-glow)",
  gradientOpacity = 0.8,
  gradientFrom = "var(--primary)",
  gradientTo = "var(--accent-glow)",
}: MagicCardProps) {
  const mouseX = useMotionValue(-gradientSize)
  const mouseY = useMotionValue(-gradientSize)

  const gradientSizeRef = useRef(gradientSize)

  useEffect(() => {
    gradientSizeRef.current = gradientSize
  }, [gradientSize])

  const reset = useCallback(() => {
    const off = -gradientSizeRef.current
    mouseX.set(off)
    mouseY.set(off)
  }, [mouseX, mouseY])

  const handlePointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      const rect = e.currentTarget.getBoundingClientRect()
      mouseX.set(e.clientX - rect.left)
      mouseY.set(e.clientY - rect.top)
    },
    [mouseX, mouseY]
  )

  useEffect(() => {
    reset()
  }, [reset])

  useEffect(() => {
    const handleGlobalPointerOut = (e: PointerEvent) => {
      if (!e.relatedTarget) reset()
    }
    const handleVisibility = () => {
      if (document.visibilityState !== "visible") reset()
    }

    window.addEventListener("pointerout", handleGlobalPointerOut)
    window.addEventListener("blur", reset)
    document.addEventListener("visibilitychange", handleVisibility)

    return () => {
      window.removeEventListener("pointerout", handleGlobalPointerOut)
      window.removeEventListener("blur", reset)
      document.removeEventListener("visibilitychange", handleVisibility)
    }
  }, [reset])

  const borderBackground = useMotionTemplate`
    linear-gradient(var(--card) 0 0) padding-box,
    radial-gradient(${gradientSize}px circle at ${mouseX}px ${mouseY}px,
      ${gradientFrom},
      ${gradientTo},
      var(--border) 100%
    ) border-box
  `
  const glowBackground = useMotionTemplate`
    radial-gradient(${gradientSize}px circle at ${mouseX}px ${mouseY}px,
      ${gradientColor},
      transparent 100%
    )
  `

  return (
    <motion.div
      className={cn(
        "group relative isolate overflow-hidden rounded-xl border border-transparent",
        className
      )}
      onPointerMove={handlePointerMove}
      onPointerLeave={reset}
      style={{ background: borderBackground }}
    >
      <div className="bg-card absolute inset-px z-20 rounded-[inherit]" />
      <motion.div
        className="pointer-events-none absolute inset-px z-30 rounded-[inherit] opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{ background: glowBackground, opacity: gradientOpacity }}
      />
      <div className="relative z-40">{children}</div>
    </motion.div>
  )
}

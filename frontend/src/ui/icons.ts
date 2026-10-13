/**
 * The app's only lucide-react import. Components use `Icons.<concept>`.
 *
 * One concept, one icon: every key maps to a different lucide component
 * (checked in icons.test.ts). Where the same concept appears in several places
 * (e.g. "medication" on the drug input, medication cards, the RxNorm source tag
 * and the About card), they share the key.
 *
 * Every icon renders with strokeWidth 1.75 and aria-hidden by default, so icons
 * are decorative unless a caller passes an accessible name. Never let an icon or
 * a colour be the only carrier of meaning: pair it with visible text.
 */
import { createElement, type ComponentType } from 'react';
import {
  ArrowDown, BadgeCheck, BookmarkCheck, BookmarkPlus, BookOpen, BookOpenCheck, Bug, ChartColumn,
  ChevronDown, ChevronsUpDown, Circle, CircleAlert, CircleCheck, CircleDashed, CircleDot, CircleHelp,
  CircleSlash, CircleX, ClipboardList, Cpu, DatabaseZap, Download, ExternalLink, Eye, FileCheck2,
  FileDown, FileJson, FilePlus2, FileText, Fingerprint, Gauge, GitCompareArrows, History, ImageUp,
  Info, Keyboard, Layers, Loader2, Moon, NotebookPen, OctagonX, Pencil, Pill, Plus,
  RotateCw, ScanSearch, ScrollText, SearchCheck, ShieldAlert, ShieldCheck, ShieldHalf, ShieldPlus,
  Signal, SlidersHorizontal, Stethoscope, Sun, Trash2, TriangleAlert, UserRound, Utensils, X,
  type LucideProps,
} from 'lucide-react';

export type IconComponent = ComponentType<LucideProps>;

/** Source of truth: concept → lucide component. */
export const ICON_SOURCES = {
  // Brand and navigation
  brand: ShieldPlus,
  analyze: Stethoscope,
  history: History,
  about: Info,
  evaluation: ChartColumn,
  audit: ScrollText,
  themeLight: Sun,
  themeDark: Moon,

  // How it works
  stepInput: ClipboardList,
  stepVerify: SearchCheck,
  stepAnswer: ShieldCheck,
  scrollToForm: ArrowDown,

  // Form
  upload: ImageUp,
  enterDrugs: Keyboard,
  medication: Pill,
  add: Plus,
  remove: X,
  edit: Pencil,
  patientContext: UserRound,
  instructions: NotebookPen,
  advancedSettings: SlidersHorizontal,
  model: Cpu,
  runAnalysis: ScanSearch,
  loading: Loader2,

  // Results sections
  interactions: GitCompareArrows,
  food: Utensils,
  conclusion: FileCheck2,
  trust: Gauge,
  riskTier: Signal,
  evidence: BookOpenCheck,
  security: ShieldHalf,
  promptInjection: Bug,
  retrievalPoisoning: DatabaseZap,
  evidenceIntegrity: Fingerprint,

  // Status (always shown with a text label)
  pass: CircleCheck,          // ALLOW, PASS, step complete, RxNorm match
  caution: TriangleAlert,     // FLAG, research-use warning, ambiguous match
  block: OctagonX,            // BLOCK, BLOCKED
  pending: CircleDashed,      // PENDING, not started, unavailable
  abstained: CircleSlash,     // abstention
  unknown: CircleHelp,        // not found
  stepIdle: Circle,
  stepRunningStatic: CircleDot, // running step under prefers-reduced-motion
  stepFailed: CircleX,

  // Evidence source types
  sourceLiterature: BookOpen,
  sourceLabel: FileText,

  // Actions and feedback
  save: BookmarkPlus,
  saved: BookmarkCheck,
  download: Download,
  exportMarkdown: FileDown,
  exportJson: FileJson,
  view: Eye,
  delete: Trash2,
  newAnalysis: FilePlus2,
  retry: RotateCw,
  error: CircleAlert,
  externalLink: ExternalLink,
  expand: ChevronDown,
  expandAll: ChevronsUpDown,

  // About: methodology
  retrieval: Layers,
  securityDefense: ShieldAlert,
  claimVerification: BadgeCheck,
} satisfies Record<string, IconComponent>;

export type IconName = keyof typeof ICON_SOURCES;

/** Sizes in px: 16 nav/inline, 20 cards, 24 section headers, 40 empty states. */
export const ICON_SIZE = { inline: 16, card: 20, section: 24, empty: 40 } as const;

export const ICON_STROKE_WIDTH = 1.75;

function withDefaults(Icon: IconComponent): IconComponent {
  const Wrapped = (props: LucideProps) =>
    createElement(Icon, {
      size: ICON_SIZE.inline,
      strokeWidth: ICON_STROKE_WIDTH,
      'aria-hidden': true,
      ...props,
    });
  Wrapped.displayName = `Icon(${Icon.displayName ?? 'lucide'})`;
  return Wrapped;
}

export const Icons = Object.fromEntries(
  Object.entries(ICON_SOURCES).map(([name, Icon]) => [name, withDefaults(Icon)])
) as Record<IconName, IconComponent>;

/**
 * Evidence `source_type` values the backend emits → icon. Seen live: DAILYMED,
 * OPENFDA, PUBMED; from the source adapters: BIOMEDICAL_LITERATURE,
 * PRIMARY_REGULATORY, ENTITY_TERMINOLOGY. No graph source type exists yet, so
 * none is mapped. Unknown types get no icon.
 */
export const SOURCE_TYPE_ICONS: Record<string, IconName> = {
  PUBMED: 'sourceLiterature',
  BIOMEDICAL_LITERATURE: 'sourceLiterature',
  DAILYMED: 'sourceLabel',
  OPENFDA: 'sourceLabel',
  PRIMARY_REGULATORY: 'sourceLabel',
  ENTITY_TERMINOLOGY: 'medication',
};

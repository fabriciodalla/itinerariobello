/**
 * Design System — Itinerário Bello
 * Fonte única de verdade dos tokens visuais do frontend.
 * Espelha as custom properties de src/index.css; qualquer alteração de marca
 * deve ser feita aqui primeiro e depois propagada ao CSS.
 */

// ---------------------------------------------------------------------------
// Colors
// ---------------------------------------------------------------------------

const colors = {
  background: {
    base: '#f4f6f3',
    top: '#fffdfa',
    surface: '#ffffff',
    surfaceMuted: '#f7f8f5',
    surfaceStrong: '#f1f4ef',
  },
  text: {
    base: '#18211d',
    strong: '#0f1714',
    muted: '#68736d',
    onPrimary: '#ffffff',
  },
  border: {
    base: '#dce4df',
    strong: '#c6d1ca',
  },
  primary: {
    base: '#003da5',
    strong: '#002b73',
    soft: '#e6f7ff',
    border: '#72d7f7',
  },
  accent: {
    base: '#f2c200',
    soft: '#fff7cc',
  },
  success: {
    base: '#17803d',
    strong: '#0f6b32',
    soft: '#e7f6ec',
  },
  danger: {
    base: '#c0292f',
    soft: '#fdecec',
  },
  warning: {
    base: '#946200',
    soft: '#fff4cc',
  },
  info: {
    base: '#1d4ed8',
    soft: '#eaf1ff',
  },
  focusRing: 'rgba(0, 61, 165, 0.2)',
  // Gradientes decorativos usados na tela de login (hero/carro/rota).
  gradients: {
    heroBackground:
      'linear-gradient(145deg, #031b49 0%, #063a93 52%, #1474ea 100%)',
    pageBackground:
      'linear-gradient(180deg, #052865 0%, #0a55d9 46%, #eef5ff 46%, #ffffff 100%)',
  },
  // Paleta própria da tela de login (azul mais claro que o --primary do app,
  // escolhida para bater com o mockup de referência). Antes vivia hardcoded
  // nas regras .login-* do CSS; agora é tokenizada aqui e injetada via
  // applyThemeCssVariables como --login-*.
  loginAccent: {
    highlight: '#65d9ff', // palavra "Itinerário" e brilho do pin de rota
    icon: '#0047c7', // ícone do painel / ícone de segurança
    iconSoft: '#edf5ff', // fundo do ícone do painel
    headingStrong: '#17336d', // "Bem-vindo(a)!"
    subtitle: '#68779f', // subtítulo do painel
    label: '#1d3771', // rótulos de campo (E-mail, Senha)
    inputBorder: '#e4e7ec', // cinza muito claro e neutro (mockup atual)
    inputIcon: '#637198',
    inputText: '#162d60',
    placeholder: '#7c8aa9',
    rememberLabel: '#20396f',
    action: '#1745c8', // botão "Entrar", links, checkbox marcado
    actionGradient: 'linear-gradient(135deg, #1745c8, #2e63e6)',
    secondaryBorder: '#1745c8',
    dividerText: '#7180a1',
    dividerLine: '#dbe4f5',
    securitySoft: '#ddecff',
    bodyMuted: '#526285',
    footer: '#53658d',
    routeGlow: '#79e5ff',
    routeDot: '#72dfff',
  },
} as const

// ---------------------------------------------------------------------------
// Typography
// ---------------------------------------------------------------------------

const typography = {
  fontFamily:
    "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  fontWeight: {
    regular: 400,
    bold: 700,
    extrabold: 800,
    black: 900,
  },
  // Escala real de tamanhos em uso no app (px), do menor rótulo ao título do hero de login.
  fontSize: {
    xs: '12px',
    sm: '13px',
    base: '14px',
    md: '15px',
    lg: '16px',
    xl: '17px',
    '2xl': '18px',
    '3xl': '20px',
    '4xl': '22px',
    '5xl': '24px',
    '6xl': '25px',
    '7xl': '27px',
    '8xl': '30px',
    '9xl': '33px',
  },
  lineHeight: {
    tight: 1.08,
    snug: 1.18,
    base: 1.35,
    relaxed: 1.45,
  },
  letterSpacing: {
    base: '0',
  },
} as const

// ---------------------------------------------------------------------------
// Border Radius
// ---------------------------------------------------------------------------

const radii = {
  none: '0px',
  xs: '4px',
  sm: '6px',
  md: '8px', // padrão da maioria dos componentes (botões, inputs, cards)
  lg: '14px', // inputs e botões da tela de login
  xl: '28px',
  '2xl': '32px', // topo do painel de login (wave)
  pill: '999px', // badges, avatares circulares, checkbox
  circle: '50%',
} as const

// ---------------------------------------------------------------------------
// Shadows
// ---------------------------------------------------------------------------

const shadows = {
  none: 'none',
  soft: '0 8px 22px rgba(24, 33, 29, 0.06)',
  base: '0 14px 36px rgba(24, 33, 29, 0.1)',
  card: '0 6px 16px rgba(24, 33, 29, 0.04)',
  iconButton: '0 4px 12px rgba(24, 33, 29, 0.04)',
  buttonPrimary: '0 10px 22px rgba(0, 61, 165, 0.24)',
  loginInput: '0 4px 14px rgba(0, 48, 130, 0.04)',
  loginButton: '0 12px 28px rgba(0, 79, 228, 0.26)',
  loginPanel: '0 -12px 32px rgba(0, 48, 130, 0.12)',
  loginPhone: '0 18px 55px rgba(0, 32, 84, 0.24)',
  focusRing: `0 0 0 3px ${colors.focusRing}`,
} as const

// ---------------------------------------------------------------------------
// Iconografia
// ---------------------------------------------------------------------------

const icons = {
  library: 'lucide-react',
  size: {
    sm: '16px',
    base: '19px', // tamanho padrão global (regra svg { width/height })
    md: '22px', // ícones dentro de inputs e botões
    lg: '24px',
    xl: '30px',
    '2xl': '36px', // ícone de destaque (login-panel-icon)
  },
  strokeWidth: {
    default: 2,
    emphasis: 2.3,
  },
} as const

// ---------------------------------------------------------------------------
// Espaçamentos
// ---------------------------------------------------------------------------

const spacing = {
  none: '0px',
  '2xs': '2px',
  xs: '4px',
  sm: '6px',
  md: '8px',
  base: '10px',
  lg: '12px',
  xl: '14px',
  '2xl': '16px',
  '3xl': '18px',
  '4xl': '20px',
  '5xl': '22px',
  '6xl': '24px',
  '7xl': '28px',
  '8xl': '32px',
  '9xl': '40px',
} as const

// ---------------------------------------------------------------------------
// Animações
// ---------------------------------------------------------------------------

const animations = {
  duration: {
    fast: '0.15s',
    base: '0.18s',
    spin: '1s',
  },
  easing: {
    base: 'ease',
    linear: 'linear',
  },
  transition: {
    button:
      'background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease, transform 0.18s ease',
    surface: 'background 0.15s ease, color 0.15s ease',
    border: 'border-color 0.15s ease',
  },
  keyframes: {
    spin: {
      name: 'spin',
      from: { transform: 'rotate(0deg)' },
      to: { transform: 'rotate(360deg)' },
    },
  },
} as const

// ---------------------------------------------------------------------------
// Estados (Hover, Focus, Active, Disabled)
// ---------------------------------------------------------------------------

const states = {
  hover: {
    primaryButton: { background: colors.primary.strong, transform: 'translateY(-1px)' },
    secondaryButton: {
      borderColor: colors.primary.border,
      color: colors.primary.base,
      background: colors.primary.soft,
    },
  },
  focus: {
    outline: `3px solid ${colors.focusRing}`,
    outlineOffset: '2px',
    inputBorderColor: colors.primary.base,
  },
  // Não há :active explícito no CSS atual; padrão consistente com o hover,
  // sem o deslocamento vertical (efeito de "afundar" o botão ao pressionar).
  active: {
    primaryButton: { background: colors.primary.strong, transform: 'translateY(0)' },
    secondaryButton: { background: colors.primary.soft, borderColor: colors.primary.base },
  },
  disabled: {
    opacity: 0.58,
    cursor: 'not-allowed',
  },
} as const

// ---------------------------------------------------------------------------
// Componentes Base
// ---------------------------------------------------------------------------

const button = {
  base: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    minHeight: '46px',
    padding: '10px 14px',
    borderRadius: radii.md,
    fontWeight: typography.fontWeight.black,
    lineHeight: 1.1,
    transition: animations.transition.button,
  },
  variants: {
    primary: {
      color: colors.text.onPrimary,
      background: colors.primary.base,
      boxShadow: shadows.buttonPrimary,
      hover: states.hover.primaryButton,
    },
    secondary: {
      color: colors.text.base,
      background: colors.background.surface,
      borderColor: colors.border.strong,
      hover: states.hover.secondaryButton,
    },
    // Mesmo visual de "secondary" no CSS atual (compartilham seletor).
    ghost: {
      color: colors.text.base,
      background: colors.background.surface,
      borderColor: colors.border.strong,
      hover: states.hover.secondaryButton,
    },
    danger: {
      color: colors.text.onPrimary,
      background: colors.danger.base,
    },
    link: {
      color: colors.primary.base,
      background: 'transparent',
      paddingInline: '0px',
    },
    icon: {
      width: '44px',
      minWidth: '44px',
      padding: '0px',
      color: colors.text.base,
      background: colors.background.surface,
      borderColor: colors.border.base,
      boxShadow: shadows.iconButton,
    },
  },
  sizes: {
    full: { width: '100%' },
    compact: { minWidth: '128px' },
    iconOnly: { width: '44px', minWidth: '44px', padding: '0px' },
  },
  disabled: states.disabled,
} as const

const input = {
  base: {
    minHeight: '48px',
    border: `1px solid ${colors.border.base}`,
    borderRadius: radii.md,
    background: colors.background.surface,
    color: colors.text.base,
    padding: '11px 12px',
  },
  focus: {
    borderColor: states.focus.inputBorderColor,
  },
  placeholderColor: colors.text.muted,
  // Variante "shell" usada na tela de login (campo + ícone leading).
  loginShell: {
    minHeight: '56px',
    borderRadius: radii.lg,
    border: '1px solid #d8e1f2',
    background: colors.background.surface,
    paddingInline: spacing['3xl'],
    boxShadow: shadows.loginInput,
    gap: spacing.lg,
  },
} as const

const card = {
  // Card padrão (telas internas / dashboard).
  panel: {
    padding: spacing['3xl'],
    border: `1px solid ${colors.border.base}`,
    borderRadius: radii.md,
    background: colors.background.surface,
    boxShadow: shadows.soft,
    gap: spacing['2xl'],
  },
  // Item de lista (viagens, veículos, etc).
  listItem: {
    padding: spacing.xl,
    border: `1px solid ${colors.border.base}`,
    borderRadius: radii.md,
    background: '#ffffff',
    boxShadow: shadows.card,
    gap: spacing.base,
  },
  // Painel branco com topo em onda da tela de login.
  loginPanel: {
    borderRadius: `${radii['2xl']} ${radii['2xl']} 0 0`,
    padding: '34px 22px 28px',
    background: '#ffffff',
    boxShadow: shadows.loginPanel,
    gap: spacing['4xl'],
  },
} as const

const badge = {
  base: {
    display: 'inline-flex',
    minHeight: '26px',
    borderRadius: radii.pill,
    padding: '4px 9px',
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.black,
  },
  variants: {
    neutral: { color: colors.text.muted, background: '#eef2f1' },
    primary: { color: colors.primary.base, background: colors.primary.soft },
    info: { color: colors.info.base, background: colors.info.soft },
    success: { color: colors.success.strong, background: colors.success.soft },
    warning: { color: colors.warning.base, background: colors.warning.soft },
  },
} as const

const avatar = {
  shape: {
    square: radii.md, // brand-mark (logo no topbar)
    circle: radii.pill, // ícones de destaque (login, security-note)
  },
  size: {
    sm: '36px', // ícone de veículo em lista
    md: '44px', // brand-mark / icon-button
    lg: '56px', // ícone do card de segurança no login
    xl: '72px', // ícone de destaque do painel de login
  },
} as const

const components = { button, input, card, badge, avatar } as const

// ---------------------------------------------------------------------------
// CSS bridge
// ---------------------------------------------------------------------------
// Mapeia os tokens de cor/sombra para as custom properties que index.css já
// consome (var(--primary), var(--text), ...). Chamado uma vez na inicialização
// para que theme.ts seja a fonte real dos valores em runtime, sem exigir
// reescrever as classes CSS existentes.

const cssVariableMap: Record<string, string> = {
  '--bg': colors.background.base,
  '--bg-top': colors.background.top,
  '--surface': colors.background.surface,
  '--surface-muted': colors.background.surfaceMuted,
  '--surface-strong': colors.background.surfaceStrong,
  '--text': colors.text.base,
  '--text-strong': colors.text.strong,
  '--muted': colors.text.muted,
  '--border': colors.border.base,
  '--border-strong': colors.border.strong,
  '--primary': colors.primary.base,
  '--primary-strong': colors.primary.strong,
  '--primary-soft': colors.primary.soft,
  '--primary-border': colors.primary.border,
  '--accent': colors.accent.base,
  '--accent-soft': colors.accent.soft,
  '--success': colors.success.base,
  '--success-strong': colors.success.strong,
  '--success-soft': colors.success.soft,
  '--danger': colors.danger.base,
  '--danger-soft': colors.danger.soft,
  '--warning': colors.warning.base,
  '--warning-soft': colors.warning.soft,
  '--info': colors.info.base,
  '--info-soft': colors.info.soft,
  '--focus': colors.focusRing,
  '--shadow': shadows.base,
  '--shadow-soft': shadows.soft,
  '--login-highlight': colors.loginAccent.highlight,
  '--login-icon': colors.loginAccent.icon,
  '--login-icon-soft': colors.loginAccent.iconSoft,
  '--login-heading-strong': colors.loginAccent.headingStrong,
  '--login-subtitle': colors.loginAccent.subtitle,
  '--login-label': colors.loginAccent.label,
  '--login-input-border': colors.loginAccent.inputBorder,
  '--login-input-icon': colors.loginAccent.inputIcon,
  '--login-input-text': colors.loginAccent.inputText,
  '--login-placeholder': colors.loginAccent.placeholder,
  '--login-remember-label': colors.loginAccent.rememberLabel,
  '--login-action': colors.loginAccent.action,
  '--login-action-gradient': colors.loginAccent.actionGradient,
  '--login-secondary-border': colors.loginAccent.secondaryBorder,
  '--login-divider-text': colors.loginAccent.dividerText,
  '--login-divider-line': colors.loginAccent.dividerLine,
  '--login-security-soft': colors.loginAccent.securitySoft,
  '--login-body-muted': colors.loginAccent.bodyMuted,
  '--login-footer': colors.loginAccent.footer,
  '--login-route-glow': colors.loginAccent.routeGlow,
  '--login-route-dot': colors.loginAccent.routeDot,
}

export function applyThemeCssVariables(target: HTMLElement = document.documentElement): void {
  for (const [name, value] of Object.entries(cssVariableMap)) {
    target.style.setProperty(name, value)
  }
}

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------

export const theme = {
  colors,
  typography,
  radii,
  shadows,
  icons,
  spacing,
  animations,
  states,
  components,
} as const

export type Theme = typeof theme

export { colors, typography, radii, shadows, icons, spacing, animations, states, components }

export default theme



/**
 * 🎨 ThemeProvider 컴포넌트
 *
 * ✅ 이 컴포넌트는 다크/라이트 테마 전환을 가능하게 해주는 컨텍스트 프로바이더입니다.
 * - `next-themes` 라이브러리를 래핑하여 사용합니다.
 * - 클라이언트 환경에서만 작동 (`'use client'` 지정)
 *
 * 🧩 주요 기능:
 * - 시스템 테마(light/dark)에 따라 자동 적용 가능
 * - 사용자 설정 테마 저장 및 복원
 * - 하위 컴포넌트에서 `useTheme()` 훅을 통해 테마 상태에 접근 가능
 *
 * 🔧 Props:
 * - `ThemeProviderProps`: next-themes의 설정들을 포함 (e.g., `attribute`, `defaultTheme`, `enableSystem` 등)
 * - `children`: 하위에 렌더링될 모든 UI 요소들
 *
 * 🧠 사용 예시:
 * ```tsx
 * <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
 *   <App />
 * </ThemeProvider>
 * ```
 *
 * 🌐 참고:
 * https://github.com/pacocoursey/next-themes
 */


'use client'

import * as React from 'react'
import {
  ThemeProvider as NextThemesProvider,
  type ThemeProviderProps,
} from 'next-themes'

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}

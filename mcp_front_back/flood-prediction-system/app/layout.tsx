// layout.tsx
// 애플리케이션의 루트 레이아웃 컴포넌트
// 모든 페이지에 공통으로 적용되는 HTML 구조와 전역 스타일을 설정함

import type { Metadata } from 'next' // Next.js에서 메타데이터 타입 정의
import { GeistSans } from 'geist/font/sans' // Geist Sans 폰트 임포트
import { GeistMono } from 'geist/font/mono' // Geist Mono 폰트 임포트
import './globals.css' // 전역 스타일 CSS 파일 임포트

// Next.js에서 사용되는 HTML 문서의 <head> 정보를 정의
export const metadata: Metadata = {
  title: 'v0 App', // 브라우저 탭 제목
  description: 'Created with v0', // 메타 설명 (검색 엔진, SNS 등에서 사용)
  generator: 'v0.dev', // 생성 도구 정보
}

// 루트 레이아웃 컴포넌트 정의
// 모든 페이지의 공통 뼈대 역할을 하며, children으로 각 페이지가 들어옴
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode // 자식 컴포넌트 (각 페이지 내용)
}>) {
  return (
    <html lang="en"> {/* HTML 문서의 루트 요소, 언어는 영어로 설정 */}
      <head>
        {/* 내장 스타일로 폰트 설정 적용 */}
        <style>{`
html {
  font-family: ${GeistSans.style.fontFamily}; 
  --font-sans: ${GeistSans.variable};         
  --font-mono: ${GeistMono.variable};       
}
        `}</style>
      </head>
      <body>{children}</body> {/* 실제 페이지 콘텐츠 삽입 위치 */}
    </html>
  )
}

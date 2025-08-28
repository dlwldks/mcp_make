// page.tsx
// 홈 페이지 컴포넌트 ("/" 경로에 해당)
// FloodDashboard를 화면에 렌더링함

import { FloodDashboard } from "@/components/flood-dashboard" 
// "@/components/flood-dashboard"에서 FloodDashboard 컴포넌트를 가져옴
// @는 tsconfig의 paths alias로, 보통 'src' 디렉토리를 의미함

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-slate-100">
      {/* 
        main 영역: 전체 화면 높이(min-h-screen)를 차지하고,
        왼쪽 위에서 오른쪽 아래로 흐르는 파란-회색 그라디언트 배경 적용
      */}
      <FloodDashboard /> 
      {/* 홍수 대시보드 컴포넌트를 렌더링 */}
    </main>
  )
}

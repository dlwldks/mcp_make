"use client" // 이 컴포넌트는 클라이언트 컴포넌트임을 명시 (Next.js 13+에서 필수)

import * as AspectRatioPrimitive from "@radix-ui/react-aspect-ratio" 
// Radix UI의 AspectRatio 컴포넌트를 불러옴
// 비율을 유지하며 콘텐츠 크기를 조절할 수 있도록 해줌 (예: 16:9, 1:1 등)

// ✅ AspectRatio 컴포넌트 정의
function AspectRatio({
  ...props
}: React.ComponentProps<typeof AspectRatioPrimitive.Root>) {
  return (
    <AspectRatioPrimitive.Root 
      data-slot="aspect-ratio" // 데이터 슬롯은 스타일링 또는 디버깅용으로 사용 가능
      {...props} // 전달받은 모든 props를 그대로 넘김
    />
  )
}

// 👉 외부에서 사용할 수 있도록 export
export { AspectRatio }

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"  // cva: 조건부 스타일 유틸 / VariantProps: 타입 보조 도구

import { cn } from "@/lib/utils"  // 클래스명을 조건부로 합치는 유틸리티 함수 (예: tailwind-classnames)


// 🔔 Alert 컴포넌트의 스타일 정의 (CVA 사용)
// - variant 속성에 따라 다른 스타일을 적용할 수 있도록 설정
const alertVariants = cva(
  "relative w-full rounded-lg border px-4 py-3 text-sm grid has-[>svg]:grid-cols-[calc(var(--spacing)*4)_1fr] grid-cols-[0_1fr] has-[>svg]:gap-x-3 gap-y-0.5 items-start [&>svg]:size-4 [&>svg]:translate-y-0.5 [&>svg]:text-current",
  {
    variants: {
      variant: {
        default: "bg-card text-card-foreground",  // 기본 알림 스타일
        destructive:
          "text-destructive bg-card [&>svg]:text-current *:data-[slot=alert-description]:text-destructive/90", // 위험 알림 스타일 (예: 에러)
      },
    },
    defaultVariants: {
      variant: "default", // 기본값 설정
    },
  }
)


// ✅ Alert 컴포넌트 본체
function Alert({
  className,
  variant,
  ...props
}: React.ComponentProps<"div"> & VariantProps<typeof alertVariants>) {
  return (
    <div
      data-slot="alert"
      role="alert" // 접근성 향상: 스크린리더에게 경고임을 알림
      className={cn(alertVariants({ variant }), className)} // variant에 따라 스타일을 적용하고 추가 className도 적용
      {...props}
    />
  )
}


// ✅ AlertTitle: 알림 제목 컴포넌트
function AlertTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="alert-title"
      className={cn(
        "col-start-2 line-clamp-1 min-h-4 font-medium tracking-tight", // 타이틀은 두 번째 열부터 시작
        className
      )}
      {...props}
    />
  )
}


// ✅ AlertDescription: 알림 설명 영역 (본문)
function AlertDescription({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="alert-description"
      className={cn(
        "text-muted-foreground col-start-2 grid justify-items-start gap-1 text-sm [&_p]:leading-relaxed", // 타이틀 아래 설명 스타일
        className
      )}
      {...props}
    />
  )
}

// 👇 구성 요소 export
export { Alert, AlertTitle, AlertDescription }

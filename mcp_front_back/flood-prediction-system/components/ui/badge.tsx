import * as React from "react"
import { Slot } from "@radix-ui/react-slot" // Slot: 컴포넌트 대신 자식 요소를 직접 사용할 수 있게 해주는 Radix 유틸
import { cva, type VariantProps } from "class-variance-authority" // cva: 클래스 이름을 조건부로 관리할 수 있는 도구

import { cn } from "@/lib/utils" // Tailwind 클래스 병합 유틸 함수

// ✅ badgeVariants: Badge의 스타일을 variant(스타일 타입)별로 정의
const badgeVariants = cva(
  // 기본 클래스 스타일 정의
  "inline-flex items-center justify-center rounded-md border px-2 py-0.5 text-xs font-medium w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive transition-[color,box-shadow] overflow-hidden",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground [a&]:hover:bg-primary/90",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/90",
        destructive:
          "border-transparent bg-destructive text-white [a&]:hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60",
        outline:
          "text-foreground [a&]:hover:bg-accent [a&]:hover:text-accent-foreground",
      },
    },
    defaultVariants: {
      variant: "default", // 기본은 'default' 스타일
    },
  }
)

// ✅ Badge 컴포넌트 정의
function Badge({
  className,     // 추가적인 클래스 이름
  variant,       // badgeVariants에서 사용할 스타일 타입
  asChild = false, // Slot을 쓸지 여부
  ...props       // 기타 HTML 속성
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  
  // 컴포넌트 타입 결정: Slot을 쓰면 외부 요소로 대체 가능
  const Comp = asChild ? Slot : "span"

  return (
    <Comp
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)} // 스타일 조합
      {...props} // 나머지 속성 전달
    />
  )
}

// ✅ Badge 및 스타일 설정 객체 export
export { Badge, badgeVariants }

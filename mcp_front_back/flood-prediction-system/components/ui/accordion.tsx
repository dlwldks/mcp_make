// "use client" 선언으로 해당 컴포넌트가 클라이언트 컴포넌트임을 명시 (Next.js 전용)
"use client"

import * as React from "react"
import * as AccordionPrimitive from "@radix-ui/react-accordion" // Radix UI의 Accordion 컴포넌트 불러옴
import { ChevronDownIcon } from "lucide-react" // 아래 화살표 아이콘 (열고 닫는 상태 표시용)
import { cn } from "@/lib/utils" // 클래스네임을 병합하는 유틸 함수 (Tailwind CSS 스타일 처리 시 자주 사용)

// Accordion 루트 컴포넌트 (전체 아코디언을 감싸는 역할)
function Accordion({
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Root>) {
  return <AccordionPrimitive.Root data-slot="accordion" {...props} />
}

// 아코디언 아이템 (각 항목 하나에 해당)
function AccordionItem({
  className,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Item>) {
  return (
    <AccordionPrimitive.Item
      data-slot="accordion-item"
      className={cn("border-b last:border-b-0", className)} // 마지막 항목은 하단 border 제거
      {...props}
    />
  )
}

// 아코디언을 클릭해서 펼치거나 닫는 버튼 역할 (Trigger)
function AccordionTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Trigger>) {
  return (
    <AccordionPrimitive.Header className="flex">
      <AccordionPrimitive.Trigger
        data-slot="accordion-trigger"
        className={cn(
          // 다양한 스타일 (마우스오버, 포커스, 열림 상태에 따른 아이콘 회전 등 포함)
          "focus-visible:border-ring focus-visible:ring-ring/50 flex flex-1 items-start justify-between gap-4 rounded-md py-4 text-left text-sm font-medium transition-all outline-none hover:underline focus-visible:ring-[3px] disabled:pointer-events-none disabled:opacity-50 [&[data-state=open]>svg]:rotate-180",
          className
        )}
        {...props}
      >
        {children}
        {/* 열림 상태일 때 회전하는 아래쪽 화살표 아이콘 */}
        <ChevronDownIcon className="text-muted-foreground pointer-events-none size-4 shrink-0 translate-y-0.5 transition-transform duration-200" />
      </AccordionPrimitive.Trigger>
    </AccordionPrimitive.Header>
  )
}

// 실제 펼쳐지는 콘텐츠 영역
function AccordionContent({
  className,
  children,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Content>) {
  return (
    <AccordionPrimitive.Content
      data-slot="accordion-content"
      className="data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down overflow-hidden text-sm"
      {...props}
    >
      {/* 내부 콘텐츠에 여백 추가 */}
      <div className={cn("pt-0 pb-4", className)}>{children}</div>
    </AccordionPrimitive.Content>
  )
}

// 각각의 컴포넌트를 export해서 다른 곳에서 불러올 수 있도록 함
export { Accordion, AccordionItem, AccordionTrigger, AccordionContent }

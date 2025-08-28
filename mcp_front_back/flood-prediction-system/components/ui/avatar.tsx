"use client" // 클라이언트 컴포넌트로 지정 (Next.js 환경에서 필수)

// Radix UI의 Avatar 컴포넌트 및 하위 컴포넌트 불러오기
import * as React from "react"
import * as AvatarPrimitive from "@radix-ui/react-avatar"

import { cn } from "@/lib/utils" // Tailwind 클래스 병합 유틸 함수

// ✅ Avatar: 아바타 루트 컴포넌트
function Avatar({
  className,
  ...props
}: React.ComponentProps<typeof AvatarPrimitive.Root>) {
  return (
    <AvatarPrimitive.Root
      data-slot="avatar"
      // 기본 스타일: 원형, overflow hidden, 사이즈 8 (2rem)
      className={cn(
        "relative flex size-8 shrink-0 overflow-hidden rounded-full",
        className
      )}
      {...props}
    />
  )
}

// ✅ AvatarImage: 실제 이미지를 렌더링하는 컴포넌트
function AvatarImage({
  className,
  ...props
}: React.ComponentProps<typeof AvatarPrimitive.Image>) {
  return (
    <AvatarPrimitive.Image
      data-slot="avatar-image"
      // 아바타 내부에서 이미지를 꽉 채우도록 설정
      className={cn("aspect-square size-full", className)}
      {...props}
    />
  )
}

// ✅ AvatarFallback: 이미지 로드 실패 시 보여줄 fallback UI (예: 이니셜)
function AvatarFallback({
  className,
  ...props
}: React.ComponentProps<typeof AvatarPrimitive.Fallback>) {
  return (
    <AvatarPrimitive.Fallback
      data-slot="avatar-fallback"
      // 배경색 적용, 중앙 정렬된 텍스트 or 아이콘 등
      className={cn(
        "bg-muted flex size-full items-center justify-center rounded-full",
        className
      )}
      {...props}
    />
  )
}

// ⬇️ 컴포넌트들을 외부에서 사용할 수 있게 export
export { Avatar, AvatarImage, AvatarFallback }

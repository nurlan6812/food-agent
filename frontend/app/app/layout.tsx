import type { Metadata } from 'next'
import { Changa_One } from 'next/font/google'
import Script from 'next/script'
import './globals.css'

const changaOne = Changa_One({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-changa',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'K-Foodie AI',
  description: 'K-Food AI 어시스턴트 - 음식 사진 분석, 맛집 추천, 레시피, 영양정보',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'K-Foodie AI',
  },
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: '#F0F4F8',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" suppressHydrationWarning className={changaOne.variable}>
      <head>
        <link
          rel="stylesheet"
          as="style"
          crossOrigin="anonymous"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css"
        />
        <Script
          src={`//dapi.kakao.com/v2/maps/sdk.js?appkey=${process.env.NEXT_PUBLIC_KAKAO_JS_KEY}&autoload=false`}
          strategy="beforeInteractive"
        />
      </head>
      <body className="font-pretendard">{children}</body>
    </html>
  )
}

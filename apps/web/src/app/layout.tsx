import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI 电商生图中台",
  description: "商品图、模特图与虚拟试穿自动化生产工作台",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="zh-CN"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

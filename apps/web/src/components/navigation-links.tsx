"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function NavigationLinks({
  items,
}: {
  items: ReadonlyArray<{ href: string; label: string }>;
}) {
  const pathname = usePathname();
  return items.map((item) => {
    const active = item.href === "/" ? pathname === "/" : pathname === item.href || pathname.startsWith(`${item.href}/`);
    return <Link key={item.href} href={item.href} className={active ? "nav-link nav-link-active" : "nav-link"} aria-current={active ? "page" : undefined}>{item.label}</Link>;
  });
}

import Link from "next/link";

import { ProductList } from "@/features/products/product-list";
import { safeApiFetch } from "@/lib/api-client";
import { Product } from "@/lib/types";

const pageSize = 50;

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const incoming = await searchParams;
  const page = Math.max(1, Number(incoming.page) || 1);
  const query = typeof incoming.query === "string" ? incoming.query.trim() : "";
  const params = new URLSearchParams({
    limit: String(pageSize),
    offset: String((page - 1) * pageSize),
  });
  if (query) params.set("query", query);
  const products = await safeApiFetch<Product[]>(`/products?${params}`, []);
  const pageHref = (target: number) => {
    const href = new URLSearchParams();
    if (query) href.set("query", query);
    href.set("page", String(target));
    return `/products?${href}`;
  };

  return <div className="space-y-7">
    <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="eyebrow">TRUTH LIBRARY</p><h1 className="page-title">商品档案</h1></div><Link href="/products/new" className="primary-button">新建商品</Link></div>
    <form className="panel flex flex-col gap-3 p-4 sm:flex-row" method="get"><div className="min-w-0 flex-1"><label className="sr-only" htmlFor="product-query">搜索 SKU、商品名或品牌</label><input className="field" id="product-query" name="query" defaultValue={query} placeholder="搜索 SKU、商品名或品牌" /></div><button className="secondary-button" type="submit">搜索</button>{query && <Link className="secondary-button" href="/products">清除</Link>}</form>
    <section className="panel p-6"><ProductList products={products} /></section>
    <nav className="flex items-center justify-between" aria-label="商品分页"><span className="text-sm text-slate-500">第 {page} 页 · 每页最多 {pageSize} 条</span><div className="flex gap-2">{page > 1 ? <Link className="secondary-button" href={pageHref(page - 1)}>上一页</Link> : <span className="secondary-button opacity-40" aria-disabled="true">上一页</span>}{products.length === pageSize ? <Link className="secondary-button" href={pageHref(page + 1)}>下一页</Link> : <span className="secondary-button opacity-40" aria-disabled="true">下一页</span>}</div></nav>
  </div>;
}

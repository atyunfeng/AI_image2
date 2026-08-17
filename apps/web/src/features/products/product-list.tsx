import Link from "next/link";
import { Product } from "@/lib/types";
export function ProductList({products}:{products:Product[]}) { if(!products.length)return <p className="empty-copy">还没有商品档案。</p>; return <div className="overflow-auto"><table className="data-table"><thead><tr><th>SKU</th><th>商品</th><th>品类</th><th></th></tr></thead><tbody>{products.map(p=><tr key={p.id}><td className="font-mono text-orange-200">{p.sku}</td><td>{p.name}</td><td>{p.category}</td><td><Link href={`/products/${p.id}`} className="text-orange-300">管理 →</Link></td></tr>)}</tbody></table></div>; }

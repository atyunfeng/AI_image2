import { cookies } from "next/headers";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000/api/v1";

async function proxy(request: Request, context: RouteContext<"/api/backend/[...path]">) {
  const { path } = await context.params;
  const token = (await cookies()).get("aiimage_session")?.value;
  if (!token) return Response.json({ detail: "Unauthorized" }, { status: 401 });
  const incoming = new URL(request.url);
  const headers = new Headers({ Authorization: `Bearer ${token}` });
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  const init: RequestInit = { method: request.method, headers, cache: "no-store" };
  if (!["GET", "HEAD"].includes(request.method)) init.body = await request.arrayBuffer();
  const upstream = await fetch(`${API_BASE_URL}/${path.join("/")}${incoming.search}`, init);
  const responseHeaders = new Headers();
  for (const name of ["content-type", "content-disposition"]) { const value = upstream.headers.get(name); if (value) responseHeaders.set(name, value); }
  return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const DELETE = proxy;

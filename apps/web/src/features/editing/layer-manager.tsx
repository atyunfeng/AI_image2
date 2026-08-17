"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { EditLayer } from "@/lib/types";

export function LayerManager({
  projectId,
  parentRevisionId,
  initialLayers,
}: {
  projectId: string;
  parentRevisionId: string;
  initialLayers: EditLayer[];
}) {
  const router = useRouter();
  const [layers, setLayers] = useState(initialLayers);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const formElement = event.currentTarget;
    try {
      const form = new FormData(formElement);
      const response = await fetch(
        `/api/backend/edit-projects/${projectId}/layers`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            layer_type: form.get("layer_type"),
            name: form.get("name"),
            content: JSON.parse(String(form.get("content"))),
            opacity: 100,
          }),
        },
      );
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "创建失败");
      setLayers((current) => [...current, body]);
      setMessage("图层已创建。 ");
      formElement.reset();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "JSON 无效");
    } finally {
      setBusy(false);
    }
  }

  async function patch(layer: EditLayer, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      const form = new FormData(event.currentTarget);
      const response = await fetch(
        `/api/backend/edit-projects/${projectId}/layers/${layer.id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: form.get("name"),
            visible: form.get("visible") === "on",
            locked: form.get("locked") === "on",
            opacity: Number(form.get("opacity")),
            content: JSON.parse(String(form.get("content"))),
          }),
        },
      );
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "保存失败");
      setLayers((current) =>
        current.map((value) => (value.id === layer.id ? body : value)),
      );
      setMessage(`${layer.name} 已保存。`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "JSON 无效");
    } finally {
      setBusy(false);
    }
  }

  async function duplicate(layer: EditLayer) {
    setBusy(true);
    const response = await fetch(
      `/api/backend/edit-projects/${projectId}/layers/${layer.id}/duplicate`,
      { method: "POST" },
    );
    const body = await response.json();
    if (response.ok) {
      setLayers((current) => [...current, body]);
      setMessage("图层副本已创建。 ");
    } else setMessage(body.detail ?? "复制失败");
    setBusy(false);
  }
  async function remove(layer: EditLayer) {
    setBusy(true);
    const response = await fetch(
      `/api/backend/edit-projects/${projectId}/layers/${layer.id}`,
      { method: "DELETE" },
    );
    if (response.ok) {
      setLayers((current) => current.filter((value) => value.id !== layer.id));
      setMessage("图层已删除。 ");
    } else {
      const body = await response.json();
      setMessage(body.detail ?? "删除失败");
    }
    setBusy(false);
  }

  async function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= layers.length) return;
    const next = [...layers];
    [next[index], next[target]] = [next[target], next[index]];
    setBusy(true);
    const response = await fetch(
      `/api/backend/edit-projects/${projectId}/layers/reorder`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ layer_ids: next.map((layer) => layer.id) }),
      },
    );
    if (response.ok) setLayers(await response.json());
    else setMessage("排序失败");
    setBusy(false);
  }

  async function compose(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const payload = new FormData();
    payload.set("parent_revision_id", parentRevisionId);
    payload.set(
      "parameters_json",
      JSON.stringify({
        use_project_layers: true,
        canvas_width: Number(form.get("canvas_width")),
        canvas_height: Number(form.get("canvas_height")),
        snapshot_label: form.get("snapshot_label") || undefined,
      }),
    );
    const response = await fetch(
      `/api/backend/edit-projects/${projectId}/revisions/compose`,
      { method: "POST", body: payload },
    );
    const body = await response.json().catch(() => ({ detail: "合成失败" }));
    if (response.ok) {
      setMessage("图层已合成为新的不可变版本。 ");
      router.refresh();
    } else setMessage(body.detail ?? "合成失败");
    setBusy(false);
  }

  return (
    <section className="panel p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="eyebrow">LAYER STACK</p>
          <h2 className="section-title mt-2">完整图层管理</h2>
        </div>
        <span className="version-chip">{layers.length} 层</span>
      </div>
      <div className="mt-5 space-y-3">
        {layers.map((layer, index) => (
          <details className="plan-slot min-h-0" key={layer.id}>
            <summary className="cursor-pointer text-sm font-semibold">
              {index + 1}. {layer.name} · {layer.layer_type}
              {layer.locked ? " · 已锁定" : ""}
            </summary>
            <form
              className="form-grid mt-4"
              onSubmit={(event) => patch(layer, event)}
            >
              <input
                className="field"
                name="name"
                defaultValue={layer.name}
                aria-label="图层名称"
              />
              <div className="flex flex-wrap gap-4 text-xs">
                <label>
                  <input
                    type="checkbox"
                    name="visible"
                    defaultChecked={layer.visible}
                  />{" "}
                  可见
                </label>
                <label>
                  <input
                    type="checkbox"
                    name="locked"
                    defaultChecked={layer.locked}
                  />{" "}
                  锁定
                </label>
              </div>
              <label className="field-label">
                不透明度
                <input
                  className="field mt-2"
                  name="opacity"
                  type="number"
                  min="0"
                  max="100"
                  defaultValue={layer.opacity}
                />
              </label>
              <textarea
                className="field min-h-28 font-mono text-xs"
                name="content"
                defaultValue={JSON.stringify(layer.content, null, 2)}
                spellCheck={false}
              />
              <div className="flex flex-wrap gap-2">
                <button
                  className="secondary-button py-2 text-xs"
                  disabled={busy}
                >
                  保存
                </button>
                <button
                  className="secondary-button py-2 text-xs"
                  type="button"
                  onClick={() => duplicate(layer)}
                  disabled={busy}
                >
                  复制
                </button>
                <button
                  className="secondary-button py-2 text-xs"
                  type="button"
                  onClick={() => move(index, -1)}
                  disabled={busy || index === 0}
                >
                  上移
                </button>
                <button
                  className="secondary-button py-2 text-xs"
                  type="button"
                  onClick={() => move(index, 1)}
                  disabled={busy || index === layers.length - 1}
                >
                  下移
                </button>
                <button
                  className="failure-pill"
                  type="button"
                  onClick={() => remove(layer)}
                  disabled={busy || layer.locked}
                >
                  删除
                </button>
              </div>
            </form>
          </details>
        ))}
      </div>
      <details className="mt-5">
        <summary className="cursor-pointer text-sm text-orange-200">
          新增图层
        </summary>
        <form className="form-grid mt-4" onSubmit={create}>
          <select className="field" name="layer_type">
            <option value="text">文字</option>
            <option value="image">图片</option>
            <option value="logo">Logo</option>
            <option value="background">背景</option>
          </select>
          <input
            className="field"
            name="name"
            placeholder="图层名称"
            required
          />
          <textarea
            className="field min-h-28 font-mono text-xs"
            name="content"
            defaultValue={
              '{\n  "text": "新品",\n  "region": [40, 40, 900, 180],\n  "font_size": 48,\n  "color": "#16181d"\n}'
            }
            spellCheck={false}
          />
          <button className="secondary-button" disabled={busy}>
            新增图层
          </button>
        </form>
      </details>
      <form
        className="form-grid mt-5 border-t border-white/10 pt-5"
        onSubmit={compose}
      >
        <div className="grid grid-cols-2 gap-3">
          <label className="field-label">
            画布宽
            <input
              className="field mt-2"
              name="canvas_width"
              type="number"
              min="64"
              max="4096"
              defaultValue="1024"
            />
          </label>
          <label className="field-label">
            画布高
            <input
              className="field mt-2"
              name="canvas_height"
              type="number"
              min="64"
              max="4096"
              defaultValue="1024"
            />
          </label>
        </div>
        <input className="field" name="snapshot_label" placeholder="版本备注" />
        <button className="primary-button" disabled={busy}>
          合成为新版本
        </button>
      </form>
      <p className="mt-3 min-h-5 text-xs text-orange-200" role="status">
        {message}
      </p>
    </section>
  );
}

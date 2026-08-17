"use client";

import { FormEvent, useState } from "react";

import {
  ModelConfiguration,
  ProductionPlan,
  ProductionPlanItem,
} from "@/lib/types";

export function PlanPreview({
  plan,
  models,
  onChange,
}: {
  plan: ProductionPlan;
  models: ModelConfiguration[];
  onChange: (plan: ProductionPlan) => void;
}) {
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function update(
    item: ProductionPlanItem,
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch(
        `/api/backend/production-plans/${plan.id}/items/${item.id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            label: form.get("label"),
            requested_view: form.get("requested_view"),
            width: Number(form.get("width")),
            height: Number(form.get("height")),
            prompt: form.get("prompt"),
            authoritative_copy: form.get("authoritative_copy") || null,
            model_configuration_id: form.get("model_configuration_id") || null,
            reference_ids: String(form.get("reference_ids") ?? "")
              .split(",")
              .map((value) => value.trim())
              .filter(Boolean),
            provider_parameters: JSON.parse(
              String(form.get("provider_parameters")),
            ),
          }),
        },
      );
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "保存失败");
      onChange({
        ...plan,
        items: plan.items.map((value) => (value.id === item.id ? body : value)),
      });
      setMessage(`${item.label} 参数已保存。`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "参数 JSON 无效");
    } finally {
      setBusy(false);
    }
  }

  async function remove(item: ProductionPlanItem) {
    setBusy(true);
    const response = await fetch(
      `/api/backend/production-plans/${plan.id}/items/${item.id}`,
      { method: "DELETE" },
    );
    if (response.ok) {
      onChange({
        ...plan,
        items: plan.items.filter((value) => value.id !== item.id),
      });
      setMessage(`${item.label} 已移除。`);
    } else setMessage("移除失败，计划可能已经执行。");
    setBusy(false);
  }

  async function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    try {
      const response = await fetch(
        `/api/backend/production-plans/${plan.id}/items`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            slot: form.get("slot"),
            label: form.get("label"),
            requested_view: form.get("requested_view"),
            width: Number(form.get("width")),
            height: Number(form.get("height")),
            prompt: form.get("prompt"),
            rules: {},
            reference_ids: [],
            provider_parameters: {},
          }),
        },
      );
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "新增失败");
      onChange({ ...plan, items: [...plan.items, body] });
      setMessage("已新增一张独立图片任务。 ");
      formElement.reset();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "新增失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      aria-labelledby="plan-preview-title"
      className="mt-6 rounded-2xl border border-orange-300/20 bg-orange-300/[0.04] p-5"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow">EDITABLE PLAN</p>
          <h2 id="plan-preview-title" className="section-title mt-2">
            逐图核对与覆盖 · {plan.items.length} 张
          </h2>
        </div>
        <span className="version-chip">
          规则哈希 {plan.compiler_hash.slice(0, 10)}
        </span>
      </div>
      <div className="mt-5 space-y-4">
        {plan.items.map((item) => (
          <details className="plan-slot min-h-0" key={item.id}>
            <summary className="cursor-pointer text-sm font-semibold">
              {item.position}. {item.label} · {item.width} × {item.height}
            </summary>
            <form
              className="form-grid mt-5"
              onSubmit={(event) => update(item, event)}
            >
              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <label className="field-label mb-2">标签</label>
                  <input
                    className="field"
                    name="label"
                    defaultValue={item.label}
                    required
                  />
                </div>
                <div>
                  <label className="field-label mb-2">视角</label>
                  <select
                    className="field"
                    name="requested_view"
                    defaultValue={item.requested_view}
                  >
                    <option value="front">正面</option>
                    <option value="side">侧面</option>
                    <option value="back">背面</option>
                    <option value="detail">细节</option>
                  </select>
                </div>
                <div>
                  <label className="field-label mb-2">宽度</label>
                  <input
                    className="field"
                    name="width"
                    type="number"
                    min="64"
                    max="4096"
                    defaultValue={item.width}
                  />
                </div>
                <div>
                  <label className="field-label mb-2">高度</label>
                  <input
                    className="field"
                    name="height"
                    type="number"
                    min="64"
                    max="4096"
                    defaultValue={item.height}
                  />
                </div>
              </div>
              <div>
                <label className="field-label mb-2">提示词</label>
                <textarea
                  className="field min-h-24"
                  name="prompt"
                  defaultValue={item.prompt}
                />
              </div>
              <div>
                <label className="field-label mb-2">权威文字</label>
                <input
                  className="field"
                  name="authoritative_copy"
                  defaultValue={item.authoritative_copy ?? ""}
                />
              </div>
              <div>
                <label className="field-label mb-2">模型覆盖</label>
                <select
                  className="field"
                  name="model_configuration_id"
                  defaultValue={item.model_configuration_id ?? ""}
                >
                  <option value="">使用计划默认模型</option>
                  {models.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="field-label mb-2">
                  参考图 ID（逗号分隔，留空使用全部）
                </label>
                <input
                  className="field font-mono text-xs"
                  name="reference_ids"
                  defaultValue={(item.reference_ids ?? []).join(", ")}
                />
              </div>
              <div>
                <label className="field-label mb-2">供应商参数 JSON</label>
                <textarea
                  className="field min-h-24 font-mono text-xs"
                  name="provider_parameters"
                  defaultValue={JSON.stringify(
                    item.provider_parameters ?? {},
                    null,
                    2,
                  )}
                />
              </div>
              <div className="flex flex-wrap gap-3">
                <button className="secondary-button" disabled={busy}>
                  保存本图参数
                </button>
                <button
                  className="failure-pill"
                  type="button"
                  disabled={busy}
                  onClick={() => remove(item)}
                >
                  移除本图
                </button>
              </div>
            </form>
          </details>
        ))}
      </div>
      <details className="mt-5 border-t border-white/10 pt-5">
        <summary className="cursor-pointer text-sm text-orange-200">
          增加一张图片
        </summary>
        <form className="form-grid mt-4" onSubmit={add}>
          <div className="grid gap-3 md:grid-cols-2">
            <input
              className="field"
              name="slot"
              placeholder="槽位标识"
              required
            />
            <input
              className="field"
              name="label"
              placeholder="图片名称"
              required
            />
            <select className="field" name="requested_view">
              <option value="front">正面</option>
              <option value="side">侧面</option>
              <option value="back">背面</option>
              <option value="detail">细节</option>
            </select>
            <div className="grid grid-cols-2 gap-2">
              <input
                className="field"
                name="width"
                type="number"
                defaultValue="1000"
                min="64"
                max="4096"
              />
              <input
                className="field"
                name="height"
                type="number"
                defaultValue="1000"
                min="64"
                max="4096"
              />
            </div>
          </div>
          <textarea
            className="field min-h-20"
            name="prompt"
            placeholder="提示词"
            required
          />
          <button className="secondary-button" disabled={busy}>
            添加图片
          </button>
        </form>
      </details>
      <div className="mt-5 flex flex-wrap gap-2">
        {Object.entries(plan.compiled_snapshot.packs).map(([kind, pack]) => (
          <span className="version-chip" key={kind}>
            {kind} · {pack.slug} v{pack.version}
          </span>
        ))}
      </div>
      <p className="mt-4 min-h-5 text-sm text-orange-200" role="status">
        {message}
      </p>
    </section>
  );
}

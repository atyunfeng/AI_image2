import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ModelForm } from "./model-form";
import { ModelList } from "./model-list";

vi.mock("next/navigation",()=>({useRouter:()=>({push:vi.fn(),refresh:vi.fn()})}));
it("never renders the provider key",()=>{render(<ModelList models={[{id:"1",name:"通义万相",provider:"generic_http",model_id:"wanx",base_url:null,billing_currency:"CNY",provider_options:{},capabilities:["reference_to_image"],has_key:true,key_suffix:"-key",is_enabled:true}]}/>);expect(screen.queryByText("secret-provider-key")).not.toBeInTheDocument();expect(screen.getByText("••••-key")).toBeVisible();});

it("lets operators advertise fashion generation capabilities", async () => {
  render(<ModelForm />);
  expect(screen.getByRole("checkbox", { name: "商品图 / 详情图" })).toBeChecked();
  await userEvent.click(screen.getByRole("checkbox", { name: "模特多角度" }));
  await userEvent.click(screen.getByRole("checkbox", { name: "虚拟试穿" }));
  expect(screen.getByRole("checkbox", { name: "模特多角度" })).toBeChecked();
  expect(screen.getByRole("checkbox", { name: "虚拟试穿" })).toBeChecked();
  expect(screen.getByRole("checkbox", { name: "局部重绘 / 消除" })).not.toBeChecked();
  expect(screen.getByRole("checkbox", { name: "扩图" })).not.toBeChecked();
});

it("shows local workflow options only for ComfyUI", async () => {
  render(<ModelForm />);
  expect(screen.queryByLabelText("ComfyUI 工作流参数")).not.toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText("服务类型"), "comfyui");
  expect(screen.getByLabelText("ComfyUI 工作流参数")).toBeVisible();
});

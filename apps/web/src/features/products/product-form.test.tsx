import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ProductForm } from "./product-form";
vi.mock("next/navigation",()=>({useRouter:()=>({push:vi.fn(),refresh:vi.fn()})}));
it("requires SKU and name",async()=>{const submit=vi.fn();render(<ProductForm onSubmit={submit}/>);await userEvent.click(screen.getByRole("button",{name:"创建商品"}));expect(screen.getByText("请输入SKU")).toBeVisible();expect(screen.getByText("请输入商品名称")).toBeVisible();expect(submit).not.toHaveBeenCalled();});

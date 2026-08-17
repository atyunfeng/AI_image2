import{render,screen}from"@testing-library/react";import{vi}from"vitest";import{ReviewPanel}from"./review-panel";
vi.mock("next/navigation",()=>({useRouter:()=>({refresh:vi.fn()})}));
it("disables export until approved",()=>{render(<ReviewPanel batch={{id:"1",product_id:"p",model_configuration_id:"m",requested_view:"front",capability:"reference_to_image",mode:"strict",status:"review_pending",prompt:"x",width:1024,height:1024}} onDecision={vi.fn()}/>);expect(screen.getByRole("button",{name:"导出"})).toBeDisabled();expect(screen.getByRole("button",{name:"通过"})).toBeEnabled();});

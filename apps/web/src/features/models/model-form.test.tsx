import { render, screen } from "@testing-library/react";
import { ModelList } from "./model-list";
it("never renders the provider key",()=>{render(<ModelList models={[{id:"1",name:"通义万相",provider:"generic_http",model_id:"wanx",base_url:null,capabilities:["reference_to_image"],has_key:true,key_suffix:"-key",is_enabled:true}]}/>);expect(screen.queryByText("secret-provider-key")).not.toBeInTheDocument();expect(screen.getByText("••••-key")).toBeVisible();});

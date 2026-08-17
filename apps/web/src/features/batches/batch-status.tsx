"use client";import{useEffect}from"react";import{useRouter}from"next/navigation";
const terminal=new Set(["review_pending","approved","rejected","exported","failed","canceled"]);
export function BatchStatus({status}:{status:string}){const router=useRouter();useEffect(()=>{if(terminal.has(status))return;const timer=setInterval(()=>router.refresh(),3000);return()=>clearInterval(timer)},[router,status]);return <span className="status-pill">{status}</span>}

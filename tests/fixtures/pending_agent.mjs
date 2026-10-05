// Independent ACP fixture for public Host pending-input behavior; no production accounts.
import readline from 'node:readline';
import {appendFileSync} from 'node:fs';
let active;let toolId=1000;const pending=new Map();
const send = m => process.stdout.write(JSON.stringify({jsonrpc:'2.0', ...m})+'\n');
const reply = (id,result) => send({id,result});
for await (const line of readline.createInterface({input:process.stdin})) {
  const m=JSON.parse(line),p=m.params??{};
  if(m.result!==undefined||m.error){pending.get(m.id)?.(m.error?{error:m.error}:m.result);pending.delete(m.id);continue;}
  if(m.method==='initialize') reply(m.id,{protocolVersion:1,agentInfo:{name:'pending-fixture',version:'1'},agentCapabilities:{loadSession:true,sessionCapabilities:{resume:{}},_meta:{'amplifier.dev/native':{version:1,...(process.env.FIXTURE_NO_STEER?{}:{activeSteering:{version:1,mode:'request_boundary',cancellable:false}})}}},authMethods:[]});
  else if(m.method==='session/new')reply(m.id,{sessionId:'native-'+Math.random().toString(36).slice(2),configOptions:[]});
  else if(m.method==='session/load'||m.method==='session/resume')reply(m.id,{configOptions:[]});
  else if(m.method==='session/close')reply(m.id,{});
  else if(m.method==='session/cancel'){if(active)active.cancelled=true;}
  else if(m.method==='_amplifier/native'&&p.operation==='steer.submit'){
    appendFileSync(process.env.FIXTURE_LOG+'.steering',JSON.stringify(p.args)+'\n');
    if(!active||active.inputId!==p.args.activeInputId){reply(m.id,{accepted:false,executed:false});continue;}
    const generationId=active.generationId;
    const outcome=p.args.text==='hold steering'?'held':'applied';
    reply(m.id,{accepted:true,inputId:p.args.inputId,activeInputId:p.args.activeInputId,generationId,disposition:'queued'});
    if(p.args.text!=='silent steering')setTimeout(()=>send({method:'_amplifier/event',params:{sessionId:p.sessionId,event:{type:'steering.'+outcome,input_id:p.args.inputId,activeInputId:p.args.activeInputId,target_generation_id:generationId,reason:outcome==='held'?'fixture-held':'request-boundary'}}}),20);
  }
  else if(m.method==='session/prompt'){
    appendFileSync(process.env.FIXTURE_LOG,JSON.stringify(p)+'\n');
    const text=p.prompt.filter(b=>b.type==='text').map(b=>b.text).join(' ');
    const turn={sessionId:p.sessionId,inputId:p._meta?.['amplifier.dev/command']?.commandId,generationId:'generation-'+m.id,cancelled:false};active=turn;
    send({method:'_amplifier/event',params:{sessionId:p.sessionId,event:{type:'generation.started',generation_id:turn.generationId,activeInputId:turn.inputId}}});
    void(async()=>{
      if(text==='busy'||text==='busy-long')await new Promise(resolve=>setTimeout(resolve,text==='busy-long'?2500:700));
      if(text==='agent queue'||text==='agent steer'){
        const call=(operation,args)=>new Promise(resolve=>{const id=toolId++;pending.set(id,resolve);send({id,method:'_amplifier/host',params:{sessionId:p.sessionId,operation,args}});});
        const inspected=await call('ui.inspect',{includeDraft:false});
        const outcome=await call('ui.action',{action:text==='agent queue'?'queue':'steer',expectedRevision:inspected.structuredContent.revision,args:{text:text==='agent queue'?'agent follow-up':'agent correction'}});
        send({method:'session/update',params:{sessionId:p.sessionId,update:{sessionUpdate:'agent_message_chunk',content:{type:'text',text:outcome.success?'Agent renderer admission confirmed':'Agent renderer refused'}}}});
        if(text==='agent steer')await new Promise(resolve=>setTimeout(resolve,100));
      }
      send({method:'session/update',params:{sessionId:p.sessionId,update:{sessionUpdate:'agent_message_chunk',content:{type:'text',text:'Echo: '+text}}}});
      reply(m.id,{stopReason:turn.cancelled?'cancelled':'end_turn'});
      if(active===turn)active=undefined;
    })();
  }
  else if(m.id!==undefined)send({id:m.id,error:{code:-32601,message:'Unsupported fixture request'}});
}

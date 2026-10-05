// Independent JSON-RPC ACP fixture: no host imports and no production models/accounts.
import readline from 'node:readline';
import { appendFileSync,readFileSync,existsSync } from 'node:fs';
const modelValues=Array.from({length:9},(_,i)=>({value:i===0?'openai/gpt-6-sol':i===1?'openai/gpt-6-astra':`fixture/model-${i}`,name:i===0?'OpenAI / gpt-6-sol':i===1?'OpenAI / gpt-6-astra':`Fixture model ${i}`}));
const modelOption=value=>({id:'model',name:'Model',type:'select',currentValue:value??modelValues[0].value,options:modelValues});
const sessions=new Map();let active;let permissionId=1000;const pending=new Map();
const send=m=>process.stdout.write(JSON.stringify({jsonrpc:'2.0',...m})+'\n');
const update=(sessionId,update)=>send({method:'session/update',params:{sessionId,update}});
const reply=(id,result)=>send({id,result});
for await(const line of readline.createInterface({input:process.stdin})) {
  const message=JSON.parse(line),p=message.params??{};
  if(message.result!==undefined||message.error){pending.get(message.id)?.(message.error?{success:false,error:message.error}:message.result);pending.delete(message.id);continue;}
  if(message.method==='initialize')reply(message.id,{protocolVersion:1,agentInfo:{name:'independent-fixture',version:'1'},agentCapabilities:{loadSession:true,sessionCapabilities:{resume:{},close:{}},promptCapabilities:{image:true,audio:true,embeddedContext:true},_meta:{'amplifier.dev/native':{version:1,history:{version:1,paging:'complete-turns',passive:true}}}},authMethods:[]});
  else if(message.method==='_amplifier/history'){
    const groups=JSON.parse(readFileSync(process.env.FIXTURE_HISTORY,'utf8'));const end=p.cursor?Number(p.cursor):groups.length,start=Math.max(0,end-p.limit);
    reply(message.id,{turnGroups:groups.slice(start,end),revision:'fixture-revision',diagnostics:[],nextCursor:start?String(start):null});
  }
  else if(message.method==='session/new'){const sessionId='native-'+Math.random().toString(36).slice(2);sessions.set(sessionId,{model:modelValues[0].value});reply(message.id,{sessionId,configOptions:[...(process.env.FIXTURE_MODELS?[modelOption()]:[]),{id:'mode',name:'Mode',type:'select',currentValue:'safe',options:[{value:'safe',name:'Safe'},{value:'fast',name:'Fast'}]}]});}
  else if(message.method==='session/resume'||message.method==='session/load'){sessions.set(p.sessionId,{});reply(message.id,{configOptions:[]});}
  else if(message.method==='session/set_config_option'&&process.env.FIXTURE_MODELS&&p.configId==='model'){
    if(process.env.FIXTURE_CONFIG_LOG)appendFileSync(process.env.FIXTURE_CONFIG_LOG,JSON.stringify(p)+'\n');
    if(p.value==='fixture/model-2'){send({id:message.id,error:{code:-32011,message:'Fixture refuses this model'}});continue;}
    sessions.get(p.sessionId).model=p.value;reply(message.id,{configOptions:[modelOption(p.value)]});
  }
  else if(message.method==='session/set_config_option')reply(message.id,{configOptions:[{id:'mode',name:'Mode',type:'select',currentValue:p.value,options:[{value:'safe',name:'Safe'},{value:'fast',name:'Fast'}]}]});
  else if(message.method==='session/close')reply(message.id,{});
  else if(message.method==='session/prompt'){
    if(process.env.FIXTURE_LOG)appendFileSync(process.env.FIXTURE_LOG,JSON.stringify(p)+'\n');
    const text=p.prompt.filter(b=>b.type==='text').map(b=>b.text).join(' '),id=message.id;
    active={id,sessionId:p.sessionId,cancelled:false};
    void(async()=>{
      const turn=active;
      if(text==='crash'){process.exit(17);return;}
      if(text==='approval'){
        const requestId=permissionId++;
        const choice=await new Promise(resolve=>{pending.set(requestId,resolve);send({id:requestId,method:'session/request_permission',params:{sessionId:p.sessionId,toolCall:{toolCallId:'tool-1',title:'Write file',kind:'edit',status:'pending'},options:[{optionId:'allow',name:'Allow once',kind:'allow_once'},{optionId:'deny',name:'Deny once',kind:'reject_once'}]}});});
        update(p.sessionId,{sessionUpdate:'tool_call_update',toolCallId:'tool-1',title:'Write file',status:choice.outcome.optionId==='allow'?'completed':'failed',content:[{type:'content',content:{type:'text',text:JSON.stringify(choice)}}]});
      }
      if(text==='slow')await new Promise(resolve=>setTimeout(resolve,180));
      if(text==='client-changes'){
        const call=(operation,args)=>new Promise(resolve=>{const requestId=permissionId++;pending.set(requestId,resolve);send({id:requestId,method:'_amplifier/host',params:{sessionId:p.sessionId,operation,args}});});
        let previous,original;
        const steps=JSON.parse(readFileSync(process.env.FIXTURE_UI_SCRIPT,'utf8'));
        const released=async path=>{if(!path)return;const deadline=Date.now()+15000;while(!existsSync(path)){if(Date.now()>deadline)throw Error('Fixture UI pause timed out');await new Promise(resolve=>setTimeout(resolve,10));}};
        for(const [index,step] of steps.entries()){
          await released(step.before);
          const inspected=await call('ui.inspect',{});
          appendFileSync(process.env.FIXTURE_UI_LOG,JSON.stringify({index,kind:'inspect',result:inspected})+'\n');
          await released(step.pause);
          const args={...step.args};if(args.id==='$original')args.id=original??inspected.structuredContent?.originalChanges?.at(-1)?.id;
          const outcome=await call('ui.action',{action:step.action,expectedRevision:step.stale?previous:inspected.structuredContent?.revision,args});
          if(outcome.structuredContent?.original?.id)original=outcome.structuredContent.original.id;
          appendFileSync(process.env.FIXTURE_UI_LOG,JSON.stringify({index,kind:'action',result:outcome})+'\n');
          previous=inspected.structuredContent?.revision;
        }
        update(p.sessionId,{sessionUpdate:'agent_message_chunk',content:{type:'text',text:'Agent changes complete'}});
      }
      if(text==='client-ui'){
        const call=operation=>async args=>{const requestId=permissionId++;return new Promise(resolve=>{pending.set(requestId,resolve);send({id:requestId,method:'_amplifier/host',params:{sessionId:p.sessionId,operation,args}});});};
        const observed=await call('ui.inspect')({includeDraft:false});
        if(!observed.success)throw Error('Target renderer inspection failed');
        const outcome=await call('ui.action')({action:'draft.replace',expectedRevision:observed.structuredContent.revision,args:{text:'Agent prepared draft'}});
        update(p.sessionId,{sessionUpdate:'agent_message_chunk',content:{type:'text',text:outcome.success?'Targeted renderer changed':'Targeted renderer refused'}});
      }
      if(text==='client-tool'){
        const requestId=permissionId++;
        const outcome=await new Promise(resolve=>{pending.set(requestId,resolve);send({id:requestId,method:'_amplifier/host',params:{sessionId:p.sessionId,operation:'ui.inspect',args:{}}});});
        update(p.sessionId,{sessionUpdate:'agent_message_chunk',content:{type:'text',text:JSON.stringify(outcome)}});
      }
      if(text==='terminal'){
        const call=method=>async params=>{const requestId=permissionId++;return new Promise(resolve=>{pending.set(requestId,resolve);send({id:requestId,method,params:{sessionId:p.sessionId,...params}});});};
        const terminal=await call('terminal/create')({command:process.execPath,args:['-e','process.stdout.write("terminal proof")']});
        await call('terminal/wait_for_exit')({terminalId:terminal.terminalId});
        update(p.sessionId,{sessionUpdate:'tool_call',toolCallId:'terminal-tool',title:'Run process',kind:'execute',status:'completed',content:[{type:'terminal',terminalId:terminal.terminalId}]});
      }
      if(text==='long-stream'){for(let i=0;i<128;i++){update(p.sessionId,{sessionUpdate:'agent_message_chunk',content:{type:'text',text:`chunk-${i.toString().padStart(3,'0')} `+'x'.repeat(1013)+'\n'}});await new Promise(resolve=>setTimeout(resolve,3));}update(p.sessionId,{sessionUpdate:'agent_message_chunk',content:{type:'text',text:'LONG-STREAM-COMPLETE'}});}
      else if(text==='many')for(let i=0;i<100;i++)update(p.sessionId,{sessionUpdate:'agent_message_chunk',content:{type:'text',text:'x'}});
      else update(p.sessionId,{sessionUpdate:'agent_message_chunk',content:{type:'text',text:'Echo: '+text}});
      reply(id,{stopReason:turn.cancelled?'cancelled':'end_turn'});
    })();
  } else if(message.method==='session/cancel'){if(active)active.cancelled=true;}
  else if(message.id!==undefined)send({id:message.id,error:{code:-32601,message:'Unsupported'}});
}

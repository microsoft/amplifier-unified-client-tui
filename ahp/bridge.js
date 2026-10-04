// Protocol semantics belong to upstream AHP; this sidecar owns only local presentation delivery.
import { AhpClient } from '@microsoft/agent-host-protocol/client';
import { WebSocketTransport } from '@microsoft/agent-host-protocol/ws';
import { chatReducer, sessionReducer, rootReducer } from '@microsoft/agent-host-protocol';
import WebSocket from 'ws';
import { createHash } from 'node:crypto';
import { createInterface } from 'node:readline';
import { readFileSync } from 'node:fs';

const ROOT='ahp-root://';
let config,client,socket,selected,chatURI,sequence=0,online=false,closing=false,connecting;
let generation=0,initialized,gate=[],ready=false;
const states=new Map(), cuts=new Map(), waiting=new Map(), offered=new Set();
function output(packet){const line=JSON.stringify(packet)+'\n';if(Buffer.byteLength(line)>32*1024*1024||process.stdout.writableLength>16*1024*1024){process.stderr.write('Protocol presentation capacity exceeded; no commands replayed\n');process.exit(2);}process.stdout.write(line);}
function publish(uri, action){const state=states.get(uri);if(!state)return;
  if(uri===ROOT){output({event:'root',state});return;}
  if(uri.startsWith('ahp-session:')){output({event:'session',uri,state});return;}
  if(uri.startsWith('ahp-chat:')){
    if(uri===chatURI&&selected)for(const part of state.activeTurn?.responseParts??[]){const tool=part.toolCall,key=selected+'/'+tool?.toolCallId;if(tool?.status==='running'&&tool.contributor?.kind==='client'&&tool.contributor.clientId===config.clientId&&!offered.has(key)){if(offered.size>=1024){socket.close(1013,'Client tool capacity exceeded');return;}offered.add(key);output({event:'clientTool',session:selected,chat:uri,turnId:state.activeTurn.id,tool});}}
    const turnId=action?.turnId;
    const turn=turnId?(state.activeTurn?.id===turnId?state.activeTurn:state.turns.find(t=>t.id===turnId)):undefined;
    const full=!action||action.type==='chat/turnsLoaded';
    const append=(action?.type==='chat/delta'||action?.type==='chat/reasoning')&&turn?.responseParts.some(p=>p.id===action.partId&&['markdown','reasoning'].includes(p.kind));
    output({event:'chat',uri,sequence,title:state.title,status:state.status,activeTurnId:state.activeTurn?.id,
      turnsNextCursor:state.turnsNextCursor, ...(full?{turns:state.turns,activeTurn:state.activeTurn}:append?{append:{turnId,partId:action.partId,content:action.content}}:{turn}),error:state.error});
  }
}
function baseline(snapshot){states.set(snapshot.resource,snapshot.state);cuts.set(snapshot.resource,snapshot.fromSeq);sequence=Math.max(sequence,snapshot.fromSeq);publish(snapshot.resource);}
function apply(envelope){
  const {channel,action,origin,rejectionReason,serverSeq}=envelope;
  if(serverSeq<=(cuts.get(channel)??-1))return;
  cuts.set(channel,serverSeq);sequence=Math.max(sequence,serverSeq);
  if(origin?.clientId===config.clientId){const pending=waiting.get(origin.clientSeq);if(pending){waiting.delete(origin.clientSeq);clearTimeout(pending.timer);rejectionReason?pending.reject(Object.assign(new Error(rejectionReason),{rejected:true})):pending.resolve({accepted:true});}}
  if(rejectionReason)return;
  const state=states.get(channel);if(!state)return;
  const reducer=channel===ROOT?rootReducer:channel.startsWith('ahp-chat:')?chatReducer:sessionReducer;
  states.set(channel,reducer(state,action));publish(channel,action);
}
async function connect(recover=false){
  if(connecting)return connecting;
  connecting=(async()=>{
    ready=false;gate=[];const current=++generation;
    socket=new WebSocket(config.url,{headers:config.token?{Authorization:`Bearer ${config.token}`}:{},ca:config.caFile?readFileSync(config.caFile):undefined,maxPayload:32*1024*1024,followRedirects:false});
    await new Promise((resolve,reject)=>{socket.once('open',resolve);socket.once('error',()=>reject(new Error('Cannot connect to AHP host')));});
    client=new AhpClient(WebSocketTransport.fromSocket(socket),{requestTimeoutMs:15000,subscriptionBuffer:512});
    const events=client.events();client.connect();
    void(async()=>{try{for await(const item of events){if(current!==generation)return;if(!ready){if(gate.length>=512)throw new Error('Handshake capacity exceeded');gate.push(item);}else consume(item);}}catch{socket.close();}})();
    const resources=[...states.keys()];
    if(recover&&resources.length){
      const result=await client.reconnect({clientId:config.clientId,lastSeenServerSeq:sequence,subscriptions:resources});
      if(result.type==='snapshot'){for(const snapshot of result.snapshots)baseline(snapshot);}
      else {for(const envelope of result.actions)apply(envelope);for(const missing of result.missing??[]){states.delete(missing);output({event:'missing',uri:missing});}}
    }else{
      initialized=await client.initialize({clientId:config.clientId,protocolVersions:['0.9.0'],initialSubscriptions:[ROOT]});
      for(const snapshot of initialized.snapshots??[])baseline(snapshot);
      sequence=initialized.serverSeq;
    }
    ready=true;for(const item of gate)consume(item);gate=[];online=true;
    output({event:'connection',online:true,generation,initialized});output({event:'catalogInvalidated'});if(selected){await optionalTools();publish(chatURI);}
    // Every reconnect clears protocol pending writes. Durable input is reconciled separately.
    void(async()=>{for await(const state of client.stateChanges()){if(state.status==='closed'&&current===generation&&!closing){online=false;output({event:'connection',online:false,generation});for(const pending of waiting.values()){clearTimeout(pending.timer);pending.reject(new Error('Disconnected; command outcome unknown'));}waiting.clear();setTimeout(()=>retry(),250);}}})();
    return initialized;
  })();try{return await connecting;}finally{connecting=undefined;}
}
function consume(item){if(item.event.type==='action')apply(item.event.params);else if(item.channel===ROOT)output({event:'catalogInvalidated'});}
let retryDelay=250;
async function retry(){if(closing)return;try{await connect(true);retryDelay=250;}catch{output({event:'connection',online:false,generation});retryDelay=Math.min(retryDelay*2,5000);setTimeout(()=>retry(),retryDelay);}}
async function subscribe(uri,view){const result=await client.subscribe(uri,{view,delivery:{maxBatchDelayMs:30}});if(!result.result.snapshot)throw new Error('Host omitted required snapshot');baseline(result.result.snapshot);}
async function dispatch(channel,action){if(!online)throw new Error('Offline; nothing automatically retried');const handle=client.dispatch(channel,action);return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{waiting.delete(handle.clientSeq);reject(new Error('Action echo unavailable; outcome unknown'));},15000);waiting.set(handle.clientSeq,{resolve,reject,timer});});}
async function optionalTools(){try{await registerTools();}catch{output({event:'optionalUnavailable',capability:'client-tools',message:'Terminal agent UI registration unavailable; core conversation retained'});}}
async function registerTools(){
  const suffix=createHash('sha256').update(config.clientId).digest('hex').slice(0,16);
  await dispatch(selected,{type:'session/activeClientSet',activeClient:{clientId:config.clientId,displayName:'Amplifier Unified TUI',tools:[
    {name:`amplifier_tui_inspect_${suffix}`,title:'Inspect this terminal view',description:'Read current renderer revision and selected view; private draft only when includeDraft=true.',inputSchema:{type:'object',properties:{includeDraft:{type:'boolean'}}}},
    {name:`amplifier_tui_action_${suffix}`,title:'Control this terminal view',description:'Use the current renderer revision for private drafts, navigation, quotes or negotiated message metadata. Never submits a prompt.',inputSchema:{type:'object',required:['action','expectedRevision'],properties:{action:{type:'string',enum:['draft.replace','view.select','panel.open','message.reply','message.replyClear','message.read','message.reaction','message.receipt','message.refresh','message.submissionInspect']},expectedRevision:{type:'integer'},args:{type:'object'}}}}
  ]}});
}
async function command(method,p){
  if(method==='open'){config=p;return connect();}
  if(method==='close'){closing=true;await client?.shutdown();return {};}
  if(!online)throw new Error('AHP host disconnected');
  if(method==='list')return client.request('listSessions',{channel:ROOT,limit:50,...(p.cursor?{cursor:p.cursor}:{})});
  if(method==='select'){
    if(selected===p.session&&states.has(chatURI)){publish(selected);publish(chatURI);return {session:selected,chat:chatURI};}
    const prior=selected,priorChat=chatURI;
    await subscribe(p.session);const nextChat=states.get(p.session).defaultChat;
    if(!nextChat)throw new Error('Session has no default chat');
    try{await subscribe(nextChat,{turns:50});}catch(error){await client.unsubscribe(p.session);states.delete(p.session);throw error;}
    selected=p.session;chatURI=nextChat;
    for(const uri of [prior,priorChat])if(uri&&uri!==selected&&uri!==chatURI){await client.unsubscribe(uri);states.delete(uri);cuts.delete(uri);}
    await optionalTools();publish(chatURI);return {session:selected,chat:chatURI};
  }
  if(method==='detach'){for(const uri of [selected,chatURI])if(uri){await client.unsubscribe(uri);states.delete(uri);cuts.delete(uri);}selected=chatURI=undefined;return {};}
  if(method==='capability'){
    const manifest=initialized?._meta?.['amplifier.dev/capabilities'];
    const action=manifest?.version===1?manifest.actions?.[p.action]:undefined;
    if(!action||action.method!=='x-amplifier/capabilityAction'||manifest.topics?.[action.topic]?.version!==1)throw Object.assign(new Error('Capability action unavailable'),{rejected:true});
    return client.request(action.method,{channel:p.channel??ROOT,topic:action.topic,operation:action.operation,version:1,args:p.args??{},commandId:p.commandId});
  }
  if(method==='messageDescriptor'){
    if(p.session!==selected)throw Object.assign(new Error('Selection changed'),{rejected:true});
    const topic=initialized?._meta?.['amplifier.dev/capabilities']?.topics?.['message-metadata'];
    if(topic?.version!==1||!topic.uri)throw Object.assign(new Error('Message metadata unavailable'),{rejected:true});
    const uri=new URL(topic.uri);uri.searchParams.set('scope',p.session);
    const result=await client.request('resourceRead',{channel:ROOT,uri:uri.href,encoding:'utf-8'});
    if(result.encoding!=='utf-8'||result.contentType!=='application/json')throw new Error('Invalid message representation');
    const record=JSON.parse(result.data);if(record.topic!=='message-metadata'||record.scope!==p.session)throw new Error('Message response changed scope');return record.data;
  }
  if(method==='managed'){
    const cap=initialized?._meta?.['amplifier.dev/managedCreation'];
    if(cap?.version!==1||cap.method!=='x-amplifier/managedSession'||!cap.operations?.includes(p.operation))throw Object.assign(new Error('Managed creation capability unavailable'),{rejected:true});
    return client.request(cap.method,{channel:ROOT,operation:p.operation,args:p.args});
  }
  if(method==='lifecycle'){
    const cap=initialized?._meta?.['amplifier.dev/sessionLifecycle'];
    if(cap?.version!==1||cap.method!=='x-amplifier/sessionLifecycle'||cap.deletion!=='preserve-history')throw Object.assign(new Error('Preserve-history lifecycle capability unavailable'),{rejected:true});
    return client.request(cap.method,{channel:p.session,operation:p.operation,args:p.args??{}});
  }
  if(method==='create'){
    const provider=p.provider??states.get(ROOT)?.agents?.[0]?.provider;if(!provider)throw new Error('Host advertised no agent');
    await client.request('createSession',{channel:p.session,provider,workingDirectories:[p.cwd??initialized.defaultDirectory]});return {session:p.session};
  }
  if(method==='toolComplete')return dispatch(p.chat,{type:'chat/toolCallComplete',turnId:p.turnId,toolCallId:p.toolCallId,result:p.result});
  if(method==='send')return dispatch(p.chat,{type:'chat/turnStarted',turnId:p.commandId,startedAt:new Date().toISOString(),message:{text:p.text,origin:{kind:'user'},...(p.reply?{_meta:{'amplifier.dev/messageReply':p.reply}}:{})}});
  if(method==='cancel')return dispatch(p.chat,{type:'chat/turnCancelled',turnId:p.turnId,duration:0});
  if(method==='refreshSession'){if(p.session!==selected)throw Object.assign(new Error('Selection changed'),{rejected:true});const result=await client.request('subscribe',{channel:p.session});if(!result.snapshot)throw new Error('Host omitted selected snapshot');baseline(result.snapshot);return {};}
  if(method==='refreshChat'){if(p.session!==selected)throw Object.assign(new Error('Selection changed'),{rejected:true});const result=await client.request('subscribe',{channel:chatURI,view:{turns:50}});if(!result.snapshot)throw new Error('Host omitted selected chat snapshot');baseline(result.snapshot);return {};}
  if(method==='configure')return dispatch(p.session,{type:'session/configChanged',config:p.config});
  if(method==='rename')return dispatch(p.session,{type:'session/titleChanged',title:p.title});
  if(method==='decision')return dispatch(p.chat,{type:'chat/toolCallConfirmed',turnId:p.turnId,toolCallId:p.toolCallId,approved:p.approved,confirmed:'user-action',selectedOptionId:p.option});
  if(method==='history')return client.request('fetchTurns',{channel:p.chat,cursor:p.cursor});
  if(method==='receipt'){if(!initialized?._meta?.['amplifier.dev/host']?.receipts)throw new Error('Host has not advertised durable receipt lookup');return client.request('x-commandReceipt',{channel:p.chat,commandId:p.commandId});}
  if(method==='disconnect'){socket.close();return {};}
  throw new Error('Unsupported protocol operation');
}
const input=createInterface({input:process.stdin,crlfDelay:Infinity});let inFlight=0;
input.on('line',line=>{if(Buffer.byteLength(line)>2*1024*1024||++inFlight>32){process.exit(2);return;}let packet;try{packet=JSON.parse(line);}catch{process.exit(2);return;}void command(packet.method,packet.params??{}).then(result=>output({id:packet.id,result})).catch(error=>output({id:packet.id,error:{message:error.message,rejected:!!error.rejected}})).finally(()=>{inFlight--;if(packet.method==='close')process.exit(0);});});
input.on('close',()=>{closing=true;void client?.shutdown().finally(()=>process.exit(0));});

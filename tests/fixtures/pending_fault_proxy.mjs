// Owned loopback fault relay for public AHP frames; no Host implementation imports.
import {createRequire} from 'node:module';
import {readFileSync,existsSync,unlinkSync,writeFileSync,appendFileSync} from 'node:fs';
const {WebSocket,WebSocketServer}=createRequire(process.env.AHP_HOST_MODULE)('ws');
const [upstream,root]=process.argv.slice(2);
const proxy=new WebSocketServer({host:'127.0.0.1',port:0,maxPayload:32*1024*1024});
await new Promise(resolve=>proxy.once('listening',resolve));
let connection=0;
proxy.on('connection',socket=>{
 const generation=++connection;
 const backend=new WebSocket(upstream,{maxPayload:32*1024*1024}),queue=[];let dropped,clientId;
 socket.on('message',data=>{
  const row=JSON.parse(String(data));if(row.method==='initialize')clientId=row.params.clientId;
  if(row.params?.action?.type==='session/activeClientSet')clientId=row.params.action.activeClient.clientId;
  appendFileSync(root+'/sent.jsonl',JSON.stringify(row)+'\n');
  if(existsSync(root+'/drop.json')){
   const target=JSON.parse(readFileSync(root+'/drop.json','utf8'));
   const action=row.params?.action;
   const matches=action?.type===target.type&&(target.id===undefined||action.id===target.id)&&(!target.fields||Object.entries(target.fields).every(([key,value])=>JSON.stringify(action[key])===JSON.stringify(value)))&&(!target.channel||row.params.channel===target.channel);
   if(matches){dropped={...target,clientSeq:row.params.clientSeq,clientId,channel:row.params.channel};unlinkSync(root+'/drop.json');}
  }
  if(backend.readyState===WebSocket.OPEN)backend.send(data,{binary:false});else queue.push(data);
 });
 backend.on('open',()=>{for(const data of queue)backend.send(data,{binary:false})});
 backend.on('message',data=>{
  const row=JSON.parse(String(data)),frames=Array.isArray(row)?row:[row];
  const lost=frames.find(frame=>frame.params?.origin?.clientSeq===dropped?.clientSeq&&frame.params?.origin?.clientId===dropped?.clientId&&frame.params?.channel===dropped?.channel&&(dropped?.id===undefined||frame.params?.action?.id===dropped?.id)&&frame.params?.action?.type===dropped?.type);
  const registered=frames.find(frame=>frame.params?.origin?.clientId===clientId&&frame.params?.action?.type==='session/activeClientSet'&&frame.params?.action?.activeClient?.clientId===clientId&&!frame.params.rejectionReason);
  if(registered)writeFileSync(root+'/registered.json',JSON.stringify({generation,...registered.params}));
  if(dropped&&lost){writeFileSync(root+'/dropped.json',JSON.stringify(lost));dropped=undefined;socket.close();backend.close();return;}
  if(socket.readyState===WebSocket.OPEN)socket.send(data,{binary:false});
 });
 socket.on('close',()=>backend.close());backend.on('close',()=>socket.close());
 socket.on('error',()=>backend.close());backend.on('error',()=>socket.close());
});
process.stdout.write(JSON.stringify({url:`ws://127.0.0.1:${proxy.address().port}/ahp`})+'\n');
process.on('SIGTERM',()=>{for(const socket of proxy.clients)socket.terminate();proxy.close(()=>process.exit(0));});

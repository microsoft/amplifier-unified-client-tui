// Owned loopback fault relay for public AHP frames; no Host implementation imports.
import {createRequire} from 'node:module';
import {readFileSync,existsSync,unlinkSync,writeFileSync,appendFileSync} from 'node:fs';
const {WebSocket,WebSocketServer}=createRequire(process.env.AHP_HOST_MODULE)('ws');
const [upstream,root]=process.argv.slice(2);
const proxy=new WebSocketServer({host:'127.0.0.1',port:0,maxPayload:32*1024*1024});
await new Promise(resolve=>proxy.once('listening',resolve));
proxy.on('connection',socket=>{
 const backend=new WebSocket(upstream,{maxPayload:32*1024*1024}),queue=[];let dropped;
 socket.on('message',data=>{
  const row=JSON.parse(String(data));appendFileSync(root+'/sent.jsonl',JSON.stringify(row)+'\n');
  if(existsSync(root+'/drop.json')){
   const target=JSON.parse(readFileSync(root+'/drop.json','utf8'));
   if(row.params?.action?.type===target.type&&row.params.action.id===target.id){dropped={...target,clientSeq:row.params.clientSeq};unlinkSync(root+'/drop.json');}
  }
  if(backend.readyState===WebSocket.OPEN)backend.send(data,{binary:false});else queue.push(data);
 });
 backend.on('open',()=>{for(const data of queue)backend.send(data,{binary:false})});
 backend.on('message',data=>{
  const row=JSON.parse(String(data)),frames=Array.isArray(row)?row:[row];
  const lost=frames.find(frame=>frame.params?.origin?.clientSeq===dropped?.clientSeq&&frame.params?.action?.id===dropped?.id&&frame.params?.action?.type===dropped?.type);
  if(dropped&&lost){writeFileSync(root+'/dropped.json',JSON.stringify(lost));dropped=undefined;socket.close();backend.close();return;}
  if(socket.readyState===WebSocket.OPEN)socket.send(data,{binary:false});
 });
 socket.on('close',()=>backend.close());backend.on('close',()=>socket.close());
 socket.on('error',()=>backend.close());backend.on('error',()=>socket.close());
});
process.stdout.write(JSON.stringify({url:`ws://127.0.0.1:${proxy.address().port}/ahp`})+'\n');
process.on('SIGTERM',()=>{for(const socket of proxy.clients)socket.terminate();proxy.close(()=>process.exit(0));});

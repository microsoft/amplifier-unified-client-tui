// Installed public distribution plus an owned loopback fault proxy. No private host imports.
import {readFile,writeFile,unlink,stat} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
const [{createDistribution},{WebSocket,WebSocketServer}]=await Promise.all([
 import(process.env.TUI_MESSAGE_DISTRIBUTION),import(pathToFileURL(process.env.TUI_MESSAGE_WS).href)]);
const root=process.argv[2],config=JSON.parse(await readFile(root+'/distribution-config.json','utf8'));
const app=await createDistribution(config),frames=[];
const proxy=new WebSocketServer({host:'127.0.0.1',port:0,maxPayload:32*1024*1024});
await new Promise(resolve=>proxy.once('listening',resolve));
proxy.on('connection',socket=>{
 const backend=new WebSocket(new URL('/ahp',app.url).href.replace(/^http/,'ws'),{maxPayload:32*1024*1024}),queue=[];let dropped;
 socket.on('message',async data=>{
  const row=JSON.parse(String(data));frames.push(row);
  if(row.params?.action?.type==='chat/turnCancelled')await writeFile(root+'/cancellation-requested.json',JSON.stringify(row.params));
  if(row.params?.operation==='message.reaction'){
   try{await stat(root+'/drop-next-reaction');await unlink(root+'/drop-next-reaction');dropped=row.id}catch{}
  }
  if(backend.readyState===WebSocket.OPEN)backend.send(data,{binary:false});else queue.push(data);
 });
 backend.on('open',()=>{for(const data of queue)backend.send(data,{binary:false})});
 backend.on('message',data=>{
  const row=JSON.parse(String(data));
  if(dropped!==undefined&&row.id===dropped){dropped=undefined;socket.send(JSON.stringify({jsonrpc:'2.0',id:row.id,error:{code:-32000,message:'Owned fixture lost the original reaction acknowledgement'}}));return;}
  if(socket.readyState===WebSocket.OPEN)socket.send(data,{binary:false});
 });
 socket.on('close',()=>backend.close());backend.on('close',()=>socket.close());
 socket.on('error',()=>backend.close());backend.on('error',()=>socket.close());
});
process.stdout.write(JSON.stringify({url:`ws://127.0.0.1:${proxy.address().port}/ahp`})+'\n');
process.on('SIGTERM',()=>void(async()=>{
 for(const socket of proxy.clients)socket.terminate();
 await new Promise(resolve=>proxy.close(resolve));
 await app.close();await writeFile(root+'/protocol-frames.json',JSON.stringify(frames,null,2)+'\n');process.exit(0);
})());

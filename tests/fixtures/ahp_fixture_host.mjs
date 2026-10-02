// Test host composition uses only the package's public API; no private implementation imports.
import {readFile} from 'node:fs/promises';
const {createHost}=await import(process.env.AHP_HOST_MODULE);
const config=JSON.parse(await readFile(process.argv[process.argv.indexOf('--config')+1],'utf8'));
let host;
host=await createHost({...config,nativeHostRequest:async(context,request)=>{
 const clients=await host.listClientTools(context.session);
 const client=clients.find(c=>c.clientId==='terminal');
 if(!client)throw Error('Explicit terminal target unavailable');
 const name=client.tools.find(t=>t.name.startsWith(request.operation==='ui.inspect'?'amplifier_tui_inspect_':'amplifier_tui_action_'))?.name;
 if(!name)throw Error('Target tool unavailable');
 return host.invokeClientTool(context.session,client.clientId,name,request.args);
}});
process.stdout.write(JSON.stringify({url:host.url})+'\n');
process.on('SIGTERM',()=>void host.close().then(()=>process.exit(0)));

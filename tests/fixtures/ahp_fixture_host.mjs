// Test host composition uses only the package's public API; no private implementation imports.
import {readFile,writeFile} from 'node:fs/promises';
const {createHost,StdioCatalog}=await import(process.env.AHP_HOST_MODULE);
const config=JSON.parse(await readFile(process.argv[process.argv.indexOf('--config')+1],'utf8'));
let host;
if(config.catalogProcess) {
 const catalog=new StdioCatalog(config.catalogProcess);delete config.catalogProcess;config.catalog=catalog;
}
// An explicit interface fixture, never evidence of complete dependent-owner protection.
if(config.fixtureManagedProtection) {
 delete config.fixtureManagedProtection;
 config.managedFilesProtection={managedFiles:{version:1,preservesCanonical:true},async acquire(){return {ownerIds:['tui-interface-fixture'],async release(){}};}};
}
if(config.workspaceOwner) {
 const {createWorkspaceCapabilities}=await import(process.env.TUI_WORKSPACES_MODULE);
 const workspace=createWorkspaceCapabilities({owner:config.workspaceOwner,catalog:config.catalog,onInvalidate:(topic,scope)=>host?.invalidateCapability(topic,scope)});
 delete config.workspaceOwner;config.capabilities=workspace;
}
host=await createHost({...config,nativeHostRequest:async(context,request)=>{
 const clients=await host.listClientTools(context.session);
 const client=clients.find(c=>c.clientId==='terminal');
 if(!client)throw Error('Explicit terminal target unavailable');
 const name=client.tools.find(t=>t.name.startsWith(request.operation==='ui.inspect'?'amplifier_tui_inspect_':'amplifier_tui_action_'))?.name;
 if(!name)throw Error('Target tool unavailable');
 return host.invokeClientTool(context.session,client.clientId,name,request.args);
}});
process.stdout.write(JSON.stringify({url:host.url})+'\n');
process.on('SIGTERM',()=>void(async()=>{
 if(config.testDiagnostics&&config.catalog){
  try{
   const page=await config.catalog.list({connectionId:'tui-diagnostic',limit:10});
   const families=await Promise.all(page.items.map(row=>config.catalog.descendants({parentUri:row.uri,limit:100})));
   await writeFile(config.testDiagnostics,JSON.stringify({page,families},null,2));
  }catch{}
 }
 await host.close();process.exit(0);
})());

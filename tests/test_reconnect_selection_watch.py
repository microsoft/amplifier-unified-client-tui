import asyncio
import json
import os
from pathlib import Path

from test_ahp_client import request, wait_for
from test_messages_installed import message_host as message_host
from test_messages_installed import open_bridge, seeded
from test_messages_installed import pytestmark as pytestmark


async def test_reconnect_during_selection_keeps_fresh_current_generation_watch(message_host):
    url,root,workspace=message_host
    bridge,_=await open_bridge(url,root,workspace,'selected-watch-review')
    other=isolated=None
    try:
        message=await seeded(bridge)
        scope=bridge.selected
        mid=message['messageReference']['messageId']
        await bridge.messages.read(message['id'])
        other,_=await open_bridge(url,root,workspace,'selected-watch-other',scope)
        msg=next(r for r in other.session['messages'] if (r.get('messageReference') or {}).get('messageId')==mid)
        assert (await other.dispatch(request(other,'message.reaction',message_id=msg['id'],emoji='👍',present=True)))[0]
        await wait_for(lambda:bridge.messages.rows[(scope,mid)]['mine']==['👍'])
        isolated,_=await open_bridge(url,root,workspace,'selected-watch-isolated')
        await seeded(isolated)
        await bridge.select(isolated.selected)
        await wait_for(lambda:not other.messages.refreshing)
        msg=next(r for r in other.session['messages'] if (r.get('messageReference') or {}).get('messageId')==mid)
        result=await other.dispatch(request(other,'message.reaction',message_id=msg['id'],emoji='👍',present=False))
        assert result[0],result
        msg=next(r for r in other.session['messages'] if (r.get('messageReference') or {}).get('messageId')==mid)
        result=await other.dispatch(request(other,'message.reaction',message_id=msg['id'],emoji='✅',present=True))
        assert result[0],result
        snapshot=bridge.transport.snapshot
        observed=[]
        accept=bridge.transport.message_metadata
        def capture(packet):
            observed.append((packet.get('scope'),bridge.transport.generation))
            accept(packet)
        bridge.transport.message_metadata=capture
        async def interrupted(identity):
            value=await snapshot(identity)
            if identity==scope:
                generation=bridge.transport.generation
                await bridge.transport.rpc('disconnect')
                await wait_for(lambda:bridge.transport.online and bridge.transport.generation>generation)
                await wait_for(lambda:any(target==scope and epoch>generation for target,epoch in observed))
            return value
        bridge.transport.snapshot=interrupted
        await bridge.select(scope)
        await asyncio.sleep(.5)
        bridge.transport.snapshot=snapshot
        automatic=bridge.messages.rows[(scope,mid)]['mine']
        current=next(r for r in bridge.session['messages'] if (r.get('messageReference') or {}).get('messageId')==mid)
        await bridge.messages.read(current['id'])
        explicit=bridge.messages.rows[(scope,mid)]['mine']
        report={'scope':scope,'automaticAfterReturn':automatic,'explicitReadAfterReturn':explicit,'selected':bridge.selected}
        Path(os.environ['TUI_EVIDENCE_DIR'],'reconnect-selection-watch-probe.json').write_text(json.dumps(report,indent=2)+'\n')
        assert automatic==['✅'],report
    finally:
        await bridge.close()
        if other:
            await other.close()
        if isolated:
            await isolated.close()

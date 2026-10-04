import asyncio,json,os
from pathlib import Path
from test_messages_installed import message_host,open_bridge,seeded
from test_ahp_client import request,wait_for

async def test_return_to_selected_chat_applies_initial_watch_snapshot(message_host):
    url,root,workspace=message_host
    bridge,_=await open_bridge(url,root,workspace,'selected-watch-review')
    other=isolated=None
    try:
        message=await seeded(bridge);scope=bridge.selected;mid=message['messageReference']['messageId']
        await bridge.messages.read(message['id'])
        other,_=await open_bridge(url,root,workspace,'selected-watch-other',scope)
        msg=next(r for r in other.session['messages'] if (r.get('messageReference') or {}).get('messageId')==mid)
        assert (await other.dispatch(request(other,'message.reaction',message_id=msg['id'],emoji='👍',present=True)))[0]
        await wait_for(lambda:bridge.messages.rows[(scope,mid)]['mine']==['👍'])
        isolated,_=await open_bridge(url,root,workspace,'selected-watch-isolated')
        await seeded(isolated);await bridge.select(isolated.selected)
        await wait_for(lambda:not other.messages.refreshing)
        msg=next(r for r in other.session['messages'] if (r.get('messageReference') or {}).get('messageId')==mid)
        result=await other.dispatch(request(other,'message.reaction',message_id=msg['id'],emoji='👍',present=False))
        assert result[0],result
        msg=next(r for r in other.session['messages'] if (r.get('messageReference') or {}).get('messageId')==mid)
        result=await other.dispatch(request(other,'message.reaction',message_id=msg['id'],emoji='✅',present=True))
        assert result[0],result
        await bridge.select(scope);await asyncio.sleep(.5)
        automatic=bridge.messages.rows[(scope,mid)]['mine']
        current=next(r for r in bridge.session['messages'] if (r.get('messageReference') or {}).get('messageId')==mid)
        await bridge.messages.read(current['id'])
        explicit=bridge.messages.rows[(scope,mid)]['mine']
        report={'scope':scope,'automaticAfterReturn':automatic,'explicitReadAfterReturn':explicit,'selected':bridge.selected}
        Path(os.environ['TUI_EVIDENCE_DIR'],'selection-watch-probe.json').write_text(json.dumps(report,indent=2)+'\n')
        assert automatic==['✅'],report
    finally:
        await bridge.close()
        if other:await other.close()
        if isolated:await isolated.close()

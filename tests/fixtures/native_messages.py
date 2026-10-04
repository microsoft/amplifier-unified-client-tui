"""Owned offline provider built against installed public Core contracts only."""
import importlib.util
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
home, module = root / 'home', root / 'provider/amplifier_module_provider_tui_fixture'
home.mkdir()
module.mkdir(parents=True)
(module.parent / 'pyproject.toml').write_text('[project]\nname="amplifier-module-provider-tui-fixture"\nversion="0.1.0"\n')
module.joinpath('__init__.py').write_text('''import asyncio,json
from pathlib import Path
from amplifier_core.models import ProviderInfo
from amplifier_core.message_models import ChatResponse,TextBlock,Usage
class Provider:
    name='fixture'
    def __init__(self,config):self.config=config
    def parse_tool_calls(self,response):return []
    def get_info(self):return ProviderInfo(id='fixture',display_name='Offline TUI fixture',defaults={'model':'fixture-model','max_tokens':4096},capabilities=[])
    async def list_models(self):return [{'id':'fixture-model'}]
    async def complete(self,request,**kwargs):
        candidates=[str(m.content) for m in request.messages if m.role=='user']
        prompt=next((text for text in reversed(candidates) if any(mark in text for mark in ('busy-fixture','original fixture source','Explicit quoted fixture response'))),'fixture source')
        with Path(self.config['audit']).open('a') as f:f.write(json.dumps({'prompt':str(prompt),'messages':[{'role':m.role,'content':str(m.content)} for m in request.messages]})+'\\n')
        if 'busy-fixture' in str(prompt):
            Path(self.config['gate']).with_suffix('.entered').touch()
            while not Path(self.config['gate']).exists():await asyncio.sleep(.02)
        return ChatResponse(content=[TextBlock(text='Offline TUI reply: '+str(prompt))],finish_reason='stop',usage=Usage(input_tokens=8,output_tokens=5,total_tokens=13))
async def mount(coordinator,config=None):await coordinator.mount('providers',Provider(config or {}),name='fixture')
''')
context = Path(importlib.util.find_spec('amplifier_module_context_simple').origin).parent
bundle = root / 'fixture.yaml'
bundle.write_text('bundle:\n  name: tui-message-fixture\n  version: 1.0.0\nsession:\n  orchestrator:\n    module: loop-live\n  context:\n    module: context-simple\n    source: '+str(context)+'\nproviders:\n  - module: provider-tui-fixture\n    source: '+str(module.parent)+'\n    config: '+json.dumps({'audit': str(root / 'provider-audit.jsonl'), 'gate': str(root / 'busy.release')})+'\n')
home.joinpath('settings.yaml').write_text('bundle:\n  app: []\n')
root.joinpath('native.json').write_text(json.dumps({'home': str(home), 'appHome': str(root / 'app'), 'bundle': str(bundle), 'startupTimeout': 90}))

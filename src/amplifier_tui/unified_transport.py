"""AHP 0.9 through bundled upstream SDK/reducers. No execution-runtime imports."""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

MAX_FRAME = 32 * 1024 * 1024


class Rejected(RuntimeError):
    def __init__(self, status, data):
        self.status, self.data = status, data
        super().__init__(data.get('error', 'AHP rejected the action'))


def validate_url(value):
    parts = urlsplit(value)
    if (parts.scheme not in {'ws', 'wss', 'http', 'https'} or not parts.hostname
            or parts.username or parts.password or parts.query or parts.fragment):
        raise ValueError('Use an AHP WebSocket URL without credentials, query or fragment')
    scheme = {'http': 'ws', 'https': 'wss'}.get(parts.scheme, parts.scheme)
    if scheme == 'ws' and parts.hostname not in {'localhost', '127.0.0.1', '::1'}:
        raise ValueError('Remote AHP connections require WSS and verified TLS')
    return urlunsplit((scheme, parts.netloc, parts.path.rstrip('/') or '/ahp', '', ''))


def _text(value):
    return value if isinstance(value, str) else value.get('value', '') if isinstance(value, dict) else ''


def _message_metadata(history):
    return {'historicalOnly': history.get('historicalOnly') is True,
            **({'reference': history['messageReference']} if 'messageReference' in history else {}),
            **({'replyTo': history['replyTo']} if 'replyTo' in history else {})}


def _turn_items(turn):
    identity = turn['id']
    message = turn.get('message', {})
    history = message.get('_meta', {}).get('amplifier.dev/history', {})
    text = message.get('text', '')
    role = 'assistant' if message.get('origin', {}).get('kind') == 'agent' else 'user'
    items = ([{'id': 'input:' + identity, 'kind': role, 'text': text, 'status': '', **_message_metadata(history),
               'detail': json.dumps(message, ensure_ascii=False)}] if text else [])
    quote = history.get('replyTo')
    if items and isinstance(quote, dict) and isinstance(quote.get('excerpt'), str):
        items.insert(0, {'id': identity + ':quote', 'kind': 'notice',
                        'text': 'Quoted ' + ('You' if quote.get('role') == 'user' else 'Amplifier') + ' · ' + quote['excerpt'][:4000],
                        'status': '', 'detail': json.dumps(quote, ensure_ascii=False)})
    if history.get('via') == 'call':
        items.append({'id': identity + ':call', 'kind': 'notice',
                      'text': 'Recorded voice · ' + str(history.get('outcome', 'recorded')),
                      'status': '', 'detail': json.dumps(history, ensure_ascii=False)})
    for index, part in enumerate(turn.get('responseParts', [])):
        kind = part.get('kind')
        item = {'id': identity + ':' + str(part.get('id', index)), 'kind': 'notice',
                'text': '', 'status': '', 'detail': json.dumps(part, ensure_ascii=False)}
        if kind in {'markdown', 'reasoning'}:
            # Text is already visible. Do not duplicate its growing body in detail.
            item['detail'] = json.dumps({k: v for k, v in part.items() if k != 'content'}, ensure_ascii=False)
            item.update(kind='assistant' if kind == 'markdown' else 'thinking', text=part.get('content', ''), status='running' if turn.get('state') is None else '')
            item.update(_message_metadata(part.get('_meta', {}).get('amplifier.dev/history', {})))
            item['historicalOnly'] = item['historicalOnly'] or history.get('historicalOnly') is True
        elif kind == 'toolCall':
            tool = part['toolCall']
            item.update(id='tool:' + identity + ':' + tool['toolCallId'], kind='tool',
                        text=_text(tool.get('displayName') or tool.get('toolName') or 'Tool'),
                        status=({'streaming': 'running', 'pending-confirmation': 'waiting', 'pending-result-confirmation': 'waiting', 'auth-required': 'waiting', 'completed': 'failed' if tool.get('success') is False else 'completed'}.get(tool.get('status'), tool.get('status', 'unknown'))))
        elif kind == 'error':
            item.update(text=part.get('error', {}).get('message', 'Execution error'), status='failed')
        else:
            item['text'] = _text(part.get('title')) or 'Resource · ' + str(part.get('uri') or part.get('resource') or kind)
        items.append(item)
    if turn.get('usage'):
        items.append({'id': identity + ':usage', 'kind': 'notice', 'text': 'Reported usage · ' + json.dumps(turn['usage']), 'status': '', 'detail': json.dumps(turn['usage'])})
    if turn.get('state') in {'cancelled', 'error'}:
        items.append({'id': identity + ':outcome', 'kind': 'notice', 'text': 'Turn ' + turn['state'], 'status': turn['state'], 'detail': ''})
    return items


class Transport:
    """Local presentation facade; the network contains only standard AHP resources."""
    def __init__(self, url, token, client_id, *, ca_file=None):
        self.url, self.token, self.client_id = validate_url(url), token, client_id
        self.ca_file = str(ca_file) if ca_file else None
        self.process = self.reader = self.stderr_reader = None
        self.pending, self.sessions_state, self.chat_state = {}, {}, {}
        self.counter, self.revision, self.generation = 0, 0, 0
        self.received_bytes = 0
        self.online = False
        self.changed = asyncio.Event()
        self.page_scope = None
        self.workspace_pages = {0: None}
        self.pages = {0: None}
        self.attached = {}
        self.selected = None
        self.closed = False
        self.optional_unavailable = {}
        self.client_tool = None
        self.message_metadata = None
        self.tool_tasks = set()

    async def open(self):
        if self.process:
            return self.attached
        helper = Path(__file__).with_name('_ahp') / 'bridge.mjs'
        if not helper.is_file():
            raise ValueError('Packaged AHP helper missing; build the protocol bundle')
        self.process = await asyncio.create_subprocess_exec(
            os.environ.get('AMPLIFIER_TUI_NODE', 'node'), str(helper),
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, limit=MAX_FRAME)
        self.reader = asyncio.create_task(self._read())
        self.stderr_reader = asyncio.create_task(self._drain())
        self.attached = await self.rpc('open', url=self.url, token=self.token,
                                       clientId=self.client_id, caFile=self.ca_file)
        return self.attached

    async def _drain(self):
        while await self.process.stderr.read(8192):
            pass  # Diagnostics cannot contaminate terminal rendering or expose auth headers.

    async def _read(self):
        try:
            while line := await self.process.stdout.readline():
                if len(line) > MAX_FRAME:
                    raise ValueError('Protocol frame exceeds local presentation bound')
                self.received_bytes += len(line)
                packet = json.loads(line)
                if 'id' in packet:
                    future = self.pending.get(packet['id'])
                    if future and not future.done():
                        if 'error' in packet:
                            error = packet['error']
                            exc = Rejected(422, {'error': error['message']}) if error.get('rejected') else OSError(error['message'])
                            future.set_exception(exc)
                        else:
                            future.set_result(packet.get('result'))
                    continue
                event = packet.get('event')
                if event == 'clientTool' and self.client_tool:
                    if len(self.tool_tasks) >= 32:
                        raise ValueError('Client tool capacity exceeded')
                    task = asyncio.create_task(self._client_tool(packet))
                    self.tool_tasks.add(task)
                    task.add_done_callback(self.tool_tasks.discard)
                elif event == 'messageMetadata' and self.message_metadata:
                    self.message_metadata(packet)
                elif event == 'optionalUnavailable':
                    self.optional_unavailable[packet['capability']] = packet['message']
                elif event == 'connection':
                    self.online, self.generation = packet['online'], packet['generation']
                    self.pages = {0: None}
                    self.workspace_pages = {0: None}
                elif event == 'catalogInvalidated':
                    self.pages = {0: None}
                    self.workspace_pages = {0: None}
                elif event == 'session':
                    self.sessions_state[packet['uri']] = packet['state']
                elif event == 'chat':
                    state = self.chat_state.setdefault(packet['uri'], {'turns': {}, 'order': [], 'items': {}})
                    if 'turns' in packet:
                        turns = packet['turns'] + ([packet['activeTurn']] if packet.get('activeTurn') else [])
                        state['turns'] = {turn['id']: turn for turn in turns}
                        state['order'] = [turn['id'] for turn in turns]
                        state['items'] = {turn['id']: _turn_items(turn) for turn in turns}
                    elif packet.get('append'):
                        delta = packet['append']
                        turn = state['turns'].get(delta['turnId'])
                        part = next((p for p in (turn or {}).get('responseParts', []) if p.get('id') == delta['partId']), None)
                        if part is None:
                            raise ValueError('Append without presentation baseline')
                        part['content'] = part.get('content', '') + delta['content']
                        identity = delta['turnId'] + ':' + delta['partId']
                        state['items'][turn['id']] = [
                            {**item, 'text': part['content']} if item['id'] == identity else item
                            for item in state['items'][turn['id']]]
                    elif packet.get('turn'):
                        turn = packet['turn']
                        state['turns'][turn['id']] = turn
                        if turn['id'] not in state['order']:
                            state['order'].append(turn['id'])
                        state['items'][turn['id']] = _turn_items(turn)
                    state.update({key: packet.get(key) for key in ('title', 'status', 'activeTurnId', 'turnsNextCursor', 'error')})
                elif event == 'missing':
                    self.sessions_state.pop(packet['uri'], None)
                    self.chat_state.pop(packet['uri'], None)
                self.revision += 1
                self.changed.set()
        except (OSError, ValueError, asyncio.IncompleteReadError):
            pass
        finally:
            self.online = False
            self.changed.set()
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(OSError('AHP helper ended; command outcome unknown'))

    async def _client_tool(self, packet):
        try:
            result = await self.client_tool(packet)
            await self.rpc('toolComplete', chat=packet['chat'], turnId=packet['turnId'], toolCallId=packet['tool']['toolCallId'], result=result)
        except (OSError, ValueError, TimeoutError):
            pass  # Durable receipt remains; never repeat the client effect.

    async def rpc(self, method, **params):
        if len(self.pending) >= 32:
            raise OSError('Client request capacity reached')
        self.counter += 1
        identity = self.counter
        future = asyncio.get_running_loop().create_future()
        self.pending[identity] = future
        try:
            data = (json.dumps({'id': identity, 'method': method, 'params': params}) + '\n').encode()
            if len(data) > 2 * 1024 * 1024:
                raise ValueError('Client command exceeds 2 MiB')
            self.process.stdin.write(data)
            await self.process.stdin.drain()
            async with asyncio.timeout(20):
                return await future
        finally:
            self.pending.pop(identity, None)

    async def close(self):
        if self.closed:
            return
        self.closed = True
        for task in self.tool_tasks:
            task.cancel()
        await asyncio.gather(*self.tool_tasks, return_exceptions=True)
        if self.process and self.process.returncode is None:
            try:
                await self.rpc('close')
            except (OSError, TimeoutError, BrokenPipeError):
                pass
            try:
                async with asyncio.timeout(2):
                    await self.process.wait()
            except TimeoutError:
                self.process.kill()
                await self.process.wait()
        for task in (self.reader, self.stderr_reader):
            if task:
                task.cancel()
        await asyncio.gather(*(t for t in (self.reader, self.stderr_reader) if t), return_exceptions=True)

    async def prepare_creation(self, choices):
        agents = [agent['provider'] for snapshot in self.attached.get('snapshots', [])
                  if snapshot.get('resource') == 'ahp-root://' for agent in snapshot['state'].get('agents', [])]
        agent = choices.get('agent')
        if agent and agent not in agents:
            raise ValueError('Agent is not advertised by this host')
        args = {'provider': agent} if agent else {}
        if not choices.get('managed'):
            return args
        options = await self.rpc('managed', operation='options', args=args)
        args['provider'] = options['provider']
        if choices.get('bundle'):
            bundle = next((b for b in options['bundles'] if b['id'] == choices['bundle']), None)
            if not bundle:
                raise ValueError('Bundle alias is not configured on this host')
            args.update(bundle=bundle['id'], bundleRevision=bundle['revision'])
        if choices.get('provider'):
            defaults = await self.rpc('managed', operation='defaults', args=args)
            if not any(p['id'] == choices['provider'] for p in defaults['providers']):
                raise ValueError('Provider instance is unavailable for the chosen bundle')
            args['selection'] = {'instance': choices['provider'], 'model': choices['model']}
            if choices.get('effort'):
                args['selection']['effort'] = choices['effort']
        return {'managed': True, **args}

    async def lifecycle(self, identity, operation, args=None):
        return await self.rpc('lifecycle', session=identity, operation=operation, args=args or {})

    async def creation_receipt(self, command_id, managed=False):
        if not managed:
            raise ValueError('Standard creation lookup unavailable; inspect the exact session URI')
        return await self.rpc('managed', operation='receipt', args={'commandId': command_id})

    async def actions(self):
        return {'conversation.send', 'conversation.stop', 'approval.respond', 'session.rename', 'session.create', 'session.history'}

    def supports(self, action):
        manifest = self.attached.get('_meta', {}).get('amplifier.dev/capabilities', {})
        record = manifest.get('actions', {}).get(action, {})
        return (manifest.get('version') == 1 and record.get('method') == 'x-amplifier/capabilityAction'
                and manifest.get('topics', {}).get(record.get('topic'), {}).get('version') == 1)

    async def capability(self, action, args, channel='ahp-root://', *, command_id=None):
        result = await self.rpc('capability', action=action, args=args, channel=channel, commandId=command_id or str(uuid.uuid4()))
        if result.get('accepted') is not True:
            data = result.get('result') or {}
            raise Rejected(422, {**data, 'error': data.get('message', data.get('reason', 'Capability refused'))})
        return result['result']

    async def workspaces(self, *, offset=0, query=''):
        if not self.supports('workspace.list'):
            raise ValueError('Workspace discovery unavailable; use an explicit --workspace host path')
        if offset == 0:
            self.workspace_pages = {0: None}
            self.workspace_query = query
        if offset not in self.workspace_pages or query != self.workspace_query:
            raise ValueError('Workspace cursor expired; reopen Workspaces')
        args = {'limit': 50}
        if query:
            args['query'] = query
        if self.workspace_pages[offset]:
            args['cursor'] = self.workspace_pages[offset]
        page = await self.capability('workspace.list', args)
        next_offset = offset + 50 if page.get('nextCursor') else None
        if next_offset:
            self.workspace_pages[next_offset] = page['nextCursor']
        return {**page, 'nextOffset': next_offset}

    async def sessions(self, *, offset=0, workspace=None, query=''):
        scope = (workspace, query)
        if offset == 0:
            self.pages = {0: None}
            self.page_scope = scope
        if offset not in self.pages or self.page_scope != scope:
            raise ValueError('Catalog cursor expired after reconnect/change; reopen Resume')
        scoped = self.supports('workspace.sessions')
        args = {'limit': 50}
        if self.pages[offset]:
            args['cursor'] = self.pages[offset]
        if scoped:
            if workspace is not None:
                # Resolve one bounded metadata page, never inspect native files or scan all sessions.
                if offset == 0:
                    choices = await self.capability('workspace.list', {'query': workspace, 'limit': 50})
                    selected = next((row for row in choices['items'] if row['path'] == workspace), None)
                    if not selected:
                        raise ValueError('Workspace is not in the bounded existing-directory page; use /workspaces')
                    self.session_workspace_id = selected['id']
                args['id'] = self.session_workspace_id
            if query:
                args['query'] = query
            page = await self.capability('workspace.sessions', args)
        else:
            page = await self.rpc('list', cursor=self.pages[offset])
        next_offset = offset + 50 if page.get('nextCursor') else None
        if next_offset:
            self.pages[next_offset] = page['nextCursor']
        rows = []
        for row in page['items']:
            directory = unquote(urlsplit((row.get('workingDirectories') or [''])[0]).path)
            if not scoped and workspace is not None and directory != workspace:
                continue
            if not scoped and query and query.casefold() not in (row['title'] + ' ' + row['resource']).casefold():
                continue
            rows.append({'id': row['resource'], 'title': row['title'], 'workspace': directory, 'status': row['status']})
        return {'items': rows, 'nextOffset': next_offset, 'scopedSearch': scoped}

    async def resolve_session(self, identity, *, workspace=None):
        if identity.startswith('ahp-session:/'):
            return identity
        matches, offset = set(), 0
        while True:
            page = await self.sessions(offset=offset, workspace=workspace)
            for row in page['items']:
                if identity == 'latest':
                    return row['id']
                if row['id'].startswith(identity) or row['id'].removeprefix('ahp-session:/').startswith(identity):
                    matches.add(row['id'])
            offset = page.get('nextOffset')
            if offset is None:
                if len(matches) == 1:
                    return matches.pop()
                raise ValueError('Session ID is ambiguous' if matches else 'No matching conversation; use --resume')

    def _snapshot(self, identity):
        source = self.sessions_state.get(identity)
        if not source:
            raise ValueError('Session baseline unavailable')
        chat = self.chat_state.get(source['defaultChat'])
        if not chat:
            raise ValueError('Chat baseline unavailable')
        turns = [chat['turns'][key] for key in chat['order']]
        approvals = []
        for turn in turns:
            if turn['id'] != chat.get('activeTurnId'):
                continue
            for part in turn.get('responseParts', []):
                tool = part.get('toolCall', {})
                if tool.get('status') == 'pending-confirmation':
                    approvals.append({'id': tool['toolCallId'], 'turnId': turn['id'], 'status': 'pending',
                                      'prompt': _text(tool.get('invocationMessage') or tool.get('displayName')),
                                      'options': [f"{o['label']} [{o['id']}]" for o in tool.get('options', [])],
                                      'rawOptions': tool.get('options', [])})
        session = {'id': identity, 'title': source.get('title'),
                   'workspace': unquote(urlsplit((source.get('workingDirectories') or [''])[0]).path),
                   'status': 'working' if chat.get('activeTurnId') else 'ready',
                   'activeTurnId': chat.get('activeTurnId'), 'chat': source['defaultChat'],
                   'messages': [{**item, 'role': item['kind'], 'messageReference': item.get('reference'),
                                 **({'inputId': turn['id'], 'delivery': {'status': 'accepted'}} if item['kind'] == 'user' and item['id'] == 'input:' + turn['id'] else {})}
                                for turn in turns for item in _turn_items(turn) if item['kind'] in {'user', 'assistant'}],
                   'displayItems': [item for key in chat['order'] for item in chat['items'][key]],
                   'approvals': approvals, 'sharedHistoryOffset': 1 if chat.get('turnsNextCursor') else 0,
                   'historyCursor': chat.get('turnsNextCursor'), 'config': source.get('config') or {}, 'error': chat.get('error'),
                   'agentCapabilities': source.get('_meta', {}).get('amplifier.dev/acp', {}).get('capabilities', {}),
                   'lastSettledTurnId': source.get('_meta', {}).get('amplifier.dev/acp', {}).get('lastSettledTurnId')}
        return {'protocolVersion': 1, 'hostInstanceId': str(self.generation), 'revision': self.revision, 'session': session}

    async def snapshot(self, identity):
        if identity != self.selected:
            await self.rpc('select', session=identity)
            self.selected = identity
            source = self.sessions_state[identity]
            self.sessions_state = {identity: source}
            self.chat_state = {source['defaultChat']: self.chat_state[source['defaultChat']]}
        return self._snapshot(identity)

    async def detach(self):
        await self.rpc('detach')
        self.selected = None
        self.sessions_state.clear()
        self.chat_state.clear()

    async def command(self, identity, action, args, command_id):
        if action == 'session.create':
            session = 'ahp-session:/' + command_id
            cwd = Path(args['workspace']).as_uri() if args.get('workspace') else None
            if args.get('managed'):
                selection = {k: v for k, v in args.items() if k not in {'managed', 'workspace'}}
                result = await self.rpc('managed', operation='create', args={
                    **selection, 'session': session, 'commandId': command_id})
            else:
                result = await self.rpc('create', session=session, cwd=cwd, provider=args.get('provider'))
            return {'accepted': True, 'result': {'sessionId': result['session']}}
        snapshot = self._snapshot(identity)['session']
        chat = snapshot['chat']
        if action == 'conversation.send':
            return await self.rpc('send', chat=chat, text=args['text'], commandId=command_id,
                                  **({'reply': args['reply']} if args.get('reply') else {}))
        if action == 'conversation.stop':
            if not snapshot['activeTurnId']:
                raise Rejected(422, {'error': 'No active turn to cancel'})
            return await self.rpc('cancel', chat=chat, turnId=snapshot['activeTurnId'])
        if action == 'session.configure':
            return await self.rpc('configure', session=identity, config=args['config'])
        if action == 'session.rename':
            return await self.rpc('rename', session=identity, title=args['title'])
        if action == 'approval.respond':
            approval = next((row for row in snapshot['approvals'] if row['id'] == args['id']), None)
            if not approval:
                raise Rejected(422, {'error': 'Approval is no longer pending'})
            option = next((o for o in approval['rawOptions'] if args['decision'] in {o['id'], f"{o['label']} [{o['id']}]"}), None)
            if not option:
                raise Rejected(422, {'error': 'Choose an offered permission option'})
            return await self.rpc('decision', chat=chat, turnId=approval['turnId'], toolCallId=approval['id'], option=option['id'], approved=option['kind'] == 'approve')
        if action == 'session.history':
            cursor = snapshot['historyCursor']
            if cursor:
                await self.rpc('history', chat=chat, cursor=cursor)
            return {'accepted': True}
        raise Rejected(422, {'error': 'Host capability is unavailable'})

    async def receipt(self, identity, command_id):
        snapshot = self._snapshot(identity)['session']
        return await self.rpc('receipt', chat=snapshot['chat'], commandId=command_id)

    async def snapshots(self, identity, connection):
        while not self.closed:
            self.changed.clear()
            connection(self.online)
            if identity in self.sessions_state and self.sessions_state[identity]['defaultChat'] in self.chat_state:
                yield self._snapshot(identity)
            await self.changed.wait()

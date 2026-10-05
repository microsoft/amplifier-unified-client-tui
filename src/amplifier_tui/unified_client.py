"""Connected backend for the existing Ratatui protocol. Unified owns all execution."""
from __future__ import annotations

import asyncio
import json
import uuid

from .unified_messages import Messages
from .unified_projection import project
from .unified_transport import Rejected


class UnifiedBridge:
    async_stop = True

    def __init__(self, emit, transport, state, *, session=None, workspace=None, resume_picker=False, creation=None):
        self.emit, self.transport, self.store = emit, transport, state
        self.selected = None if resume_picker else session or state.data.get('session')
        self.resume_picker = resume_picker
        self.workspace = workspace
        self.creation = creation or {}
        self.creation_args = {}
        self.reviews = {}
        self.workspace_choices = {}
        self.published_controls = None
        self.published_followups = None
        self.session = {}
        self.messages = Messages(self)
        self.transport.message_metadata = self.messages.accept
        self.actions = set()
        self.pump = None
        self.tasks = set()
        self.online = False
        self.generation = 0
        self.revision = -1
        self.instance = None
        self.opened = False
        self.deleted = False
        self.selection_lock = asyncio.Lock()
        self.switch_lock = asyncio.Lock()
        self.submission_lock = asyncio.Lock()
        self.retired_instances = set()
        self.ui_requests = {}
        self.transport.client_tool = self.client_tool
        self.published = {}
        self.published_order = []
        self.published_title = None

    def send(self, kind, **fields):
        self.emit({'type': kind, 'session_id': self.selected or '', **fields})

    def later(self, coroutine):
        task = asyncio.create_task(coroutine)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    async def client_tool(self, packet):
        tool = packet['tool']
        session = packet['session']
        key = session + '/' + tool['toolCallId']
        receipts = self.store.data.setdefault('clientEffects', {})
        prior = receipts.get(key)
        if prior:
            return prior.get('result') or {'success': False, 'pastTenseMessage': 'Preserved unknown client outcome', 'error': {'code': 'CLIENT_OUTCOME_UNKNOWN', 'message': 'No effect was repeated'}}
        if len(receipts) >= 512:
            raise ValueError('Local client effect receipt capacity reached')
        receipts[key] = {'status': 'unknown'}
        self.store.save()
        try:
            if session != self.selected:
                raise ValueError('Client selection changed')
            tool_input = tool.get('toolInput') or '{}'
            if not isinstance(tool_input, str) or len(tool_input.encode()) > 65536:
                raise ValueError('Client tool input must be bounded inline JSON')
            args = json.loads(tool_input)
            operation = 'inspect' if '_inspect_' in tool['toolName'] else args.get('action')
            settings_actions = {'settings', 'setting_choices', 'setting_set', 'rename', 'host_effects', 'host_receipt'}
            if operation not in {'inspect', 'draft.replace', 'view.select', 'panel.open', 'message.reply', 'message.replyClear', 'message.read', 'message.reaction', 'message.receipt', 'message.refresh', 'message.submissionInspect', 'queue', 'queue_edit', 'queue_remove', 'queue_run', 'queue_inspect', 'steer', 'steer_remove', 'steer_inspect'} | settings_actions:
                raise ValueError('Client action is unavailable')
            token = str(uuid.uuid4())
            future = asyncio.get_running_loop().create_future()
            self.ui_requests[token] = future
            self.send('client_ui', token=token, operation=operation, args=args.get('args', {}),
                      expectedRevision=args.get('expectedRevision'), includeDraft=args.get('includeDraft') is True)
            try:
                async with asyncio.timeout(5):
                    result = await future
            finally:
                self.ui_requests.pop(token, None)
            if not result.get('accepted'):
                raise ValueError(result.get('error', 'Client refused the action'))
            if session != self.selected and (operation == 'inspect' or operation in settings_actions):
                raise ValueError('Client selection changed; no selected settings or naming action applied')
            if operation == 'inspect':
                result.update(connected=self.online, title=self.session.get('title'),
                              settings=self.settings_projection(), originalChanges=self.change_receipts())
                result['quotedSubmissions'] = [{'id': command, 'admission': row.get('admission'), 'execution': row.get('execution')}
                                              for command, row in list(self.messages.submissions().items())[-32:]
                                              if row['session'] == session]
                result['messageRequests'] = [{'id': command, 'operation': effect['operation'], 'status': effect['status']}
                                             for command, effect in list(self.store.data.get('messageEffects', {}).items())[-32:]
                                              if effect['session'] == session]
            if operation in settings_actions:
                payload = args.get('args', {})
                allowed = {'settings': set(), 'setting_choices': {'property'},
                           'setting_set': {'property', 'value'}, 'rename': {'title'},
                           'host_effects': set(), 'host_receipt': {'id'}}[operation]
                if not isinstance(payload, dict) or set(payload) != allowed:
                    raise ValueError('Exact selected settings or naming arguments required')
                if any(not isinstance(payload[field], str) for field in allowed - {'value'}):
                    raise ValueError('Selected setting, name and receipt identities must be text')
                if operation == 'host_receipt' and payload['id'] not in self.change_effects():
                    raise ValueError('Original settings or naming receipt unavailable in this conversation')
                ok, reason = await self.dispatch({'op': operation, 'session_id': session,
                                                 'request_id': token, **payload})
                if session != self.selected:
                    raise ValueError('Client selection changed; inspect the original change in its conversation')
                original = next(({'id': identity, **row} for identity, row in self.change_effects().items()
                                 if row.get('local_request') == token), None)
                result.update(accepted=ok, action=operation, result=reason,
                              settings=self.settings_projection(), originalChanges=self.change_receipts())
                if original:
                    result['original'] = original
                if operation == 'host_receipt':
                    result['original'] = {'id': payload['id'], **self.change_effects()[payload['id']]}
                if not ok:
                    value = {'success': False, 'pastTenseMessage': 'Selected change remains refused or unconfirmed',
                             'error': {'code': 'CLIENT_ACTION_FAILED', 'message': reason}, 'structuredContent': result}
                    receipts[key] = {'status': 'completed', 'result': value}
                    self.store.save()
                    return value
            if operation.startswith('message.') or operation.startswith('queue') or operation.startswith('steer'):
                if session != self.selected:
                    raise ValueError('Client selection changed; no message control applied')
                allowed = {'message_id', 'emoji', 'present', 'id'} if operation.startswith('message.') else {'id', 'text'}
                payload = args.get('args', {})
                if not isinstance(payload, dict) or not set(payload) <= allowed:
                    raise ValueError('Exact selected message arguments required')
                ok, reason = await self.dispatch({'op': operation, 'session_id': session,
                                                  'request_id': token, **payload})
                if not ok:
                    raise ValueError(reason)
                result = {**result, 'messageControl': operation, 'result': reason}
            value = {'success': True, 'pastTenseMessage': 'Observed the targeted terminal result',
                     'content': [{'type': 'text', 'text': json.dumps(result)}], 'structuredContent': result}
        except (OSError, ValueError, TimeoutError) as exc:
            value = {'success': False, 'pastTenseMessage': 'Client operation did not return success',
                     'error': {'code': 'CLIENT_ACTION_FAILED', 'message': str(exc) or 'Renderer response unavailable; effects may be unknown'}}
        receipts[key] = {'status': 'completed', 'result': value}
        self.store.save()
        return value

    async def open(self):
        await self.transport.open()
        self.actions = await self.transport.actions()
        if self.creation:
            self.creation_args = await self.transport.prepare_creation(self.creation)
        self.online = True
        if self.selected:
            await self.select(self.selected)
        else:
            self.session = {'id': None, 'messages': []}
            self.initial()
        self.opened = True

    def initial(self, preserve_draft=False):
        self.published_controls = None
        self.published_followups = None
        self.messages.preview_key = None
        self.published, self.published_order, self.published_title = {}, [], None
        self.send('snapshot', reset=not preserve_draft, connected=True, ready=True, navigation=True,
                  resume_picker=self.resume_picker,
                  durable=bool(self.selected), mode='UNIFIED', title=self.session.get('title') or 'Amplifier',
                  context=self.transport.url + ' · ' + (self.session.get('workspace') or self.workspace or 'Host workspace'),
                  draft=self.store.data['drafts'].get(self.selected or '', ''), items=self.items(),
                  system=['Connected to ' + self.transport.url,
                          'Exit detaches; work continues on Unified.',
                          'Recover this view with --client ' + self.store.identity,
                          'Unavailable host capabilities are shown explicitly.',
                          *self.transport.optional_unavailable.values()])
        self.resume_picker = False
        self.send('system', lines=['Host: ' + self.transport.url,
                  'Client: ' + self.store.identity,
                  'Stop uses Unified cancellation; graceful/force stages are not negotiated.',
                  'Use /deliveries to inspect uncertain input. Rich artifacts open in the web client.'],
                  commands=['/new', '/resume', '/rename', '/stop', '/deliveries', '/effects'], steer=False)
        self.publish_controls()
        # The connected protocol does not negotiate standalone mode controls.
        self.send('mode_status', supported=False)
        self.publish()

    def publish_controls(self):
        commands = ['/new', '/resume', '/rename', '/stop', '/deliveries', '/effects']
        if self.selected and 'conversation.queue.set' in self.actions:
            commands += ['/queue', '/pending']
        if self.steering_supported():
            commands.append('/steer')
        properties = self.session.get('config', {}).get('schema', {}).get('properties', {})
        if self.selected and any(prop.get('sessionMutable') is True and prop.get('enum') for prop in properties.values()):
            commands.append('/settings')
        lifecycle = getattr(self.transport, 'attached', {}).get('_meta', {}).get('amplifier.dev/sessionLifecycle', {})
        if self.selected and lifecycle.get('version') == 1 and lifecycle.get('method') == 'x-amplifier/sessionLifecycle' and lifecycle.get('deletion') == 'preserve-history':
            commands += ['/details', '/recovery', '/managed-files']
        if getattr(self.transport, 'supports', lambda _: False)('workspace.list'):
            commands.append('/workspaces')
        if self.published_controls != commands:
            self.send('commands', commands=commands, steer='/steer' in commands)
            self.published_controls = commands

    def settings_projection(self):
        config = self.session.get('config', {})
        return [{'id': key, 'label': prop.get('title') or key,
                 'current': config.get('values', {}).get(key),
                 'choices': [{'value': value, 'label': prop.get('enumLabels', [])[index]
                             if index < len(prop.get('enumLabels', [])) else str(value)}
                            for index, value in enumerate(prop['enum'])]}
                for key, prop in config.get('schema', {}).get('properties', {}).items()
                if prop.get('sessionMutable') is True and prop.get('enum')]

    def change_effects(self):
        effects = {**self.store.data.get('hostEffects', {}), **self.store.data.get('configEffects', {})}
        # Retain pre-existing naming outbox identities, including unknown records.
        effects.update({identity: row for identity, row in self.store.data['outbox'].items()
                        if row.get('action') == 'session.rename'})
        return {identity: row for identity, row in effects.items() if row.get('session') == self.selected
                and (row.get('operation') in {'session.configure', 'session.rename'}
                     or row.get('action') == 'session.rename')}

    def change_receipts(self):
        return [{'id': identity, 'operation': row.get('operation', row.get('action')), 'status': row['status']}
                for identity, row in list(self.change_effects().items())[-32:]]

    def settings_menu(self, property_id=None, notice=""):
        config = self.session.get('config', {})
        properties = config.get('schema', {}).get('properties', {})
        if property_id is None:
            rows = [{'id': row['id'], 'label': row['label'],
                     'current': next((choice['label'] for choice in row['choices'] if choice['value'] == row['current']), row['current'])}
                    for row in self.settings_projection()]
            uncertain = any(row.get('session') == self.selected and row.get('status') == 'unknown' for row in self.store.data.get('configEffects', {}).values())
            self.send('settings', properties=rows, uncertain=uncertain, notice=notice)
            return bool(rows), 'Choose a model or setting' if rows else 'This host has not provided changeable settings. Keep your draft and choose another conversation.'
        prop = properties.get(property_id, {})
        if prop.get('sessionMutable') is not True or not prop.get('enum'):
            return False, 'This setting cannot be changed here. Your draft is kept.'
        labels = prop.get('enumLabels', [])
        self.send('setting_choices', property=property_id, title=prop.get('title') or property_id,
                  current=config.get('values', {}).get(property_id), choices=[
                      {'value': value, 'label': labels[i] if i < len(labels) else str(value)}
                      for i, value in enumerate(prop['enum'])])
        return True, 'Choose an offered value; no message will be sent'

    async def configure(self, request, target):
        key, value = request.get('property'), request.get('value')
        config = self.session.get('config', {})
        prop = config.get('schema', {}).get('properties', {}).get(key, {})
        if not target or prop.get('sessionMutable') is not True or value not in prop.get('enum', []):
            return False, 'That choice is no longer available. Reopen Model and settings; your draft is kept.'
        effects = self.store.data.setdefault('configEffects', {})
        if len(effects) >= 512:
            return False, 'Saved setting receipts are full. Existing evidence and your draft are kept.'
        identity = str(uuid.uuid4())
        row = {'session': target, 'operation': 'session.configure', 'args': {'config': {key: value}},
               'status': 'unknown', 'local_request': request.get('request_id')}
        effects[identity] = row
        self.store.journal(identity, row)
        self.store.save()
        try:
            result = await self.transport.command(target, 'session.configure', row['args'], identity)
            if result.get('delivery') == 'unknown':
                raise ValueError('Original setting acknowledgement unavailable')
            if self.selected != target:
                raise ValueError('Selection changed while setting result was pending')
            snapshot = await self.transport.snapshot(target)
            self.reconcile(snapshot)
            observed = snapshot['session'].get('config', {}).get('values', {})
            if observed.get(key) != value:
                raise ValueError('Accepted echo has no matching setting readback')
            row.update(status='confirmed', observed=observed)
            message = 'Setting changed. Your draft is kept; no message was sent.'
            ok = True
        except Rejected as exc:
            row.update(status='refused', error=str(exc))
            message, ok = 'This host declined the setting change. Reopen Model and settings to choose an available value; your draft is kept.', False
        except (OSError, ValueError, TimeoutError) as exc:
            row['error'] = str(exc)
            message, ok = 'Setting change is not confirmed. Open Original receipts before making another change; your draft is kept.', False
        self.store.journal(identity, row)
        self.store.save()
        if self.selected == target:
            self.settings_menu(notice=message)
        return ok, message

    async def rename(self, request, target):
        title = request.get('title', request.get('text', ''))
        if self.deleted:
            return False, 'Conversation removed; use New or Resume to choose another'
        if not target or 'session.rename' not in self.actions:
            return False, 'Select a conversation with naming support; your draft is kept.'
        if not isinstance(title, str) or not title.strip() or len(title.encode()) > 2048:
            return False, 'Use a nonempty conversation name of at most 2048 bytes; your draft is kept.'
        effects = self.store.data.setdefault('hostEffects', {})
        if len(effects) >= 512:
            return False, 'Saved host-effect receipts are full. Existing evidence and your draft are kept.'
        identity = str(uuid.uuid4())
        row = {'session': target, 'operation': 'session.rename', 'args': {'title': title},
               'status': 'unknown', 'local_request': request.get('request_id')}
        effects[identity] = row
        self.store.journal(identity, row)
        self.store.save()
        try:
            result = await self.transport.command(target, 'session.rename', row['args'], identity)
            if result.get('delivery') == 'unknown':
                raise ValueError('Original naming acknowledgement unavailable')
            if self.selected != target:
                raise ValueError('Selection changed while naming result was pending')
            snapshot = await self.transport.snapshot(target)
            self.reconcile(snapshot)
            if snapshot['session'].get('title') != title:
                raise ValueError('Accepted echo has no matching name readback')
            row.update(status='confirmed', observedTitle=title)
            ok, message = True, 'Conversation named. Your draft is kept; no message was sent.'
        except Rejected as exc:
            row.update(status='refused', error=str(exc))
            ok, message = False, 'This host declined the name. Your draft is kept.'
        except (OSError, ValueError, TimeoutError) as exc:
            row['error'] = str(exc)
            ok, message = False, 'Naming change is not confirmed. Inspect Original receipts; your draft is kept.'
        self.store.journal(identity, row)
        self.store.save()
        return ok, message

    def items(self):
        items = self.messages.decorate(project(self.session, self.store.data['outbox']))
        pending = self.session.get('steeringMessage')
        pending_held = bool(pending and pending['message'].get('_meta', {}).get('amplifier.dev/steering', {}).get('held'))
        for identity, row in self.store.data['outbox'].items():
            if row['session'] == self.selected and row['action'] == 'conversation.steer.set':
                disposition = row.get('steeringDisposition', 'unconfirmed' if row['status'] == 'unknown' else 'refused' if row['status'] == 'failed' else 'pending')
                if disposition == 'pending' and pending_held and pending['id'] == identity:
                    disposition = 'held'
                items.append({'id': 'correction:' + identity, 'kind': 'correction', 'text': row['args']['text'],
                              'status': disposition, 'detail': 'Selected chat steering; host acceptance is not insertion proof'})
        if pending and not any(item['id'] == 'correction:' + pending['id'] for item in items):
            items.append({'id': 'correction:' + pending['id'], 'kind': 'correction', 'text': pending['message']['text'],
                          'status': 'held' if pending_held else 'pending', 'detail': 'Shared pending steering; host acceptance is not insertion proof'})
        return items

    def publish(self):
        self.messages.publish()
        items = self.items()
        current = {item['id']: item for item in items}
        order = list(current)
        if self.published_order == order[:len(self.published_order)] and set(self.published) <= set(current):
            changed = []
            for item in items:
                previous = self.published.get(item['id'])
                if previous == item:
                    continue
                if (previous and item.get('kind') in {'assistant', 'thinking'}
                        and item.get('status') == 'running'
                        and item.get('text', '').startswith(previous.get('text', ''))
                        and {k: v for k, v in item.items() if k != 'text'} == {k: v for k, v in previous.items() if k != 'text'}):
                    self.send('delta', id=item['id'], text=item['text'][len(previous.get('text', '')):])
                else:
                    changed.append(item)
            if changed or self.published_title != self.session.get('title', 'Amplifier'):
                self.send('remote_patch', items=changed, title=self.session.get('title', 'Amplifier'))
        else:
            self.send('remote_items', items=items, title=self.session.get('title', 'Amplifier'))
        self.published, self.published_order = current, order
        self.published_title = self.session.get('title', 'Amplifier')
        status = self.session.get('status', 'ready')
        ownership = self.session.get('ownership', {})
        blocked = ownership.get('status') in {'blocked', 'yielded', 'yielding', 'taking-over', 'yield-failed'}
        # Clear an earlier ownership block after the server reports acquisition.
        if blocked or getattr(self, '_blocked', False):
            self.send('ownership', status='blocked' if blocked else 'owned',
                      message=('In use by ' + ownership.get('source', 'another application')
                               + ' · Continue here requests takeover') if blocked else 'Connected')
        self._blocked = blocked
        pending = next((row for row in self.session.get('approvals', [])
                        if row.get('status') == 'pending'), None)
        approval = ({'id': pending['id'], 'prompt': pending.get('prompt', 'Approval requested'),
                     'options': pending.get('options') or ['allow', 'deny']} if pending else None)
        rows = [{'id': row['id'], 'text': row['message']['text'], 'state': 'queued',
                 'held': row['message'].get('_meta', {}).get('amplifier.dev/queue', {}).get('held') is True}
                for row in self.session.get('queuedMessages', [])]
        if rows != self.published_followups:
            self.send('followups', rows=rows, paused=False)
            self.published_followups = rows
        self.send('state', ready=self.online and not blocked and not self.deleted, busy=status in {'working', 'starting', 'stopping'},
                  status=('Disconnected · reconnecting; no input resent' if not self.online else
                          'Choose a conversation or send to start one' if not self.selected else
                          'Unified · ' + status), approval=approval,
                  cancellation='remote' if status == 'stopping' else '', turn_id=self.session.get('id', ''))

    def connection(self, online):
        if self.online != online:
            self.online = online
            self.publish()

    def reconcile(self, snapshot):
        if snapshot.get('protocolVersion') != 1:
            raise ValueError('Unsupported session snapshot version')
        if snapshot.get('deleted'):
            self.deleted = True
            self.send('state', ready=False, busy=False, status='Conversation removed on the host', approval=None)
            return
        session = snapshot.get('session')
        if not isinstance(session, dict) or session.get('id') != self.selected:
            raise ValueError('Snapshot targets a different conversation')
        instance, revision = snapshot.get('hostInstanceId'), snapshot.get('revision')
        if not isinstance(instance, str) or type(revision) is not int:
            raise ValueError('Missing snapshot identity/revision')
        if instance in self.retired_instances:
            return
        if instance == self.instance and revision < self.revision:
            return
        if self.instance and self.instance != instance:
            self.retired_instances.add(self.instance)
        self.instance, self.revision, self.session = instance, revision, session
        self.publish_controls()
        if self.messages.canonical_refresh_needed():
            self.later(self.messages.settled_refresh(self.selected))
        changed = False
        for message in session.get('messages', []):
            identity = message.get('inputId')
            if identity in self.store.data['outbox'] and message.get('delivery', {}).get('status') == 'accepted':
                self.messages.admission(identity, 'accepted')
                self.store.journal(identity, {**self.store.data['outbox'][identity], 'status': 'accepted'})
                del self.store.data['outbox'][identity]
                changed = True
        if changed:
            self.store.save()
        self.publish()

    async def watch(self, identity, generation):
        try:
            async for snapshot in self.transport.snapshots(identity, self.connection):
                if generation != self.generation:
                    return
                self.reconcile(snapshot)
        except (Rejected, ValueError, OSError) as exc:
            if generation == self.generation:
                self.online = False
                self.send('state', ready=False, busy=False, approval=None,
                          status=f'Connection unavailable: {exc}; no work resent')

    async def select(self, identity, *, preserve_draft=False):
        async with self.selection_lock:
            identity = await self.transport.resolve_session(identity, workspace=self.workspace)
            token = self.messages.begin_selection(identity)
            try:
                snapshot = await self.transport.snapshot(identity)
                if self.pump:
                    self.pump.cancel()
                    await asyncio.gather(self.pump, return_exceptions=True)
                self.generation += 1
                self.selected = identity
                self.deleted = False
                self.instance, self.revision = None, -1
                self.session = snapshot['session']
                self.store.data['session'] = identity
                self.store.save()
                self.online = True
                self.initial(preserve_draft=preserve_draft)
                self.reconcile(snapshot)
                self.messages.finish_selection(token, committed=True)
                self.pump = asyncio.create_task(self.watch(identity, self.generation))
            except BaseException:
                self.transport.selected = None
                raise
            finally:
                self.messages.finish_selection(token)

    async def host_review(self, purpose, target):
        if not target:
            return False, 'Select a conversation first'
        if purpose == 'managed-files':
            review = await self.transport.lifecycle(target, 'managedFiles.preview', {'protectSessionIds': []})
            if review.get('session') != target or review.get('preservesCanonical') is not True:
                raise ValueError('Managed review identity or preservation proof differs')
            operation = 'managedFiles.dispose'
            args = {key: review[key] for key in ('reviewId', 'reviewHash')}
            args.update(expectedHistoryRevision=review['historyRevision'], protectSessionIds=[])
            label = 'Dispose reviewed owned files — preserve canonical history'
        else:
            review = await self.transport.lifecycle(target, 'inspect')
            if review.get('session') != target:
                raise ValueError('Native inspection belongs to another conversation')
            if purpose == 'details':
                self.send('host_review', purpose=purpose, detail=json.dumps(review, indent=2), label='')
                return True, 'Selected native details; no model work started'
            capability = review.get('lifecycleCapabilities', {}).get('recoveryCopy', {})
            if capability.get('version') != 1:
                return False, 'Recovery copy is unavailable for the selected agent; original retained'
            operation = 'fork'
            args = {'expectedHistoryRevision': review['historyRevision'], 'mode': 'recovery'}
            label = 'Create independent recovery copy — never replay old work'
        token = str(uuid.uuid4())
        self.reviews = {token: {'session': target, 'operation': operation, 'args': args}}
        self.send('host_review', purpose=purpose, token=token, target=target, label=label,
                  detail=json.dumps(review, indent=2))
        return True, 'Review exact source and limits; Escape preserves the draft'

    async def apply_host_review(self, request, target):
        review = self.reviews.pop(request.get('token'), None)
        if not review or review['session'] != target or request.get('target') != target:
            return False, 'Review expired or selection changed; nothing executed'
        if len(self.store.data.get('hostEffects', {})) >= 512:
            return False, 'Local host-effect receipt capacity reached; existing evidence retained'
        command_id = str(uuid.uuid4())
        args = {**review['args'], 'commandId': command_id}
        effects = self.store.data.setdefault('hostEffects', {})
        row = {'session': target, 'operation': review['operation'], 'args': args, 'status': 'unknown'}
        effects[command_id] = row
        self.store.journal(command_id, row)
        self.store.save()  # Original request survives lost replies; never replayed.
        try:
            result = await self.transport.lifecycle(target, review['operation'], args)
            if row['operation'] == 'fork' and (result.get('creationConfirmed') is not True
                    or result.get('preservedSource') is not True or result.get('workReplayed') is not False
                    or not isinstance(result.get('uri'), str) or result.get('receipt', {}).get('commandId') != command_id):
                raise ValueError('Recovery result lacks exact preservation and command proof')
            row.update(status=result.get('status', 'reported'), result=result)
            self.store.journal(command_id, row)
            self.store.save()
            self.send('host_review', purpose='result', detail=json.dumps(result, indent=2), label='',
                      open_target=result.get('uri') if row['operation'] == 'fork' else None)
            return result.get('status') != 'unknown', 'Host returned the reviewed operation; /effects inspects its original receipt'
        except (OSError, ValueError, TimeoutError) as exc:
            row['error'] = str(exc)
            self.store.save()
            return False, ('History is still updating, so the recovery copy could not be created. Keep this conversation and inspect Original receipts before trying again.' if 'Indexed family coverage' in str(exc) else 'This change is not confirmed. Open Original receipts before trying again; your draft is kept.')

    def steering_supported(self):
        capability = self.session.get('agentCapabilities', {}).get('_meta', {}).get('amplifier.dev/native', {}).get('activeSteering', {})
        return (bool(self.selected) and 'conversation.steer.set' in self.actions
                and capability.get('version') == 1 and capability.get('mode') == 'request_boundary')

    async def queue_change(self, request, target):
        steering = request['op'].startswith('steer')
        prefix = 'conversation.steer.' if steering else 'conversation.queue.'
        if not target or not self.online or prefix + 'set' not in self.actions or steering and not self.steering_supported():
            return False, 'Select a connected conversation whose host advertises follow-ups'
        op = request['op']
        if op == 'steer' and request.get('id') is not None and request['id'] != target:
            return False, 'Steering prompt belongs to another conversation; text retained, nothing sent'
        if op in {'queue_inspect', 'steer_inspect'}:
            await self.transport.rpc('refreshChat', session=target)
            if self.selected != target:
                return False, 'Conversation changed; nothing queued'
            self.reconcile(await self.transport.snapshot(target))
            return True, 'Shared pending follow-ups refreshed; no input replayed'
        if op not in {'queue', 'queue_edit', 'queue_remove', 'queue_run', 'steer', 'steer_remove'}:
            return False, 'Global pause/run is unavailable; resume a selected held follow-up'
        rows = ([self.session['steeringMessage']] if self.session.get('steeringMessage') else []) if steering else self.session.get('queuedMessages', [])
        pending_id = request.get('id')
        existing = next((row for row in rows if row['id'] == pending_id), None)
        if op not in {'queue', 'steer'} and existing is None:
            return False, 'Follow-up changed or already started; refresh before changing it'
        if op in {'queue', 'steer'} and (self.messages.quote() or request.get('image_id')):
            return False, 'Queued quotes and attachments are unavailable; your draft and quote are kept'
        if any(row['session'] == target and row['action'].startswith(prefix)
               and row['status'] in {'sending', 'unknown'} and row.get('receiptLookup', {}).get('status') not in {'completed', 'failed'} and (op in {'queue', 'steer'} or row['args'].get('id') == pending_id)
               for row in self.store.data['outbox'].values()):
            return False, 'An original queue change is unconfirmed; inspect Deliveries without replay'
        text = existing['message']['text'] if op == 'queue_run' else request.get('text', '')
        if op not in {'queue_remove', 'steer_remove'} and (not isinstance(text, str) or not text.strip() or len(text.encode()) > 65536 or steering and len(text.encode('utf-16-le')) // 2 > 16000):
            return False, 'Write bounded follow-up text; existing intent is kept'
        if len(self.store.data['outbox']) >= 512:
            return False, 'Original delivery records are full; existing intent is kept'
        command_id = str(uuid.uuid4())
        pending_id = command_id if op in {'queue', 'steer'} else pending_id
        action = prefix + ('remove' if op in {'queue_remove', 'steer_remove'} else 'set')
        args = {'id': pending_id, **({'text': text} if op not in {'queue_remove', 'steer_remove'} else {})}
        row = {'session': target, 'chat': self.session['chat'], 'action': action, 'args': args, 'status': 'sending',
               'local_request': request['request_id'], 'generation': self.generation}
        self.store.data['outbox'][command_id] = row
        ok, reason = await self.deliver(command_id, row)
        if ok:
            if op == 'steer_remove':
                for original, intent in self.store.data['outbox'].items():
                    if intent['session'] == target and intent['action'] == 'conversation.steer.set' and intent['args']['id'] == pending_id:
                        intent['steeringDisposition'] = 'withdrawn'
                        self.store.journal(original, intent)
                self.store.save()
                self.publish()
            if op == 'queue' and self.store.data['drafts'].get(target) == text:
                self.store.draft(target, '')
            return True, 'Host acknowledged steering for this chat/current-or-next turn; insertion is not confirmed' if steering else 'Host saved the queue change; execution remains separate'
        return False, reason

    async def dispatch(self, request):
        op = request.get('op')
        if op == 'client_ui_reply':
            pending = self.ui_requests.get(request.get('token'))
            if pending and not pending.done():
                pending.set_result(request.get('result', {}))
            return True, 'Renderer observation received'
        target = request.get('session_id') or None
        if target != self.selected:
            return False, 'This control belongs to another conversation; nothing sent'
        if op.startswith('queue') or op in {'steer', 'steer_remove', 'steer_inspect'}:
            try:
                return await self.queue_change(request, target)
            except (Rejected, OSError, ValueError, TimeoutError) as exc:
                return False, str(exc) or 'Queue change unavailable; original intent kept'
        if op in {'draft', 'editor_draft'}:
            self.store.draft(target, request.get('text', ''))
            return True, 'Draft saved locally'
        if op in {'message.reply', 'message.replyClear', 'message.read', 'message.reaction', 'message.receipt', 'message.refresh', 'message.submissionInspect'}:
            try:
                if op == 'message.reply':
                    self.messages.select_quote(request.get('message_id'))
                    return True, 'Quote selected privately. Write your reply and Send when ready.'
                if op == 'message.replyClear':
                    self.messages.clear_quote()
                    return True, 'Quote removed. Your message text is kept.'
                if op == 'message.submissionInspect':
                    self.messages.inspect_submission(request.get('id'))
                    return True, 'Original quoted submission inspected privately. Nothing was repeated.'
                if not self.online:
                    return False, 'Reconnect before inspecting shared messages; your draft is kept.'
                if op == 'message.refresh':
                    await self.messages.refresh(target)
                    return True, 'Saved message references refreshed. No message was sent.'
                if op == 'message.read':
                    await self.messages.read(request.get('message_id'))
                    return True, 'Shared reactions inspected. No message was sent.'
                if op == 'message.receipt':
                    return await self.messages.recover(request.get('id'))
                return await self.messages.react(request.get('message_id'), request.get('emoji'), request.get('present'))
            except (Rejected, OSError, ValueError, TimeoutError) as exc:
                return False, str(exc) or 'Message control unavailable. Your draft is kept.'
        if op in {'settings', 'setting_choices', 'setting_set'}:
            if not self.online:
                return False, 'Reconnect before changing settings; your draft is kept.'
            if op == 'setting_set':
                return await self.configure(request, target)
            if target:
                try:
                    await self.transport.rpc('refreshSession', session=target)
                    if self.selected != target:
                        return False, 'Conversation changed. Reopen Model and settings; your draft is kept.'
                    self.reconcile(await self.transport.snapshot(target))
                except (Rejected, OSError, ValueError, TimeoutError):
                    return False, 'Settings could not be loaded. Reconnect and open Model and settings again; your draft is kept.'
            return self.settings_menu(request.get('property') if op == 'setting_choices' else None)
        if op in {'host_review', 'host_apply', 'host_effects', 'host_receipt'}:
            local_change = self.change_effects().get(request.get('id')) if op == 'host_receipt' else None
            if not self.online and op != 'host_effects' and not local_change:
                return False, 'Disconnected; optional read unavailable; draft and original receipts retained'
            try:
                if op == 'host_review':
                    if request.get('purpose') not in {'details', 'recovery', 'managed-files'}:
                        return False, 'Unknown review action'
                    return await self.host_review(request['purpose'], target)
                if op == 'host_apply':
                    return await self.apply_host_review(request, target)
                effects = {**self.store.data.get('hostEffects', {}), **self.store.data.get('configEffects', {}), **self.messages.effects()}
                effects.update(self.change_effects())
                if op == 'host_effects':
                    self.send('host_effects', entries=[{'id': key, **row} for key, row in effects.items()
                                                      if row['session'] == target])
                    return True, 'Original host effect receipts; nothing resubmitted'
                row = effects.get(request.get('id'))
                if not row or row['session'] != target:
                    return False, 'Receipt target differs'
                operation_name = row.get('operation', row.get('action'))
                if operation_name == 'message.reaction':
                    self.send('host_review', purpose='receipt', detail=json.dumps({'original': row, 'limits': 'Only the original message receipt can settle an unknown reaction. Current counts cannot prove it; nothing was repeated.'}, indent=2), label='')
                    return await self.messages.recover(request['id'])
                if operation_name in {'session.configure', 'session.rename'}:
                    self.send('host_review', purpose='receipt', detail=json.dumps({'commandId': request['id'], 'original': row,
                              'currentObservedValues': self.session.get('config', {}).get('values', {}),
                              'currentObservedTitle': self.session.get('title'),
                              'limits': 'Current values or title do not prove the outcome of an unknown request. The standard action uses its original echo; this local command ID is not a remote receipt ID. Nothing was resent.'}, indent=2), label='')
                    return True, 'Original change receipt inspected. Nothing was resent.'
                self.send('host_review', purpose='receipt', detail=json.dumps({'original': row, 'limits': 'Saved original evidence; lookup does not resend the change.'}, indent=2), label='')
                operation = 'managedFiles.receipt' if row['operation'] == 'managedFiles.dispose' else 'receipt'
                result = await self.transport.lifecycle(target, operation, {'commandId': request['id']})
                row['receiptLookup'] = result
                self.store.journal(request['id'], row)
                self.store.save()
                self.send('host_review', purpose='receipt', detail=json.dumps({'original': row, 'hostReceipt': result}, indent=2), label='',
                          open_target=(result or {}).get('result', {}).get('uri') if row['operation'] == 'fork' else None)
                return True, 'Original receipt inspected; no mutation replay'
            except (OSError, ValueError, TimeoutError, KeyError):
                return False, 'This action is not available right now. Keep your draft and use Original receipts to inspect a previous change.'
        if op == 'deliveries':
            originals = [{'id': key, **row} for key, row in self.messages.submissions().items() if row['session'] == target][-8:]
            self.send('deliveries', entries=[{'id': key, **row} for key, row in self.store.data['outbox'].items()
                                             if row.get('session') == target and key not in self.messages.submissions()] + originals)
            return True, 'Pending delivery; inspect receipts without resubmitting'
        if op == 'edit_delivery':
            row = self.store.data['outbox'].get(request.get('id'))
            if not row or row.get('session') != target or row['status'] != 'failed':
                return False, 'Only definitively rejected input can be edited; unknown input is retained'
            self.send('delivery_draft', text=row['args'].get('text', ''))
            row['status'] = 'edited'
            self.store.draft(target, row['args'].get('text', ''))
            self.store.save()
            self.publish()
            return True, 'Unsent text copied to composer; nothing submitted'
        if not self.online:
            return False, 'Disconnected; draft retained. Wait for reconnect before sending'
        if op == 'rename':
            return await self.rename(request, target)
        if op == 'workspaces':
            page = await self.transport.workspaces(offset=request.get('offset', 0), query=request.get('query', ''))
            self.workspace_choices = {row['id']: row for row in page['items']}
            self.send('workspaces', items=page['items'], next_offset=page.get('nextOffset'),
                      query=request.get('query', ''), coverage=page.get('coverage'))
            return True, 'Bounded existing-workspace page; no agent started'
        if op == 'workspace_select':
            workspace = self.workspace_choices.get(request.get('id'))
            if not workspace or not workspace.get('available') or workspace.get('path') != request.get('path'):
                return False, 'Workspace choice changed or unavailable; reopen Workspaces'
            self.store.draft(target, request.get('draft', ''))
            self.workspace = workspace['path']
            self.store.data['workspace'] = self.workspace
            result = await self.dispatch({**request, 'op': 'switch', 'target': 'new'})
            return result
        if op == 'conversations':
            page = await self.transport.sessions(offset=request.get('offset', 0), workspace=self.workspace,
                                                 query=request.get('query', ''))
            query = request.get('query', '').casefold()
            rows = [{'id': row['id'], 'title': row.get('title', 'Untitled'), 'cwd': row.get('workspace', ''),
                     'status': row.get('status', '')} for row in page['items']
                    if page.get('scopedSearch') or not query or query in ' '.join(str(row.get(key) or '') for key in
                        ('title', 'id', 'nativeIdentity', 'runtimeSessionId')).casefold()]
            self.send('conversations', request_id=request['request_id'], sessions=rows,
                      offset=request.get('offset', 0), page_size=50, next_offset=page.get('nextOffset'),
                      truncated=page.get('nextOffset') is not None, query=request.get('query', ''),
                      partial=bool(query and page.get('nextOffset') and not page.get('scopedSearch')),
                      scope=('Host-filtered root sessions · existing selected workspace' if page.get('scopedSearch')
                             else 'Standard host catalog · local workspace/title/ID filter on this page; child status unverified'))
            return True, 'Conversations loaded'
        if op == 'switch':
            async with self.switch_lock:
                if target != self.selected:
                    return False, 'Selection changed; nothing opened'
                self.store.draft(target, request.get('draft', ''))
                if request.get('target') == 'new':
                    await self.transport.detach()
                    self.selected = None
                    self.deleted = False
                    self.session = {'id': None, 'messages': []}
                    self.store.data['session'] = None
                    self.store.save()
                    self.generation += 1
                    if self.pump:
                        self.pump.cancel()
                        await asyncio.gather(self.pump, return_exceptions=True)
                    self.initial()
                else:
                    await self.select(request['target'])
            self.send('switch_result', request_id=request['request_id'], ok=True)
            return True, 'Conversation opened'
        if op == 'inspect':
            self.send('inspection', request_id=request['request_id'], category=request.get('category'),
                      rows=[], partial=True, scope='Inspect full runtime details in the Unified web client; no local runtime is mounted.')
            return True, 'Host inspection boundary'
        if op == 'history_page':
            offset = request.get('offset', 0)
            if type(offset) is not int or not 0 <= offset <= 1000000:
                return False, 'Invalid history offset'
            try:
                async with asyncio.timeout(15):
                    while len(project(self.session, {}, live=False)) < offset + 100 and self.session.get('sharedHistoryOffset', 0):
                        before = self.session.get('historyCursor', self.session['sharedHistoryOffset'])
                        await self.transport.command(target, 'session.history', {'before': before, 'limit': 100}, str(uuid.uuid4()))
                        while self.selected == target and self.session.get('historyCursor', self.session.get('sharedHistoryOffset')) == before:
                            self.reconcile(await self.transport.snapshot(target))
                            if self.session.get('historyError'):
                                raise ValueError(self.session['historyError'])
                            await asyncio.sleep(.05)
                if target != self.selected:
                    return False, 'Selection changed; earlier history was not opened'
                history = project(self.session, {}, live=False)
                end = max(0, len(history) - offset)
                start = max(0, end - 100)
                remaining = self.session.get('sharedHistoryOffset', 0)
                rows = history[start:end]
                self.send('history_page', request_id=request['request_id'], items=rows, offset=offset,
                          next_offset=offset + 100 if start or remaining else None,
                          previous_offset=max(0, offset - 100) if offset else None,
                          start=remaining + start + 1 if rows else 0, end=remaining + end,
                          total=remaining + len(history), scope='Host timeline; read only; earlier activity depends on host retention')
                return True, 'History loaded'
            except (OSError, ValueError, Rejected, TimeoutError) as exc:
                self.send('history_page', request_id=request['request_id'], error=str(exc) or 'History is still unavailable; retry explicitly')
                return False, 'Earlier history unavailable; current conversation retained'
        if op == 'cancel_switch':
            return False, 'Opening completes independently; choose another conversation afterwards'
        if self.deleted:
            return False, 'Conversation removed; use New or Resume to choose another'
        if op not in {'submit', 'stop', 'decision', 'continue_here', 'retry_delivery'}:
            return False, 'This action is not available in this conversation. Your draft is kept; check the available Actions.'
        async with self.submission_lock if op == 'submit' and target is None else _Unlocked():
            if op == 'submit' and target != self.selected:
                return False, 'Selection changed; text retained, nothing sent'
            # Capture the request target, never the possibly newer selected conversation.
            if op == 'retry_delivery':
                identity = request.get('id')
                row = self.store.data['outbox'].get(identity)
                if not row or row.get('session') != target or (row['status'] not in {'unknown', 'failed'} and row['action'] != 'conversation.steer.set'):
                    return False, 'Delivery changed; inspect it again'
            else:
                action, args = {
                    'submit': ('conversation.send', {'text': request.get('text', '')}),
                    'stop': ('conversation.stop', {}),
                    'decision': ('approval.respond', {'id': request.get('approval_id'), 'decision': request.get('option')}),
                    'continue_here': ('session.takeover', {}),
                }[op]
                if action not in self.actions:
                    return False, 'This host does not offer that action'
                if op == 'submit' and not args['text'].strip():
                    return False, 'Write a message first'
                if op == 'submit':
                    try:
                        quote = self.messages.prepare()
                        if quote and len(self.messages.submissions()) >= 512:
                            raise ValueError('Original quoted submissions are full. Your draft and quote are retained.')
                    except ValueError as exc:
                        return False, str(exc)
                    if quote:
                        args['reply'] = quote['reference']
                        args['replyId'] = quote['id']
                if request.get('image_id'):
                    return False, 'Connected image upload is not available; use the web client'
                if len(self.store.data['outbox']) >= 512:
                    return False, 'Local delivery capacity reached; all original intents retained'
                identity = str(uuid.uuid4())
                row = {'session': target, 'action': action, 'args': args, 'status': 'sending',
                       'local_request': request['request_id'], 'generation': self.generation}
                if op == 'submit' and quote:
                    row['quote'] = quote
                if target is None:
                    if op != 'submit':
                        return False, 'Select a conversation first'
                    row['create_id'] = str(uuid.uuid4())
                    row['creation'] = {'workspace': self.workspace, **self.creation_args}
                self.store.data['outbox'][identity] = row
            if op == 'retry_delivery':
                if row['action'] == 'session.rename':
                    return await self.dispatch({**request, 'op': 'host_receipt'})
                if row['action'].startswith(('conversation.queue.', 'conversation.steer.')) and row['args'].get('id') != identity:
                    return False, 'Original pending change remains unconfirmed; no separate mutation receipt was sent. Current shared state is not proof; original intent kept, nothing resubmitted.'
                await self.refresh_delivery(row)
                if row['session']:
                    try:
                        receipt = await self.transport.receipt(row['session'], identity)
                    except (Rejected, OSError, ValueError, TimeoutError) as exc:
                        return False, 'Receipt unavailable: ' + str(exc) + '; nothing resubmitted'
                    if row['action'] == 'conversation.steer.set':
                        if not isinstance(receipt, dict) or receipt.get('commandId') != identity or receipt.get('channel') != row.get('chat'):
                            return False, 'Receipt identity changed; original steering kept'
                        row['receiptLookup'] = receipt
                        disposition = {'completed': 'applied', 'failed': 'held'}.get(receipt.get('status'))
                        row['steeringDisposition'] = (disposition if disposition and str(receipt.get('detail', '')).startswith('steering:' + disposition + ':')
                                                      else 'pending' if receipt.get('status') in {'admitted', 'dispatching'} else 'unconfirmed')
                        self.store.journal(identity, row)
                        self.store.save()
                        self.publish()
                        return True, 'Steering receipt: ' + str(receipt) + '; nothing resubmitted'
                    return False, 'Receipt: ' + str(receipt) + '; nothing resubmitted'
                try:
                    receipt = await self.transport.creation_receipt(row['create_id'], row.get('creation', {}).get('managed', False))
                    return False, 'Creation receipt: ' + str(receipt) + '; original input remains unsent'
                except (OSError, ValueError, TimeoutError) as exc:
                    return False, 'Creation receipt unavailable: ' + str(exc) + '; nothing resubmitted'
            return await self.deliver(identity, row)

    async def deliver(self, identity, row):
        row['status'] = 'sending'
        self.messages.retain_submission(identity, row)
        self.store.journal(identity, row)
        self.store.save()  # Durable intent before the first request, including session creation.
        if row['action'] == 'conversation.send' and row['session'] == self.selected and row['args'].get('replyId'):
            self.messages.clear_quote(row['args']['replyId'])
        self.publish()
        if row['action'] == 'conversation.send' and row.get('generation') == self.generation:
            self.send('input_pending', request_id=row.get('local_request'), text=row['args']['text'])
            if self.store.data['drafts'].get(row['session'] or '') == row['args']['text']:
                self.store.draft(row['session'], '')
        acknowledged = False
        try:
            if row['session'] is None:
                created = await self.transport.command(None, 'session.create',
                    row.get('creation', {'workspace': self.workspace}), row['create_id'])
                state = created.get('state', {})
                new_id = created.get('result', {}).get('sessionId') or state.get('selectedSessionId')
                if not new_id:
                    raise ValueError('Creation outcome unknown; retain this request for exact retry')
                row['session'] = new_id
                self.store.save()
                if self.selected is None and row.get('generation') == self.generation:
                    self.store.data['drafts'][new_id] = self.store.data['drafts'].pop('', '')
                    await self.select(new_id, preserve_draft=True)
            result = await self.transport.command(row['session'], row['action'], row['args'], identity)
            uncertain = result.get('delivery') == 'unknown'
            acknowledged = not uncertain
            self.messages.admission(identity, 'unconfirmed' if uncertain else 'accepted')
            # A concurrent snapshot may already have acknowledged and removed this entry.
            if identity in self.store.data['outbox']:
                row['status'] = 'unknown' if uncertain else 'accepted'
                if uncertain:
                    row['error'] = 'Unified saved this request, but execution is unconfirmed.'
                else:
                    row.pop('error', None)
                if not uncertain and row['action'] not in {'conversation.send', 'conversation.steer.set'}:
                    self.store.journal(identity, row)
                    del self.store.data['outbox'][identity]
                self.store.save()
            if result.get('session', {}).get('id') == self.selected:
                self.reconcile(result)
            if uncertain and identity in self.store.data['outbox']:
                self.publish()
                return False, 'Execution unconfirmed · /deliveries retains the original request'
            return True, 'Accepted by Unified; execution outcome is separate'
        except Rejected as exc:
            if identity not in self.store.data['outbox']:
                return True, 'Acceptance confirmed by the conversation stream'
            row['status'] = 'failed' if 400 <= exc.status < 500 and exc.status != 408 else 'unknown'
            row['error'] = str(exc)
            self.messages.admission(identity, 'refused' if row['status'] == 'failed' else 'unconfirmed')
            self.store.save()
            self.publish()
            await self.refresh_delivery(row)
            if identity not in self.store.data['outbox']:
                return True, 'Acceptance confirmed by the conversation'
            self.publish()
            return False, str(exc) + ' · /deliveries retains this request'
        except (OSError, ValueError, TimeoutError) as exc:
            if identity not in self.store.data['outbox']:
                return True, 'Acceptance confirmed by the conversation stream'
            if acknowledged:
                self.publish()
                return True, 'Accepted by Unified; live view could not refresh'
            row['status'], row['error'] = 'unknown', (
                'The response could not be verified.' if isinstance(exc, ValueError)
                else 'The connection ended before delivery was confirmed.')
            self.store.save()
            self.publish()
            await self.refresh_delivery(row)
            if identity not in self.store.data['outbox']:
                return True, 'Acceptance confirmed by the conversation'
            self.publish()
            return False, 'Delivery unknown · /deliveries to inspect; nothing resubmitted'

    async def refresh_delivery(self, row):
        identity, generation = self.selected, self.generation
        if not identity or row['session'] != identity:
            return
        try:
            async with asyncio.timeout(5):
                snapshot = await self.transport.snapshot(identity)
            if identity == self.selected and generation == self.generation:
                self.reconcile(snapshot)
        except (OSError, ValueError, Rejected, TimeoutError):
            pass  # Failed observation cannot authorize another command.

    async def close(self):
        if self.pump:
            self.pump.cancel()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, *([self.pump] if self.pump else []), return_exceptions=True)
        await self.transport.close()
        self.store.close()  # Never sends Stop or releases the host's execution lock.


class _Unlocked:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

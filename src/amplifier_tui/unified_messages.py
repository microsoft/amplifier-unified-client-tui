"""Private quotes and negotiated, account-bound canonical message reactions."""
import json
import uuid
from copy import deepcopy

from .unified_transport import Rejected

EMOJI = ['👍', '❤️', '😂', '🎉', '😮', '😢', '👎', '✅']


def reference(value, *, reaction=False):
    if not isinstance(value, dict) or not {'messageId', 'position', 'historyEpoch', 'sourceDigest'} <= value.keys():
        return None
    message = value.get('messageId')
    epoch, digest = value.get('historyEpoch'), value.get('sourceDigest')
    if (not isinstance(message, str) or not 0 < len(message) <= 200
            or message.startswith('archive:') or type(value.get('position')) is not int
            or value['position'] < 0 or not (epoch is None or isinstance(epoch, str) and 0 < len(epoch) <= 200)
            or not isinstance(digest, str) or len(digest) != 64
            or any(c not in '0123456789abcdef' for c in digest)):
        return None
    result = {key: value[key] for key in ('messageId', 'position', 'historyEpoch', 'sourceDigest')}
    if reaction:
        native = value.get('sessionId')
        if not isinstance(native, str) or not 0 < len(native) <= 200:
            return None
        result['sessionId'] = native
    return result


def reaction_row(value):
    if (not isinstance(value, dict) or not isinstance(value.get('sessionId'), str)
            or not isinstance(value.get('messageId'), str) or type(value.get('revision')) is not int
            or value['revision'] < 0 or not isinstance(value.get('counts'), dict)):
        raise ValueError('The reaction response could not be verified')
    reactions, mine, counts = value.get('reactions'), value.get('mine'), value['counts']
    if (not isinstance(reactions, list) or not isinstance(mine, list) or len(reactions) > 8
            or len(mine) > 8 or any(emoji not in EMOJI for emoji in reactions + mine)
            or len(set(reactions)) != len(reactions) or len(set(mine)) != len(mine)
            or any(emoji not in reactions for emoji in mine) or set(counts) != set(reactions)
            or any(type(n) is not int or n < 1 for n in counts.values())):
        raise ValueError('The reaction response could not be verified')
    return deepcopy({key: value[key] for key in ('sessionId', 'messageId', 'revision', 'reactions', 'mine', 'counts')})


class Messages:
    def __init__(self, bridge):
        self.bridge = bridge
        self.rows = {}
        self.running = set()
        self.markers = {}
        self.refreshing = set()
        self.preview_key = None
        self.descriptors = {}

    def quote_supported(self):
        descriptor = self.descriptors.get(self.bridge.selected)
        if descriptor and self.reactions_supported():
            quote = descriptor.get('quote', {})
            return (descriptor.get('available') is True and quote.get('available') is True
                    and quote.get('referenceMeta') == 'amplifier.dev/history.messageReference' and quote.get('maxChars') == 4000)
        capabilities = self.bridge.session.get('agentCapabilities')
        meta = capabilities.get('_meta') if isinstance(capabilities, dict) else None
        native = meta.get('amplifier.dev/native') if isinstance(meta, dict) else None
        marker = native.get('messageInteractions') if isinstance(native, dict) else None
        if not isinstance(marker, dict):
            return False
        return (marker.get('version') == 1 and marker.get('quoteMeta') == 'amplifier.dev/messageReply'
                and marker.get('privateReplySelection') is True and marker.get('maxQuoteChars') == 4000)

    def reactions_supported(self):
        supports = getattr(self.bridge.transport, 'supports', lambda _: False)
        return all(supports(name) for name in ('message.read', 'message.reaction', 'message.receipt'))

    def message(self, identity):
        for row in self.bridge.session.get('messages', []):
            if row['id'] == identity and row.get('role') in {'user', 'assistant'} and not row.get('historicalOnly'):
                return row
        raise ValueError('This saved message is unavailable. Keep your draft and refresh saved messages.')

    def quote(self):
        quotes = self.bridge.store.data.get('quotes', {})
        if not isinstance(quotes, dict):
            raise ValueError('Saved quotes could not be read. Original storage was preserved.')
        quote = quotes.get(self.bridge.selected)
        if quote is not None and (not isinstance(quote, dict) or quote.get('sessionId') != self.bridge.selected
                or not reference(quote.get('reference')) or not isinstance(quote.get('excerpt'), str)
                or len(quote['excerpt']) > 4000 or not isinstance(quote.get('id'), str)):
            raise ValueError('The saved quote could not be read. Its original private record was preserved.')
        return deepcopy(quote)

    def publish(self):
        try:
            quote, error = self.quote(), ''
        except ValueError as exc:
            quote, error = None, str(exc)
        key = (self.bridge.selected, quote and quote['id'], self.quote_supported(), self.reactions_supported(), error)
        if self.preview_key != key:
            self.preview_key = key
            self.bridge.send('message_controls', quote_available=self.quote_supported(), reactions_available=self.reactions_supported(), quote=quote, error=error)

    def effects(self):
        effects = self.bridge.store.data.get('messageEffects', {})
        if not isinstance(effects, dict):
            raise ValueError('Saved reaction evidence could not be read. Original storage was preserved.')
        for command, effect in effects.items():
            args = effect.get('args') if isinstance(effect, dict) else None
            if (not isinstance(command, str) or not 0 < len(command) <= 256
                    or not isinstance(effect, dict) or not isinstance(effect.get('session'), str)
                    or effect.get('operation') != 'message.reaction'
                    or effect.get('status') not in {'unknown', 'confirmed', 'refused'}
                    or not isinstance(args, dict) or set(args) != {'reference', 'emoji', 'present'}
                    or not reference(args.get('reference'), reaction=True)
                    or args.get('emoji') not in EMOJI or type(args.get('present')) is not bool):
                raise ValueError('Saved reaction evidence could not be verified. Original storage was preserved.')
        return effects

    def submissions(self):
        rows = self.bridge.store.data.get('quotedSubmissions', {})
        if not isinstance(rows, dict):
            raise ValueError('Original quoted submissions could not be read. Private storage was preserved.')
        for command, row in rows.items():
            args = row.get('args') if isinstance(row, dict) else None
            quote = row.get('quote') if isinstance(row, dict) else None
            if (not isinstance(command, str) or not 0 < len(command) <= 256
                    or not isinstance(row, dict) or not isinstance(row.get('session'), str)
                    or row.get('action') != 'conversation.send' or row.get('quotedSubmission') is not True
                    or row.get('admission') not in {'accepted', 'unconfirmed', 'refused'}
                    or row.get('execution') != 'unverified'
                    or not isinstance(args, dict) or not isinstance(args.get('text'), str)
                    or not isinstance(quote, dict) or quote.get('sessionId') != row['session']
                    or not isinstance(quote.get('id'), str) or not 0 < len(quote['id']) <= 256
                    or quote.get('role') not in {'user', 'assistant'} or args.get('replyId') != quote['id']
                    or not reference(quote.get('reference')) or args.get('reply') != quote['reference']
                    or not isinstance(quote.get('excerpt'), str) or len(quote['excerpt']) > 4000):
                raise ValueError('Original quoted submission could not be verified. Private storage was preserved.')
        return rows

    def retain_submission(self, command, row):
        quote = row.get('quote')
        if quote is None:
            return
        rows = self.submissions()
        if command in rows:
            return
        if len(rows) >= 512:
            raise ValueError('Original quoted submissions are full. Your draft and quote are retained.')
        original = {'session': row['session'], 'action': row['action'],
                    'args': deepcopy(row['args']), 'quote': deepcopy(quote),
                    'admission': 'unconfirmed', 'execution': 'unverified',
                    'status': 'unknown', 'quotedSubmission': True}
        self.bridge.store.data.setdefault('quotedSubmissions', rows)[command] = original
        self.bridge.store.journal(command, original)

    def admission(self, command, status):
        rows = self.bridge.store.data.get('quotedSubmissions', {})
        if not isinstance(rows, dict) or command not in rows:
            return False
        row = self.submissions().get(command)
        if row and row.get('admission') != 'accepted' and row.get('admission') != status:
            row['admission'] = status
            self.bridge.store.journal(command, row)
            return True
        return False

    def inspect_submission(self, command):
        row = self.submissions().get(command)
        if not row or row['session'] != self.bridge.selected:
            raise ValueError('Select the original conversation before inspecting this quoted submission')
        self.bridge.send('host_review', purpose='quoted-original', label='', detail=json.dumps({
            'commandId': command, 'original': row,
            'limits': 'Host admission does not prove native execution. This is the frozen private submission. Inspection and copying never repeat it or replace a newer draft or quote.'}, ensure_ascii=False))

    def select_quote(self, identity):
        self.quote()
        if not self.quote_supported():
            raise ValueError('Quoted replies are not available here. Your draft is kept.')
        row = self.message(identity)
        locator = reference(row.get('messageReference'))
        if not locator or not row.get('text', '').strip():
            raise ValueError('This message has no saved quote reference yet. Refresh saved messages; your draft is kept.')
        source = ''.join(part.get('text', '') for part in self.bridge.session['messages']
                         if reference(part.get('messageReference')) == locator and part.get('role') == row['role'])
        quote = {'id': str(uuid.uuid4()), 'sessionId': self.bridge.selected, 'messageId': identity,
                 'reference': locator, 'role': row['role'], 'excerpt': source[:4000], 'truncated': len(source) > 4000}
        self.bridge.store.data.setdefault('quotes', {})[self.bridge.selected] = quote
        self.bridge.store.save()
        self.publish()

    def clear_quote(self, identity=None):
        quote = self.quote()
        if quote and (identity is None or quote['id'] == identity):
            del self.bridge.store.data['quotes'][self.bridge.selected]
            self.bridge.store.save()
        self.publish()

    def prepare(self):
        quote = self.quote()
        if quote and not self.quote_supported():
            raise ValueError('Quoted replies are unavailable here. Your draft and quote are kept.')
        return quote

    def canonical_refresh_needed(self):
        b = self.bridge
        marker = b.session.get('lastSettledTurnId')
        if (b.selected and self.quote_supported() and not b.session.get('activeTurnId')
                and isinstance(marker, str) and 0 < len(marker) <= 512
                and self.markers.get(b.selected) != marker and b.selected not in self.refreshing):
            self.markers[b.selected] = marker
            if len(self.markers) > 32:
                self.markers.pop(next(iter(self.markers)))
            return True
        return False

    async def refresh(self, target):
        if target in self.refreshing:
            return
        self.refreshing.add(target)
        try:
            if self.reactions_supported():
                descriptor = await self.bridge.transport.rpc('messageDescriptor', session=target)
                if self.bridge.selected != target:
                    return
                if not isinstance(descriptor, dict) or not isinstance(descriptor.get('quote'), dict):
                    raise ValueError('Selected message descriptor could not be verified')
                self.descriptors[target] = descriptor
                if len(self.descriptors) > 32:
                    self.descriptors.pop(next(iter(self.descriptors)))
            value = await self.bridge.transport.lifecycle(target, 'history.refresh', {'limit': 50})
            if self.bridge.selected != target:
                return
            if value.get('refreshed') is not True or value.get('chat') != self.bridge.session.get('chat'):
                raise ValueError('Saved message refresh returned another conversation')
            await self.bridge.transport.rpc('refreshChat', session=target)
            if self.bridge.selected == target:
                self.bridge.reconcile(await self.bridge.transport.snapshot(target))
        finally:
            self.refreshing.discard(target)

    async def settled_refresh(self, target):
        try:
            await self.refresh(target)
        except (Rejected, OSError, ValueError, TimeoutError):
            if self.bridge.selected == target:
                self.bridge.send('system', lines=['Saved message references are unavailable. Open Messages and refresh saved messages; your draft is kept.'])

    def merge(self, scope, value, locator):
        row = reaction_row(value)
        if row['sessionId'] != locator['sessionId'] or row['messageId'] != locator['messageId']:
            raise ValueError('The reaction response changed its original message scope')
        key = (scope, row['messageId'])
        old = self.rows.get(key)
        if old is None or old['revision'] < row['revision']:
            self.rows[key] = row
        if len(self.rows) > 200:
            self.rows.pop(next(iter(self.rows)))

    def decorate(self, items):
        result = []
        for item in items:
            result.append(item)
            locator = reference(item.get('reference'), reaction=True)
            row = locator and self.rows.get((self.bridge.selected, locator['messageId']))
            if row and row['sessionId'] == locator['sessionId'] and row['reactions']:
                result.append({'id': 'reaction:' + item['id'], 'kind': 'notice', 'text': 'Reactions · ' + ' · '.join(
                    emoji + ' ' + str(row['counts'][emoji]) + (' · yours' if emoji in row['mine'] else '')
                    for emoji in row['reactions']), 'status': '', 'detail': ''})
        return result

    async def read(self, identity):
        b, scope = self.bridge, self.bridge.selected
        if not self.reactions_supported():
            raise ValueError('Shared reactions are not offered by this host')
        row = self.message(identity)
        locator = reference(row.get('messageReference'), reaction=True)
        if not locator:
            raise ValueError('Refresh saved messages before inspecting reactions')
        value = await b.transport.capability('message.read', {'messageIds': [locator['messageId']]}, scope)
        if (value.get('coverage') != 'selected' or value.get('sent') is not False
                or not isinstance(value.get('items'), list) or len(value['items']) != 1):
            raise ValueError('The selected reaction response could not be verified')
        self.merge(scope, value['items'][0], locator)
        if b.selected == scope:
            b.publish()
            state = self.rows[(scope, locator['messageId'])]
            pending = next(({'id': command, **effect} for command, effect in self.effects().items()
                            if effect['session'] == scope and effect['args']['reference']['messageId'] == locator['messageId'] and effect['status'] == 'unknown'), None)
            b.send('message_reactions', message_id=identity, mine=state['mine'], counts=state['counts'], emoji=EMOJI, pending=pending)

    def verify(self, command, effect, value):
        row = reaction_row(value)
        args = effect['args']
        if (value.get('commandId') != command or value.get('sent') is not False
                or type(value.get('changed')) is not bool or row['sessionId'] != args['reference']['sessionId']
                or row['messageId'] != args['reference']['messageId'] or (args['emoji'] in row['mine']) != args['present']):
            raise ValueError('The original reaction receipt does not match the saved request')

    async def react(self, identity, emoji, present):
        b, scope = self.bridge, self.bridge.selected
        if not self.reactions_supported():
            raise ValueError('Shared reactions are not available here. Your draft is kept.')
        if emoji not in EMOJI or type(present) is not bool:
            raise ValueError('Choose an offered shared reaction')
        row = self.message(identity)
        locator = reference(row.get('messageReference'), reaction=True)
        if not locator:
            raise ValueError('This message has no saved reaction reference. Your draft is kept.')
        effects = self.effects()
        b.store.data.setdefault('messageEffects', effects)
        if len(effects) >= 512 or any(effect['session'] == scope and effect['args']['reference']['messageId'] == locator['messageId'] and effect['status'] == 'unknown' for effect in effects.values()):
            raise ValueError('Inspect the original reaction receipt before changing this message again')
        command = str(uuid.uuid4())
        effect = {'session': scope, 'operation': 'message.reaction', 'args': {'reference': locator, 'emoji': emoji, 'present': present}, 'status': 'unknown'}
        effects[command] = effect
        b.store.journal(command, effect)
        b.store.save()
        self.running.add(command)
        try:
            value = await b.transport.capability('message.reaction', deepcopy(effect['args']), scope, command_id=command)
            self.verify(command, effect, value)
            self.merge(scope, value, locator)
            effect.update(status='confirmed', result=value)
            return True, 'Reaction saved. No message was sent.'
        except Rejected as exc:
            if exc.data.get('executed') is False and exc.data.get('outcome') != 'unknown' and exc.data.get('applied') is not True:
                effect.update(status='refused', error=str(exc))
                return False, 'The host declined the reaction. Your draft is kept.'
            effect['error'] = str(exc)
            return False, 'Reaction is not confirmed. Inspect Original receipts; nothing will be repeated.'
        except (OSError, ValueError, TimeoutError) as exc:
            effect['error'] = str(exc)
            return False, 'Reaction is not confirmed. Inspect Original receipts; nothing will be repeated.'
        finally:
            self.running.discard(command)
            b.store.journal(command, effect)
            b.store.save()
            if b.selected == scope:
                b.publish()

    async def recover(self, command):
        b = self.bridge
        effect = self.effects().get(command)
        if not effect or effect['session'] != b.selected or command in self.running:
            raise ValueError('Select the original conversation and wait for its request before inspecting this receipt')
        value = await b.transport.capability('message.receipt', {'commandId': command}, effect['session'])
        if value.get('replayed') is not False or not isinstance(value.get('receipt'), dict):
            raise ValueError('The original reaction is still unconfirmed. Nothing was repeated.')
        self.verify(command, effect, value['receipt'])
        effect.update(status='confirmed', result=value['receipt'])
        b.store.journal(command, effect)
        b.store.save()
        # Original evidence is not a current-state read and cannot replace newer counts.
        if b.selected == effect['session']:
            b.send('host_review', purpose='result', detail=json.dumps(value, ensure_ascii=False), label='')
        return True, 'Original reaction confirmed. Inspect shared reactions for current counts.'

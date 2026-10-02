"""Current renderer gate: retained keyboard, layout, clipboard and stale-focus tests.

These use controlled presentation events and real Ratatui PTYs. Runtime execution
coverage belongs to test_ahp_client and test_ahp_terminal, with an independent ACP
subprocess. The imported cases preserve the selected renderer behavior from the original client.
"""
import os

import pytest
from renderer_structured import (
    test_code_catalog_limits_and_oversized_copy_explanation as test_code_catalog_limits_and_oversized_copy_explanation,
)
from renderer_structured import (
    test_headings_are_typography_not_source_syntax as test_headings_are_typography_not_source_syntax,
)
from renderer_structured import (
    test_mixed_markdown_retains_exact_copy_and_draft_at_terminal_widths as test_mixed_markdown_retains_exact_copy_and_draft_at_terminal_widths,
)
from renderer_structured import (
    test_open_code_snapshot_does_not_change_with_simulated_source_updates as test_open_code_snapshot_does_not_change_with_simulated_source_updates,
)
from renderer_structured import (
    test_syntax_colour_native_inspection_copy_and_plain_fallback as test_syntax_colour_native_inspection_copy_and_plain_fallback,
)
from test_brand_terminal import (
    test_brand_activity_and_static_fallback_keep_input_and_terminal_ownership as test_brand_activity_and_static_fallback_keep_input_and_terminal_ownership,
)
from test_brand_terminal import (
    test_lost_runtime_does_not_keep_animating_stale_work as test_lost_runtime_does_not_keep_animating_stale_work,
)
from test_compact_terminal import (
    test_borderless_composer_uses_full_width_and_quiet_live_labels as test_borderless_composer_uses_full_width_and_quiet_live_labels,
)
from test_compact_terminal import (
    test_content_height_wrap_editing_and_quiet_idle as test_content_height_wrap_editing_and_quiet_idle,
)
from test_compact_terminal import (
    test_delayed_startup_retains_selection_saved_draft_and_never_auto_sends as test_delayed_startup_retains_selection_saved_draft_and_never_auto_sends,
)
from test_compact_terminal import (
    test_inspection_without_cursor_replies_preserves_draft_and_primary_history as test_inspection_without_cursor_replies_preserves_draft_and_primary_history,
)
from test_compact_terminal import (
    test_silent_resize_probe_is_bounded_and_retains_paste as test_silent_resize_probe_is_bounded_and_retains_paste,
)
from test_compact_terminal import (
    test_skill_menu_inserts_arguments_and_ignores_stale_catalog as test_skill_menu_inserts_arguments_and_ignores_stale_catalog,
)
from test_compact_terminal import (
    test_startup_cursor_timeout_is_bounded_and_preserves_input as test_startup_cursor_timeout_is_bounded_and_preserves_input,
)
from test_compact_terminal import (
    test_startup_failure_remains_visible_after_send_and_late_draft_refusal as test_startup_failure_remains_visible_after_send_and_late_draft_refusal,
)
from test_compact_terminal import (
    test_transient_auth_prompts_do_not_steal_focus_or_become_history as test_transient_auth_prompts_do_not_steal_focus_or_become_history,
)
from test_interaction import (
    test_actions_cancel_preserves_selection_and_paste_is_local as test_actions_cancel_preserves_selection_and_paste_is_local,
)
from test_interaction import (
    test_menu_resize_keeps_draft_and_keyboard_access as test_menu_resize_keeps_draft_and_keyboard_access,
)
from test_interaction import (
    test_open_decision_keeps_identity_when_backend_replaces_it as test_open_decision_keeps_identity_when_backend_replaces_it,
)
from test_reading_terminal import (
    test_boundary_history_and_tab_completion_keep_neighbors as test_boundary_history_and_tab_completion_keep_neighbors,
)
from test_reading_terminal import (
    test_markdown_visual_line_scroll_anchor_stream_and_resize as test_markdown_visual_line_scroll_anchor_stream_and_resize,
)

pytestmark = pytest.mark.skipif(os.environ.get("TUI_TEST_CANDIDATES") != "1", reason="Build Ratatui")

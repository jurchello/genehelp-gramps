#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026 Yurii Liubymyi <jurchello@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# ----------------------------------------------------------------------------

"""GTK UI facade for the GeneHelp gramplet."""

from typing import Any, Callable, Optional

import gi

gi.require_version("Gdk", "3.0")  # pylint: disable=wrong-import-position
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gdk, Gtk, Pango

from genehelp.api_contract import API_BASE_URL
from genehelp.config import CSS_FILE, DATA_SOURCE_MEDIA, UI_FILE
from genehelp.country_utils import (
    COUNTRY_DROPDOWN_LIMIT as DEFAULT_COUNTRY_DROPDOWN_LIMIT,
    UNKNOWN_COUNTRY_LABEL as DEFAULT_UNKNOWN_COUNTRY_LABEL,
)
from genehelp.l10n import _
from genehelp.markdown import MarkdownRenderer
from genehelp.models import CountryOption, ImportedContext, PageHandler, ThemeOption
from genehelp.ui_countries import CountryUiMixin
from genehelp.ui_help_offer import HelpOfferViewMixin
from genehelp.ui_requests import RequestListMixin


def info_markdown(base_url: str = API_BASE_URL) -> str:
    """Info markdown."""
    base_url = base_url.rstrip("/")
    return (
        _(
            """**GeneHelp** helps you find genealogy help — or offer help to others —
with archives, documents, photos, places, research dead ends, and even complete
family history research.

## What this gramplet does

The gramplet takes the current object from **Gramps** and helps you prepare a request for GeneHelp.

Before sending, you can review and edit the request text.

## What you can send

Requests based on **media**, **notes**, **repositories**, **citations**, **sources**,
**places**, **events**, **families**, and **people** pages are currently supported.

For each page type, the gramplet inserts the matching request template.

## Privacy

**Data is not sent automatically.** The request is sent to GeneHelp only after your action.

To send a request, you need a **GeneHelp integration token**, which you can generate in
your user profile.

[Open GeneHelp](%(base_url)s)

[Generate an integration token](%(profile_url)s)

[Privacy Policy](%(privacy_url)s)
"""
        )
        % {
            "base_url": f"{base_url}/go/gramps-open",
            "profile_url": f"{base_url}/profile?tab=integrations",
            "privacy_url": f"{base_url}/privacy-policy",
        }
    )


class Ui(CountryUiMixin, RequestListMixin, HelpOfferViewMixin):
    """GTK UI facade for the GeneHelp gramplet.
    It binds GtkBuilder objects, applies styling, renders API data, and exposes form state.
    The controller calls this class instead of touching individual widgets directly.
    """

    UNKNOWN_COUNTRY_LABEL = DEFAULT_UNKNOWN_COUNTRY_LABEL
    COUNTRY_DROPDOWN_LIMIT = DEFAULT_COUNTRY_DROPDOWN_LIMIT

    def __init__(
        self,
        page_handlers: dict[str, PageHandler],
        on_submit: Callable,
        on_theme_changed: Callable,
        on_form_changed: Callable,
        on_countries_needed: Callable,
        on_help_offer_needed: Callable,
        on_help_offer_refresh: Callable,
        on_help_offer_profile_open: Callable,
        on_requests_needed: Callable,
        on_requests_refresh: Callable,
        on_request_activated: Callable,
        api_base_url: str = API_BASE_URL,
    ) -> None:
        """Initialize the object."""
        self.page_handlers = page_handlers
        self.on_submit = on_submit
        self.on_theme_changed = on_theme_changed
        self.on_form_changed = on_form_changed
        self.on_countries_needed = on_countries_needed
        self.on_help_offer_needed = on_help_offer_needed
        self.on_help_offer_refresh = on_help_offer_refresh
        self.on_help_offer_profile_open = on_help_offer_profile_open
        self.on_requests_needed = on_requests_needed
        self.on_requests_refresh = on_requests_refresh
        self.on_request_activated = on_request_activated
        self.api_base_url = api_base_url
        self.form_change_callbacks_enabled = False
        self.country_options_request_pending = False
        self.default_request_country_code = ""
        self.country_model_updates_enabled = True
        self.all_countries: list[CountryOption] = []
        self.theme_boxes: dict[str, Gtk.Widget] = {}
        self.theme_section_labels: dict[str, Gtk.Label] = {}
        self.theme_buttons: dict[str, dict[str, Gtk.CheckButton]] = {}
        self.help_offer_profile_url = ""

        builder = Gtk.Builder()
        builder.set_translation_domain("addon")
        builder.add_from_file(UI_FILE)
        self.bind(builder)
        self.connect_signals()
        self.apply_styles()
        self.configure_widgets()
        self.clear_theme_selection()
        self.update_title_placeholder_visibility()
        self.update_text_placeholder_visibility()
        self.clear_status()
        self.form_change_callbacks_enabled = True

    @staticmethod
    def install_styles() -> None:
        """Install the gramplet CSS provider."""
        screen = Gdk.Screen.get_default()
        if screen is None:
            return

        provider = Gtk.CssProvider()
        provider.load_from_path(CSS_FILE)
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def bind(self, builder: Gtk.Builder) -> None:
        """Bind."""
        self.root = self.require_object(builder, "root")
        self.notebook = self.require_object(builder, "notebook")
        self.request_page = self.require_object(builder, "request_page")
        self.help_offer_page = self.require_object(builder, "help_offer_page")
        self.help_offer_content_scroller = self.require_object(
            builder,
            "help_offer_content_scroller",
        )
        self.help_offer_content_viewport = self.require_object(
            builder,
            "help_offer_content_viewport",
        )
        self.help_offer_content_box = self.require_object(
            builder,
            "help_offer_content_box",
        )
        self.help_offer_error_box = self.require_object(builder, "help_offer_error_box")
        self.help_offer_error_label = self.require_object(
            builder,
            "help_offer_error_label",
        )
        self.help_offer_retry_button = self.require_object(
            builder,
            "help_offer_retry_button",
        )
        self.help_offer_footer_box = self.require_object(
            builder,
            "help_offer_footer_box",
        )
        self.help_offer_refresh_button = self.require_object(
            builder,
            "help_offer_refresh_button",
        )
        self.help_offer_profile_button = self.require_object(
            builder,
            "help_offer_profile_button",
        )
        self.info_page = self.require_object(builder, "info_page")
        self.info_text_view = self.require_object(builder, "info_text_view")
        self.requests_page = self.require_object(builder, "requests_page")
        self.requests_scroller = self.require_object(builder, "requests_scroller")
        self.requests_tree_view = self.require_object(builder, "requests_tree_view")
        self.requests_error_box = self.require_object(builder, "requests_error_box")
        self.requests_error_label = self.require_object(builder, "requests_error_label")
        self.requests_retry_button = self.require_object(builder, "requests_retry_button")
        self.requests_footer_box = self.require_object(builder, "requests_footer_box")
        self.requests_refresh_button = self.require_object(
            builder,
            "requests_refresh_button",
        )
        self.page_headers = (
            self.require_object(builder, "request_page_header"),
            self.require_object(builder, "help_offer_page_header"),
            self.require_object(builder, "requests_page_header"),
            self.require_object(builder, "info_page_header"),
        )
        self.product_title_label = self.require_object(builder, "product_title_label")
        self.help_offer_page_title = self.require_object(builder, "help_offer_page_title")
        self.requests_page_title = self.require_object(builder, "requests_page_title")
        self.info_page_title = self.require_object(builder, "info_page_title")
        self.page_titles = (
            self.product_title_label,
            self.help_offer_page_title,
            self.requests_page_title,
            self.info_page_title,
        )
        self.page_title_rules = (
            self.require_object(builder, "request_page_title_rule"),
            self.require_object(builder, "help_offer_page_title_rule"),
            self.require_object(builder, "requests_page_title_rule"),
            self.require_object(builder, "info_page_title_rule"),
        )
        self.test_request_checkbox = self.require_object(builder, "test_request_checkbox")
        self.country_fields_box = self.require_object(builder, "country_fields_box")
        self.request_form_box = self.require_object(builder, "request_form_box")
        self.title_label = self.require_object(builder, "title_label")
        self.title_buffer = self.require_object(builder, "title_text_buffer")
        self.title_overlay = self.require_object(builder, "title_overlay")
        self.title_scroller = self.require_object(builder, "title_scroller")
        self.title_text_view = self.require_object(builder, "title_text_view")
        self.title_placeholder_label = self.require_object(
            builder,
            "title_placeholder_label",
        )
        self.request_country_label = self.require_object(
            builder,
            "request_country_label",
        )
        self.request_country_combo = self.require_object(
            builder,
            "request_country_combo",
        )
        self.helper_country_label = self.require_object(
            builder,
            "helper_country_label",
        )
        self.helper_country_combo = self.require_object(
            builder,
            "helper_country_combo",
        )
        self.text_label = self.require_object(builder, "text_label")
        self.text_buffer = self.require_object(builder, "request_text_buffer")
        self.text_overlay = self.require_object(builder, "text_overlay")
        self.text_scroller = self.require_object(builder, "text_scroller")
        self.text_view = self.require_object(builder, "text_view")
        self.text_placeholder_label = self.require_object(
            builder,
            "text_placeholder_label",
        )
        self.submit_button = self.require_object(builder, "submit_button")
        self.status_label = self.require_object(builder, "status_label")
        self.status_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.status_label.set_line_wrap(False)
        self.info_markdown = MarkdownRenderer(self.info_text_view)

        for nav_type, handler in self.page_handlers.items():
            self.theme_boxes[nav_type] = self.require_object(builder, handler.theme_box_id)
            self.theme_section_labels[nav_type] = self.require_object(
                builder,
                handler.theme_section_label_id,
            )
            self.theme_buttons[nav_type] = {
                theme.key: self.require_object(builder, theme.button_id) for theme in handler.themes
            }

    def connect_signals(self) -> None:
        """Connect GTK widget signals."""
        for button in self.all_theme_buttons():
            button.connect("toggled", self.on_theme_changed)

        self.title_buffer.connect(
            "changed",
            self.on_title_buffer_changed,
        )
        self.text_buffer.connect(
            "changed",
            self.on_text_buffer_changed,
        )
        self.request_country_combo.connect("changed", self.on_country_changed)
        self.helper_country_combo.connect("changed", self.on_country_changed)
        self.request_country_combo.connect(
            "notify::popup-shown",
            self.on_country_popup_shown,
        )
        self.helper_country_combo.connect(
            "notify::popup-shown",
            self.on_country_popup_shown,
        )
        self.submit_button.connect("clicked", self.on_submit)
        self.help_offer_profile_button.connect(
            "clicked",
            self.on_help_offer_profile_button_clicked,
        )
        self.help_offer_retry_button.connect("clicked", self.on_help_offer_retry_clicked)
        self.help_offer_refresh_button.connect(
            "clicked",
            self.on_help_offer_refresh_clicked,
        )
        self.notebook.connect("switch-page", self.on_notebook_page_switched)
        self.requests_tree_view.connect("row-activated", self.on_request_row_activated)
        self.requests_retry_button.connect("clicked", self.on_requests_retry_clicked)
        self.requests_refresh_button.connect("clicked", self.on_requests_refresh_clicked)

    def apply_styles(self) -> None:
        """Apply styles."""
        self.add_css_class(self.root, "genehelp-root")
        self.add_css_class(self.request_page, "genehelp-root")
        self.add_css_class(self.help_offer_page, "genehelp-root")
        self.add_css_class(self.help_offer_content_scroller, "genehelp-scroll-frame")
        self.add_css_class(self.help_offer_content_viewport, "genehelp-scroll-viewport")
        self.add_css_class(self.help_offer_content_box, "genehelp-help-offer")
        self.add_css_class(self.help_offer_error_box, "genehelp-data-error")
        self.add_css_class(self.help_offer_error_label, "genehelp-data-error-label")
        self.add_css_class(self.help_offer_retry_button, "genehelp-primary-button")
        self.add_css_class(self.help_offer_refresh_button, "genehelp-primary-button")
        self.add_css_class(self.info_page, "genehelp-info-panel")
        self.add_css_class(self.info_text_view, "genehelp-info-panel")
        self.add_css_class(self.requests_page, "genehelp-info-panel")
        self.add_css_class(self.requests_tree_view, "genehelp-requests-tree")
        self.add_css_class(self.requests_error_box, "genehelp-data-error")
        self.add_css_class(self.requests_error_label, "genehelp-data-error-label")
        self.add_css_class(self.requests_retry_button, "genehelp-primary-button")
        self.add_css_class(self.requests_refresh_button, "genehelp-primary-button")
        self.add_css_class(self.product_title_label, "genehelp-title")
        for header in self.page_headers:
            self.add_css_class(header, "genehelp-page-header")
        for label in self.page_titles:
            self.add_css_class(label, "genehelp-page-title")
        for rule in self.page_title_rules:
            self.add_css_class(rule, "genehelp-page-title-rule")
        for label in self.theme_section_labels.values():
            self.add_css_class(label, "genehelp-section-title")
        for button in self.all_theme_buttons():
            self.add_css_class(button, "genehelp-theme-option")
        self.add_css_class(self.title_label, "genehelp-field-label")
        self.add_css_class(self.title_scroller, "genehelp-text-area")
        self.add_css_class(self.title_text_view, "genehelp-text-area")
        self.add_css_class(self.title_placeholder_label, "genehelp-placeholder")
        self.add_css_class(self.test_request_checkbox, "genehelp-test-request-option")
        self.add_css_class(self.country_fields_box, "genehelp-field-group")
        self.add_css_class(self.request_country_label, "genehelp-field-label")
        self.add_css_class(self.request_country_combo, "genehelp-country-combo")
        self.add_css_class(self.helper_country_label, "genehelp-field-label")
        self.add_css_class(self.helper_country_combo, "genehelp-country-combo")
        self.add_css_class(self.text_label, "genehelp-field-label")
        self.add_css_class(self.text_scroller, "genehelp-text-area")
        self.add_css_class(self.text_view, "genehelp-text-area")
        self.add_css_class(self.text_placeholder_label, "genehelp-placeholder")
        self.add_css_class(self.submit_button, "genehelp-primary-button")
        self.add_css_class(self.help_offer_profile_button, "genehelp-primary-button")
        self.add_css_class(
            self.help_offer_profile_button,
            "genehelp-help-offer-profile-button",
        )
        self.add_css_class(self.status_label, "genehelp-status")

    def configure_widgets(self) -> None:
        """Configure initial GTK widget behavior."""
        self.apply_static_texts()

        for widget in (
            self.root,
            self.notebook,
            self.request_page,
            self.help_offer_page,
            self.help_offer_content_scroller,
            self.help_offer_content_viewport,
            self.help_offer_content_box,
            self.help_offer_error_box,
            self.info_page,
            self.info_text_view,
            self.requests_page,
            self.requests_scroller,
            self.requests_tree_view,
            self.requests_error_box,
            self.country_fields_box,
            self.request_form_box,
            self.title_overlay,
            self.text_overlay,
            self.title_scroller,
            self.request_country_combo,
            self.helper_country_combo,
            self.text_scroller,
            self.help_offer_profile_button,
            self.title_text_view,
            self.text_view,
        ):
            widget.set_hexpand(True)

        for label in (self.title_placeholder_label, self.text_placeholder_label):
            label.set_line_wrap(True)
            label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        for label in (
            *self.page_titles,
            *self.theme_section_labels.values(),
            self.title_label,
            self.request_country_label,
            self.helper_country_label,
            self.text_label,
        ):
            self.configure_wrapping_label(label)

        self.configure_button_label(self.test_request_checkbox)
        for button in self.all_theme_buttons():
            self.configure_button_label(button)

        self.request_country_model = Gtk.ListStore(str, str, str)
        self.helper_country_model = Gtk.ListStore(str, str, str)
        self.requests_model = Gtk.TreeStore(
            str,
            str,
            str,
            str,
            str,
            str,
            bool,
            int,
        )
        self.configure_requests_tree()
        self.configure_country_combo(
            self.request_country_combo,
            self.request_country_model,
        )
        self.configure_country_combo(
            self.helper_country_combo,
            self.helper_country_model,
        )
        self.set_countries([])
        self.title_text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.title_text_view.set_editable(True)
        self.text_view.set_editable(True)
        self.info_text_view.set_editable(False)
        self.title_text_view.set_cursor_visible(True)
        self.text_view.set_cursor_visible(True)
        self.info_text_view.set_cursor_visible(False)
        self.info_text_view.set_can_focus(True)
        self.info_text_view.set_focus_on_click(True)
        self.info_text_view.set_accepts_tab(False)
        self.info_markdown.render(info_markdown(self.api_base_url))
        self.configure_notebook_tab_icons()
        self.help_offer_content_scroller.set_shadow_type(Gtk.ShadowType.NONE)
        self.help_offer_content_scroller.set_policy(
            Gtk.PolicyType.NEVER,
            Gtk.PolicyType.NEVER,
        )
        self.help_offer_content_viewport.set_shadow_type(Gtk.ShadowType.NONE)
        self.title_overlay.set_overlay_pass_through(
            self.title_placeholder_label,
            True,
        )
        self.text_overlay.set_overlay_pass_through(
            self.text_placeholder_label,
            True,
        )

    def attach_to_gramps_container(self, container: Gtk.Container, old_widget: Gtk.Widget):
        """Attach to gramps container."""
        self.add_css_class(container, "genehelp-container")
        container.remove(old_widget)
        container.add(self.root)
        self.root.show_all()
        self.update_placeholder_visibility()

    def show_workflow(self, nav_type: Optional[str]) -> None:
        """Show workflow."""
        for page_type, theme_box in self.theme_boxes.items():
            self.set_widget_visible(theme_box, nav_type == page_type)

        workflow_visible = nav_type in self.page_handlers
        self.update_submit_button_label(nav_type)
        self.set_widget_visible(self.test_request_checkbox, workflow_visible)
        self.set_widget_visible(self.country_fields_box, workflow_visible)
        self.set_widget_visible(self.title_label, workflow_visible)
        self.set_widget_visible(self.title_overlay, workflow_visible)
        self.set_widget_visible(self.request_country_label, workflow_visible)
        self.set_widget_visible(self.request_country_combo, workflow_visible)
        self.set_widget_visible(self.helper_country_label, workflow_visible)
        self.set_widget_visible(self.helper_country_combo, workflow_visible)
        self.set_widget_visible(self.text_label, workflow_visible)
        self.set_widget_visible(self.text_overlay, workflow_visible)
        self.set_widget_visible(self.submit_button, workflow_visible)
        self.update_placeholder_visibility()

    def import_context(self, context: ImportedContext) -> None:
        """Import context."""
        self.clear_theme_selection(context.nav_type)
        self.update_theme_labels(context.nav_type, context.title_values)
        self.set_title_text("")
        self.set_description_text(context.description)
        self.set_submit_sensitive(False)
        self.clear_status()

    def reset_imported_payload(self, nav_type: Optional[str]) -> None:
        """Reset imported payload."""
        self.set_description_text("")
        self.clear_status()
        self.clear_theme_selection(nav_type)
        self.set_title_text("")
        self.set_submit_sensitive(False)

    def selected_theme_key(self, nav_type: Optional[str]) -> str:
        """Selected theme key."""
        group = self.theme_buttons.get(nav_type or "")
        if group is None:
            return ""

        for key, button in group.items():
            if button.get_active():
                return key
        return ""

    def theme_group_for_button(self, button: Gtk.CheckButton):
        """Theme group for button."""
        for nav_type, group in self.theme_buttons.items():
            for key, theme_button in group.items():
                if theme_button is button:
                    return nav_type, group, key
        return None, None, None

    def clear_theme_selection(self, nav_type: Optional[str] = None) -> None:
        """Clear selected request topic buttons."""
        if nav_type in self.theme_buttons:
            groups = (self.theme_buttons[nav_type],)
        else:
            groups = self.theme_buttons.values()

        for group in groups:
            for button in group.values():
                button.set_active(False)

    def update_theme_labels(self, nav_type: str, values: dict[str, str]) -> None:
        """Update theme labels."""
        handler = self.page_handlers.get(nav_type)
        if handler is None:
            return

        buttons = self.theme_buttons.get(nav_type, {})
        for theme in handler.themes:
            button = buttons.get(theme.key)
            if button is not None:
                button.set_label(format_template(theme.label, values))
                self.configure_button_label(button)

    def select_theme_title(self, theme: ThemeOption, values: dict[str, str]) -> None:
        """Select theme title."""
        self.set_title_text(format_template(theme.default_title, values))

    def title_text(self) -> str:
        """Title text."""
        return self.text_from_buffer(self.title_buffer)

    def description_text(self) -> str:
        """Description text."""
        return self.text_from_buffer(self.text_buffer)

    def is_test_request(self) -> bool:
        """Return whether test request."""
        return bool(self.test_request_checkbox.get_active())

    def set_title_text(self, text: str) -> None:
        """Set title text."""
        self.title_buffer.set_text(text)
        self.update_title_placeholder_visibility()
        self.notify_form_changed()

    def set_description_text(self, text: str) -> None:
        """Set description text."""
        self.text_buffer.set_text(text)
        self.update_text_placeholder_visibility()
        self.notify_form_changed()

    def set_submit_sensitive(self, sensitive: bool) -> None:
        """Set submit sensitive."""
        self.submit_button.set_sensitive(sensitive)

    def update_submit_button_label(self, nav_type: Optional[str]) -> None:
        """Update the submit button label for the page type."""
        if nav_type == DATA_SOURCE_MEDIA:
            self.submit_button.set_label(_("Send request WITH MEDIA to GeneHelp"))
            return
        self.submit_button.set_label(_("Send request to GeneHelp"))

    def on_title_buffer_changed(self, _buffer) -> None:
        """Handle title buffer changed."""
        self.update_title_placeholder_visibility()
        self.notify_form_changed()

    def on_text_buffer_changed(self, _buffer) -> None:
        """Handle text buffer changed."""
        self.update_text_placeholder_visibility()
        self.notify_form_changed()

    def notify_form_changed(self) -> None:
        """Notify the owner that form data changed."""
        if self.form_change_callbacks_enabled:
            self.on_form_changed()

    def on_notebook_page_switched(self, _notebook, _page, _page_num) -> None:
        """Handle notebook page switched."""
        self.update_placeholder_visibility()
        if _page is self.help_offer_page:
            self.on_help_offer_needed()
        if _page is self.requests_page:
            self.on_requests_needed()

    def set_status(self, text: str) -> None:
        """Set status."""
        self.status_label.set_no_show_all(False)
        self.status_label.show()
        self.status_label.set_text(text)

    def clear_status(self) -> None:
        """Clear the status label."""
        self.status_label.set_text("")
        self.status_label.set_no_show_all(True)
        self.status_label.hide()

    def all_theme_buttons(self):
        """Return every request topic button."""
        for group in self.theme_buttons.values():
            yield from group.values()

    def update_title_placeholder_visibility(self) -> None:
        """Update title placeholder visibility."""
        self.set_placeholder_visible(
            self.title_placeholder_label,
            self.title_buffer.get_char_count() == 0,
        )

    def update_text_placeholder_visibility(self) -> None:
        """Update text placeholder visibility."""
        self.set_placeholder_visible(
            self.text_placeholder_label,
            self.text_buffer.get_char_count() == 0,
        )

    def update_placeholder_visibility(self) -> None:
        """Update title and description placeholders."""
        self.update_title_placeholder_visibility()
        self.update_text_placeholder_visibility()

    @staticmethod
    def require_object(builder: Gtk.Builder, object_id: str) -> Any:
        """Require object."""
        widget = builder.get_object(object_id)
        if widget is None:
            raise RuntimeError(f"Missing UI object: {object_id}")
        return widget

    @staticmethod
    def add_css_class(widget: Gtk.Widget, class_name: str) -> None:
        """Add a CSS class to a GTK widget."""
        widget.get_style_context().add_class(class_name)

    @staticmethod
    def configure_wrapping_label(label: Gtk.Label) -> None:
        """Configure wrapping label."""
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(42)

    def configure_button_label(self, button: Gtk.Button) -> None:
        """Configure wrapping for a button label."""
        button.set_hexpand(True)
        button.set_halign(Gtk.Align.FILL)
        self.configure_child_labels(button)

    def apply_static_texts(self) -> None:
        """Apply static texts."""
        self.product_title_label.set_label(_("CREATE A GENEALOGY REQUEST IN GENEHELP"))
        self.test_request_checkbox.set_label(_("Create as a test genealogy request"))
        self.test_request_checkbox.set_tooltip_text(
            _(
                "Only you will see a test request. It does not participate in helper "
                "matching and will be automatically deleted after 7 days unless you make "
                "it a regular request in GeneHelp."
            )
        )
        self.request_country_label.set_label(_("Request author's country"))
        self.helper_country_label.set_label(_("Helper needed in country"))
        self.title_label.set_label(_("Request title (edit if needed)"))
        self.title_placeholder_label.set_label(_("Enter a genealogy request title"))
        self.text_label.set_label(_("Request description (edit if needed)"))
        self.text_placeholder_label.set_label(_("Enter the genealogy request text"))
        self.help_offer_page_title.set_label(_("MY HELP PROFILE"))
        self.help_offer_refresh_button.set_label(_("Refresh"))
        self.help_offer_profile_button.set_label(_("Open profile"))
        self.requests_page_title.set_label(_("MY GENEALOGY REQUESTS"))
        self.requests_refresh_button.set_label(_("Refresh"))
        self.update_submit_button_label(None)

        for label in self.theme_section_labels.values():
            label.set_label(_("Some request topic templates"))

        for nav_type, handler in self.page_handlers.items():
            values: dict[str, str] = {}
            buttons = self.theme_buttons.get(nav_type, {})
            for theme in handler.themes:
                button = buttons.get(theme.key)
                if button is not None:
                    button.set_label(format_template(theme.label, values))

        for widget in (self.help_offer_error_label, self.requests_error_label):
            widget.set_label(_("Data loading error"))
        for widget in (self.help_offer_retry_button, self.requests_retry_button):
            widget.set_label(_("Try again"))

    def show_content_or_error(
        self,
        content_widget: Gtk.Widget,
        error_widget: Gtk.Widget,
        show_content: bool,
    ) -> None:
        """Show content or error."""
        self.set_widget_visible(error_widget, not show_content)
        self.set_widget_visible(content_widget, show_content)

    def configure_notebook_tab_icons(self) -> None:
        """Configure notebook tab icons and tooltips."""
        self.set_notebook_tab(self.request_page, "📝", _("Genealogy request"))
        self.set_notebook_tab(self.help_offer_page, "🤝", _("My Help Profile"))
        self.set_notebook_tab(self.requests_page, "📋", _("My requests"))
        self.set_notebook_tab(self.info_page, "ℹ️", _("Info"))

    def set_notebook_tab(self, page: Gtk.Widget, icon: str, tooltip: str) -> None:
        """Set notebook tab."""
        self.notebook.set_tab_label_text(page, icon)
        tab_label = self.notebook.get_tab_label(page)
        if tab_label is not None:
            tab_label.set_tooltip_text(tooltip)

    def configure_child_labels(self, widget: Gtk.Widget) -> None:
        """Configure wrapping on nested GTK labels."""
        if isinstance(widget, Gtk.Label):
            self.configure_wrapping_label(widget)
            widget.set_xalign(0)
            widget.set_hexpand(True)
            return

        if not isinstance(widget, Gtk.Container):
            return

        for child in widget.get_children():
            self.configure_child_labels(child)

    @staticmethod
    def set_widget_visible(widget: Gtk.Widget, visible: bool) -> None:
        """Set widget visible."""
        widget.set_no_show_all(not visible)
        if visible:
            widget.show_all()
        else:
            widget.hide()

    @staticmethod
    def set_placeholder_visible(label: Gtk.Label, visible: bool) -> None:
        """Set placeholder visible."""
        label.set_no_show_all(not visible)
        if visible:
            label.show()
        else:
            label.hide()

    @staticmethod
    def text_from_buffer(buffer: Gtk.TextBuffer) -> str:
        """Text from buffer."""
        start = buffer.get_start_iter()
        end = buffer.get_end_iter()
        return buffer.get_text(start, end, True)

    @staticmethod
    def clear_box(box: Gtk.Container) -> None:
        """Remove all children from a GTK container."""
        for child in box.get_children():
            box.remove(child)


def format_template(template: str, values: dict[str, str]) -> str:
    """Format template."""
    try:
        return template.format(**values)
    except KeyError:
        return template

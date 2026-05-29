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

"""GeneHelp gramplet controller for creating requests from Gramps data."""

# pylint: disable=invalid-name

import webbrowser
from typing import Optional

from gramps.gen.plug import Gramplet
from gramps.gen.plug.menu import StringOption

from genehelp.api_client import ApiClient
from genehelp.config import (
    API_TOKEN_OPTION_LABEL,
    DEFAULT_REQUEST_COUNTRY_OPTION_LABEL,
    INTEGRATION_GENEALOGY_REQUESTS_PATH,
    Config,
    normalize_country_code,
)
from genehelp.countries import CountryRepository
from genehelp.country_combo import CountryCombo
from genehelp.diagnostics import print_error_diagnostic, print_exception_diagnostic
from genehelp.gramps_context import GrampsContext
from genehelp.help_offer import HelpOfferRepository
from genehelp.l10n import _
from genehelp.models import ImportedContext
from genehelp.notification import NotificationCenter
from genehelp.payloads import build_submit_payload
from genehelp.genealogy_requests import GenealogyRequestRepository
from genehelp.themes import PAGE_HANDLERS, SUPPORTED_NAV_TYPES, theme_for_key
from genehelp.ui import Ui


class GeneHelpGramplet(Gramplet):
    """Main Gramps gramplet controller for the GeneHelp integration.
    It coordinates Gramps context detection, UI state, API calls, and request submission.
    """

    def init(self) -> None:
        """Initialize the object."""
        self.settings = Config()
        self.api_base_url = self.settings.api_base_url()
        self.api_token_option = None
        self.default_request_country_option = None
        self.default_request_country_widget = None
        self.current_nav_type: Optional[str] = None
        self.imported_context: Optional[ImportedContext] = None
        self.notebook_connected = False
        self.countries_fetching = False
        self.help_offer_fetching = False
        self.help_offer_loaded = False
        self.requests_fetching = False
        self.requests_loaded = False
        self.context = GrampsContext(self)
        self.notifications = NotificationCenter()

        Ui.install_styles()
        self.ui = Ui(
            PAGE_HANDLERS,
            on_submit=self.on_submit,
            on_theme_changed=self.on_theme_changed,
            on_form_changed=self.update_submit_button_state,
            on_countries_needed=self.load_countries,
            on_help_offer_needed=self.load_help_offer,
            on_help_offer_refresh=self.refresh_help_offer,
            on_help_offer_profile_open=self.open_genealogy_request,
            on_requests_needed=self.load_genealogy_requests,
            on_requests_refresh=self.refresh_genealogy_requests,
            on_request_activated=self.open_genealogy_request,
            api_base_url=self.api_base_url,
        )
        self.ui.set_default_request_country_code(self.option_default_request_country_code())
        self.gui.WIDGET = self.ui.root
        self.ui.attach_to_gramps_container(
            self.gui.get_container_widget(),
            self.gui.textview,
        )
        self.load_cached_countries()
        self.connect_notebook_switch()
        self.update_context_ui()

    def build_options(self) -> None:
        """Build Gramps configuration options."""
        self.api_token_option = StringOption(
            API_TOKEN_OPTION_LABEL,
            self.settings.api_token(),
        )
        self.default_request_country_option = StringOption(
            DEFAULT_REQUEST_COUNTRY_OPTION_LABEL,
            self.settings.default_request_country_code(),
        )
        self.api_token_option.set_help(
            _("The token is available in your GeneHelp profile, Integrations tab.")
        )
        self.add_option(self.api_token_option)
        self.add_option(self.default_request_country_option)
        self.default_request_country_widget = CountryCombo(
            self.settings.default_request_country_code(),
            on_countries_needed=self.load_settings_countries,
            placeholder_text=_("Recommended, but can be left empty"),
        )
        self.option_dict[DEFAULT_REQUEST_COUNTRY_OPTION_LABEL][
            0
        ] = self.default_request_country_widget
        self.load_cached_settings_countries()
        self.style_option_widget(API_TOKEN_OPTION_LABEL, hide_text=True)
        self.style_option_widget(DEFAULT_REQUEST_COUNTRY_OPTION_LABEL)

    def style_option_widget(self, label: str, hide_text: bool = False) -> None:
        """Apply common styling to an option widget."""
        widget = self.get_option_widget(label)
        widget.set_hexpand(True)
        widget.set_margin_top(4)
        widget.set_margin_bottom(4)

        if hasattr(widget, "set_width_chars"):
            widget.set_width_chars(42)

        if hide_text and hasattr(widget, "set_visibility"):
            widget.set_visibility(False)
            widget.set_invisible_char("*")

    def save_options(self) -> None:
        """Persist Gramps configuration options."""
        self.settings.save(
            self.option_api_token(),
            self.option_default_request_country_code(),
        )

    def save_update_options(self, _widget=None) -> None:
        """Save options and refresh dependent data."""
        self.save_options()
        self.ui.set_default_request_country_code(self.option_default_request_country_code())
        self.load_cached_countries()
        self.help_offer_loaded = False
        self.requests_loaded = False
        self.ui.set_help_offer_refresh_visible(False)
        self.ui.set_requests_refresh_visible(False)
        self.update()

    def option_api_token(self) -> str:
        """Option api token."""
        if self.api_token_option is None:
            return self.settings.api_token()
        return (self.api_token_option.get_value() or "").strip()

    def option_default_request_country_code(self) -> str:
        """Option default request country code."""
        if self.default_request_country_widget is not None:
            return self.default_request_country_widget.get_value()
        if self.default_request_country_option is None:
            return self.settings.default_request_country_code()
        return normalize_country_code(self.default_request_country_option.get_value() or "")

    def db_changed(self) -> None:
        """Handle Gramps database changes."""
        for nav_type in SUPPORTED_NAV_TYPES:
            self.connect_signal(nav_type, self.update)
        self.connect_notebook_switch()

    def active_changed(self, _handle) -> None:
        """Handle active Gramps object changes."""
        self.update()

    def main(self) -> None:
        """Refresh the gramplet for the active Gramps object."""
        nav_type = self.context.detect_nav_type()
        self.update_context_ui(nav_type)
        self.set_has_data(
            nav_type in PAGE_HANDLERS and self.context.active_object(nav_type) is not None
        )

    def connect_notebook_switch(self) -> None:
        """Connect the Gramps notebook switch signal."""
        if self.notebook_connected:
            return

        try:
            notebook = self.gui.uistate.viewmanager.notebook
        except AttributeError:
            return

        if notebook:
            notebook.connect("switch-page", self.on_page_switched)
            self.notebook_connected = True

    def on_page_switched(self, _notebook, _page, _page_num) -> None:
        """Handle page switched."""
        self.update()

    def update_context_ui(self, nav_type: Optional[str] = None) -> None:
        """Refresh UI from the active Gramps context."""
        if nav_type is None:
            nav_type = self.context.detect_nav_type()

        if nav_type != self.current_nav_type:
            self.current_nav_type = nav_type
            self.imported_context = None
            self.ui.reset_imported_payload(nav_type)

        self.ui.show_workflow(nav_type)

        if nav_type not in PAGE_HANDLERS:
            self.ui.set_submit_sensitive(False)
            return

        active_handle = self.context.active_handle(nav_type)
        active_object = self.context.active_object(nav_type, active_handle)
        self.import_active_object(nav_type, active_object, active_handle)

    def import_active_object(self, nav_type, active_object, active_handle) -> None:
        """Import active object."""
        if active_object is None or active_handle is None:
            if self.imported_context is not None:
                self.imported_context = None
                self.ui.reset_imported_payload(nav_type)
            else:
                self.ui.set_submit_sensitive(False)
            return

        if (
            self.imported_context is not None
            and self.imported_context.nav_type == nav_type
            and self.imported_context.handle == active_handle
        ):
            self.update_submit_button_state()
            return

        handler = PAGE_HANDLERS[nav_type]
        imported_context = handler.extractor(
            self.dbstate.db,
            active_object,
            active_handle,
        )

        self.imported_context = imported_context
        self.ui.import_context(imported_context)
        for warning in imported_context.warnings:
            self.show_notification(warning, "error")
        self.update_submit_button_state()

    def on_theme_changed(self, button) -> None:
        """Handle theme changed."""
        if not button.get_active():
            self.update_submit_button_state()
            return

        nav_type, group, key = self.ui.theme_group_for_button(button)
        if nav_type is None or group is None or key is None:
            return

        for other_button in group.values():
            if other_button is not button:
                other_button.set_active(False)

        theme = theme_for_key(nav_type, key)
        if theme is None:
            return

        title_values = {}
        if self.imported_context is not None:
            title_values = self.imported_context.title_values
        self.ui.select_theme_title(theme, title_values)
        self.update_submit_button_state()

    def on_submit(self, _button) -> None:
        """Submit the current genealogy request form."""
        self.save_options()

        if self.imported_context is None:
            return

        if self.imported_context.nav_type != self.current_nav_type:
            return

        title = self.ui.title_text().strip()
        description = self.ui.description_text().strip()
        if not title or not description:
            return

        theme = self.selected_theme()
        if theme is None:
            return

        token = self.option_api_token()
        if not token:
            return

        request_country_code = self.ui.request_country_code()
        helper_country_code = self.ui.helper_country_code()

        try:
            payload = build_submit_payload(
                self.imported_context,
                theme,
                title,
                description,
                request_country_code,
                helper_country_code,
                self.ui.is_test_request(),
            )
            response = ApiClient(
                INTEGRATION_GENEALOGY_REQUESTS_PATH,
                token,
                base_url=self.api_base_url,
            ).create_request(payload)
        except Exception as exc:  # pylint: disable=broad-except
            print_exception_diagnostic("GeneHelp request submission failed.")
            self.show_notification(self.user_message_for_exception(exc), "error")
            return

        self.requests_loaded = False
        self.show_notification(_("Genealogy request created successfully"))
        self.reset_successfully_submitted_form()
        self.open_created_request(response)

    def selected_theme(self):
        """Return the selected request topic."""
        if self.imported_context is None:
            return None

        selected_key = self.ui.selected_theme_key(self.imported_context.nav_type)
        if not selected_key:
            return None

        return theme_for_key(self.imported_context.nav_type, selected_key)

    def open_created_request(self, response: dict) -> None:
        """Open created request."""
        client = ApiClient(
            INTEGRATION_GENEALOGY_REQUESTS_PATH,
            self.option_api_token(),
            base_url=self.api_base_url,
        )
        url = client.absolute_url(
            response.get("edit_url") or edit_url_from_public_url(response.get("url") or "")
        )
        if url:
            webbrowser.open(url)
        else:
            print_error_diagnostic("GeneHelp create response has no url for edit page.")

    def reset_successfully_submitted_form(self) -> None:
        """Reset the form after successful submission."""
        if self.imported_context is None:
            self.ui.set_submit_sensitive(False)
            return

        self.imported_context = None
        self.ui.reset_imported_payload(self.current_nav_type)

    def update_submit_button_state(self) -> None:
        """Update whether the submit button is enabled."""
        self.ui.set_submit_sensitive(self.can_submit())

    def can_submit(self) -> bool:
        """Return whether the current form can be submitted."""
        return (
            self.imported_context is not None
            and self.imported_context.nav_type == self.current_nav_type
            and bool(self.ui.title_text().strip())
            and bool(self.ui.description_text().strip())
            and self.selected_theme() is not None
            and bool(self.option_api_token())
        )

    def load_cached_countries(self) -> None:
        """Load cached country options into the form."""
        if self.ui.country_options_loaded():
            return

        repository = CountryRepository(self.option_api_token(), base_url=self.api_base_url)
        cached_countries = repository.load_cached()
        if cached_countries:
            self.ui.set_countries(cached_countries)
            self.update_submit_button_state()
            return

        self.update_submit_button_state()

    def load_countries(self) -> None:
        """Load country options for the request form."""
        if self.ui.country_options_loaded() or self.countries_fetching:
            return

        repository = CountryRepository(self.option_api_token(), base_url=self.api_base_url)
        cached_countries = repository.load_cached()
        if cached_countries:
            self.ui.set_countries(cached_countries)
            self.update_submit_button_state()
            return

        if not self.option_api_token():
            self.update_submit_button_state()
            return

        self.countries_fetching = True
        try:
            countries = repository.fetch()
            if countries:
                repository.save(countries)
                self.ui.set_countries(countries)
        except Exception:  # pylint: disable=broad-except
            print_exception_diagnostic(
                f"GeneHelp countries loading failed for base_url={self.api_base_url!r} "
                f"locale={repository.locale!r}."
            )
        finally:
            self.countries_fetching = False
            self.update_submit_button_state()

    def load_settings_countries(self):
        """Load country options for settings."""
        if hasattr(self, "ui") and self.ui.country_options_loaded():
            return self.ui.all_countries

        repository = CountryRepository(self.option_api_token(), base_url=self.api_base_url)
        cached_countries = repository.load_cached()
        if cached_countries:
            if hasattr(self, "ui") and not self.ui.country_options_loaded():
                self.ui.set_countries(cached_countries)
            return cached_countries

        if not self.option_api_token():
            return []

        try:
            countries = repository.fetch()
            if countries:
                repository.save(countries)
                if hasattr(self, "ui") and not self.ui.country_options_loaded():
                    self.ui.set_countries(countries)
            return countries
        except Exception:  # pylint: disable=broad-except
            print_exception_diagnostic(
                "GeneHelp settings countries loading failed for "
                f"base_url={self.api_base_url!r} locale={repository.locale!r}."
            )
            return []

    def load_cached_settings_countries(self) -> None:
        """Load cached country options into settings."""
        if self.default_request_country_widget is None:
            return
        if self.default_request_country_widget.country_options_loaded():
            return

        if hasattr(self, "ui") and self.ui.country_options_loaded():
            self.default_request_country_widget.set_countries(self.ui.all_countries)
            return

        repository = CountryRepository(self.option_api_token(), base_url=self.api_base_url)
        cached_countries = repository.load_cached()
        if cached_countries:
            self.default_request_country_widget.set_countries(cached_countries)

    def load_genealogy_requests(self, show_error_notification: bool = False) -> None:
        """Load the owner genealogy request list."""
        if self.requests_loaded or self.requests_fetching:
            return

        token = self.option_api_token()
        if not token:
            return

        self.load_cached_countries()
        self.requests_fetching = True
        try:
            groups = GenealogyRequestRepository(token, base_url=self.api_base_url).fetch()
            self.ui.set_genealogy_requests(groups)
            self.requests_loaded = True
        except Exception as exc:  # pylint: disable=broad-except
            self.log_genealogy_requests_loading_error(exc)
            self.ui.show_genealogy_requests_error()
            if show_error_notification:
                self.show_api_error_notification(exc)
        finally:
            self.requests_fetching = False

    def refresh_genealogy_requests(self) -> None:
        """Reload the owner genealogy request list."""
        if self.requests_fetching:
            return

        self.requests_loaded = False
        self.ui.set_requests_refresh_visible(False)
        self.load_genealogy_requests(show_error_notification=True)

    def load_help_offer(self, show_error_notification: bool = False) -> None:
        """Load the owner help profile."""
        if self.help_offer_loaded or self.help_offer_fetching:
            return

        token = self.option_api_token()
        if not token:
            return

        self.load_countries()
        self.help_offer_fetching = True
        try:
            offer = HelpOfferRepository(token, base_url=self.api_base_url).fetch()
            if offer is not None:
                self.ui.set_help_offer(offer)
                self.help_offer_loaded = True
        except Exception as exc:  # pylint: disable=broad-except
            print_exception_diagnostic("GeneHelp help offer loading failed.")
            self.ui.show_help_offer_error()
            if show_error_notification:
                self.show_api_error_notification(exc)
        finally:
            self.help_offer_fetching = False

    def refresh_help_offer(self) -> None:
        """Reload the owner help profile."""
        if self.help_offer_fetching:
            return

        self.help_offer_loaded = False
        self.ui.set_help_offer_refresh_visible(False)
        self.load_help_offer(show_error_notification=True)

    @staticmethod
    def open_genealogy_request(url: str) -> None:
        """Open genealogy request."""
        webbrowser.open(url)

    def show_notification(self, message: str, notification_type: str = "success") -> None:
        """Show a floating notification."""
        self.notifications.show(message, notification_type)

    def show_api_error_notification(self, exc: Exception) -> None:
        """Show a localized API error notification when one is available."""
        message = api_error_message_for_exception(exc)
        if message:
            self.show_notification(message, "error")

    @staticmethod
    def log_genealogy_requests_loading_error(exc: Exception) -> None:
        """Log genealogy requests loading error."""
        status = getattr(exc, "status", None)
        if isinstance(status, int) and status >= 400:
            print_exception_diagnostic(
                f"GeneHelp genealogy requests list loading failed with HTTP status {status}."
            )
        else:
            print_exception_diagnostic("GeneHelp genealogy requests loading failed.")

    @staticmethod
    def user_message_for_exception(exc: Exception) -> str:
        """User message for exception."""
        detail = api_error_message_for_exception(exc)
        if detail:
            message = _("Could not create the GeneHelp request.")
            return _("%s %s") % (message, detail)

        message = _("Could not create the GeneHelp request. Please try again.")
        status = getattr(exc, "status", None)
        if isinstance(status, int):
            detail = str(exc).strip()
            if detail:
                return _("%s HTTP status: %s. %s") % (message, status, detail)
            return _("%s HTTP status: %s.") % (message, status)
        detail = str(exc).strip()
        if detail:
            return _("%s Reason: %s") % (message, detail)
        return _("%s HTTP status: missing.") % message


def edit_url_from_public_url(url: str) -> str:
    """Edit url from public url."""
    normalized = (url or "").strip().rstrip("/")
    if not normalized:
        return ""
    if normalized.endswith("/edit"):
        return normalized
    return f"{normalized}/edit"


def api_error_message_for_exception(exc: Exception) -> str:
    """Return a localized user message for a GeneHelp API exception."""
    code = getattr(exc, "code", "")
    if not isinstance(code, str) or not code:
        return ""

    return api_error_message_for_code(
        code,
        getattr(exc, "retry_after_seconds", None),
    )


def api_error_message_for_code(code: str, retry_after_seconds: int | None = None) -> str:
    """Return a localized user message for a GeneHelp API error code."""
    retry_after_minutes = retry_after_minutes_from_seconds(retry_after_seconds)

    if code == "too_many_requests" and retry_after_minutes is not None:
        return _("Too many requests were sent. Wait %(minutes)s minute(s) and try again.") % {
            "minutes": retry_after_minutes,
        }

    messages = {
        "http_error": _("GeneHelp rejected the request."),
        "internal_server_error": _("GeneHelp could not process the request right now."),
        "integration_token_invalid": _("The GeneHelp integration token is invalid or revoked."),
        "integration_token_missing": _(
            "Add the GeneHelp integration token in the gramplet settings."
        ),
        "integration_user_inactive": _(
            "The GeneHelp account for this integration token is inactive or not verified."
        ),
        "method_not_allowed": _("This GeneHelp API endpoint does not support the request method."),
        "resource_not_found": _("The GeneHelp API endpoint was not found."),
        "too_many_requests": _("Too many requests were sent. Wait a moment and try again."),
        "upstream_service_unavailable": _(
            "A GeneHelp upstream service is temporarily unavailable."
        ),
        "validation_failed": _(
            "GeneHelp rejected the request data. Check the title, description, "
            "countries, and media file."
        ),
    }

    return messages.get(code, "")


def retry_after_minutes_from_seconds(seconds: int | None) -> int | None:
    """Convert Retry-After seconds to a user-facing rounded-up minute count."""
    if seconds is None or seconds <= 0:
        return None

    return max(1, (seconds + 59) // 60)

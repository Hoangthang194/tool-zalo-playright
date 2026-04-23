from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from browser_automation.application.ports.zalo_workspace_store import ZaloWorkspaceStore
from browser_automation.application.use_cases._click_target_support import (
    normalize_click_target_name,
    normalize_selector_kind,
    normalize_selector_value,
)
from browser_automation.domain.exceptions import (
    ZaloClickTargetConflictError,
    ZaloClickTargetNotFoundError,
)
from browser_automation.domain.zalo_workspace import (
    SavedZaloClickTarget,
    ZaloWorkspaceLibrary,
)


@dataclass(frozen=True, slots=True)
class ZaloClickTargetUpsertRequest:
    name: str
    selector_kind: str
    selector_value: str
    click_target_id: str | None = None


@dataclass(frozen=True, slots=True)
class ZaloClickTargetManagerState:
    click_targets: tuple[SavedZaloClickTarget, ...]
    selected_click_target_id: str | None


class ZaloClickTargetManagerUseCase:
    def __init__(self, workspace_store: ZaloWorkspaceStore) -> None:
        self._workspace_store = workspace_store

    def load_state(self) -> ZaloClickTargetManagerState:
        return self._build_state(self._normalized_library(self._workspace_store.load()))

    def select_click_target(self, click_target_id: str) -> ZaloClickTargetManagerState:
        library = self._normalized_library(self._workspace_store.load())
        self._find_click_target(click_target_id, library)
        updated_library = ZaloWorkspaceLibrary(
            accounts=library.accounts,
            click_targets=library.click_targets,
            selected_account_id=library.selected_account_id,
            selected_click_target_id=click_target_id,
        )
        self._workspace_store.save(updated_library)
        return self._build_state(updated_library)

    def save_click_target(self, request: ZaloClickTargetUpsertRequest) -> ZaloClickTargetManagerState:
        library = self._normalized_library(self._workspace_store.load())
        target_name = normalize_click_target_name(request.name)
        selector_kind = normalize_selector_kind(request.selector_kind)
        selector_value = normalize_selector_value(request.selector_value)

        self._ensure_unique_name(target_name, request.click_target_id, library)

        click_target = SavedZaloClickTarget(
            id=request.click_target_id or uuid4().hex,
            name=target_name,
            selector_kind=selector_kind,
            selector_value=selector_value,
        )
        next_targets = self._replace_or_append_target(click_target, library.click_targets)
        updated_library = ZaloWorkspaceLibrary(
            accounts=library.accounts,
            click_targets=next_targets,
            selected_account_id=library.selected_account_id,
            selected_click_target_id=click_target.id,
        )
        self._workspace_store.save(updated_library)
        return self._build_state(updated_library)

    def delete_click_target(self, click_target_id: str) -> ZaloClickTargetManagerState:
        library = self._normalized_library(self._workspace_store.load())
        self._find_click_target(click_target_id, library)
        next_targets = tuple(target for target in library.click_targets if target.id != click_target_id)
        next_selected_click_target_id = library.selected_click_target_id
        remaining_ids = {target.id for target in next_targets}
        if next_selected_click_target_id not in remaining_ids:
            next_selected_click_target_id = next_targets[0].id if next_targets else None

        updated_library = ZaloWorkspaceLibrary(
            accounts=library.accounts,
            click_targets=next_targets,
            selected_account_id=library.selected_account_id,
            selected_click_target_id=next_selected_click_target_id,
        )
        self._workspace_store.save(updated_library)
        return self._build_state(updated_library)

    def _build_state(self, library: ZaloWorkspaceLibrary) -> ZaloClickTargetManagerState:
        return ZaloClickTargetManagerState(
            click_targets=library.click_targets,
            selected_click_target_id=library.selected_click_target_id,
        )

    def _normalized_library(self, library: ZaloWorkspaceLibrary) -> ZaloWorkspaceLibrary:
        click_target_ids = {target.id for target in library.click_targets}
        selected_click_target_id = library.selected_click_target_id
        if selected_click_target_id not in click_target_ids:
            selected_click_target_id = library.click_targets[0].id if library.click_targets else None

        return ZaloWorkspaceLibrary(
            accounts=library.accounts,
            click_targets=library.click_targets,
            selected_account_id=library.selected_account_id,
            selected_click_target_id=selected_click_target_id,
        )

    def _replace_or_append_target(
        self,
        click_target: SavedZaloClickTarget,
        existing_targets: tuple[SavedZaloClickTarget, ...],
    ) -> tuple[SavedZaloClickTarget, ...]:
        next_targets: list[SavedZaloClickTarget] = []
        replaced = False
        for current_target in existing_targets:
            if current_target.id == click_target.id:
                next_targets.append(click_target)
                replaced = True
            else:
                next_targets.append(current_target)
        if not replaced:
            next_targets.append(click_target)
        return tuple(next_targets)

    def _find_click_target(
        self,
        click_target_id: str,
        library: ZaloWorkspaceLibrary,
    ) -> SavedZaloClickTarget:
        for click_target in library.click_targets:
            if click_target.id == click_target_id:
                return click_target
        raise ZaloClickTargetNotFoundError(f"Saved click target not found: {click_target_id}")

    def _ensure_unique_name(
        self,
        target_name: str,
        current_click_target_id: str | None,
        library: ZaloWorkspaceLibrary,
    ) -> None:
        expected_name = target_name.casefold()
        for click_target in library.click_targets:
            if click_target.id == current_click_target_id:
                continue
            if click_target.name.casefold() == expected_name:
                raise ZaloClickTargetConflictError(
                    f"A click target named '{target_name}' already exists."
                )

"""Project-specific adjustments for the built-in ok-script task pages."""


def move_group_task_info_below_cards(main_window, group_name="全自動"):
    """Keep a grouped task page's status/log card below its task cards."""
    for tab in getattr(main_window, "grouped_task_tabs", ()):
        if getattr(tab, "group_name", None) != group_name:
            continue

        info_container = getattr(tab, "task_info_container", None)
        layout = getattr(tab, "vBoxLayout", None)
        if info_container is None or layout is None:
            return False

        layout.removeWidget(info_container)
        layout.addWidget(info_container)
        return True

    return False


def move_group_navigation_before_capture(main_window, group_name="全自動"):
    """Move a grouped task page before the built-in capture page in navigation."""
    group_tab = next(
        (
            tab
            for tab in getattr(main_window, "grouped_task_tabs", ())
            if getattr(tab, "group_name", None) == group_name
        ),
        None,
    )
    capture_tab = getattr(main_window, "start_tab", None)
    navigation = getattr(main_window, "navigationInterface", None)
    navigation_container = getattr(navigation, "panel", navigation)
    if group_tab is None or capture_tab is None or navigation_container is None:
        return False

    items = getattr(navigation_container, "items", {})
    group_item = items.get(group_tab.objectName())
    capture_item = items.get(capture_tab.objectName())
    if group_item is None or capture_item is None:
        return False

    group_widget = getattr(group_item, "widget", group_item)
    capture_widget = getattr(capture_item, "widget", capture_item)
    layout = navigation_container.topLayout
    capture_index = layout.indexOf(capture_widget)
    if capture_index < 0:
        return False

    layout.removeWidget(group_widget)
    layout.insertWidget(capture_index, group_widget)
    return True


def select_group_as_default_page(main_window, group_name="全自動"):
    """Select a grouped task page as the page shown when the window opens."""
    group_tab = next(
        (
            tab
            for tab in getattr(main_window, "grouped_task_tabs", ())
            if getattr(tab, "group_name", None) == group_name
        ),
        None,
    )
    if group_tab is None or not hasattr(main_window, "switchTo"):
        return False

    main_window.switchTo(group_tab)
    stacked_widget = getattr(main_window, "stackedWidget", None)
    return stacked_widget is None or stacked_widget.currentWidget() is group_tab


def select_group_after_stop_notification(
    main_window, message, group_name="全自動"
):
    """Return to the grouped task page after ok-script handles a task stop."""
    if message != "Stopped":
        return False
    return select_group_as_default_page(main_window, group_name)

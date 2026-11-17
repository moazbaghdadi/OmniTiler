pragma ComponentBehavior: Bound
import QtQuick
import qs.Ui as Ui
import qs.Commons as Commons

Ui.Panel {
    id: root
    property Item anchorItem: null
    property var service: null
    property int workspace: 0
    property var initialRatios: [30, 40, 30]
    manageIpc: false
    function showSettings() {
        workspace = service && service.state.current_workspace ? service.state.current_workspace : 0
        initialRatios = service && service.state.profile ? service.state.profile.ratios : [30, 40, 30]
        let content = panel.contentView
        if (content && typeof content.cancel === "function") content.cancel()
        root.open()
    }
    Ui.KeyboardPanel {
        id: panel
        bar: root.bar
        anchorItem: root.anchorItem
        owner: root
        open: root.opened
        readonly property var contentView: panel.loadedContent
        focusTarget: contentView ? contentView.focusItem : null
        contentWidth: panel.fittedContentWidth(Commons.Style.space(390))
        contentHeight: panel.fittedContentHeight(panel.loadedContentHeight)
        content: Component {
            Flickable {
                id: viewport
                property alias focusItem: settingsContent
                implicitHeight: settingsContent.implicitHeight
                contentHeight: settingsContent.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                interactive: contentHeight > height
                Keys.onEscapePressed: root.close()
                SettingsContent {
                    id: settingsContent
                    width: viewport.width
                    service: root.service
                    workspace: root.workspace
                    initialRatios: root.initialRatios
                    onDismissed: root.close()
                }
                function cancel() { settingsContent.cancel() }
            }
        }
    }
}

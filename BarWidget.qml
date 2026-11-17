pragma ComponentBehavior: Bound
import QtQuick
import qs.Ui
import qs.Commons as Commons
import "TextSafety.js" as TextSafety

BarWidget {
    id: root
    moduleName: "theboxer71.omnitiler"
    property var service: null
    implicitWidth: button.implicitWidth
    implicitHeight: barSize
    Commons.Translations { id: strings; directory: Qt.resolvedUrl("i18n") }
    SettingsPanel { id: settingsPanel; bar: root.bar; anchorItem: button; service: root.service }
    readonly property bool opened: settingsPanel.opened
    function open() { settingsPanel.showSettings() }
    function close() { settingsPanel.close() }

    // Service registration can finish after the widget is instantiated.
    function findService() {
        service = bar && bar.shell ? bar.shell.serviceFor(moduleName) : null
    }
    Component.onCompleted: findService()
    onBarChanged: findService()
    Timer { interval: 1000; running: true; repeat: true; onTriggered: root.findService() }

    function tooltip() {
        if (!service) return strings.t("starting")
        let s = service.state
        let profile = s.profile || { ratios: [30, 40, 30], overflow: "stack" }
        let lines = [strings.t("workspace").arg(s.current_workspace || "—")
                .arg(strings.t(s.current_active ? "on" : "off")),
            strings.t("layout").arg(Commons.I18n.formatNumber(profile.ratios[0]))
                .arg(Commons.I18n.formatNumber(profile.ratios[1]))
                .arg(Commons.I18n.formatNumber(profile.ratios[2]))
                .arg(strings.t(profile.overflow === "stack" ? "stack" : "overflow")),
            strings.t("automatic").arg(strings.t(s.auto_running ? "on" : "off"))]
        if (s.active) {
            for (let i = 0; i < s.workspaces.length; i++) {
                let w = s.workspaces[i]
                let slots = (s.counts || {})[String(w)] || {}
                lines.push(strings.t("occupancy").arg(Commons.I18n.formatNumber(w))
                    .arg(Commons.I18n.formatNumber(slots.left || 0))
                    .arg(Commons.I18n.formatNumber(slots.center || 0))
                    .arg(Commons.I18n.formatNumber(slots.right || 0)))
            }
        }
        if (s.error) lines.push(s.error)
        lines.push(strings.t("move"))
        lines.push(strings.t(s.current_active ? "disable" : "enable"))
        lines.push(strings.t("controls"))
        return lines.join("\n")
    }

    BarIconButton {
        id: button
        bar: root.bar
        active: root.service ? root.service.active : false
        activeColor: Commons.Color.accent
        dimmed: !button.active
        // The shell owns this text sink. Escape markup in compositor errors.
        tooltipText: TextSafety.escapeMarkup(root.tooltip())
        onPressed: function(mouseButton) {
            if (mouseButton === Qt.LeftButton && root.service) root.service.toggle()
            if (mouseButton === Qt.RightButton && root.service) {
                if (settingsPanel.opened) root.close()
                else root.open()
            }
            if (mouseButton === Qt.MiddleButton && root.service) root.service.toggleAuto()
        }
        iconComponent: Component {
            Item {
                Row {
                    anchors.centerIn: parent
                    spacing: 2
                    Repeater {
                        model: [4, 6, 4]
                        Rectangle {
                            required property int modelData
                            required property int index
                            width: modelData
                            height: 13
                            radius: 1
                            color: button.active && index === 1 ? Commons.Color.accent : "transparent"
                            border.width: 1
                            border.color: button.active ? Commons.Color.accent : button.foreground
                        }
                    }
                }
            }
        }
    }
}

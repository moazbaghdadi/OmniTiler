pragma ComponentBehavior: Bound
import QtQuick
import qs.Ui as Ui
import qs.Commons as Commons

FocusScope {
    id: root
    property var service: null
    property int workspace: 0
    property var initialRatios: [30, 40, 30]
    property bool editing: false
    property var editingId: null
    property int pendingRequest: 0
    property string error: ""
    readonly property var fonts: Commons.Style.font
    readonly property var presets: service && service.state.presets ? service.state.presets : []
    readonly property var currentRatios: {
        if (!service) return initialRatios
        let s = service.state
        let profile = s.profiles && s.profiles[String(workspace)]
        if (!profile && s.current_workspace === workspace) profile = s.profile
        return profile ? profile.ratios : initialRatios
    }
    readonly property var draft: [Number(leftField.text), Number(centerField.text), Number(rightField.text)]
    readonly property real total: draft[0] + draft[1] + draft[2]
    readonly property bool valid: leftField.text.trim() !== "" && centerField.text.trim() !== ""
        && rightField.text.trim() !== "" && draft.every(n => Number.isFinite(n) && (n === 0 || n >= 5))
        && Math.abs(total - 100) <= 0.001
    implicitHeight: layout.implicitHeight
    signal dismissed()
    Commons.Translations { id: strings; directory: Qt.resolvedUrl("i18n") }

    function label(values) {
        return values.map(n => Commons.I18n.formatNumber(n) + "%").join(" / ")
    }
    function edit(preset) {
        if (pendingRequest) return
        editingId = preset ? preset.id : null
        let values = preset ? preset.ratios : currentRatios
        leftField.text = String(values[0])
        centerField.text = String(values[1])
        rightField.text = String(values[2])
        error = ""
        editing = true
        Qt.callLater(function() { leftField.forceActiveFocus(); leftField.selectAll() })
    }
    function cancel() {
        if (pendingRequest) return
        editing = false
        error = ""
        root.forceActiveFocus()
    }
    function apply(preset) {
        if (!service || pendingRequest || workspace <= 0) return
        error = ""
        pendingRequest = service.applyPreset(preset.id, workspace)
        responseTimeout.restart()
    }
    function save() {
        if (!service || pendingRequest || workspace <= 0 || !valid) return
        error = ""
        pendingRequest = service.savePreset(editingId, draft, workspace)
        responseTimeout.restart()
    }
    Keys.onEscapePressed: event => {
        if (editing && !pendingRequest) cancel()
        else root.dismissed()
        event.accepted = true
    }
    Timer {
        id: responseTimeout
        interval: 10000
        onTriggered: { root.pendingRequest = 0; root.error = strings.t("panel.timeout") }
    }
    Connections {
        target: root.service
        function onCompleted(requestId, success, message) {
            if (requestId !== root.pendingRequest) return
            responseTimeout.stop()
            root.pendingRequest = 0
            root.error = success ? "" : message
            if (success) {
                root.editing = false
                root.forceActiveFocus()
            }
        }
    }

    component Label: Text {
        textFormat: Text.PlainText
        color: Commons.Color.foreground
        font.family: root.fonts.family
        font.pixelSize: root.fonts.body
        wrapMode: Text.WordWrap
    }

    Column {
        id: layout
        width: root.width
        spacing: Commons.Style.space(12)
        Label { text: strings.t("panel.title"); font.bold: true; font.pixelSize: root.fonts.body + 2 }
        Label {
            width: parent.width
            text: root.workspace > 0 ? strings.t("panel.workspace").arg(Commons.I18n.formatNumber(root.workspace))
                                     : strings.t("panel.noWorkspace")
            opacity: 0.75
        }
        Label { width: parent.width; text: strings.t("panel.current").arg(root.label(root.currentRatios)) }

        Flickable {
            id: presetList
            width: parent.width
            height: Math.min(presetRows.implicitHeight, Commons.Style.space(244))
            contentHeight: presetRows.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            interactive: contentHeight > height
            visible: !root.editing
            Column {
                id: presetRows
                width: presetList.width
                spacing: Commons.Style.space(6)
                Repeater {
                    model: root.presets
                    Row {
                        id: presetRow
                        required property var modelData
                        width: presetRows.width
                        spacing: Commons.Style.space(8)
                        Ui.Button {
                            id: applyButton
                            objectName: "applyPreset_" + presetRow.modelData.id
                            width: presetRow.width - editButton.width - presetRow.spacing
                            height: Commons.Style.space(64)
                            focusable: true
                            enabled: root.workspace > 0 && !root.pendingRequest
                            selected: JSON.stringify(presetRow.modelData.ratios) === JSON.stringify(root.currentRatios)
                            bordered: true
                            Accessible.name: strings.t("panel.apply").arg(root.label(presetRow.modelData.ratios))
                            onClicked: root.apply(presetRow.modelData)
                            onActiveFocusChanged: if (activeFocus) presetList.contentY = Math.max(0,
                                Math.min(presetRow.y, presetList.contentHeight - presetList.height))
                            Column {
                                anchors.centerIn: parent
                                width: parent.width - Commons.Style.space(24)
                                spacing: Commons.Style.space(6)
                                RatioPreview {
                                    width: parent.width
                                    height: Commons.Style.space(14)
                                    ratios: presetRow.modelData.ratios
                                    selected: applyButton.selected
                                }
                                Label {
                                    width: parent.width
                                    horizontalAlignment: Text.AlignHCenter
                                    text: root.label(presetRow.modelData.ratios)
                                    color: applyButton.selected ? Commons.Color.background : Commons.Color.foreground
                                }
                            }
                        }
                        Ui.Button {
                            id: editButton
                            objectName: "editPreset_" + presetRow.modelData.id
                            text: strings.t("panel.edit")
                            anchors.verticalCenter: parent.verticalCenter
                            focusable: true
                            enabled: !root.pendingRequest
                            onClicked: root.edit(presetRow.modelData)
                            onActiveFocusChanged: if (activeFocus) presetList.contentY = Math.max(0,
                                Math.min(presetRow.y, presetList.contentHeight - presetList.height))
                        }
                    }
                }
            }
        }
        Ui.Button {
            objectName: "addPreset"
            visible: !root.editing
            width: parent.width
            text: strings.t("panel.add")
            focusable: true
            bordered: true
            enabled: root.workspace > 0 && !root.pendingRequest && root.presets.length < 16
            onClicked: root.edit(null)
        }
        Column {
            visible: root.editing
            width: parent.width
            spacing: Commons.Style.space(10)
            Label { text: strings.t(root.editingId ? "panel.editTitle" : "panel.addTitle"); font.bold: true }
            RatioPreview { objectName: "draftPreview"; width: parent.width; height: Commons.Style.space(24); ratios: root.valid ? root.draft : [30, 40, 30]; selected: root.valid }
            Row {
                id: fields
                width: parent.width
                spacing: Commons.Style.space(10)
                Column {
                    width: (fields.width - 2 * fields.spacing) / 3
                    spacing: Commons.Style.space(6)
                    Label { text: strings.t("panel.left") }
                    Ui.TextField {
                        id: leftField
                        objectName: "leftRatio"
                        width: parent.width
                        enabled: !root.pendingRequest
                        maximumLength: 6
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        Accessible.name: strings.t("panel.left")
                        onAccepted: root.save()
                    }
                }
                Column {
                    width: (fields.width - 2 * fields.spacing) / 3
                    spacing: Commons.Style.space(6)
                    Label { text: strings.t("panel.center") }
                    Ui.TextField {
                        id: centerField
                        objectName: "centerRatio"
                        width: parent.width
                        enabled: !root.pendingRequest
                        maximumLength: 6
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        Accessible.name: strings.t("panel.center")
                        onAccepted: root.save()
                    }
                }
                Column {
                    width: (fields.width - 2 * fields.spacing) / 3
                    spacing: Commons.Style.space(6)
                    Label { text: strings.t("panel.right") }
                    Ui.TextField {
                        id: rightField
                        objectName: "rightRatio"
                        width: parent.width
                        enabled: !root.pendingRequest
                        maximumLength: 6
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        Accessible.name: strings.t("panel.right")
                        onAccepted: root.save()
                    }
                }
            }
            Label {
                width: parent.width
                text: strings.t("panel.total").arg(Number.isFinite(root.total) ? Commons.I18n.formatNumber(root.total) : "—")
            }
            Label { width: parent.width; text: strings.t("panel.validation"); opacity: 0.7; font.pixelSize: root.fonts.bodySmall }
            Row {
                width: parent.width
                spacing: Commons.Style.space(8)
                Ui.Button {
                    objectName: "savePreset"
                    text: strings.t(root.pendingRequest ? "panel.saving" : "panel.save")
                    enabled: root.valid && root.workspace > 0 && !root.pendingRequest
                    focusable: true
                    bordered: true
                    onClicked: root.save()
                }
                Ui.Button { text: strings.t("panel.cancel"); enabled: !root.pendingRequest; focusable: true; onClicked: root.cancel() }
            }
        }
        Label { width: parent.width; visible: root.error !== ""; text: root.error }
        Label { width: parent.width; text: strings.t("panel.scope"); opacity: 0.65; font.pixelSize: root.fonts.bodySmall }
    }
}

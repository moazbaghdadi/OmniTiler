import QtQuick
import QtTest
import Quickshell
import qs.Commons as Commons
import "../.." as Plugin

Window {
    id: window
    visible: true
    width: 422
    height: content.implicitHeight + 32
    color: Commons.Color.background
    QtObject {
        id: service
        signal completed(int requestId, bool success, string message)
        property var state: ({current_workspace: 4, profile: {ratios: [30,40,30]},
            profiles: {}, presets: [{id: "balanced", ratios: [30,40,30]},
                                    {id: "wide-center", ratios: [25,50,25]}]})
        property int next: 0
        property var last: null
        function applyPreset(id, workspace) { last = {id: id, workspace: workspace}; return ++next }
        function savePreset(id, ratios, workspace) { last = {id: id, ratios: ratios, workspace: workspace}; return ++next }
    }
    Plugin.SettingsContent { id: content; x: 16; y: 16; width: window.width - 32; service: service; workspace: 4 }
    TestCase {
        id: tests
        name: "PresetPanel"
        when: false
        function require(value, message) { if (!value) throw new Error(message) }
        function click(name) {
            wait(30) // Let visibility and the panel's size settle before hit-testing.
            let button = findChild(content, name)
            require(button !== null, "Missing button " + name)
            mouseClick(button, button.width / 2, button.height / 2)
        }
        function runChecks() {
            click("applyPreset_wide-center")
            require(service.last.id === "wide-center" && service.last.workspace === 4, "Apply must target panel workspace")
            service.completed(content.pendingRequest, true, "")
            click("editPreset_balanced")
            require(content.editing && content.editingId === "balanced", "Edit existing preset")
            let left = findChild(content, "leftRatio")
            let center = findChild(content, "centerRatio")
            let right = findChild(content, "rightRatio")
            left.text = "20"; center.text = "50"; right.text = "20"
            require(!content.valid, "Reject total below 100")
            content.save()
            require(!content.pendingRequest, "Invalid form must not submit")
            center.text = "60"
            require(content.valid, "Accept total 100")
            click("savePreset")
            require(service.last.id === "balanced" && service.last.ratios[1] === 60, "Save edited ratios")
            service.completed(content.pendingRequest, false, "Disk full")
            require(content.editing && content.error === "Disk full", "Keep draft on failed save")
            content.save()
            service.completed(content.pendingRequest, true, "")
            require(!content.editing, "Close editor only after successful save")
            click("addPreset")
            require(content.editing && content.editingId === null, "New preset must not overwrite existing ID")
            wait(30)
            keyClick(Qt.Key_Escape)
            require(!content.editing, "Escape cancels editor")
            content.edit(null)
            wait(30)
            left.text = "0"; center.text = "70"; right.text = "30"
            require(content.valid, "Zero disables a column")
            require(findChild(content, "draftPreview").columnCount === 2, "Preview removes disabled column")
            center.text = "0"; right.text = "100"
            require(content.valid, "Allow one full-width column")
            require(findChild(content, "draftPreview").columnCount === 1, "Preview supports full-width column")
            right.text = "0"
            require(!content.valid, "Reject disabling every column")
            left.text = "20.5"; center.text = "49"; right.text = "30.5"
            require(content.valid, "Accept fractional proportions")
            keyClick(Qt.Key_Return)
            require(service.last.id === null && service.last.ratios[0] === 20.5, "Enter saves a new preset")
            service.completed(content.pendingRequest, true, "")
            console.log("OMNITILER_PANEL_TESTS_PASSED")
        }
    }
    function capture(name, next) {
        let directory = Quickshell.env("OMNITILER_TEST_ARTIFACTS")
        if (!directory) { next(); return }
        content.grabToImage(result => { result.saveToFile(directory + "/" + name + ".png"); next() })
    }
    Timer {
        interval: 300
        running: true
        onTriggered: window.capture("presets", function() {
            try {
                tests.runChecks()
                content.edit(service.state.presets[0])
                editorCapture.start()
            } catch (e) { console.error("OMNITILER_PANEL_TEST_FAILED", e); Qt.exit(1) }
        })
    }
    Timer { id: editorCapture; interval: 100; onTriggered: window.capture("editor", function() { Qt.quit() }) }
}

pragma ComponentBehavior: Bound
import QtQuick
import qs.Commons as Commons

Row {
    id: root
    property var ratios: [30, 40, 30]
    property bool selected: false
    readonly property int columnCount: ratios.filter(n => n > 0).length
    spacing: Commons.Style.space(3)
    Repeater {
        model: root.ratios
        Rectangle {
            required property real modelData
            required property int index
            visible: modelData > 0
            width: Math.max(0, (root.width - Math.max(0, root.columnCount - 1) * root.spacing) * modelData / 100)
            height: root.height
            radius: Commons.Style.space(2)
            color: root.selected ? Commons.Color.accent : Commons.Color.foreground
            opacity: index === 1 ? 0.9 : 0.45
        }
    }
}

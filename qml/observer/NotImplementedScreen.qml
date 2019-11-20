import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1

// Placeholder for Screens Not Yet Implemented

ScrollView {
    id: scrollView1
    function page_state_id() { // for transitions
        return "not_implemented_state";
    }
    width: parent.width
    height: parent.height

    flickableItem.interactive: true

    ListView {
        id: listView1
        anchors.fill: parent
        model: NotImplementedModel {}
        delegate: DaylightDelegate {
            text: detailName
            //  modelData
        }
    }
    style: ScrollViewStyle {
        transientScrollBars: true
        handle: Item {
            implicitWidth: 14
            implicitHeight: 26
            Rectangle {
                color: "#424246"
                anchors.fill: parent
                anchors.topMargin: 6
                anchors.leftMargin: 4
                anchors.rightMargin: 4
                anchors.bottomMargin: 6
            }
        }
        scrollBarBackground: Item {
            implicitWidth: 14
            implicitHeight: 26
        }
    }
}

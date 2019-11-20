import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Window 2.2


import "../common"

Item {

    Component.onDestruction: {
        tbdSM.to_home_state()
    }
    RowLayout {
        id: rwlHeader
        x: 20
        y: 20
        spacing: 20
        Label {
            id: lblHaul
            text: "Haul ID"
            font.pixelSize: 24
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
        }
        TrawlBackdeckTextFieldDisabled {
            id: tfHaul
            font.pixelSize: 24
            text: stateMachine.haul["haul_number"]
            Layout.preferredWidth: 220
            Layout.preferredHeight: this.height
        }
    }


    TrawlBackdeckButton {
        text: qsTr("Done")
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        onClicked: screens.pop()
    }
}
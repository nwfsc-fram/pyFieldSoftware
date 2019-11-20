import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1

import "../common"

Item {
    TrawlBackdeckButton {
        text: qsTr("Done")
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        onClicked: screens.pop()
    }
}
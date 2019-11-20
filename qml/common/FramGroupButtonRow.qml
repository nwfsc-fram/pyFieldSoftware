import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2

import "../common"
import "."

Row {
    // Note: in hosting QML, requires:
    //    ExclusiveGroup { id: groupbuttonGroup }
    // (See CatchCategoriesDetailsScreen.qml)

    id: fgbRow
    property string label: ""
    property int labelWidth: root.width/2

    Label {
        text: label
        width: labelWidth
        height: 80
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 25
    }
}

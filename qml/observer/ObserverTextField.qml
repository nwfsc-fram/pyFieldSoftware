import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

// Simpler looking textfield that is gray when readOnly
TextField {
    id: control


    property string textColor: "black"
//    property alias textColor : textColor

    style: TextFieldStyle {
        textColor: control.textColor
        background: Rectangle {
            radius: 2
            implicitWidth: 100
            implicitHeight: 30
            border.color: "#333"
            border.width: 1
            color: control.readOnly ? "#DDDDDD": "white"
        }
    }
}

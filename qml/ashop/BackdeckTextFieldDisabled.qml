import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

TextField {
    font.pixelSize: 24
    readOnly: true
    style: TextFieldStyle {
        background: Rectangle {
            implicitWidth: 120
//            color: "#eeeeee"
            color: "#f3f3f3"
            border.width: 1
            border.color: "#bbbbbb"
        }
    }
}
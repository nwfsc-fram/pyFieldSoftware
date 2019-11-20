import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0

ComboBox {
    width: parent.width/2 - 10
    editable: false // This won't use the font used by label, bug?
    height: 80
    property int downButtonWidth: 25
    property int fontsize: 25
    property int dropdownfontsize: 18
    style: ComboBoxStyle {
        dropDownButtonWidth: downButtonWidth

        // This hides the dropdown arrow:
//        background: Rectangle {
//            id: rectCategory
//            height: 80
//            color: "white"
//            radius: 5
//            border.width: 2
//        }

        font.pixelSize: fontsize
        label: Text {
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: fontsize
            color: "black"
            text: control.currentText
        }


        // drop-down customization here
        property Component __dropDownStyle: MenuStyle {
            __maxPopupHeight: 600
            __menuItemType: "comboboxitem"

            itemDelegate.label:             // an item text
                Text {
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    font.pixelSize: dropdownfontsize
                    font.capitalization: Font.Capitalize
                    color: styleData.selected ? "white" : "black"
                    text: styleData.text
                }

            itemDelegate.background: Rectangle {  // selection of an item
                radius: 2
                color: styleData.selected ? "darkGray" : "transparent"
            }

            __scrollerStyle: ScrollViewStyle { }
        }
        property Component __popupStyle: Style {
            property int __maxPopupHeight: 400
            property int submenuOverlap: 0

            property Component frame: Rectangle {
                width: (parent ? parent.contentWidth : 0)
                height: (parent ? parent.contentHeight : 0) + 2
                border.color: "black"
                property real maxHeight: 500
                property int margin: 1
            }

            property Component menuItemPanel: Text {
                text: "NOT IMPLEMENTED"
                color: "red"
                font {
                    pixelSize: 20
                    bold: true
                }
            }

            property Component __scrollerStyle: null
        }
    }
}

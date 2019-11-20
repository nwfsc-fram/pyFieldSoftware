import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0

ComboBox {
    style: ComboBoxStyle {
        dropDownButtonWidth: 25
/*
        background: Rectangle {
            id: rectCategory
            height: 80
            color: "white"
            radius: 5
            border.width: 2
        }
*/
//        font.pixelSize: 20
        label: Text {
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: 20
            color: "black"
            text: control.currentText
        }


        // drop-down customization here
        property Component __dropDownStyle: MenuStyle {
            __maxPopupHeight: 600
            __menuItemType: "comboboxitem"



            frame: Rectangle {              // background
                color: "#fff"
      //          border.width: 2
     //           radius: 5
            }

            itemDelegate.label:             // an item text
                Text {
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    font.pixelSize: 20
                 //   font.family: "Courier"
                //    font.capitalization: Font.SmallCaps
  //                  color: styleData.selected ? "white" : "black"
                    text: styleData.text
                }

//            itemDelegate.background: Rectangle {  // selection of an item
//                radius: 2
//                color: styleData.selected ? "darkGray" : "transparent"
//            }

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

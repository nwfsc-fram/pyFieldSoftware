import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

import "../common"

Item {

    signal resetfocus
    onResetfocus: {
        // Just set focus to something benign
        lblWeight.forceActiveFocus();
    }


    property FramAutoComplete current_ac // Currently active autocomplete

    Keys.forwardTo: [framNumPadDetails] // Required for capture of Enter key

    Connections {
        target: observerFooterRow
        onClickedDone: {
            obsSM.to_previous_state();
            stackView.pop();
        }
    }

    Component.onCompleted: {
        init_ui();
    }

    function init_ui() {

        slidingKeyboardBS.showbottomkeyboard(false);
    }

    ListView
    {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: parent.height - toolBar.height - 15

        function resetfocus() {  // For numpad
            lblWeight.forceActiveFocus();
        }

        FramBigScrollView
        {
            id: svBioDetails

            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: slidingKeyboardBS.top

            flickableItem.interactive: true
            flickableItem.flickableDirection: Flickable.VerticalFlick
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

            handleWidth: 50 // custom property

            property int labelColWidth: 300
            property int dataColWidth: Math.min(400, root.width/2 - handleWidth)

            Column {
                id: detailsCol
                spacing: 4


                Row {
                    Label {
                        id: lblWeight
                        text:  qsTr("Weight (kg)")
                        width: svBioDetails.labelColWidth
                        height: 80
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                    }
                    TextField {
                        id: textWeightValue
                        width: svBioDetails.dataColWidth
                        height: 80
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                        placeholderText: qsTr("Weight (kg)")
                        onFocusChanged: {
                            if (focus){
                                framNumPadDetails.visible = true
                                framNumPadDetails.attachresult_tf(textWeightValue)
                                framNumPadDetails.setnumpadhint(placeholderText)
                                framNumPadDetails.setnumpadvalue(text)
                                framNumPadDetails.setstate("popup_basic")
                                framNumPadDetails.show(true)
                            } else {
                                framNumPadDetails.show(false)
                            }
                        }
                    }
                }

                Row {
                    Label {
                        id: lblLength
                        text:  qsTr("Length (cm)")
                        width: svBioDetails.labelColWidth
                        height: 80
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                    }
                    TextField {
                        id: textLength
                        width: svBioDetails.dataColWidth
                        height: 80
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                        placeholderText: qsTr("Length (cm)")
                        onFocusChanged: {
                            if (focus){
                                framNumPadDetails.attachresult_tf(textLength)
                                framNumPadDetails.setnumpadhint(placeholderText)
                                framNumPadDetails.setnumpadvalue(text)
                                framNumPadDetails.setstate("popup_basic")
                                framNumPadDetails.show(true)
                            } else {
                                framNumPadDetails.show(false)
                            }
                        }
                    }
                }


                FramGroupButtonRow {
                     id: sexRow
                     label: "Sex"
                     labelWidth: svBioDetails.labelColWidth
                     ExclusiveGroup { id: sexGroup }
                     property int bwidth: svBioDetails.dataColWidth/4 // used by FramGroupButtonRowButton
                     FramGroupButtonRowButton {
                         id: buttonDispM
                         text: "Male"
                         exclusiveGroup: sexGroup
                         onClicked: {
                             if (checked) {
                                console.debug("Male Checked")
//                                ccModel.setProperty(ccIndex, "retain_discard", "D");
                             }
                         }
                     }
                     FramGroupButtonRowButton {
                         id: buttonDispF
                         text: "Female"
                         exclusiveGroup: sexGroup
                         onClicked: {
                             if (checked) {
                                console.debug("Female Checked")
//                                ccModel.setProperty(ccIndex, "retain_discard", "D");
                             }
                         }
                     }
                     FramGroupButtonRowButton {
                         id: buttonDispU
                         text: "Undet."
                         exclusiveGroup: sexGroup
                         onClicked: {
                             if (checked) {
                                console.debug("Undet. Checked")
//                                ccModel.setProperty(ccIndex, "retain_discard", "D");
                             }
                         }
                     }
                     FramGroupButtonRowButton {
                         id: buttonDispNA
                         text: "N/A"
                         exclusiveGroup: sexGroup
                         onClicked: {
                             if (checked) {
                                console.debug("N/A Checked")
//                                ccModel.setProperty(ccIndex, "retain_discard", "D");
                             }
                         }
                     }
                }

                Row {
                    Label {
                        id: lblViability
                        text: qsTr("Viability")
                        width: svBioDetails.labelColWidth
                        height: 80
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                    }

                    FramComboBox {
                        id: comboViability
                        width: svBioDetails.dataColWidth
                        downButtonWidth: 75
                        model: ListModel {}  // TODO{wsmith} Viability options = ?
                        textRole: 'text'  // req'd for QAbstractListModel
                    }
                }

                Row {
                    Label {
                        text: qsTr("Adipose Present")
                        width: svBioDetails.labelColWidth
                        height: 80
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                    }
                    CheckBox {
                        text: qsTr("")
                        checked: false
                        width: svBioDetails.dataColWidth
                        height: 80
                        style: CheckBoxStyle {
                            indicator: Rectangle {
                                implicitWidth: 40
                                implicitHeight: 40
                                radius: 3
                                border.color: control.activeFocus ? "darkblue" : "gray"
                                border.width: 1
                                Rectangle {
                                    visible: control.checked
                                    color: "#555"
                                    border.color: "#333"
                                    radius: 1
                                    anchors.margins: 4
                                    anchors.fill: parent
                                }
                            }
                        }
                    }
                }
                Row {
                    Label {
                        text: qsTr("Eggs Present")
                        width: svBioDetails.labelColWidth
                        height: 80
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                    }
                    CheckBox {
                        text: qsTr("")
                        checked: false
                        width: svBioDetails.dataColWidth
                        height: 80
                        style: CheckBoxStyle {
                            indicator: Rectangle {
                                implicitWidth: 40
                                implicitHeight: 40
                                radius: 3
                                border.color: control.activeFocus ? "darkblue" : "gray"
                                border.width: 1
                                Rectangle {
                                    visible: control.checked
                                    color: "#555"
                                    border.color: "#333"
                                    radius: 1
                                    anchors.margins: 4
                                    anchors.fill: parent
                                }
                            }
                        }
                    }
                }

                BioDetailsBarcodeRow {
                    label: qsTr("Whole Specimen")
                    placeholderText: qsTr("Barcode #")
                    property string role: "specimen_barcode"
                    onChanged: {
                        console.debug("New barcode for " + label + ": " + text)
                    }
                }

                BioDetailsBarcodeRow {
                    label: qsTr("Fin Ray")
                    placeholderText: qsTr("Barcode #")
                    property string role: "finray_barcode"
                    onChanged: {
                        console.debug("New barcode for " + label + ": " + text)
                    }
                }

                BioDetailsBarcodeRow {
                    label: qsTr("Tissue")
                    placeholderText: qsTr("Barcode #")
                    property string role: "tissue_barcode"
                    onChanged: {
                        console.debug("New barcode for " + label + ": " + text)
                    }
                }

                BioDetailsBarcodeRow {
                    label: qsTr("Scales")
                    placeholderText: qsTr("Barcode #")
                    property string role: "scales_barcode"
                    onChanged: {
                        console.debug("New barcode for " + label + ": " + text)
                    }
                }

                BioDetailsBarcodeRow {
                    label: qsTr("Fin Clip")
                    placeholderText: qsTr("Barcode #")
                    property string role: "finclip_barcode"
                    onChanged: {
                        console.debug("New barcode for " + label + ": " + text)
                    }
                }

                BioDetailsBarcodeRow {
                    label: qsTr("Otolith")
                    placeholderText: qsTr("Barcode #")
                    property string role: "otolith_barcode"
                    onChanged: {
                        console.debug("New barcode for " + label + ": " + text)
                    }
                }

                BioDetailsBarcodeRow {
                    label: qsTr("Snout")
                    placeholderText: qsTr("Barcode #")
                    property string role: "snout_barcode"
                    onChanged: {
                        console.debug("New barcode for " + label + ": " + text)
                    }
                }

                Row {
                    Label {
                        id: lblBiosMethod
                        text: qsTr("Biosample Method")
                        width: svBioDetails.labelColWidth
                        height: 80
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                    }

                    FramComboBox {
                        id: comboBiosMethod
                        width: svBioDetails.dataColWidth
                        downButtonWidth: 75
                        model: ListModel {}  // TODO{wsmith} methods = ?
                        textRole: 'text'  // req'd for QAbstractListModel
                    }
                }

                BioDetailsBarcodeRow {
                    label: qsTr("Existing Tag #")
                    placeholderText: qsTr("Tag #")
                    property string role: "existing_tagnum"
                    onChanged: {
                        console.debug("New barcode for " + label + ": " + text)
                    }
                }

                //TODO{wsmith} Pictures = ?
                Row {
                    Label {
                        id: lblPictures
                        text:  qsTr("Pictures")
                        width: svBioDetails.labelColWidth
                        height: 80
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                    }
                    Label {
                        id: lblPicturesPlaceholder
                        text:  qsTr("[TBD]")
                        width: svBioDetails.dataColWidth
                        height: 80
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                    }
                }

                //TODO{wsmith} Special = ?
                Row {
                    Label {
                        text: qsTr("Comments")
                        width: svBioDetails.width
                        height: 100
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                    }
                }
                Row {
                    id: taRow
                    TextArea {
                        id: taComments
                        width: svBioDetails.width - svBioDetails.handleWidth
                        height: 400
                        font.pixelSize: 25
                        onFocusChanged: {
                            if(focus) {
                                var fi = svBioDetails.flickableItem;
                                fi.contentY = fi.contentHeight;
                                slidingKeyboardBS.showbottomkeyboard(true);
                                slidingKeyboardBS.keyboard.showCR(true);
                                slidingKeyboardBS.connect_ta(taComments);
                            }
                        }
//                        onTextChanged: {
//                            if (text.length > 0)
//                                ccModel.setProperty(ccIndex, "comments", text);
//                        }
//                        Component.onCompleted: {
//                            var curElem = ccModel.get(ccIndex);
//                            text = curElem.comments;
//                        }
                    }
               }


            } // Column
        } // ScrollView

        FramNumPad {
            id: framNumPadDetails
            x: 328
            y: 327
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            visible: false
            enable_audio: ObserverSettings.enableAudio
        }

        FramSlidingKeyboard {
            id: slidingKeyboardBS
            width: svBioDetails.width
            height: 500
            visible: false
            onButtonOk: {
                resetfocus();
            }
            onKeyEntry: {
                // Update cursor position on virtual key entry
                if (taComments.focus)
                    taComments.cursorPosition = taComments.text.length;
            }
        }
    }

}

import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

import "../common"
import "."  // For ObserverSettings
Item {
    id: detailsPageItem
    width: parent.width
    height: parent.height - framFooter.height
    signal resetfocus
    onResetfocus: {
        // "Clear" active focus by setting to a label
        observerLabel.forceActiveFocus();
    }

    property FramAutoComplete current_ac // Currently active autocomplete
    property TextField current_tf // Currently active textfield

    Keys.forwardTo: [framNumPadDetails, slidingKeyboard] // Required for capture of Enter key

    Component.onCompleted: {
        slidingKeyboard.showbottomkeyboard(false);
        if (appstate.firstRun)
            framHeader.show_back_arrow(false);
        if (appstate.currentObserver != null)
            tfObserverName.text = appstate.currentObserver;
    }

    Component.onDestruction: {
        validate_fields();
        framHeader.show_back_arrow(true);
    }

    Connections {
        target: observerFooterRow
        onClickedDone: {
            obsSM.to_previous_state();
            stackView.pop();
        }
    }

    function validate_fields() {
        if(tfObserverName.text.length > 0) {
            appstate.firstRun = false;
            appstate.currentObserver = tfObserverName.text;
            return true;
        }
        else {
            appstate.firstRun = true;
            return false;
        }
    }

    FramBigScrollView
    {
        id: svSettings
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: slidingKeyboard.top
        anchors.leftMargin: 50
        implicitHeight: 500

        flickableItem.interactive: true
        flickableItem.flickableDirection: Flickable.VerticalFlick
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

        handleWidth: 50 // property for big scrollbar
        property int textFieldHeight: 80

        property int labelColWidth: 300
        property int dataColWidth: Math.min( 400, root.width/2 - handleWidth) // limit width

        Column {
            id: detailsCol
            spacing: 4
            FramGroupButtonRow {
                 id: gearTypeRow
                 label: "Gear Type"
                 labelWidth: svSettings.labelColWidth
                 ExclusiveGroup { id: gearGroup }
                 property int bwidth: svSettings.dataColWidth/2 // used by FramGroupButtonRowButton

                 Component.onCompleted: {
                     if (appstate.isGearTypeTrawl) {
                         buttonGearTrawl.checked = true;
                     } else {
                         buttonGearFixed.checked = true;
                     }
                 }

                 FramGroupButtonRowButton {
                     id: buttonGearTrawl
                     text: "Trawl"
                     exclusiveGroup: gearGroup
                     onClicked: { // Is this needed? Copied from older code
                         appstate.isGearTypeTrawl = true;
                     }
                     Component.onCompleted: {
                         checked = appstate.isGearTypeTrawl;
                     }
                     onCheckedChanged: {
                         if(appstate.isGearTypeTrawl != checked) {
                             appstate.isGearTypeTrawl = checked;
                             mainPageModel.update_model(appstate.isGearTypeTrawl);
                             if (ObserverSettings.test_mode) {
                                 // Temporary: CLEAR ALL DATA
                                 console.warn("RESETTING IN-MEMORY DATA");
                                 appstate.reset();
                                 catchCategory.reset();
                                 countsWeights.reset();
                                 biospecimens.reset();
                             }
                         }
                     }
                 }
                 FramGroupButtonRowButton {
                     id: buttonGearFixed
                     text: "Fixed Gear"
                     exclusiveGroup: gearGroup
                     onClicked: {
                         appstate.isGearTypeTrawl = false;
                     }
                     Component.onCompleted: {
                         checked = !appstate.isGearTypeTrawl;
                     }
                 }
            }
            FramGroupButtonRow {
                 id: fisheryRow
                 label: "Fishery"
                 labelWidth: svSettings.labelColWidth
                 ExclusiveGroup { id: fisheryGroup }
                 property int bwidth: svSettings.dataColWidth/2 // used by FramGroupButtonRowButton
                 FramGroupButtonRowButton {
                     id: buttonCatchShares
                     text: "Catch Shares"
                     exclusiveGroup: fisheryGroup
                     Component.onCompleted: {
                         checked = appstate.defaultCatchShare;
                     }
                     onCheckedChanged: {
                         appstate.defaultCatchShare = checked;
                     }
                 }
                 FramGroupButtonRowButton {
                     id: buttonNoCatchShares
                     text: "Non-Catch Shares"
                     exclusiveGroup: fisheryGroup
                     Component.onCompleted: {
                         checked = !appstate.defaultCatchShare;
                     }
                 }
            }
            Row {
                Label {
                    id: observerLabel
                    text: qsTr("Observer Name")
                    width: svSettings.labelColWidth
                    height: svSettings.textFieldHeight
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25
                }
                TextField {
                    id: tfObserverName
                    height: svSettings.textFieldHeight
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25
                    width: svSettings.dataColWidth
                    placeholderText: observerLabel.text
                    onActiveFocusChanged: {
                        if (focus) {
                            autocomplete.suggest("observers");
                            slidingKeyboard.connect_tf(tfObserverName, placeholderText); // Connect TextField
                        }
                        slidingKeyboard.showbottomkeyboard(focus);
                    }
                }
            }
        }
    } // FramBigScrollView
    FramWideKeyboardAndList {
        id: slidingKeyboard
        desired_height: 365
        enable_audio: ObserverSettings.enableAudio
        onButtonOk: {
            resetfocus();
            if(current_ac)
                current_ac.showautocompletebox(false);
        }
    }

    FramNumPad {
        id: framNumPadDetails
        x: 328
        y: 327
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter
        visible: false
        enable_audio: ObserverSettings.enableAudio
    }

}

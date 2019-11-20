import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Window 2.2
import QtQuick.Extras 1.4

import "." // For ScreenUnits

Item {
    id: root
    visible: false

    width: parent.width * 0.5
    height: parent.height * 0.8

//    x: parent.width / 2 - width / 2
    x: 3*parent.width/4 - width/2
    y: parent.height / 2 - height / 2

    property string action_label: "<test>"

    property bool auto_hide: true  // Sets visible = false upon confirmation automatically.
    property bool auto_label: true  // Use template "Are you sure you want to _____ ?" for act_label


    signal setconfirmaction(string action)
    onSetconfirmaction: {
        action_label = action
    }

    signal show(string act_label, string act_name)
    onShow: {
        // act_label: Text box label (depends on auto_label)
        // act_name: the name of the action (returned on confirm/cancel signals)
        if (auto_label) {
            action_label = "Are you sure you want to \n" + act_label + "?"
        } else {
            action_label = act_label;
        }
        action_name = act_name;
        visible = true;
    }

    signal hide
    onHide: {
        visible = false;
    }

    signal confirmed()
    // OnConfirmed Triggered when user confirms "Yes"

    signal confirmedFunc(string action_name)
    // OnConfirmed Triggered when user confirms "Yes" + action_name

    signal cancelled()
    // onCancelled Triggered on "No"

    signal cancelledFunc(string action_name)
    // onCancelled Triggered on "No" + action_name


    property string action_name: ""

    Rectangle {
        id: rectangleNPBackground
        width: parent.width
        height: parent.height
        color: "#a4a4a4"

        MouseArea {
            anchors.fill: parent
        }

        Text {
            id: lblHeader
            anchors.top: parent.top
            anchors.topMargin: 20
            anchors.horizontalCenter: parent.horizontalCenter
            fontSizeMode: Text.HorizontalFit
            text: qsTr(action_label)
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: 24
        } // lblHeader

        TrawlBackdeckTableView {
            id: tvItems
            anchors.top: lblHeader.bottom
            anchors.topMargin: 20
            anchors.horizontalCenter: parent.horizontalCenter
//            x: rwlHeader.x
//            y: rwlHeader.y + rwlHeader.height + 30
            width: parent.width * 0.9
            height: parent.height - lblHeader.height - rwlButtons.height - 70
//            width: 600
//            height: main.height - rwlHeader.height - 130
            selectionMode: SelectionMode.SingleSelection
            headerVisible: true
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
            model: specialActions.model
            onClicked: {
                if (this.model.get(row).value)
                    numPad.textNumPad.text = this.model.get(row).value
                else
                    numPad.textNumPad.text = ""

                if (this.currentRow != -1) {
                    btnAssignTagId.state = qsTr("enabled")
                    btnPrintLabel.state = qsTr("enabled")
                } else {
                    btnAssignTagId.state = qsTr("disabled")
                    btnPrintLabel.state = qsTr("disabled")
                }
            }
            TableViewColumn {
                role: "principalInvestigator"
                title: "PI"
                width: 120
            }
            TableViewColumn {
                role: "specialAction"
                title: "Special Action"
                width: 240
            }
        } // tvItems

        Text {
            text: "These don't work yet!!!"
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            font.pixelSize: 48
        }

        RowLayout {
            id: rwlButtons
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 20
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 10

            TrawlBackdeckButton {
                id: btnOkay
                text: "OK"
                Layout.preferredHeight: this.height
                Layout.preferredWidth: this.width
                onClicked: {
                    confirmed(); // emit
                    confirmedFunc(action_name); // emit
                    if(auto_hide)
                        hide();
                }
            } // btnOkay
            TrawlBackdeckButton {
                id: btnCancel
                text: "Cancel"
                Layout.preferredHeight: this.height
                Layout.preferredWidth: this.width
                isDefault: true
                onClicked: {
                    cancelled();  // emit
                    cancelledFunc(action_name); // emit
                    if(auto_hide)
                        hide();
                }
            } // btnCancel
        }
    }
}

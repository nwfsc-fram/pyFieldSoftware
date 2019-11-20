import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Window 2.2
import QtQuick.Extras 1.4

import "." // For ScreenUnits

Item {
    id: confirmDlg
    visible: false

    width: 360
    height: 230

    x: parent.width / 2 - width / 2
    y: parent.height / 2 - height / 2

    property string action_label: "<test>"

    property bool auto_hide: true  // Sets visible = false upon confirmation automatically.
    property bool auto_label: true  // Use template "Are you sure you want to _____ ?" for act_label
    // Message alignment: default to center alignment, but allow override via this property alias:
    property alias textHorizontalAlignment: textConfirm.horizontalAlignment

    // Properties related to the calculating of buttonYes.x and buttonNo.x
    // (for centering the button set when a non-default width (not 360) is specified).
    property int buttonHorizontalSeparation: 32
    property int twoButtonSpan: buttonYes.width + buttonHorizontalSeparation + buttonNo.width
    property alias buttonYesX: buttonYes.x  // Allow Yes button's x offset to be specified.

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

        Button {
            id: buttonNo
            x: buttonYes.x + buttonYes.width + buttonHorizontalSeparation
            y: 124
            width: 156
            height: 78
            isDefault: true
            onClicked: {
                cancelled();  // emit
                cancelledFunc(action_name); // emit
                if(auto_hide)
                    hide();
            }
            style: ButtonStyle {
                label: Component {
                    Text {
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        font.family: "Helvetica"
                        font.pixelSize: 25
                        text: qsTr("No")
                    }
                }
            }
        }

        Button {
            id: buttonYes
            x: Math.round((parent.width - twoButtonSpan)/2)  // Align the button set in the center horizontally.
            y: 124
            width: 141
            height: 78
            onClicked: {
                confirmed(); // emit
                confirmedFunc(action_name); // emit
                if(auto_hide)
                    hide();
            }
            style: ButtonStyle {
                label: Component {
                    Text {
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        font.family: "Helvetica"
                        font.pixelSize: 25
                        text: qsTr("Yes")
                    }
                }
            }
        }

        Text {
            id: textConfirm
            anchors.left: parent.left
            anchors.margins: 10
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: buttonYes.top
            fontSizeMode: Text.HorizontalFit
            text: qsTr(action_label)
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: 24
        }


    }
}

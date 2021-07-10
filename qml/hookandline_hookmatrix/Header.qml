import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Controls.Styles 1.3

import "."

BorderImage {
    id: toolBar
    border.bottom: 35
    width: parent.width
    height: 45

    property alias backButton: backButton
    property alias forwardButton: forwardButton
    property string forwardTitle: ""  // sets text label for forward nav
    property string backwardTitle: ""  // sets text label for backward nav
    property string title: "Title"  // center title text
    property int nav_click_width: 100 // width of toolbar area that can be clicked to nav back/fwd
    property bool forwardEnabled: false  // allow disabling of forward nav
    property bool forwardVisible: false  // allow hiding of forward nav
    property variant forwardAction: null;  // do we need this???

    signal backClicked();
    onBackClicked: {
//        if (screens.busy)
//            return;
//        screens.pop();
        console.info('clicking back, screen: ' + stateMachine.screen);

        switch (stateMachine.screen) {
            case "drops":
                smHookMatrix.to_sites_state();
                break;
            case "gear_performance":
                smHookMatrix.to_drops_state();
                break;
            case "hooks":
                smHookMatrix.to_drops_state();
                break;
        }
    }

    signal forwardEnable(bool enable)
    onForwardEnable: {
        forward_enabled = enable;
        console.debug("Forward button enable: " + forward_enabled);
    }
    signal forwardClicked()
    onForwardClicked: {
        // #143: refactored for nav between gear perf and hooks screens
        var current_screen = stateMachine.screen
        if (forwardEnabled) {
            console.log("Clicked forward from " + stateMachine.screen)
            switch(current_screen) {
                case "gear_performance":
                    smHookMatrix.to_hooks_state()
                    break;
                case "hooks":
                    smHookMatrix.to_gear_performance_state()
                    break;
            }
        }
    }
/*  #143: commenting out but leaving for reference, see onForwardClicked above for current functionality
    signal forwardClicked(string to_state, string text_clicked);
    onForwardClicked: {
        if (stackView.busy || !forward_enabled)
            return;
        console.log("Clicked " + text_clicked + " > " + to_state);
        // Trigger state machine transition BEFORE push
        // (data will change upon push)
//        obsSM.to_next_state(); // generic logical next state button
        switch (to_state) {
            // TODO: look up these qml file paths via state name
            case "drops_state":
//                stackView.push(Qt.resolvedUrl("DropsScreen.qml"));
                smHookMatrix.to_drops_state();
                break;
            case "hooks_state":
//                stackView.push(Qt.resolvedUrl("HooksScreen.qml"));
                smHookMatrix.to_hooks_state();
                break;
        }

    }
*/
    function show_buttons(show) {
        // Keeping this here in case we want to add buttons again
        quickButtonRow.visible = show;
    }
    function check_button(btname, check) {
        switch(btname) {
            case "CC":
                buttonHeaderCC.checked = check;
                break;
            case "Sp":
                buttonHeaderSpecies.checked = check;
                break;
            case "Wt":
                buttonHeaderWeights.checked = check;
                break;
            case "Bio":
                buttonHeaderBiospecimens.checked = check;
                break;
        }
    }
    function show_back_arrow(show) { backButton.visible = show; }
    function show_fwd_arrow(show) { backButton.visible = show; }

    Rectangle {
        id: backButton
        width: opacity ? 60 : 0
        anchors.left: parent.left
        anchors.leftMargin: 20
        visible: (title == "Sites") ? false : true;
//        opacity: stackView.depth > 1 ? 1 : 0
        anchors.verticalCenter: parent.verticalCenter
        antialiasing: true
        height: 40
        radius: 4
        color: "transparent"
        Behavior on opacity { NumberAnimation{} }
        Image {
            anchors.verticalCenter: parent.verticalCenter
            source: Qt.resolvedUrl("/resources/images/navigation_previous_item_dark.png")
        }
        MouseArea {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: nav_click_width
            onClicked: {
                backClicked();
//                screens.pop()
//                backClicked(obsSM.leftButtonStateName, textLeftBanner.text);
            }
        }
    } // backButton
    Text {
        id: textLeftBanner
        font.pixelSize: 22
//        Behavior on x { NumberAnimation{ easing.type: Easing.OutCubic} }
        x: backButton.x + backButton.width + 20
        anchors.verticalCenter: parent.verticalCenter
        color: "black"
        text: backwardTitle

    } // textLeftBanner
    Text {
        id: textTitle
        font.pixelSize: 25
//        Behavior on x { NumberAnimation{ easing.type: Easing.OutCubic} }
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        color: "black"
        text: title
    } // textTitle
    Text {
        id: textRightBanner
        font.pixelSize: 22
//        Behavior on x { NumberAnimation{ easing.type: Easing.OutCubic} }
        x: forwardButton.x - this.width - 20
        anchors.verticalCenter: parent.verticalCenter
        color: "black"
        text: forwardTitle
        visible: forwardVisible
    } // textRightBanner
    Rectangle {
        id: forwardButton
        width: opacity ? 60 : 0
        anchors.right: parent.right
        anchors.rightMargin: 20
        anchors.verticalCenter: parent.verticalCenter
        antialiasing: true
        visible: forwardVisible
        height: 40
        radius: 4
        color: "transparent"
//        visible: textRightBanner.text == "" ? false: true
//        Behavior on opacity { NumberAnimation{} }
        Image {
            anchors.verticalCenter: parent.verticalCenter
            source: Qt.resolvedUrl("/resources/images/navigation_next_item_dark.png")
        }
        MouseArea {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: nav_click_width

            onClicked: {
                forwardClicked()
            }
        }
    } // forwardButton
}

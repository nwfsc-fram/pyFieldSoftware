import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Controls.Styles 1.3

import "."

BorderImage {
    id: toolBar
    border.bottom: 35
//        source: "/images/toolbar.png"
    width: parent.width
    height: 45

    property alias textLeftBanner: textLeftBanner
    property alias textRightBanner: textRightBanner
    property alias dlgCWNoCountCheck: dlgCWNoCountCheck
    property string title: "Title"

    // width of toolbar area that can be clicked to nav back/fwd
    property int nav_click_width: 300
    property bool backward_enabled: true
    property bool forward_enabled: true

    // opacity of backward or forward banner text and arrow when disabled
    property real navigation_disabled_opacity: 0.3

    signal backwardEnable(bool enable)
    onBackwardEnable: {
        backward_enabled = enable;
        console.debug("Backward button enable: " + backward_enabled);
    }

    signal revertToCW
    // dlg called onExit of CWs screen
    ProtocolWarningDialog {
        // FIELD-2039: warning if all baskets are no count, dlg sends you back to CW tab or ignores
        id: dlgCWNoCountCheck
        message: "You have not entered a count yet!\nAt least one basket must have a real count. \nEnsure you will be able to enter a count\nlater if dismissing this warning."
        btnOKText:"Return to\nCatch/Weights"
        btnAckText: "Dismiss: I'm going\nto have another\nbasket later\nI promise"
        onAccepted: {
            if (stackView.currentItem.page_state_id() === 'tabs_screen') {
                revertToCW()  // signal tabs_screen to change index to 2 (counts/weights)
            } else if (stackView.currentItem.page_state_id() === 'hauls_state') {
                /* if you've gone all the way to hauls...
                1. go to haul details state
                2. push haul details qml
                3. go to next state (cc_entry screen)
                4. push tab screen
                5. reactivate old selected catch, and species records
                6. revert to CW tab
                */
                var speciesCompItemId = appstate.catches.species.currentSpeciesCompItemID
                var catchId = appstate.catches.currentCatchID
                obsSM.to_haul_details_state()
                stackView.push(Qt.resolvedUrl("HaulDetailsScreen.qml"));
                obsSM.to_next_state()
                stackView.push(Qt.resolvedUrl("ObserverTabsScreen.qml"))
                appstate.catches.reactivateCC(catchId)
                appstate.catches.species.reactivateSpecies(speciesCompItemId)
                revertToCW()
            }
        }
        onRejected: {
            console.info("ignoring no count for now...")
        }
    }

    signal backClicked(string to_state, string text_clicked);
    onBackClicked: {
        if (!backward_enabled)
            return;
        console.info("Clicked " + text_clicked + ", goal state = " + to_state);
        if (stackView.busy || !backward_enabled)
            return;
        while(stackView.depth > 1 &&
              stackView.currentItem.page_state_id() !== to_state) {
              stackView.pop();
//            console.log("Now on " + stackView.currentItem.page_state_id())
        }
        console.info("Transitioned back to " + stackView.currentItem.page_state_id())

        obsSM.to_previous_state(); // generic logical previous state button
    }

    signal forwardEnable(bool enable)
    onForwardEnable: {
        forward_enabled = enable;
        console.debug("Forward button enable: " + forward_enabled);
    }

    // Transition from a Catch Categories subsidiary screen to a Tab (Species or Biospecimens)
    signal jumpFromCCSubsidiaryScreenToTab()
    onJumpFromCCSubsidiaryScreenToTab: {
        if (stackView.currentItem.page_state_id() === "cc_details_state" ||
            stackView.currentItem.page_state_id() === "cc_details_fg_state" ||
            stackView.currentItem.page_state_id() === "cc_baskets_state") {
            stackView.pop()
        }
    }

    signal forwardClicked(string to_state, string text_clicked);
    onForwardClicked: {
        if (stackView.busy || !forward_enabled)
            return;
        console.log("Clicked " + text_clicked + " > " + to_state);
        // Trigger state machine transition BEFORE push
        // (data will change upon push)
        obsSM.to_next_state(); // generic logical next state button
        switch (to_state) {
            // TODO: look up these qml file paths via state name
          case "sets_state":
              stackView.push(Qt.resolvedUrl("SetsScreen.qml"));
              break;
          case "hauls_state":
              stackView.push(Qt.resolvedUrl("HaulsScreen.qml"));
              break;
          case "cc_entry_state":
              stackView.push(Qt.resolvedUrl("ObserverTabsScreen.qml"));
              break;
          case "cc_entry_fg_state":
              stackView.push(Qt.resolvedUrl("ObserverTabsFGScreen.qml"));
              break;
          case "cc_baskets_state":
              console.debug("Transition to CC Baskets Screen");
              stackView.pop();
              stackView.push(Qt.resolvedUrl("CatchCategoriesBasketsScreen.qml"));
              break;
          case "tabs_screen":
              jumpFromCCSubsidiaryScreenToTab();
              break;
        }
    }


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

    function show_back_arrow(show) {
        backButton.visible = show;
    }
    function show_fwd_arrow(show) {
        forwardButton.visible = show;
    }

    Row {
        // These are not currently used, but left here for potential future use
        id: quickButtonRow
        x: toolBar.width - width
        spacing: 5
        visible: false
        ObserverHeaderButton {
            // Quick jump to Catch Categories
            id: buttonHeaderCC
            text: qsTr("CC")
        }
        ObserverHeaderButton {
            // Quick jump to Species
            id: buttonHeaderSpecies
            text: qsTr("Sp")
        }
        ObserverHeaderButton {
            // Quick jump to Weights/ Counts
            id: buttonHeaderWeights
            text: qsTr("Wt")
        }
        ObserverHeaderButton {
            // Quick jump to Biospecimens
            id: buttonHeaderBiospecimens
            text: qsTr("Bio")
        }
    }

    Rectangle {
        id: backButton
        width: opacity ? 60 : 0
        anchors.left: parent.left
        anchors.leftMargin: 20
        // Opacity of button:
        //      Don't show at all on Home screen.
        //      Show fully opaque if backward navigation is enabled.
        //      Show mostly transparent if backward navigation is disabled.
        opacity: stackView.depth > 1 ?
            (!backward_enabled ? navigation_disabled_opacity : 1) : 0
        visible: (textLeftBanner.text == "") ? false : true
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
                backClicked(obsSM.leftButtonStateName, textLeftBanner.text);
            }
        }
    }


    Text {
        id: textLeftBanner
        font.pixelSize: 22
//        Behavior on x { NumberAnimation{ easing.type: Easing.OutCubic} }
        x: backButton.x + backButton.width + 20
        anchors.verticalCenter: parent.verticalCenter
        color: "black"
        opacity: backward_enabled ? 1.0 : navigation_disabled_opacity

        text: obsSM.bannerLeftText
        
    }

    Text {
        id: textTitle
        font.pixelSize: 25
//        Behavior on x { NumberAnimation{ easing.type: Easing.OutCubic} }
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        color: "black"
        text: obsSM.titleText
    }

    Text {
        id: textRightBanner
        font.pixelSize: 22
//        Behavior on x { NumberAnimation{ easing.type: Easing.OutCubic} }
        x: forwardButton.x - this.width - 20
        anchors.verticalCenter: parent.verticalCenter
        color: "black"
        opacity: forward_enabled ? 1.0 : navigation_disabled_opacity
        text: obsSM.bannerRightText
        visible: true
    }

    Rectangle {
        id: forwardButton
        width: opacity ? 60 : 0
        anchors.right: parent.right
        anchors.rightMargin: 20
        anchors.verticalCenter: parent.verticalCenter
        antialiasing: true
        height: 40
        radius: 4
        color: "transparent"
        opacity: (textRightBanner.text == "" || !forward_enabled) ? navigation_disabled_opacity : 1.0
        visible: (textRightBanner.text == "") ? false : true
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
                forwardClicked(obsSM.rightButtonStateName, textRightBanner.text);
            }
        }
    }


}

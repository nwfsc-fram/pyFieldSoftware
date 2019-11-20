import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Window 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4
import QtQuick.Extras 1.0
import QtQuick.Dialogs 1.2
import QtQuick.Controls.Styles.Flat 1.0 as Flat

import "../common"
import "."

ApplicationWindow {
    id: login
    visible: true
    width: Screen.width
    height: Screen.height

    property alias loginStackView: stackLoginView
    property alias loginFooter: loginFooterRow
    property alias dlgDBSync: dlgDBSync

    Loader { id: pageLoader }

    style: ApplicationWindowStyle {
        background: Rectangle {
                    color: appstate.isTestMode ? "pink" : (appstate.isTrainingMode ? "yellow": ObserverSettings.default_bgcolor)
                }
    }

    onClosing: {
        soundPlayer.stop_thread()
    }

    function maximizeWindow() {
        // This routine is very sensitive to order, and changes might break fullscreen.
        login.x = 0;
        login.y = ObserverSettings.startup_small_window ? 50 : 0;
        if (ObserverSettings.startup_small_window) {
            login.width = 1280;
            login.height = 758;
        } else {
            console.debug("Setting Full Screen mode.")
            // Opens up in Win10 Tablet mode, but shows title bar
            // flags = Qt.CustomizeWindowHint | Qt.MaximizeUsingFullscreenGeometryHint;

            // Qt.WindowFullScreen causes odd navigation bugs
            // Current best compromise in Win10:
            visibility = Window.Maximized;
            flags = Qt.CustomizeWindowHint;
        }
    }

    function enableDebrieferWindow() {
        console.log("Enabling Debriefer Window Mode");
        login.visibility = Window.Maximized;
        login.flags = Qt.Window | Qt.WindowCloseButtonHint |
        Qt.WindowMinMaxButtonsHint | Qt.WindowTitleHint;
        login.width = 1280;
        login.height = 758;
    }

    Timer {
            id: timer
    }

    function delay(delayTime, cb) {
        timer.interval = delayTime;
        timer.repeat = false;
        timer.triggered.connect(cb);
        timer.start();
    }

    Component.onCompleted: {
        maximizeWindow();
    }

    StackView {
        id: stackLoginView
        objectName: "loginWindow"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: loginFooterRow.top
        focus: true

        initialItem: Item {
            width: parent.width
            height: parent.height

            GridLayout {
                id: loginGrid
                anchors.fill: parent
                columns: 3
                columnSpacing: 20

                FramLabel {
                    text: "Login"
                    font.bold: true
                    Layout.columnSpan: 3
                    Layout.alignment: Qt.AlignHCenter
                }
                Rectangle {
                        Layout.preferredWidth: 300
                        color: "transparent"
                }
                GridLayout {
                    columns: 1
                    Image {
                        id: wcgopLogo
                        source: appstate.isTrainingMode || appstate.isTestMode ? 'qrc:/resources/images/wcgop_logo_training.png' : 'qrc:/resources/images/wcgop_logo.png'
                        horizontalAlignment: Image.AlignHCenter
                        //visible: !appstate.isTestMode // Make it more obvious we're in test mode
                    }
                    Label {
                        text: "Version: " + appstate.optecsVersion
                        font.pixelSize: 24
                        Layout.preferredWidth: wcgopLogo.width
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap // Just in case build number gets long
                    }
                    Label {
                        text: "DB Version: " + appstate.dbVersion
                        font.pixelSize: 16
                        Layout.preferredWidth: wcgopLogo.width
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap // Just in case build number gets long
                    }
                    Label {
                        text: appstate.isTestMode ? "TEST MODE\n(" + appstate.optecsMode +" DB)" : "PRODUCTION DB"
                        color: appstate.isTestMode ? "red" : "black"
                        font.pixelSize: 24
                        Layout.preferredWidth: wcgopLogo.width
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap // Just in case build number gets long
                    }
                     Label {
                        text: "TRAINING MODE"
                        visible: appstate.isTrainingMode
                        font.pixelSize: 24
                        Layout.preferredWidth: wcgopLogo.width
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap // Just in case build number gets long
                    }

                }
                GridLayout {
                    id: idEntry
                    columns: 2
                    Layout.alignment: Qt.AlignHCenter
                    property int default_width: 300
                    FramLabel {
                        id: lblUsername
                        Layout.fillWidth: true
                        text: "User"
                        Layout.alignment: Layout.Right
                        horizontalAlignment: Text.AlignRight
                    }
                    TextField {
                        id: textUser
                        Layout.preferredWidth: idEntry.default_width
                        font.pixelSize: 24
                        Layout.preferredHeight: ObserverSettings.default_tf_height
                        Layout.alignment: Qt.AlignCenter
                        KeyNavigation.tab: textPassword
//                      focus: true
                        text: appstate.isTestMode ? (appstate.currentObserver ? appstate.currentObserver : "") : ""
                        onEditingFinished: {                            
                            save();
                        }
                        function open_username_keyboard() {
                            framKeyboard.placeholderText = "Username";
                            framKeyboard.connected_tf = textUser;
                            framKeyboard.passwordMode = false;
                            framKeyboard.set_caps(true);
                            framKeyboard.open();
                        }

                        function save() {
                            if (text != "") { // Handle bad user when they hit Login
                                appstate.currentObserver = text;
                                appstate.users.updateProgramsForUser(text);
                            }
                        }

                        onActiveFocusChanged: {
                            if (focus) {
                                open_username_keyboard();
                                focus=false;
                            }
                        }
                        Component.onCompleted: {
                             appstate.users.updateProgramsForUser(appstate.currentObserver);
                        }

                    }
                    FramLabel {
                        id: lblPassword
                        Layout.fillWidth: true
                        text: "Password"
                        horizontalAlignment: Text.AlignRight
                    }
                    TextField {
                        id: textPassword
                        echoMode: TextInput.Password
                        Layout.preferredWidth: idEntry.default_width
                        font.pixelSize: 24
                        Layout.preferredHeight: ObserverSettings.default_tf_height
                        Layout.alignment: Qt.AlignCenter
                        KeyNavigation.tab: buttonLogin
                        onActiveFocusChanged: {
                            if (focus) {
                                framKeyboard.placeholderText = "Password";
                                framKeyboard.connected_tf = this;
                                framKeyboard.passwordMode = true;
                                framKeyboard.set_caps(false);
                                framKeyboard.open();
                                focus=false;
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        color: "transparent"
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignCenter
                        Label {
                            id: lblPasswordExpiry
                            font.pixelSize: 20
                            text: "Password expiration: " + appstate.users.currentUserPwExpires
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        color: "transparent"
                    }
                    FramButton {
                        text: "Change Local Password"
                        Layout.alignment: Qt.AlignHCenter
                        fontsize: 19
                        onClicked: {
                            dlgChangePwd.userName = textUser.text;
                            dlgChangePwd.oldPassword = textPassword.text;
                            dlgChangePwd.open();
                        }
                    }

                    Rectangle {  // two-column spacer
                        Layout.fillWidth: true
                        Layout.preferredHeight: 20
                        Layout.columnSpan: 2
                        color: "transparent"
                    }

                    FramLabel {
                        id: lblRoles
                        Layout.fillWidth: true
                        text: "Program"
                        horizontalAlignment: Text.AlignRight
                    }

                    ObserverHomeButton {
                        id: btnCurrentProgram
                        Layout.alignment: Qt.AlignHCenter                        
                        text: dlgProgramPicker.currentProgram
                        fontsize: 19
                        onClicked: {
                            var model_rows = appstate.users.AvailablePrograms.rowCount();
                            if (model_rows > 0) {
                                dlgProgramPicker.open();
                            }
                        }

                        Connections {
                            target: appstate.users
                            onProgramModelChanged: {
                                var prog = appstate.users.currentProgramName;
                                if (prog) {
                                    dlgProgramPicker.currentProgram = prog;
                                }
                            }
                        }
                    }

                    FramLabel {
                        Layout.fillWidth: true
                        text: "Trip Type"
                        horizontalAlignment: Text.AlignRight
                    }

                    ExclusiveGroup {
                        id: groupTrawlGear
                    }
                    RowLayout {
                        spacing: 10
                        Layout.alignment: Qt.AlignCenter

                        ObserverGroupButton {
                            id: buttonTrawl
                            text: "Trawl"
                            checked: appstate.isGearTypeTrawl
                            exclusiveGroup: groupTrawlGear
                            onClicked: {
                                appstate.isGearTypeTrawl = true;                                
                            }
                        }
                        ObserverGroupButton {
                            id: buttonFixedGear
                            text: "Fixed Gear"
                            exclusiveGroup: groupTrawlGear
                            checked: !appstate.isGearTypeTrawl
                            onClicked: {
                                appstate.isGearTypeTrawl = false;                                
                            }
                        }



                    }

                    Rectangle {  // two-column spacer
                        Layout.fillWidth: true
                        Layout.preferredHeight: 50
                        Layout.columnSpan: 2
                        color: "transparent"
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        color: "transparent"
                    }

                    ObserverCheckBox {
                        id: debrieferMode
                        text: "Enable Debriefer Mode"
                        Layout.alignment: Qt.AlignCenter
                        visible: appstate.users.currentUserIsDebriefer

                        function setDebrieferMode() {
                            appstate.trips.setDebrieferMode(checked && appstate.users.currentUserIsDebriefer);
                            if(checked) {
                              enableDebrieferWindow();
                            }
                        }
                        onCheckedChanged: {
                            setDebrieferMode();
                        }
                        onVisibleChanged: {
                            if (!appstate.users.currentUserIsDebriefer) {
                                checked = false;
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        color: "transparent"
                        visible: debrieferMode.visible
                    }

                    ObserverHomeButton {
                        id: buttonLogin
                        text: "Login"
                        Layout.alignment: Qt.AlignCenter
                        fontsize: 20
                        Keys.onPressed: {
                            if (event.key === Qt.Key_Enter || event.key === Qt.Key_Return) {
                                clicked();
                            }
                        }
                        KeyNavigation.tab: textUser
                        onClicked: {
                            if (textUser.text == "") {
                                textUser.focus = true;
                                return;
                            }
                            if (!appstate.users.userExists(textUser.text)) {
                                noteBadUser.open();
                                return;
                            }
                            // FIELD-1866: Enabled all program types for FG
//                            if (appstate.isFixedGear && btnCurrentProgram.text === 'Catch Shares') { // Catch Shares + Fixed Gear = Bad
//                                noteBadPassword.message = "Catch Shares cannot\n have a Fixed Gear trip.\nSelect a different program\n or trip type.";
//                                noteBadPassword.open();
//                                return;
//                            }

                            if (!appstate.users.userLogin(textUser.text, textPassword.text)) {                                
                                if (ObserverSettings.allow_bad_password) {
                                    noteBadPassword.message = "Password incorrect, but\nTest mode allows login.";
                                    noteBadPassword.open();
                                } else {
                                    noteBadPassword.open();
                                    return;
                                }
                            }

                            if (!appstate.isTestMode) {
                                textUser.text = ""
                                textPassword.text = ""
                            }

                            // Hack to propagate debriefer mode in case debriefer logged out and in.
                            // Do this hack before reloading trips: debriefer mode affects trip list.
                            debrieferMode.setDebrieferMode();

                            appstate.trips.reloadTrips();
                            // hack to "clear" current trip ID if one exists but user changed

                            var previous_trip_id = appstate.trips.tripId;
                            appstate.trips.tripId = previous_trip_id;

                            if (!stackLoginView.busy) {
                                  framKeyboard.close();
                                dlgDBSync.download_only = false;
                                stackLoginView.push(Qt.resolvedUrl("ObserverHome.qml"));
                            }
                            if (ObserverSettings.enableAudio) {
                                soundPlayer.play_sound("login", false)
                            }
                        }
                    }
                    FramNoteDialog {
                        id: noteBadUser
                        message: "User name not found in database.\nCheck spelling or re-sync the DB."
                    }

                    FramNoteDialog {
                        id: noteBadPassword
                        message: "Password incorrect.\nYou may need to re-sync the DB."
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        color: "transparent"
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        color: "transparent"
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        color: "transparent"
                    }
                    ObserverHomeButton {
                        id: syncDB
                        text: "Retrieve Updates"
                        Layout.alignment: Qt.AlignCenter
                        fontsize: 20
                        onClicked: {
                            db_sync.updateDBSyncInfo();
                            dlgDBSync.initSync(textUser.text, textPassword.text);
                        }
                    }                    

                    Rectangle {
                        Layout.fillWidth: true
                        color: "transparent"
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignCenter
                        Label {
                            id: lblDBSync
                            font.pixelSize: 20
                            Layout.alignment: Qt.AlignHCenter
                            text: "Last DB sync: " + db_sync.dbSyncTime
                        }
                    }
                }
            }
        }

        delegate: StackViewDelegate {
            function transitionFinished(properties)
            {
                properties.exitItem.opacity = 1
            }

            pushTransition: StackViewTransition {
                PropertyAnimation {
                    target: enterItem
                    property: "opacity"
                    from: 0
                    to: 1
                }
                PropertyAnimation {
                    target: exitItem
                    property: "opacity"
                    from: 1
                    to: 0
                }
            }
        }
    }

    Rectangle { // Background
        anchors.fill: loginFooterRow
        color: "#BBBBBB"
    }

    ObserverFooterRow {
        id: loginFooterRow
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        width: parent.width
        height: 50
        state: "login"

        onClickedLogout: {
            appstate.users.logOut();
            stackLoginView.pop();
            state = "login";
            dlgDBSync.download_only = true;
        }
    }

    ObserverKeyboardDialog {
        id: framKeyboard
        placeholderText: ""

        onValueAccepted: {
            // console.log("Got value "+ accepted_value);
            textUser.save();
        }
    }

    ObserverDBSyncDialog {
        id: dlgDBSync
        download_only: true

    }

    ObserverChangePasswordDialog {
        id: dlgChangePwd
        onAccepted: {
            textPassword.text = validated_new_pw;
        }
    }

    ObserverProgramPickerDialog {
        id: dlgProgramPicker

        function setSelectedProgram() {
            // Set current program in python app
            console.log("Setting current program to " + currentProgram);
            appstate.users.currentProgramName = currentProgram;
            appstate.users.isFixedGear = appstate.isFixedGear;
        }

        onAccepted: {
            setSelectedProgram()
        }
    }

}


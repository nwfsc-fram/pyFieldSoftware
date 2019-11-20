import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"
import "."

Dialog {
    id: dlg
    width: 700
    height: 600
    title: "Local-only OPTECS Password Change"

    property alias userName: tfUsername.text
    property alias oldPassword: tfOldPw.text
    property string validated_new_pw: ""

    function validateWebPassword(password)

    {
        // Mostly copied directly from the Observer Web page
        // (refactored particularly glaring issues, use simple RE's

        // return === true if OK, or error message

        if (password.length < 8 || password.length > 15) {
            return "New password must be between 8 and 15 characters.";
        }

        var re = /[0-9]+/;
        if (null === re.exec(password)) {
            return "Your new password must contain at least one number.";
        }

        var re = /[A-Z]+/;
        if (null === re.exec(password)) {
            return "Your new password must contain at least one capital letter (A - Z).";
        }

        var re = /[`~!@#$%^\&\*()\-_+=?<>{}\[\]]/;
//        var validodd = "`~!@#$%^&*()-_+=?<>{}[]"
        if (null === re.exec(password)) {
            return "Your new password must contain at least one special character: `~!@#$%^&*()-_+=?<>{}[]";
        }

        // TODO this section should be rewritten,
        // leaving it for now due to its confounding nature
        var wassix = 0
        var isdups = 0
        for (var i = 0; i < password.length; i++) {
            var validchar = password.charAt(i);
            wassix = 0
            for (var j = 0; j < password.length; j++) {
                if (validchar.indexOf(password.charAt(
                                          j)) > -1) {
                    wassix = wassix + 1
                }
            }
            if (wassix > 1) {
                isdups = isdups + 1
                wassix = 0
            }
        }
        if ((password.length - isdups) < 6) {
            return "Your new password must contain six characters that do not occur more than once in the password.";
        }

        var re = /[ ]+/;
        if (re.exec(password) !== null) {
            return "Your new password must not contain a space.";
        }

        return true;
    }

    function check_password_history(username, password) {
        // Return true if password is in user history
        return appstate.users.isPasswordInHistory(username, password);
    }

    function validate_user_new_pw(username, old_pw, new_pw, repeat_new_pw) {

        // return === true if OK, or error message
        validated_new_pw = ""
        // validate username
        if (!appstate.users.userExists(username)) {
            return "Could not find username locally. You may need to re-sync the database."
        }

        // validate old password
        if (!appstate.users.userLogin(username, old_pw)) {
            return "Old password incorrect.\nRetry, or re-sync the DB\nwith current online password."
        }

        if (!new_pw || !old_pw || !repeat_new_pw) {
            return "Please enter all password fields."
        }

        if (new_pw.length > 0 && new_pw !== repeat_new_pw) {
            return "New passwords do not match."
        }

        var validate_result = validateWebPassword(new_pw);
        if (validate_result !== true) {
            return validate_result;
        }

        // in our case, we might not already have the old pw in history, set it here
        check_password_history(username, old_pw);

        // now check new pw (catches duplicates)
        if (check_password_history(username, new_pw)) {
            return "Password duplicate found in history. Choose new password.";
        }

        if (!appstate.users.userChangePassword(username, old_pw, new_pw)) {
            return "Error changing user password."
        }

        validated_new_pw = new_pw
        console.log("LOCAL Password for user " + username + " changed.")
        return true;
    }

    contentItem: Rectangle {
        id: rectPW
        color: "lightgray"

        GridLayout {
            anchors.fill: parent
            columns: 2

            FramLabel {
                Layout.columnSpan: 2
                text: "NOTE: Local-only password changes performed here\nwill also need to be performed on the Observer website."
                Layout.alignment: Qt.AlignCenter
                font.pixelSize: 18
            }

            FramLabel {
                text: "Username"
                font.pixelSize: 18
                Layout.leftMargin: 100
            }
            TextField {
                id: tfUsername
                placeholderText: "Username"
                font.pixelSize: 18
                Layout.fillWidth: true
                Layout.rightMargin: 100
                onActiveFocusChanged: {
                    if (focus) {
                        keyboardCP.set_active_tf(this)
                    }
                }
            }

            FramLabel {
                text: "Old Password"
                font.pixelSize: 18
                Layout.leftMargin: 100
            }
            TextField {
                id: tfOldPw
                placeholderText: "Old Password"
                font.pixelSize: 18
                Layout.fillWidth: true
                Layout.rightMargin: 100
                echoMode: TextInput.Password
                onActiveFocusChanged: {
                    if (focus) {
                        keyboardCP.set_active_tf(this)
                    }
                }
            }

            FramLabel {
                text: "New Password"
                font.pixelSize: 18
                Layout.leftMargin: 100
            }
            TextField {
                id: tfNewPw
                placeholderText: "New Password"
                font.pixelSize: 18
                Layout.fillWidth: true
                Layout.rightMargin: 100
                echoMode: TextInput.Password
                onActiveFocusChanged: {
                    if (focus) {
                        keyboardCP.set_active_tf(this)
                    }
                }
                Component.onCompleted: {
                    keyboardCP.set_active_tf(this)
                    forceActiveFocus()
                }
            }

            FramLabel {
                text: "Repeat New Password"
                font.pixelSize: 18
                Layout.leftMargin: 100
            }
            TextField {
                id: tfRepeatNewPw
                placeholderText: "Repeat Password"
                font.pixelSize: 18
                Layout.fillWidth: true
                Layout.rightMargin: 100
                echoMode: TextInput.Password
                onActiveFocusChanged: {
                    if (focus) {
                        keyboardCP.set_active_tf(this)
                    }
                }
            }

            Rectangle {
                Layout.columnSpan: 2
                Layout.preferredHeight: 300
                Layout.fillWidth: true
                FramScalingKeyboard {
                    id: keyboardCP
                    anchors.fill: parent
                    hide_ok: true // hide OK button
                    enable_audio: ObserverSettings.enableAudio
                    Component.onCompleted: {
                        hide_tf()
                        setkeyboardlowercase()
                        password_mode(true)
                    }

                    onKbTextChanged: {

                        // TODO Filter Table
                        // catchCategory.filter = kbtext;
                    }
                }
            }

            FramButton {
                Layout.preferredHeight: 40
                Layout.alignment: Qt.AlignHCenter
                text: "Cancel"
                Layout.bottomMargin: 20
                onClicked: dlg.reject()
            }

            FramButton {
                Layout.preferredHeight: 40
                Layout.alignment: Qt.AlignHCenter
                text: "OK"
                enabled: true // TODO passwords entered
                Layout.bottomMargin: 20
                onClicked: {
                    // TODO verify dialog- tell user to change online
                    // TODO verify password match, old pw is OK
                    var valid_new_pw = validate_user_new_pw(tfUsername.text,
                                                            tfOldPw.text,
                                                            tfNewPw.text,
                                                            tfRepeatNewPw.text)
                    if (valid_new_pw === true) {
                        tfNewPw.text = "";
                        tfRepeatNewPw.text = "";
                        dlg.accept()
                    } else {
                        dlgPwError.message = valid_new_pw
                        dlgPwError.open()
                    }
                }
            }
        }
        FramNoteDialog {
            id: dlgPwError
            message: "Password error, not changed."
            wrapMode: Text.WordWrap
        }

        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
}

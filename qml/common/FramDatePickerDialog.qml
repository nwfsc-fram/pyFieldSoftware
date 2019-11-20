import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.2
// import QtQuick.Extras 1.4  // For Tumbler

import "../common"

Dialog {
    id: dlgDatePicker
    width: 1000
    height: 700
    title: "Choose Date"
    property string message: ""
    property string accepted_action: ""
    property var locale: Qt.locale()
    property date currentDateTime: new Date()
    property date selectedDateTime: new Date()
    property bool date_only: false
    property alias enable_audio: scalingNumPad.enable_audio

    signal dateAccepted(var selected_date)

    onAccepted: {
        // Warning, screens should use onDateAccepted to get the date that is picked
        var final_datetime = new Date(calendar.selectedDate);
        if (!date_only){
            var new_datetime = Date.fromLocaleTimeString(locale, tfHour.text + ":" + tfMins.text, 'H:m');
            final_datetime.setHours(new_datetime.getHours());
            final_datetime.setMinutes(new_datetime.getMinutes());
        }
        selectedDateTime = final_datetime;

        // Done, now emit
        dateAccepted(selectedDateTime);
    }

    onVisibleChanged: {
        if (visible) {
            var hrs = selectedDateTime.getHours();
            var mins = selectedDateTime.getMinutes();
            tfHour.text = (hrs < 10 && hrs > 0) ? "0" + hrs : hrs;
            tfMins.text = (mins < 10 && hrs > 0) ? "0" + mins : mins;
            tfHour.forceActiveFocus();
            tfMins.selectAll();
        }
    }

    contentItem: ColumnLayout {
        // Calendar on left, taking up 50% of width, numpad on right taking the balance.
        id: contentLayout
        RowLayout {
            Rectangle {
                id: rectCalendar
                color: "#eeeeee"
                // Rectangular Calendar, slightly wider than tall
                Layout.preferredHeight: contentLayout.width * 0.5
                Layout.preferredWidth: contentLayout.width * 0.5
                Calendar {
                    id: calendar
                    anchors.fill: parent
                }
            }
            Rectangle {
                id: rectTime
                Layout.leftMargin: 40
                Layout.alignment: Qt.AlignTop | Qt.AlignRight

                Layout.preferredWidth: contentLayout.width * 0.5
                ColumnLayout {
                    id: colTime
                    spacing: 20 // Between tumbler label and left-most cylinder
                    visible: !dlgDatePicker.date_only
                    RowLayout {
                        Layout.alignment: Qt.AlignCenter
                        Layout.preferredHeight: 100
                        FramLabel {
                            text: message + " (Local 24h)"
                            font.pixelSize: 20
                            Layout.alignment: Qt.AlignVCenter
                        }
                        FramTextField {
                            id: tfHour
                            Layout.preferredWidth: 50
                            font.pixelSize: 20
                            Layout.alignment: Qt.AlignVCenter
                            onActiveFocusChanged: {
                                if(focus) {                                    
                                    scalingNumPad.directConnectTf(tfHour);
                                    labelTimeEntryStatus.text = "Enter hour 0 - 23."
                                    scalingNumPad.entering_hour = true;
                                    selectAll();
                                }
                            }
                            onTextChanged: {
                                if (parseInt(text) > 23) {
                                    text = "23"
                                }
                                if (text.length >1) {
                                    tfMins.forceActiveFocus();
                                    tfMins.selectAll();
                                }

                            }
                        }
                        FramLabel {
                            text: ":"
                            font.pixelSize: 25
                            Layout.alignment: Qt.AlignVCenter
                        }

                        FramTextField {
                            id: tfMins
                            Layout.preferredWidth: 50
                            font.pixelSize: 20
                            Layout.alignment: Qt.AlignVCenter
                            onActiveFocusChanged: {
                                if(focus) {
                                    scalingNumPad.directConnectTf(tfMins);
                                    scalingNumPad.entering_hour = false;
                                    labelTimeEntryStatus.text = "Enter minute 0 - 59."
                                    text = "";
                                }
                            }
                            onTextChanged: {
                                if (parseInt(text) > 59) {
                                    text = "59"
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignCenter
                        Layout.preferredHeight: 50
                        FramLabel {
                            id: labelTimeEntryStatus
                            text: "Enter hour 0 - 23."
                            font.pixelSize: 18
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: rectTime.width
                        Layout.preferredHeight: 400
                        FramScalingNumPad {
                            id: scalingNumPad
                            anchors.fill: parent
                            direct_connect: true
                            time_mode: true
                            leading_zero_mode: true
                            onNumpadok: { // ":" not OK, for time_mode
                                if (entering_hour) {
                                    tfMins.forceActiveFocus();
                                    tfMins.selectAll();
                                }
                            }                            
                        }
                    }
                }
            }
        }
        RowLayout {
            id: okayCancelButtons
            Layout.alignment: Qt.AlignCenter | Qt.AlignBottom
            Layout.preferredHeight: 100
            height: 100
            spacing: 20 // Give a gloved hand space between Cancel and OK            
            FramButton {
                id: btnCancel
                text: "Cancel"
                onClicked: {
                    dlgDatePicker.reject();
                }
            } // btnCancel
            FramButton {
                id: btnOkay
                text: "Okay"
                function validate_and_quit() {
                    if (parseInt(tfHour.text) < 24 && parseInt(tfMins.text) < 60) {
                        dlgDatePicker.accept();
                    } else {
                        labelTimeEntryStatus.text = "Enter a valid time."
                    }
                }
                onClicked: {
                    validate_and_quit();
                }
            } // btnOkay
        }

        Keys.onEnterPressed: dlgDatePicker.accept()
        Keys.onReturnPressed: dlgDatePicker.accept()
        Keys.onEscapePressed: dlgDatePicker.accept()
        Keys.onBackPressed: dlgDatePicker.accept() // especially necessary on Android
    }
}

// Photos & Alphanumeric Tags Tab
// Photos not yet implemented
// Alphanumeric tags are existing (externally attached) tags and Observer tags.

import QtQuick 2.6
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2

import "../common"

Item {
    id: itemPhotoET
    Layout.fillWidth: true
    Layout.margins: 50
    property bool enable_entry: true
    property bool keyboardVisible: false
    property int maxExistingTags: 3  // How many external tags can be added to a biospecimen?

    property var currentID: null

    signal readyNextTab  // this tab is complete, move to next tab

    property var pending_protocols_array: null
    // Function remaining_protcol_count called by BiospecimensScreen.
    function remaining_protocol_count() {
        return pending_protocols_array ? pending_protocols_array.length : 0;
    }

    onCurrentIDChanged: {
        console.debug("Biospecies Item ID Changed to " + currentID);
        if (currentID) {
            appstate.catches.biospecimens.loadExistingTags(); // Existing Tags and Observer Tags
            // Load Observer tag into text box explicitly.
            tfObserverTag.text = appstate.catches.biospecimens.get_barcode_value_by_type('9')
            console.debug("Set Observer Tag to '" + tfObserverTag.text + "'.");
            check_pending_protocols();
        } else {
            appstate.catches.biospecimens.clearTags();
        }
    }

    Connections {
        target: screenBio
        onAddEntry: {
            check_pending_protocols();
        }
        //onModifyEntryClicked: {
        //    console.debug("Biospecimens's modify button is checked? " + screenBio.modifyEntryChecked);
        //    check_pending_protocols();
        //}
    }

    function existing_tag_is_populated() {
        var is_populated = appstate.catches.biospecimens.ExistingTagsModel.is_item_in_model('dissection_type', '8');
        return is_populated;
    }

    function observer_tag_is_populated() {
        var is_populated = (tfObserverTag.text.length > 0);
        return is_populated;
    }

    function check_pending_protocols() {  // For this screen
        // Re-calculate pending protocols from the initial list required for this screen
        pending_protocols_array = appstate.catches.species.requiredProtocolsTags;
        console.debug("Protocols pending at start: " + pending_protocols_array);

    	var existing_tag_required = (pending_protocols_array.indexOf('ET') !== -1);
        var existing_tag_populated = existing_tag_is_populated();
        if (existing_tag_required) {
            if (existing_tag_populated) {
                var pending_pos = pending_protocols_array.indexOf('ET');
                pending_protocols_array.splice(pending_pos, 1);
                console.log('ET is specified, ET protocol removed from required protocol list.');
            } else {
                console.debug("ET required but not yet specified.")
            }
        }

        // Observer Tag protocol is abbreviated 'OT', but there's also a deprecated version ('T'). Test for both.
    	var observer_tag_required = (pending_protocols_array.indexOf('OT') !== -1);
    	var observer_tag_required_deprecated_version = (pending_protocols_array.indexOf('T') != -1);
        var observer_tag_populated = observer_tag_is_populated();
        if (observer_tag_required || observer_tag_required_deprecated_version) {
            if (observer_tag_populated) {
                var protocol_abbreviation = observer_tag_required ? 'OT' : 'T';
                var pending_pos = pending_protocols_array.indexOf(protocol_abbreviation);
                pending_protocols_array.splice(pending_pos, 1);
                console.log('OT is specified, OT protocol removed from required protocol list.');
            } else {
                console.debug("OT required but not yet specified.")
            }
        }

        // NOT YET IMPLEMENTED: Photo. Eventually it will be be handled in this tab.
        // If photo protocol required, remove to bring outstanding protocols down, with a log message.
        var photo_tag_required = (pending_protocols_array.indexOf('P') !== -1);
        if (photo_tag_required) {
            var pending_pos = pending_protocols_array.indexOf('P');
            pending_protocols_array.splice(pending_pos, 1);
            console.log('P is required, but not yet supported in OPTECS. Removed from required protocol list.');
        }

        check_label_highlighting(existing_tag_required, existing_tag_populated,
                observer_tag_required || observer_tag_required_deprecated_version, observer_tag_populated);

        if (pending_protocols_array.length > 0) {
            console.log('Tag protocols still pending after check: ' + pending_protocols_array)
        } else {
            console.log('All required tag protocols complete!')
            itemPhotoET.readyNextTab();
        }
        return pending_protocols_array.length
    }

    function check_label_highlighting(
            existing_tag_in_protocols, existing_tag_populated,
            observer_tag_in_protocols, observer_tag_populated) {

        //console.debug("ET: Req'd="+ existing_tag_in_protocols + ", Spec'd=" + existing_tag_populated);
        //console.debug("OT: Req'd="+ observer_tag_in_protocols + ", Spec'd=" + observer_tag_populated);
        //console.debug("screenBio.modifyEntryChecked=" + screenBio.modifyEntryChecked);

        // Highlight or un-highlight labels depending on:
        // - Modify enabled or not.
        // - Protocol specified for this species or not.
        // - Field has been filled in or not
        var highlightExistingTags = false;
        var highlightObserverTag = false;
        if (screenBio.modifyEntryChecked) {
            highlightExistingTags = existing_tag_in_protocols && !existing_tag_populated;
            highlightObserverTag = observer_tag_in_protocols && !observer_tag_populated;
        }
        console.debug("Label highlighting: Existing=" + highlightExistingTags + ", Observer=" + highlightObserverTag);
        lblExistingTags.highlight(highlightExistingTags);
        lblObserverTag.highlight(highlightObserverTag);
    }

    GridLayout {
        columns: 2
        columnSpacing: 50
        ColumnLayout {
            Layout.alignment: Qt.AlignTop
            FramLabelHighlightCapable {
                id: lblExistingTags

                Layout.topMargin: 50
                font.pixelSize: 20

                text: "Existing Tag(s):"
            }
            FramButton {
                id: buttonAddExistingTag
                Layout.preferredWidth: 250
                Layout.preferredHeight: 50
                text: "Add Existing Tag"
                enabled: enable_entry
                onClicked: {
                    console.debug("++++++ EXISTING TAG ++++++");
                    if (appstate.catches.biospecimens.ExistingTagsModel.count >= maxExistingTags) {
                        dlgTooManyExistingTags.open()
                        return;
                    }
                    appstate.catches.biospecimens.add_existing_tag("");
                }
            }

            ListView {
                id: lvExistingTags
                anchors.top: buttonAddExistingTag.bottom
                anchors.topMargin: 20
                anchors.left: buttonAddExistingTag.left
                //anchors.right: parent.right
                anchors.bottom: parent.bottom
                Layout.topMargin: 10
                Layout.preferredHeight: 500
                spacing: 20

                model: appstate.catches.biospecimens.ExistingTagsModel

                delegate: RowLayout {
                    Layout.preferredHeight: 300
                    ColumnLayout {
                        spacing: 5
                        FramButton {
                            text: "-"
                            fontsize: 25
                            Layout.preferredHeight: 40
                            Layout.preferredWidth: 40
                            enabled: enable_entry
                            onClicked: {
                                console.debug("------ EXISTING TAG ------");
                                appstate.catches.biospecimens.delete_existing_tag(index);
                                appstate.catches.biospecimens.update_tags_str(); // update model
                                check_pending_protocols();
                            }
                        }
                    }
                    TextField {
                        text: band
                        font.pixelSize: 18
                        placeholderText: "Existing Tag Number"
                        Layout.preferredHeight: 50
                        Layout.preferredWidth: 200
                        enabled: enable_entry
                        onActiveFocusChanged: {
                            if (focus) {
                                keyboardBarcodes.connected_tf = this;
                                keyboardBarcodes.open();
                                focus=false;
                            }
                        }
                        onEditingFinished: {
                            if (text.length > 15) {
                                dlgBarcodeMoreThan15Digits.attemptedBarcodeValue = text;
                                dlgBarcodeMoreThan15Digits.open();
                                text = '';
                                return;
                            }
                            console.debug("Current existing tags index = " + index);
                            appstate.catches.biospecimens.set_existing_tag(index, text);
                            appstate.catches.biospecimens.update_tags_str(); // update model
                        }
                    }
                }
            }
        }
        ColumnLayout {
             Layout.alignment: Qt.AlignTop
             FramLabelHighlightCapable {
                id: lblObserverTag

                Layout.topMargin: 50
                font.pixelSize: 20

                text: "Observer Tag:"
             }
             TextField {
                id: tfObserverTag

                Layout.preferredHeight: 50
                Layout.preferredWidth: 250

                text: ""    // Set in onCurrentIDChanged signal
                font.pixelSize: 18
                placeholderText: "Observer Tag Value"
                enabled: enable_entry
                onActiveFocusChanged: {
                    if (focus) {
                        keyboardBarcodes.connected_tf = this;
                        keyboardBarcodes.open();
                        focus=false;
                    }
                }
                onEditingFinished: {
                    if (text.length > 15) {
                        dlgBarcodeMoreThan15Digits.attemptedBarcodeValue = text;
                        dlgBarcodeMoreThan15Digits.open()
                        text = '';
                        return;
                    } else if (text.length > 0) {
                        appstate.catches.biospecimens.save_dissection_type('9', text);  // Create or over-write.
                    } else {
                        var original_value = appstate.catches.biospecimens.get_barcode_value_by_type('9')
                        appstate.catches.biospecimens.deleteExistingDissectionByBarcodeTypeAndValue('9', original_value);
                    }
                    appstate.catches.biospecimens.update_tags_str(); // update model
                    check_pending_protocols();
                }
            }
        }
    }

    ObserverKeyboardDialog {
        id: keyboardBarcodes
        max_digits: 6
        placeholderText: "Barcode Value"

        onValueAccepted: {
            // console.log("Got value "+ accepted_value);
            check_pending_protocols();
        }
    }
    FramNoteDialog {
        id: dlgTooManyExistingTags
        message: "At most " + maxExistingTags + " existing tags\nare supported."
    }
    FramNoteDialog {
        id: dlgBarcodeMoreThan15Digits
        property string barcodeTypeDescription;
        property string attemptedBarcodeValue;
        message: "Barcode longer than 15 digits." +
            "\nAttempted barcode value of " +
            "\n" + attemptedBarcodeValue + "\nhas " + attemptedBarcodeValue.length + " digits."
    }
}
